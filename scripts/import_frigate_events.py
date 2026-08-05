#!/usr/bin/env python3
"""Import recent events from Frigate HTTP API into DB + AI queue."""

from __future__ import annotations

import argparse
import logging

import httpx
from sqlalchemy import select

from nanexus.config import get_settings
from nanexus.db import SessionLocal, init_db
from nanexus.frigate import parse_frigate_event
from nanexus.models import Event
from nanexus.queue import AIJob, AIQueue

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("import_frigate")


def fetch_events(base_url: str, limit: int, camera: str | None) -> list[dict]:
    params: dict = {"limit": limit, "has_snapshot": 1}
    if camera:
        params["cameras"] = camera
    url = f"{base_url.rstrip('/')}/api/events"
    headers = {}
    token = get_settings().frigate_token
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=30.0, headers=headers) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    if not isinstance(data, list):
        raise RuntimeError(f"unexpected events response: {type(data)}")
    return data


def upsert_and_enqueue(raw: dict, queue: AIQueue, force: bool) -> str:
    parsed = parse_frigate_event({"type": "end", "after": raw})
    if not parsed:
        return "skipped-unparsed"

    db = SessionLocal()
    try:
        event = db.scalar(select(Event).where(Event.frigate_id == parsed["frigate_id"]))
        if event is None:
            event = Event(
                frigate_id=parsed["frigate_id"],
                camera=parsed["camera"],
                label=parsed["label"],
                sub_label=parsed.get("sub_label"),
                start_time=parsed["start_time"],
                end_time=parsed.get("end_time"),
                snapshot_uri=parsed.get("snapshot_uri"),
                clip_uri=parsed.get("clip_uri"),
                status="pending",
                raw_payload=parsed.get("raw_payload"),
            )
            db.add(event)
        else:
            event.camera = parsed["camera"]
            event.label = parsed["label"]
            event.sub_label = parsed.get("sub_label")
            event.start_time = parsed["start_time"]
            event.end_time = parsed.get("end_time")
            event.snapshot_uri = parsed.get("snapshot_uri") or event.snapshot_uri
            event.clip_uri = parsed.get("clip_uri") or event.clip_uri
            event.raw_payload = parsed.get("raw_payload")

        db.commit()
        db.refresh(event)

        should_enqueue = force or event.status in ("pending", "failed")
        if not should_enqueue:
            return f"exists id={event.id} status={event.status}"

        queue.unmark_processed(event.frigate_id)
        queue.mark_processed(event.frigate_id)
        event.status = "queued"
        db.add(event)
        db.commit()
        queue.enqueue(
            AIJob(
                event_id=event.id,
                frigate_id=event.frigate_id,
                snapshot_uri=event.snapshot_uri,
            )
        )
        return f"enqueued id={event.id}"
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Frigate API events")
    parser.add_argument("-n", "--limit", type=int, default=10)
    parser.add_argument("--camera", default=None)
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-enqueue even if already processed",
    )
    args = parser.parse_args()

    settings = get_settings()
    init_db()
    queue = AIQueue()
    events = fetch_events(settings.frigate_base_url, args.limit, args.camera)
    logger.info("fetched %s events from %s", len(events), settings.frigate_base_url)
    for raw in events:
        result = upsert_and_enqueue(raw, queue, force=args.force)
        logger.info(
            "%s camera=%s label=%s -> %s",
            raw.get("id"),
            raw.get("camera"),
            raw.get("label"),
            result,
        )


if __name__ == "__main__":
    main()
