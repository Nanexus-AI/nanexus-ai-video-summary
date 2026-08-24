from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from nanexus.config import get_settings
from nanexus.db import Base

_DIM = get_settings().embedding_dim


class Event(Base):
    """Frozen legacy event table; new Search must not read this model."""

    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("frigate_id", name="uq_events_frigate_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    frigate_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    camera: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sub_label: Mapped[str | None] = mapped_column(String(128))
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    snapshot_uri: Mapped[str | None] = mapped_column(Text)
    clip_uri: Mapped[str | None] = mapped_column(Text)
    caption: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    embedding = mapped_column(Vector(_DIM))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class EmbeddingRecord(Base):
    __tablename__ = "embedding_records"
    __table_args__ = (
        CheckConstraint(f"dimensions = {_DIM}", name="ck_embedding_dimensions"),
        UniqueConstraint(
            "subject_type",
            "subject_id",
            "subject_revision",
            "modality",
            "provider",
            "model",
            "model_version",
            "content_hash",
            name="uq_embedding_identity",
        ),
        Index("ix_embedding_subject", "subject_type", "subject_id"),
        Index("ix_embedding_filters", "camera", "site", "occurred_at"),
        Index("ix_embedding_active_model", "model", "model_version", "superseded_at"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    subject_revision: Mapped[str] = mapped_column(String(128), nullable=False)
    modality: Mapped[str] = mapped_column(String(32), nullable=False)
    vector = mapped_column(Vector(_DIM), nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    model_version: Mapped[str] = mapped_column(String(255), nullable=False)
    source_claim_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    source_job_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    camera: Mapped[str | None] = mapped_column(String(255))
    site: Mapped[str | None] = mapped_column(String(255))
    labels: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DailySummary(Base):
    __tablename__ = "daily_summaries"
    __table_args__ = (
        UniqueConstraint("summary_date", "camera", name="uq_daily_summaries_date_camera"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    summary_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    camera: Mapped[str | None] = mapped_column(String(128))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False, default="rule-v0")
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, default="local", index=True)
    title: Mapped[str | None] = mapped_column(String(256))
    messages: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    related_event_ids: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
