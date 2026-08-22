from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from nanexus.models import Event
from nanexus.config import get_settings


def get_vision_pipeline():
    """Rollback-only lazy import retained for baseline test compatibility."""
    from nanexus.vision import get_vision_pipeline as factory

    return factory()


def search_events(
    db: Session,
    query: str,
    *,
    limit: int = 20,
    camera: str | None = None,
    label: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> tuple[list[Event], list[float | None], str]:
    """
    Semantic search via pgvector when embeddings exist; keyword fallback in stub mode
    or when no vectors are available.
    """
    settings = get_settings()
    filters = [Event.embedding.is_not(None), Event.status == "done"]
    if camera:
        filters.append(Event.camera == camera)
    if label:
        filters.append(Event.label == label)
    if since:
        filters.append(Event.start_time >= since)
    if until:
        filters.append(Event.start_time < until)

    if not settings.legacy_api_model_inference_enabled:
        events = _keyword_search(
            db, query, limit=limit, camera=camera, label=label, since=since, until=until
        )
        return events, [], "keyword-stub"

    # Rollback-only legacy path. Kept until the later Search migration stage.
    pipeline = get_vision_pipeline()
    if pipeline.mode == "stub":
        return _keyword_search(db, query, limit=limit, camera=camera, label=label, since=since, until=until), [], "keyword-stub"

    query_vec = pipeline.embed_text(query)
    distance = Event.embedding.cosine_distance(query_vec)
    stmt: Select = (
        select(Event, distance.label("distance"))
        .where(*filters)
        .order_by(distance)
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    if not rows:
        # Fall back to keyword if DB has no embeddings yet.
        events = _keyword_search(
            db, query, limit=limit, camera=camera, label=label, since=since, until=until
        )
        return events, [None] * len(events), "keyword-fallback"

    events = [row[0] for row in rows]
    # cosine_distance -> similarity score roughly 1 - distance (pgvector)
    scores = [max(0.0, 1.0 - float(row[1])) for row in rows]
    return events, scores, "openclip-pgvector"


def _keyword_search(
    db: Session,
    query: str,
    *,
    limit: int,
    camera: str | None,
    label: str | None,
    since: datetime | None,
    until: datetime | None,
) -> list[Event]:
    pattern = f"%{query}%"
    filters = [
        or_(
            Event.caption.ilike(pattern),
            Event.label.ilike(pattern),
            Event.sub_label.ilike(pattern),
            Event.camera.ilike(pattern),
        )
    ]
    if camera:
        filters.append(Event.camera == camera)
    if label:
        filters.append(Event.label == label)
    if since:
        filters.append(Event.start_time >= since)
    if until:
        filters.append(Event.start_time < until)

    return list(
        db.scalars(
            select(Event).where(*filters).order_by(Event.start_time.desc()).limit(limit)
        ).all()
    )
