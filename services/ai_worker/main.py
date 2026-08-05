from __future__ import annotations

import hashlib
import logging
import signal
import sys
import time
from typing import Any

from nanexus.config import get_settings
from nanexus.db import SessionLocal, init_db
from nanexus.models import Event
from nanexus.queue import AIJob, AIQueue

logging.basicConfig(
    level=get_settings().log_level,
    format="%(asctime)s %(levelname)s [ai_worker] %(message)s",
)
logger = logging.getLogger("ai_worker")

_running = True


def _handle_signal(signum: int, frame: Any) -> None:
    global _running
    logger.info("signal %s received, shutting down", signum)
    _running = False


def stub_caption(event: Event) -> str:
    where = event.camera.replace("_", " ")
    detail = event.sub_label or event.label
    return f"Stub vision: {detail} near {where}"


def stub_embedding(frigate_id: str, dim: int) -> list[float]:
    """Deterministic pseudo-embedding for M0 (replace with OpenCLIP later)."""
    digest = hashlib.sha256(frigate_id.encode("utf-8")).digest()
    values: list[float] = []
    while len(values) < dim:
        for b in digest:
            values.append((b / 255.0) * 2 - 1)
            if len(values) >= dim:
                break
        digest = hashlib.sha256(digest).digest()
    # L2 normalize lightly
    norm = sum(v * v for v in values) ** 0.5 or 1.0
    return [v / norm for v in values]


def process_job(job: AIJob) -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        event = db.get(Event, job.event_id)
        if not event:
            logger.warning("event %s not found, skipping", job.event_id)
            return

        event.status = "processing"
        db.add(event)
        db.commit()

        # M0 stub pipeline: snapshot URI is recorded but not downloaded yet.
        caption = stub_caption(event)
        embedding = stub_embedding(event.frigate_id, settings.embedding_dim)
        tags = [event.label]
        if event.sub_label:
            tags.append(str(event.sub_label))

        event.caption = caption
        event.embedding = embedding
        event.tags = tags
        event.status = "done"
        db.add(event)
        db.commit()
        logger.info(
            "processed event id=%s frigate_id=%s caption=%r",
            event.id,
            event.frigate_id,
            caption,
        )
    except Exception:
        db.rollback()
        event = db.get(Event, job.event_id)
        if event:
            event.status = "failed"
            db.add(event)
            db.commit()
        logger.exception("failed job event_id=%s", job.event_id)
    finally:
        db.close()


def main() -> None:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    init_db()
    queue = AIQueue()
    logger.info("AI worker started; waiting on queue")

    while _running:
        job = queue.dequeue(timeout=2)
        if job is None:
            continue
        process_job(job)

    logger.info("stopped")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("fatal error")
        sys.exit(1)
