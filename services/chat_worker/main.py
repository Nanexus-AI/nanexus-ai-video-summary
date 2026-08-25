from __future__ import annotations

import logging
import signal
from typing import Any
from uuid import UUID

from nanexus.chat_v1 import process_chat_job
from nanexus.config import get_settings
from nanexus.db import SessionLocal, init_db
from nanexus.models import ChatJob
from nanexus.queue import AIQueue

logging.basicConfig(level=get_settings().log_level)
logger = logging.getLogger("chat_worker")
_running = True


def _stop(_signum: int, _frame: Any) -> None:
    global _running
    _running = False


def process(job_id: str) -> None:
    db = SessionLocal()
    job = None
    try:
        job = db.get(ChatJob, UUID(job_id))
        if job is None or job.status == "ready":
            return
        process_chat_job(db, job)
    except Exception:
        db.rollback()
        if job is not None:
            job.status = "failed"
            job.error_code = "worker_failure"
            db.add(job)
            db.commit()
        logger.exception("chat job failed id=%s", job_id)
    finally:
        db.close()


def main() -> None:
    init_db()
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    queue = AIQueue()
    recovered = queue.recover_chats()
    if recovered:
        logger.warning("recovered %d in-flight chat jobs", recovered)
    while _running:
        queue.heartbeat("chat")
        item = queue.dequeue_chat(timeout=2)
        if item:
            try:
                process(item.job_id)
            finally:
                queue.acknowledge_chat(item)


if __name__ == "__main__":
    main()
