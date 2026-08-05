from __future__ import annotations

import logging
import signal
import sys
from typing import Any

from nanexus.config import get_settings
from nanexus.db import SessionLocal, init_db
from nanexus.media import fetch_snapshot_bytes
from nanexus.models import Event
from nanexus.queue import AIJob, AIQueue
from nanexus.vision import get_vision_pipeline

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


def process_job(job: AIJob) -> None:
    db = SessionLocal()
    pipeline = get_vision_pipeline()
    try:
        event = db.get(Event, job.event_id)
        if not event:
            logger.warning("event %s not found, skipping", job.event_id)
            return

        event.status = "processing"
        db.add(event)
        db.commit()

        uri = job.snapshot_uri or event.snapshot_uri
        image_bytes = fetch_snapshot_bytes(uri)
        result = pipeline.analyze_image(
            image_bytes,
            camera=event.camera,
            label=event.label,
            sub_label=event.sub_label,
        )

        event.caption = result.caption
        event.embedding = result.embedding
        event.tags = result.tags
        event.status = "done"
        db.add(event)
        db.commit()
        logger.info(
            "processed event id=%s frigate_id=%s model=%s caption=%r",
            event.id,
            event.frigate_id,
            result.model,
            result.caption,
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

    settings = get_settings()
    init_db()
    pipeline = get_vision_pipeline()
    if pipeline.mode != "stub":
        logger.info("preloading vision model (ai_mode=%s)...", settings.ai_mode)
        pipeline.ensure_loaded()
    else:
        logger.info("AI worker in stub mode")

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
