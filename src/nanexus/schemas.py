from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    frigate_id: str
    camera: str
    label: str
    sub_label: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    snapshot_uri: str | None = None
    clip_uri: str | None = None
    caption: str | None = None
    tags: list[str] | None = None
    status: str


class TimelineResponse(BaseModel):
    total: int
    items: list[EventOut]


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    summary_date: date
    camera: str | None = None
    content: str
    model: str
    event_count: int
    created_at: datetime


class SummaryResponse(BaseModel):
    date: date
    summary: SummaryOut | None = None
    fallback: str | None = Field(
        default=None,
        description="Generated on the fly when no precomputed summary exists",
    )


class HealthResponse(BaseModel):
    status: str
    database: bool
    redis: bool
    ai_mode: str
    summary_mode: str
    chat_mode: str


class RegenerateSummaryRequest(BaseModel):
    summary_date: date | None = None
    camera: str | None = None
    mode: str | None = Field(default=None, description="rule|llm")
    sync: bool = Field(
        default=False,
        description="If true, build inline; otherwise enqueue summary_worker",
    )


class SummaryQueuedResponse(BaseModel):
    status: str
    summary_date: date
    camera: str | None = None
    mode: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)
    camera: str | None = None
    label: str | None = None
    since: datetime | None = None
    until: datetime | None = None


class SearchHit(BaseModel):
    event: EventOut
    score: float | None = None


class SearchResponse(BaseModel):
    query: str
    method: str
    total: int
    items: list[SearchHit]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: int | None = None
    camera: str | None = None
    user_id: str = "local"


class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    method: str
    related_event_ids: list[int]
    related_events: list[EventOut] = Field(default_factory=list)


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    title: str | None = None
    messages: list[dict[str, Any]] | None = None
    related_event_ids: list[int] | None = None
    created_at: datetime
    updated_at: datetime
