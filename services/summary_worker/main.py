from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
import time
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from nanexus.config import get_settings
from nanexus.db import SessionLocal, init_db
from nanexus.event_intelligence_client import EventIntelligenceClient
from nanexus.models import Summary
from nanexus.queue import AIQueue, SummaryJob
from nanexus.summary import (
    aggregate_reviews,
    complete_summary_generation,
    fail_summary_generation,
    local_day_bounds,
    queue_summary_generation,
)

logging.basicConfig(
    level=get_settings().log_level,
    format="%(asctime)s %(levelname)s [summary_worker] %(message)s",
)
logger = logging.getLogger("summary_worker")

_running = True


def _handle_signal(signum: int, frame: Any) -> None:
    global _running
    logger.info("signal %s received, shutting down", signum)
    _running = False


def _now() -> datetime:
    settings = get_settings()
    if settings.summary_timezone.upper() == "UTC":
        return datetime.now(tz=UTC)
    try:
        return datetime.now(tz=ZoneInfo(settings.summary_timezone))
    except Exception:
        logger.warning("invalid SUMMARY_TIMEZONE=%s, using UTC", settings.summary_timezone)
        return datetime.now(tz=UTC)


def process_job(job: SummaryJob) -> None:
    day = date.fromisoformat(job.summary_date)
    db = SessionLocal()
    summary: Summary | None = None
    try:
        summary = db.get(Summary, job.summary_id) if job.summary_id else None
        if summary is None:
            summary = queue_summary_generation(
                db,
                day=day,
                timezone=job.timezone,
                site_id=job.site_id,
                camera_id=job.camera,
                mode=job.mode or get_settings().summary_mode,
            )
        if summary.status == "ready":
            logger.info("summary job %s already ready", summary.id)
            return
        summary.status = "running"
        db.add(summary)
        db.commit()
        start, end = local_day_bounds(day, summary.timezone)

        async def load_reviews():
            settings = get_settings()
            async with EventIntelligenceClient(
                settings.event_intelligence_url,
                settings.event_intelligence_token,
                timeout_seconds=settings.event_intelligence_timeout_seconds,
            ) as client:
                return await client.review_details(occurred_from=start, occurred_to=end)

        details = asyncio.run(load_reviews())
        reviews = aggregate_reviews(details, summary.timezone)
        reviews = [review for review in reviews if start <= review.started_at < end]
        reviews = [review for review in reviews if review.site_id == summary.site_id]
        if summary.camera_id is not None:
            reviews = [review for review in reviews if review.camera_id == summary.camera_id]
        summary = complete_summary_generation(db, summary, reviews)
        logger.info(
            "summary ready id=%s date=%s site=%s camera=%s reviews=%s generator=%s",
            summary.id,
            summary.local_date,
            summary.site_id,
            summary.camera_id,
            summary.structured_content["review_count"],
            summary.structured_content["generation"]["effective_generator"],
        )
    except Exception as error:
        if summary is not None:
            fail_summary_generation(db, summary, error)
        logger.exception("failed summary job %s", job)
    finally:
        db.close()


def run_once(day: date | None = None, camera: str | None = None, mode: str | None = None) -> None:
    target = day or _now().date()
    settings = get_settings()
    process_job(
        SummaryJob(
            summary_date=target.isoformat(),
            camera=camera,
            mode=mode,
            timezone=settings.summary_timezone,
            site_id=settings.summary_site_id,
        )
    )


def maybe_enqueue_scheduled(queue: AIQueue) -> None:
    """At SUMMARY_HOUR:SUMMARY_MINUTE once per day, enqueue today's summary."""
    settings = get_settings()
    now = _now()
    if now.hour != settings.summary_hour or now.minute != settings.summary_minute:
        return

    day = now.date().isoformat()
    if queue.mark_summary_done(day):
        db = SessionLocal()
        try:
            summary = queue_summary_generation(
                db,
                day=now.date(),
                timezone=settings.summary_timezone,
                site_id=settings.summary_site_id,
                camera_id=None,
                mode=settings.summary_mode,
            )
            if summary.status != "ready":
                queue.enqueue_summary(
                    SummaryJob(
                        summary_id=str(summary.id),
                        summary_date=day,
                        camera=None,
                        mode=settings.summary_mode,
                        timezone=settings.summary_timezone,
                        site_id=settings.summary_site_id,
                    )
                )
        except Exception:
            queue.clear_summary_done(day)
            raise
        finally:
            db.close()
        logger.info("scheduled summary enqueued for %s", day)


def main() -> None:
    parser = argparse.ArgumentParser(description="Nanexus summary worker")
    parser.add_argument("--once", action="store_true", help="build one summary and exit")
    parser.add_argument("--date", type=str, default=None, help="YYYY-MM-DD for --once")
    parser.add_argument("--camera", type=str, default=None)
    parser.add_argument("--mode", type=str, default=None, help="rule|llm")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    settings = get_settings()
    init_db()

    if args.once:
        day = date.fromisoformat(args.date) if args.date else None
        run_once(day=day, camera=args.camera, mode=args.mode)
        return

    queue = AIQueue()
    logger.info(
        "summary worker started mode=%s schedule=%02d:%02d %s",
        settings.summary_mode,
        settings.summary_hour,
        settings.summary_minute,
        settings.summary_timezone,
    )

    last_schedule_check = 0.0
    while _running:
        job = queue.dequeue_summary(timeout=2)
        if job is not None:
            process_job(job)

        now_ts = time.time()
        if now_ts - last_schedule_check >= 20:
            maybe_enqueue_scheduled(queue)
            last_schedule_check = now_ts

    logger.info("stopped")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("fatal error")
        sys.exit(1)
