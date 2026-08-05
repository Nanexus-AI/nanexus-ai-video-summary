#!/usr/bin/env python3
"""Re-queue events for AI processing (useful after switching stub → openclip)."""

from __future__ import annotations

import argparse

from sqlalchemy import select

from nanexus.db import SessionLocal, init_db
from nanexus.models import Event
from nanexus.queue import AIJob, AIQueue


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", default=None, help="only requeue events with this status")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    init_db()
    queue = AIQueue()
    db = SessionLocal()
    try:
        stmt = select(Event).order_by(Event.id.asc()).limit(args.limit)
        if args.status:
            stmt = stmt.where(Event.status == args.status)
        events = list(db.scalars(stmt).all())
        for event in events:
            queue.unmark_processed(event.frigate_id)
            event.status = "queued"
            db.add(event)
            db.commit()
            queue.mark_processed(event.frigate_id)
            queue.enqueue(
                AIJob(
                    event_id=event.id,
                    frigate_id=event.frigate_id,
                    snapshot_uri=event.snapshot_uri,
                )
            )
            print(f"requeued id={event.id} frigate_id={event.frigate_id}")
        print(f"done: {len(events)} events")
    finally:
        db.close()


if __name__ == "__main__":
    main()
