import logging

from nanexus.db import SessionLocal
from nanexus.indexing import EmbeddingQueue, persist_embedding
from nanexus.queue import AIQueue

logger = logging.getLogger("embedding_worker")


def process_once(queue=None, session_factory=SessionLocal):
    queue = queue or EmbeddingQueue()
    job = queue.dequeue()
    if job is None:
        return False
    try:
        with session_factory() as db:
            persist_embedding(db, job)
    except Exception as error:
        logger.exception("embedding index failed subject=%s", job.subject_id)
        queue.retry_or_dead_letter(job, type(error).__name__)
    finally:
        queue.acknowledge(job)
    return True


def main():
    logging.basicConfig(level=logging.INFO)
    health = AIQueue()
    queue = EmbeddingQueue()
    recovered = queue.recover_in_flight()
    if recovered:
        logger.warning("recovered %d in-flight embedding jobs", recovered)
    while True:
        health.heartbeat("embedding")
        process_once(queue)


if __name__ == "__main__":
    main()
