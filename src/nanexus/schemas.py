from __future__ import annotations

from datetime import date, datetime

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


class RegenerateSummaryRequest(BaseModel):
    summary_date: date | None = None
    camera: str | None = None


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
