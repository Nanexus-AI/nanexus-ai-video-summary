import json
from pathlib import Path

from nanexus.config import get_settings
from nanexus.indexing import EmbeddingJob, EmbeddingQueue


class FakeRedis:
    def __init__(self):
        self.lists = {}

    def lpush(self, key, value):
        self.lists.setdefault(key, []).insert(0, value)

    def brpop(self, key, timeout=0):
        values = self.lists.get(key, [])
        return (key, values.pop()) if values else None


def job(attempt=0):
    return EmbeddingJob(
        "review_item",
        "00000000-0000-0000-0000-000000000001",
        "r1",
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003",
        [],
        "image",
        [0.0] * 512,
        "p",
        "m",
        "v",
        "hash",
        attempt=attempt,
    )


def test_embedding_queue_retries_then_dead_letters(monkeypatch):
    monkeypatch.setenv("EMBEDDING_MAX_ATTEMPTS", "2")
    get_settings.cache_clear()
    redis = FakeRedis()
    queue = EmbeddingQueue(redis)
    assert queue.retry_or_dead_letter(job(), "database") is True
    retried = queue.dequeue(timeout=0)
    assert retried.attempt == 1
    assert queue.retry_or_dead_letter(retried, "database") is False
    payload = json.loads(redis.lists[queue.settings.embedding_dlq_key][0])
    assert payload["reason"] == "database" and payload["job"]["attempt"] == 2
    get_settings.cache_clear()


def test_migration_has_dimension_vector_and_filter_indexes():
    migration = (
        Path(__file__).parents[1] / "alembic/versions/5a1c001007_embedding_records.py"
    ).read_text()
    assert "Vector(DIMENSIONS)" in migration and "ck_embedding_dimensions" in migration
    assert "hnsw" in migration and "ix_embedding_filters" in migration
