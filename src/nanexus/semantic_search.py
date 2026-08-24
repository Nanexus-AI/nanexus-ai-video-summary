"""Stage-5 Search over application-owned embeddings only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from nanexus.config import get_settings
from nanexus.models import EmbeddingRecord


@dataclass(frozen=True)
class QueryEmbedding:
    vector: list[float]
    dimensions: int
    provider: str
    model: str
    model_version: str


class QueryEmbeddingUnavailable(RuntimeError):
    pass


def embed_query(text: str, *, transport=None) -> QueryEmbedding:
    settings = get_settings()
    try:
        with httpx.Client(
            base_url=settings.model_service_url,
            timeout=settings.model_timeout_seconds,
            transport=transport,
        ) as client:
            response = client.post("/v1/embeddings/text", json={"text": text})
            response.raise_for_status()
    except (httpx.HTTPError, ValueError) as error:
        raise QueryEmbeddingUnavailable(type(error).__name__) from error
    payload = response.json()
    if (
        payload["dimensions"] != settings.embedding_dim
        or len(payload["vector"]) != settings.embedding_dim
    ):
        raise QueryEmbeddingUnavailable("model dimension mismatch")
    return QueryEmbedding(**payload)


def semantic_search(
    db: Session,
    query: QueryEmbedding,
    *,
    limit: int,
    offset: int = 0,
    camera: str | None = None,
    site: str | None = None,
    label: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    subject_type: str | None = None,
    minimum_similarity: float = 0.0,
):
    distance = EmbeddingRecord.vector.cosine_distance(query.vector)
    filters = [
        EmbeddingRecord.superseded_at.is_(None),
        EmbeddingRecord.provider == query.provider,
        EmbeddingRecord.model == query.model,
        EmbeddingRecord.model_version == query.model_version,
        distance <= 1.0 - minimum_similarity,
    ]
    if camera:
        filters.append(EmbeddingRecord.camera == camera)
    if site:
        filters.append(EmbeddingRecord.site == site)
    if label:
        filters.append(EmbeddingRecord.labels.contains([label]))
    if since:
        filters.append(EmbeddingRecord.occurred_at >= since)
    if until:
        filters.append(EmbeddingRecord.occurred_at < until)
    if subject_type:
        filters.append(EmbeddingRecord.subject_type == subject_type)
    statement = (
        select(EmbeddingRecord, distance.label("distance"))
        .where(*filters)
        .order_by(distance, EmbeddingRecord.id)
        .offset(offset)
        .limit(limit + 1)
    )
    rows = list(db.execute(statement).all())
    return [(row[0], max(-1.0, min(1.0, 1.0 - float(row[1])))) for row in rows]
