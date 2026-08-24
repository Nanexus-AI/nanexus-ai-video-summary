"""Application-owned, retryable embedding indexing pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import UUID

import redis
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nanexus.config import get_settings
from nanexus.models import EmbeddingRecord


@dataclass(frozen=True)
class EmbeddingJob:
    subject_type: str
    subject_id: str
    subject_revision: str
    source_claim_id: str
    source_job_id: str
    evidence_ids: list[str]
    modality: str
    vector: list[float]
    provider: str
    model: str
    model_version: str
    content_hash: str
    camera: str | None = None
    site: str | None = None
    occurred_at: str | None = None
    labels: list[str] | None = None
    attempt: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, payload: str | bytes) -> EmbeddingJob:
        return cls(**json.loads(payload))


class EmbeddingQueue:
    def __init__(self, client: redis.Redis | None = None):
        self.settings = get_settings()
        self.client = client or redis.Redis.from_url(self.settings.redis_url, decode_responses=True)

    def enqueue(self, job: EmbeddingJob):
        self.client.lpush(self.settings.embedding_queue_key, job.to_json())

    def dequeue(self, timeout: int = 5):
        item = self.client.brpop(self.settings.embedding_queue_key, timeout=timeout)
        return EmbeddingJob.from_json(item[1]) if item else None

    def retry_or_dead_letter(self, job: EmbeddingJob, reason: str) -> bool:
        next_job = EmbeddingJob(**{**asdict(job), "attempt": job.attempt + 1})
        if next_job.attempt >= self.settings.embedding_max_attempts:
            self.client.lpush(
                self.settings.embedding_dlq_key,
                json.dumps({"job": asdict(next_job), "reason": reason}),
            )
            return False
        self.enqueue(next_job)
        return True


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def persist_embedding(db: Session, job: EmbeddingJob) -> EmbeddingRecord:
    settings = get_settings()
    if len(job.vector) != settings.embedding_dim:
        raise ValueError(f"embedding dimensions {len(job.vector)} != {settings.embedding_dim}")
    existing = db.scalar(
        select(EmbeddingRecord).where(
            EmbeddingRecord.subject_type == job.subject_type,
            EmbeddingRecord.subject_id == UUID(job.subject_id),
            EmbeddingRecord.subject_revision == job.subject_revision,
            EmbeddingRecord.modality == job.modality,
            EmbeddingRecord.provider == job.provider,
            EmbeddingRecord.model == job.model,
            EmbeddingRecord.model_version == job.model_version,
            EmbeddingRecord.content_hash == job.content_hash,
        )
    )
    if existing:
        return existing
    record = EmbeddingRecord(
        subject_type=job.subject_type,
        subject_id=UUID(job.subject_id),
        subject_revision=job.subject_revision,
        modality=job.modality,
        vector=job.vector,
        dimensions=len(job.vector),
        provider=job.provider,
        model=job.model,
        model_version=job.model_version,
        source_claim_id=UUID(job.source_claim_id),
        source_job_id=UUID(job.source_job_id),
        content_hash=job.content_hash,
        camera=job.camera,
        site=job.site,
        labels=job.labels or [],
        occurred_at=datetime.fromisoformat(job.occurred_at) if job.occurred_at else None,
        evidence_ids=job.evidence_ids,
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return db.scalar(
            select(EmbeddingRecord).where(
                EmbeddingRecord.source_claim_id == UUID(job.source_claim_id),
                EmbeddingRecord.model_version == job.model_version,
            )
        )
    db.refresh(record)
    return record


def activate_model(db: Session, *, model: str, model_version: str, dry_run: bool = False) -> int:
    count = len(
        list(
            db.scalars(
                select(EmbeddingRecord.id).where(
                    EmbeddingRecord.model == model, EmbeddingRecord.model_version == model_version
                )
            )
        )
    )
    if dry_run or count == 0:
        return count
    db.execute(
        update(EmbeddingRecord)
        .where(
            EmbeddingRecord.model == model,
            EmbeddingRecord.model_version != model_version,
            EmbeddingRecord.superseded_at.is_(None),
        )
        .values(superseded_at=datetime.now(UTC))
    )
    db.commit()
    return count
