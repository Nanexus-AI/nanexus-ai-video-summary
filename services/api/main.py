from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import Depends, FastAPI, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from nanexus.config import get_settings
from nanexus.db import get_db, init_db
from nanexus.models import DailySummary, Event
from nanexus.queue import AIQueue
from nanexus.schemas import (
    HealthResponse,
    RegenerateSummaryRequest,
    SummaryOut,
    SummaryResponse,
    TimelineResponse,
)
from nanexus.summary import build_rule_summary, fallback_summary_text

settings = get_settings()
app = FastAPI(title="Nanexus AI Video Summary", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    db_ok = False
    redis_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    try:
        redis_ok = bool(AIQueue().ping())
    except Exception:
        redis_ok = False
    status = "ok" if db_ok and redis_ok else "degraded"
    return HealthResponse(status=status, database=db_ok, redis=redis_ok)


@app.get("/timeline", response_model=TimelineResponse)
def timeline(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    camera: str | None = None,
    label: str | None = None,
    db: Session = Depends(get_db),
) -> TimelineResponse:
    filters = []
    if camera:
        filters.append(Event.camera == camera)
    if label:
        filters.append(Event.label == label)

    total = db.scalar(select(func.count()).select_from(Event).where(*filters)) or 0
    items = list(
        db.scalars(
            select(Event)
            .where(*filters)
            .order_by(Event.start_time.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    )
    return TimelineResponse(total=total, items=items)


@app.get("/summary/today", response_model=SummaryResponse)
def summary_today(
    camera: str | None = None,
    db: Session = Depends(get_db),
) -> SummaryResponse:
    today = datetime.now(tz=UTC).date()
    stmt = select(DailySummary).where(DailySummary.summary_date == today)
    if camera is None:
        stmt = stmt.where(DailySummary.camera.is_(None))
    else:
        stmt = stmt.where(DailySummary.camera == camera)
    summary = db.scalar(stmt)
    if summary:
        return SummaryResponse(date=today, summary=SummaryOut.model_validate(summary))
    return SummaryResponse(
        date=today,
        summary=None,
        fallback=fallback_summary_text(db, today),
    )


@app.post("/summary/regenerate", response_model=SummaryOut)
def regenerate_summary(
    body: RegenerateSummaryRequest,
    db: Session = Depends(get_db),
) -> DailySummary:
    day = body.summary_date or datetime.now(tz=UTC).date()
    return build_rule_summary(db, day, camera=body.camera)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "nanexus-ai-video-summary",
        "docs": "/docs",
        "health": "/health",
        "timeline": "/timeline",
        "summary": "/summary/today",
    }
