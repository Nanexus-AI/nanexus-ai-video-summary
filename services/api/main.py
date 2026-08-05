from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from nanexus.config import get_settings
from nanexus.db import get_db, init_db
from nanexus.media import local_snapshot_path, snapshots_dir
from nanexus.models import DailySummary, Event
from nanexus.queue import AIJob, AIQueue
from nanexus.schemas import (
    EventOut,
    HealthResponse,
    RegenerateSummaryRequest,
    SearchHit,
    SearchRequest,
    SearchResponse,
    SummaryOut,
    SummaryResponse,
    TimelineResponse,
)
from nanexus.search import search_events
from nanexus.summary import build_rule_summary, fallback_summary_text

settings = get_settings()
app = FastAPI(title="Nanexus AI Video Summary", version="0.2.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    snapshots_dir()


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
    return HealthResponse(
        status=status,
        database=db_ok,
        redis=redis_ok,
        ai_mode=settings.ai_mode,
    )


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


@app.post("/search", response_model=SearchResponse)
def search(body: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    events, scores, method = search_events(
        db,
        body.query,
        limit=body.limit,
        camera=body.camera,
        label=body.label,
        since=body.since,
        until=body.until,
    )
    items: list[SearchHit] = []
    for idx, event in enumerate(events):
        score = scores[idx] if idx < len(scores) else None
        items.append(SearchHit(event=EventOut.model_validate(event), score=score))
    return SearchResponse(query=body.query, method=method, total=len(items), items=items)


@app.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)) -> Event:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    return event


@app.api_route("/events/{event_id}/snapshot", methods=["GET", "HEAD"])
def event_snapshot(event_id: int, db: Session = Depends(get_db)):
    """Return local demo snapshot or redirect to Frigate media URI."""
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="event not found")

    local = local_snapshot_path(event.frigate_id)
    if local.is_file():
        return FileResponse(local, media_type="image/jpeg")

    if event.snapshot_uri:
        if event.snapshot_uri.startswith("file://"):
            path = Path(event.snapshot_uri.removeprefix("file://"))
            if path.is_file():
                return FileResponse(path, media_type="image/jpeg")
        if event.snapshot_uri.startswith(("http://", "https://")):
            return RedirectResponse(url=event.snapshot_uri, status_code=307)

    raise HTTPException(status_code=404, detail="snapshot not available")


@app.api_route("/media/snapshots/{filename}", methods=["GET", "HEAD"])
def media_snapshot(filename: str):
    """Serve demo/local snapshots used when Frigate is unavailable."""
    safe = Path(filename).name
    path = snapshots_dir() / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="snapshot file not found")
    return FileResponse(path, media_type="image/jpeg")


@app.post("/events/{event_id}/reprocess", response_model=EventOut)
def reprocess_event(event_id: int, db: Session = Depends(get_db)) -> Event:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="event not found")

    queue = AIQueue()
    queue.unmark_processed(event.frigate_id)
    event.status = "queued"
    db.add(event)
    db.commit()
    db.refresh(event)
    queue.mark_processed(event.frigate_id)
    queue.enqueue(
        AIJob(
            event_id=event.id,
            frigate_id=event.frigate_id,
            snapshot_uri=event.snapshot_uri,
        )
    )
    return event


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "nanexus-ai-video-summary",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
        "timeline": "/timeline",
        "summary": "/summary/today",
        "search": "/search",
    }
