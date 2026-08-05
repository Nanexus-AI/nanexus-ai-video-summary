from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

import redis

from nanexus.config import get_settings


@dataclass
class AIJob:
    event_id: int
    frigate_id: str
    snapshot_uri: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, payload: str | bytes) -> AIJob:
        data = json.loads(payload)
        return cls(**data)


class AIQueue:
    def __init__(self, client: redis.Redis | None = None) -> None:
        settings = get_settings()
        self._settings = settings
        self._client = client or redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def enqueue(self, job: AIJob) -> None:
        self._client.lpush(self._settings.ai_queue_key, job.to_json())

    def dequeue(self, timeout: int = 5) -> AIJob | None:
        item = self._client.brpop(self._settings.ai_queue_key, timeout=timeout)
        if not item:
            return None
        _, payload = item
        return AIJob.from_json(payload)

    def mark_processed(self, frigate_id: str) -> bool:
        """Return True if this frigate_id was newly marked (not a duplicate)."""
        return bool(self._client.sadd(self._settings.processed_set_key, frigate_id))

    def unmark_processed(self, frigate_id: str) -> None:
        self._client.srem(self._settings.processed_set_key, frigate_id)

    def ping(self) -> Any:
        return self._client.ping()
