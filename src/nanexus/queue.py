from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID

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


@dataclass
class SummaryJob:
    summary_date: str  # YYYY-MM-DD
    camera: str | None = None
    mode: str | None = None
    summary_id: str | None = None
    timezone: str = "UTC"
    site_id: str = "default"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, payload: str | bytes) -> SummaryJob:
        data = json.loads(payload)
        return cls(**data)


@dataclass
class ChatQueueJob:
    job_id: str

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, payload: str | bytes) -> ChatQueueJob:
        data = json.loads(payload)
        UUID(data["job_id"])
        return cls(**data)


class AIQueue:
    def __init__(self, client: redis.Redis | None = None) -> None:
        settings = get_settings()
        self._settings = settings
        self._client = client or redis.Redis.from_url(
            settings.redis_url, decode_responses=True
        )

    def enqueue(self, job: AIJob) -> None:
        self._client.lpush(self._settings.ai_queue_key, job.to_json())

    def dequeue(self, timeout: int = 5) -> AIJob | None:
        item = self._client.brpop(self._settings.ai_queue_key, timeout=timeout)
        if not item:
            return None
        _, payload = item
        return AIJob.from_json(payload)

    def enqueue_summary(self, job: SummaryJob) -> None:
        self._client.lpush(self._settings.summary_queue_key, job.to_json())

    def dequeue_summary(self, timeout: int = 5) -> SummaryJob | None:
        payload = self._client.brpoplpush(
            self._settings.summary_queue_key,
            f"{self._settings.summary_queue_key}:processing",
            timeout=timeout,
        )
        if not payload:
            return None
        return SummaryJob.from_json(payload)

    def acknowledge_summary(self, job: SummaryJob) -> None:
        key = f"{self._settings.summary_queue_key}:processing"
        self._acknowledge(key, job, SummaryJob.from_json)

    def recover_summaries(self) -> int:
        return self._recover(
            f"{self._settings.summary_queue_key}:processing", self._settings.summary_queue_key
        )

    def enqueue_chat(self, job: ChatQueueJob) -> None:
        self._client.lpush(self._settings.chat_queue_key, job.to_json())

    def dequeue_chat(self, timeout: int = 5) -> ChatQueueJob | None:
        payload = self._client.brpoplpush(
            self._settings.chat_queue_key,
            f"{self._settings.chat_queue_key}:processing",
            timeout=timeout,
        )
        if not payload:
            return None
        return ChatQueueJob.from_json(payload)

    def acknowledge_chat(self, job: ChatQueueJob) -> None:
        key = f"{self._settings.chat_queue_key}:processing"
        self._acknowledge(key, job, ChatQueueJob.from_json)

    def recover_chats(self) -> int:
        return self._recover(
            f"{self._settings.chat_queue_key}:processing", self._settings.chat_queue_key
        )

    def _recover(self, processing_key: str, queue_key: str) -> int:
        recovered = 0
        while self._client.rpoplpush(processing_key, queue_key):
            recovered += 1
        return recovered

    def _acknowledge(self, key: str, job: Any, parser: Any) -> None:
        for payload in self._client.lrange(key, 0, -1):
            if parser(payload) == job:
                serialized = payload.decode() if isinstance(payload, bytes) else payload
                self._client.lrem(key, 1, serialized)
                return

    def mark_processed(self, frigate_id: str) -> bool:
        """Return True if this frigate_id was newly marked (not a duplicate)."""
        return bool(self._client.sadd(self._settings.processed_set_key, frigate_id))

    def unmark_processed(self, frigate_id: str) -> None:
        self._client.srem(self._settings.processed_set_key, frigate_id)

    def mark_summary_done(self, day: str, camera: str | None = None) -> bool:
        key = f"{day}:{camera or '*'}"
        return bool(self._client.sadd(self._settings.summary_done_set_key, key))

    def clear_summary_done(self, day: str, camera: str | None = None) -> None:
        key = f"{day}:{camera or '*'}"
        self._client.srem(self._settings.summary_done_set_key, key)

    def ping(self) -> Any:
        return self._client.ping()

    def heartbeat(self, worker: str) -> None:
        self._client.set(
            f"nanexus:heartbeat:{worker}",
            __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
            ex=self._settings.worker_heartbeat_ttl_seconds,
        )
