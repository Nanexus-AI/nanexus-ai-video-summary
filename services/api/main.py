from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from nanexus.chat import run_chat
from nanexus.auth import Principal, current_principal
from nanexus.compatibility import check_event_intelligence
from nanexus.chat_v1 import create_chat_job
from nanexus.config import get_settings
from nanexus.db import get_db, init_db
from nanexus.event_intelligence_client import (
    EventIntelligenceClient,
    EventIntelligenceError,
)
from nanexus.media import local_snapshot_path, snapshots_dir
from nanexus.models import (
    ChatJob,
    ChatMessage,
    Conversation,
    DailySummary,
    Event,
    Summary,
)
from nanexus.queue import AIJob, AIQueue, ChatQueueJob, SummaryJob
from nanexus.observability import prometheus, snapshot
from nanexus.public_paths import (
    SUBJECT_PATH_TEMPLATE,
    evidence_proxy_url,
    event_intelligence_review_item_url,
    subject_path,
)
from nanexus.schemas import (
    ChatJobV1Out,
    ChatMessageV1Out,
    ChatRequest,
    ChatResponse,
    ChatV1Request,
    ClientCapabilitiesV1,
    ClientFeatureCapability,
    ConversationOut,
    ConversationV1Out,
    EventOut,
    HealthResponse,
    RegenerateSummaryRequest,
    SearchHit,
    SearchRequest,
    SearchResponse,
    SemanticSearchHit,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SummaryJobV1Response,
    SummaryOut,
    SummaryQueuedResponse,
    SummaryRebuildV1Request,
    SummaryResponse,
    SummaryV1Out,
    SummaryV1Response,
    TimelineResponse,
)
from nanexus.search import search_events
from nanexus.semantic_search import (
    QueryEmbeddingUnavailable,
    embed_query,
    semantic_search,
)
from nanexus.summary import (
    build_daily_summary,
    fallback_summary_text,
    local_day_bounds,
    queue_summary_generation,
)

settings = get_settings()
app = FastAPI(title="Nanexus AI Video Summary", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[item.strip() for item in settings.cors_allowed_origins.split(",") if item.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "HEAD"],
    allow_headers=["Authorization", "Content-Type", "X-Nanexus-Dev-Owner"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.on_event("startup")
def on_startup() -> None:
    settings.validate_runtime()
    init_db()
    if settings.capability_check_enabled:
        compatibility = check_event_intelligence(settings)
        if not compatibility.compatible:
            raise RuntimeError(compatibility.reason)
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
        model_provider=settings.model_provider,
    )


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
def readiness(db: Session = Depends(get_db)) -> Response:
    try:
        db.execute(text("SELECT 1"))
        state = snapshot(db)
    except Exception:
        return Response('{"status":"not-ready"}', status_code=503, media_type="application/json")
    missing_workers = [name for name, value in state["worker_heartbeats"].items() if not value]
    missing_services: list[str] = []
    try:
        import httpx

        if httpx.get(f"{settings.model_service_url.rstrip('/')}/health", timeout=2).status_code != 200:
            missing_services.append("model")
    except Exception:
        missing_services.append("model")
    if not check_event_intelligence(settings).compatible:
        missing_services.append("event_intelligence")
    status = "degraded" if missing_workers or missing_services else "ready"
    return Response(
        content=__import__("json").dumps(
            {"status": status, "missing_workers": missing_workers, "missing_services": missing_services}
        ),
        status_code=200,
        media_type="application/json",
    )


@app.get("/api/v1/operations/status")
def operations_status(
    db: Session = Depends(get_db), principal: Principal = Depends(current_principal)
) -> dict:
    principal.require("admin")
    data = snapshot(db)
    compatibility = check_event_intelligence(settings)
    data["event_intelligence"] = {
        "connected": compatibility.compatible,
        "reason": compatibility.reason,
    }
    data["migration_schema"] = "managed-by-alembic"
    return data


@app.get("/metrics")
def metrics(
    db: Session = Depends(get_db), principal: Principal = Depends(current_principal)
) -> Response:
    principal.require("admin")
    return Response(prometheus(snapshot(db)), media_type="text/plain; version=0.0.4")


@app.get("/api/v1/capabilities", response_model=ClientCapabilitiesV1)
def client_capabilities_v1() -> ClientCapabilitiesV1:
    """Public client contract; deliberately excludes tokens and internal URLs."""
    return ClientCapabilitiesV1(
        subject_path_template=SUBJECT_PATH_TEMPLATE,
        summary=ClientFeatureCapability(available=True, mode=settings.summary_mode, asynchronous=True),
        search=ClientFeatureCapability(available=True, mode="semantic"),
        chat=ClientFeatureCapability(available=True, mode=settings.chat_mode, asynchronous=True),
        legacy_fallback_available=settings.legacy_client_api_enabled,
        ownership_authentication=settings.auth_mode,
    )


@app.get("/api/v1/subjects/{subject_id}")
def open_subject_v1(
    subject_id: UUID, principal: Principal = Depends(current_principal)
) -> RedirectResponse:
    """Open the canonical ReviewItem through Event Intelligence's public review-item route."""
    target = event_intelligence_review_item_url(
        settings.event_intelligence_public_url, subject_id
    )
    return RedirectResponse(url=target, status_code=307)


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
    return TimelineResponse(
        total=total,
        items=[EventOut.model_validate(item) for item in items],
    )


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
    queue.enqueue_summary(
        SummaryJob(summary_date=day.isoformat(), camera=body.camera, mode=mode)
    )
    return SummaryQueuedResponse(
        status="queued",
        summary_date=day,
        camera=body.camera,
        mode=mode,
    )


@app.get("/api/v1/summaries/{local_date}", response_model=SummaryV1Response)
def summary_v1(
    local_date: date,
    timezone: str,
    site_id: str = "default",
    camera_id: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(current_principal),
) -> SummaryV1Response:
    """Read the active precomputed Summary; this endpoint never generates inline."""
    principal.require("reader", "user", "admin", site_id=site_id)
    filters = [
        Summary.summary_type == "daily",
        Summary.local_date == local_date,
        Summary.timezone == timezone,
        Summary.site_id == site_id,
        Summary.status == "ready",
        Summary.superseded_at.is_(None),
    ]
    filters.append(
        Summary.camera_id.is_(None)
        if camera_id is None
        else Summary.camera_id == camera_id
    )
    summary = db.scalar(
        select(Summary).where(*filters).order_by(Summary.created_at.desc())
    )
    return SummaryV1Response(
        summary=SummaryV1Out.model_validate(summary) if summary is not None else None
    )


@app.post("/api/v1/summaries/rebuild", response_model=SummaryJobV1Response)
def rebuild_summary_v1(
    body: SummaryRebuildV1Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(current_principal),
) -> SummaryJobV1Response:
    """Queue generation only; LLM and Event Intelligence calls remain worker-only."""
    principal.require("user", "admin", site_id=body.site_id)
    try:
        local_day_bounds(body.local_date, body.timezone)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    summary = queue_summary_generation(
        db,
        day=body.local_date,
        timezone=body.timezone,
        site_id=body.site_id,
        camera_id=body.camera_id,
        mode=body.mode,
    )
    if summary.status in {"queued", "failed"}:
        summary.status = "queued"
        db.add(summary)
        db.commit()
        AIQueue().enqueue_summary(
            SummaryJob(
                summary_id=str(summary.id),
                summary_date=body.local_date.isoformat(),
                camera=body.camera_id,
                mode=body.mode,
                timezone=body.timezone,
                site_id=body.site_id,
            )
        )
    return SummaryJobV1Response(id=summary.id, status=summary.status)


@app.get("/api/v1/summaries/jobs/{summary_id}", response_model=SummaryJobV1Response)
def summary_job_v1(
    summary_id: UUID,
    db: Session = Depends(get_db),
    principal: Principal = Depends(current_principal),
) -> SummaryJobV1Response:
    summary = db.get(Summary, summary_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="summary job not found")
    principal.require("reader", "user", "admin", site_id=summary.site_id)
    return SummaryJobV1Response(id=summary.id, status=summary.status)


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
    return SearchResponse(
        query=body.query, method=method, total=len(items), items=items
    )


@app.post("/api/v1/search", response_model=SemanticSearchResponse)
def semantic_search_v1(
    body: SemanticSearchRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(current_principal),
) -> SemanticSearchResponse:
    principal.require("reader", "user", "admin", site_id=body.site)
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
                evidence_proxy_url(settings.public_base_url, record.source_job_id, evidence_id)
                for evidence_id in record.evidence_ids
            ],
            subject_path=subject_path(record.subject_id),
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
async def semantic_search_evidence(
    job_id: str,
    evidence_id: str,
    principal: Principal = Depends(current_principal),
) -> Response:
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
        status_code = (
            error.status_code if isinstance(error, EventIntelligenceError) else 400
        )
        raise HTTPException(
            status_code=status_code or 502, detail="evidence unavailable"
        ) from error
    return Response(
        content=media.content,
        media_type=media.content_type,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
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
        related_events = list(
            db.scalars(select(Event).where(Event.id.in_(related_ids))).all()
        )
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


@app.post("/api/v1/chat/jobs", response_model=ChatJobV1Out, status_code=202)
def create_chat_job_v1(
    body: ChatV1Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(current_principal),
) -> ChatJobV1Out:
    """Persist and queue only; retrieval and LLM execution are worker-only."""
    principal.require("user", "admin", site_id=body.site_id)
    if settings.auth_mode != "development" and body.owner_id not in {None, principal.owner_id}:
        raise HTTPException(status_code=403, detail="owner is bound to authenticated identity")
    owner_id = principal.owner_id if settings.auth_mode != "development" else (body.owner_id or principal.owner_id)
    try:
        job = create_chat_job(
            db,
            owner_id=owner_id,
            question=body.message,
            conversation_id=body.conversation_id,
            camera=body.camera,
            site_id=body.site_id,
            timezone=body.timezone,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404 if body.conversation_id else 422, detail=str(error)
        ) from error
    AIQueue().enqueue_chat(ChatQueueJob(job_id=str(job.id)))
    return ChatJobV1Out(
        id=job.id, conversation_id=job.conversation_id, status=job.status
    )


@app.get("/api/v1/chat/jobs/{job_id}", response_model=ChatJobV1Out)
def get_chat_job_v1(
    job_id: UUID,
    owner_id: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(current_principal),
) -> ChatJobV1Out:
    principal.require("reader", "user", "admin")
    effective_owner = owner_id if settings.auth_mode == "development" else principal.owner_id
    job = db.get(ChatJob, job_id)
    if job is None or job.owner_id != effective_owner:
        raise HTTPException(status_code=404, detail="chat job not found")
    answer = (
        db.get(ChatMessage, job.assistant_message_id)
        if job.assistant_message_id
        else None
    )
    return ChatJobV1Out(
        id=job.id,
        conversation_id=job.conversation_id,
        status=job.status,
        error_code=job.error_code,
        answer=ChatMessageV1Out.model_validate(answer) if answer else None,
    )


@app.get(
    "/api/v1/chat/conversations/{conversation_id}", response_model=ConversationV1Out
)
def get_conversation_v1(
    conversation_id: int,
    owner_id: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(current_principal),
) -> ConversationV1Out:
    principal.require("reader", "user", "admin")
    effective_owner = owner_id if settings.auth_mode == "development" else principal.owner_id
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != effective_owner:
        raise HTTPException(status_code=404, detail="conversation not found")
    messages = list(
        db.scalars(
            select(ChatMessage)
            .where(
                ChatMessage.conversation_id == conversation_id,
                ChatMessage.owner_id == effective_owner,
            )
            .order_by(ChatMessage.created_at, ChatMessage.id)
        ).all()
    )
    return ConversationV1Out(
        id=conversation.id,
        owner_id=effective_owner,
        title=conversation.title,
        messages=[ChatMessageV1Out.model_validate(item) for item in messages],
    )


@app.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: int, db: Session = Depends(get_db)
) -> Conversation:
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
