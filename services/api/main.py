from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse, Response
from nanexus.chat import run_chat
from nanexus.config import get_settings
from nanexus.db import get_db, init_db
from nanexus.event_intelligence_client import EventIntelligenceClient, EventIntelligenceError
from nanexus.media import local_snapshot_path, snapshots_dir
from nanexus.models import Conversation, DailySummary, Event
from nanexus.queue import AIJob, AIQueue, SummaryJob
from nanexus.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationOut,
    EventOut,
    HealthResponse,
    RegenerateSummaryRequest,
    SearchHit,
    SearchRequest,
    SearchResponse,
    SemanticSearchHit,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SummaryOut,
    SummaryQueuedResponse,
    SummaryResponse,
    TimelineResponse,
)
from nanexus.search import search_events
from nanexus.semantic_search import QueryEmbeddingUnavailable, embed_query, semantic_search
from nanexus.summary import build_daily_summary, fallback_summary_text
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

settings = get_settings()
app = FastAPI(title="Nanexus AI Video Summary", version="0.3.0")


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
        summary_mode=settings.summary_mode,
        chat_mode=settings.chat_mode,
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


@app.post("/summary/regenerate")
def regenerate_summary(
    body: RegenerateSummaryRequest,
    db: Session = Depends(get_db),
):
    day = body.summary_date or datetime.now(tz=UTC).date()
    mode = body.mode or settings.summary_mode

    if body.sync:
        summary = build_daily_summary(db, day, camera=body.camera, mode=mode)
        return SummaryOut.model_validate(summary)

    queue = AIQueue()
    queue.clear_summary_done(day.isoformat(), body.camera)
    queue.enqueue_summary(SummaryJob(summary_date=day.isoformat(), camera=body.camera, mode=mode))
    return SummaryQueuedResponse(
        status="queued",
        summary_date=day,
        camera=body.camera,
        mode=mode,
    )


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


@app.post("/api/v1/search", response_model=SemanticSearchResponse)
def semantic_search_v1(
    body: SemanticSearchRequest, db: Session = Depends(get_db)
) -> SemanticSearchResponse:
    try:
        query_embedding = embed_query(body.query)
    except QueryEmbeddingUnavailable as error:
        return SemanticSearchResponse(
            query=body.query,
            method="semantic-unavailable",
            degraded=True,
            degradation_reason=str(error),
            total=0,
            items=[],
        )
    rows = semantic_search(
        db,
        query_embedding,
        limit=body.limit,
        offset=body.offset,
        camera=body.camera,
        site=body.site,
        label=body.label,
        since=body.since,
        until=body.until,
        subject_type=body.subject_type,
        minimum_similarity=body.minimum_similarity,
    )
    has_more = len(rows) > body.limit
    rows = rows[: body.limit]
    items = [
        SemanticSearchHit(
            subject_type=record.subject_type,
            subject_id=str(record.subject_id),
            subject_revision=record.subject_revision,
            source_claim_id=str(record.source_claim_id),
            score=score,
            camera=record.camera,
            site=record.site,
            labels=record.labels,
            occurred_at=record.occurred_at,
            evidence=[
                f"{settings.public_base_url}/api/v1/search/evidence/"
                f"{record.source_job_id}/evidence/{evidence_id}"
                for evidence_id in record.evidence_ids
            ],
        )
        for record, score in rows
    ]
    return SemanticSearchResponse(
        query=body.query,
        method="cosine-pgvector",
        model=query_embedding.model,
        model_version=query_embedding.model_version,
        total=len(items),
        next_offset=body.offset + body.limit if has_more else None,
        items=items,
    )


@app.get("/api/v1/search/evidence/{job_id}/{evidence_id}")
async def semantic_search_evidence(job_id: str, evidence_id: str) -> Response:
    """Open Evidence through the authoritative, job-scoped public boundary."""
    from uuid import UUID

    try:
        async with EventIntelligenceClient(
            settings.event_intelligence_url,
            settings.event_intelligence_token,
            timeout_seconds=settings.event_intelligence_timeout_seconds,
        ) as client:
            media = await client.evidence(UUID(job_id), UUID(evidence_id))
    except (ValueError, EventIntelligenceError) as error:
        status_code = error.status_code if isinstance(error, EventIntelligenceError) else 400
        raise HTTPException(
            status_code=status_code or 502, detail="evidence unavailable"
        ) from error
    return Response(
        content=media.content,
        media_type=media.content_type,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    try:
        conv, answer, related_ids, method = run_chat(
            db,
            body.message,
            conversation_id=body.conversation_id,
            camera=body.camera,
            user_id=body.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    related_events = []
    if related_ids:
        related_events = list(db.scalars(select(Event).where(Event.id.in_(related_ids))).all())
        # Preserve retrieval order
        by_id = {e.id: e for e in related_events}
        related_events = [by_id[i] for i in related_ids if i in by_id]

    return ChatResponse(
        conversation_id=conv.id,
        answer=answer,
        method=method,
        related_event_ids=related_ids,
        related_events=[EventOut.model_validate(e) for e in related_events],
    )


@app.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)) -> Conversation:
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="conversation not found")
    return conv


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
        "version": "0.3.0",
        "docs": "/docs",
        "health": "/health",
        "timeline": "/timeline",
        "summary": "/summary/today",
        "search": "/search",
        "chat": "/chat",
    }
