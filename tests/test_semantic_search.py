import json
from pathlib import Path

import httpx
import pytest
from nanexus.config import get_settings
from nanexus.indexing import EmbeddingJob
from nanexus.semantic_search import (
    QueryEmbedding,
    QueryEmbeddingUnavailable,
    embed_query,
    semantic_search,
)
from sqlalchemy.dialects import postgresql


def test_query_embedding_uses_model_service_and_validates_dimensions(monkeypatch):
    monkeypatch.setenv("EMBEDDING_DIM", "3")
    get_settings.cache_clear()

    def handler(request):
        assert request.url.path == "/v1/embeddings/text"
        return httpx.Response(
            200,
            json={
                "vector": [1, 0, 0],
                "dimensions": 3,
                "provider": "p",
                "model": "m",
                "model_version": "v",
            },
        )

    result = embed_query("红衣服的人", transport=httpx.MockTransport(handler))
    assert result.dimensions == 3
    get_settings.cache_clear()


def test_query_embedding_has_explicit_unavailable_semantics(monkeypatch):
    monkeypatch.setenv("EMBEDDING_DIM", "3")
    get_settings.cache_clear()
    with pytest.raises(QueryEmbeddingUnavailable):
        embed_query("query", transport=httpx.MockTransport(lambda _: httpx.Response(503)))
    get_settings.cache_clear()


class CaptureSession:
    def execute(self, statement):
        self.statement = statement
        return type("R", (), {"all": lambda self: []})()


def test_search_statement_uses_only_embedding_records_and_all_filters():
    db = CaptureSession()
    rows = semantic_search(
        db,
        QueryEmbedding([0.0] * 512, 512, "p", "m", "v"),
        limit=10,
        camera="front",
        site="home",
        label="person",
        subject_type="review_item",
        minimum_similarity=0.2,
    )
    sql = str(db.statement.compile(dialect=postgresql.dialect()))
    assert rows == [] and "embedding_records" in sql and "events" not in sql
    assert all(
        name in sql for name in ("camera", "site", "labels", "subject_type", "superseded_at")
    )


def test_embedding_job_round_trip_and_fixed_bilingual_evaluation_set():
    job = EmbeddingJob(
        "review_item",
        "00000000-0000-0000-0000-000000000001",
        "r1",
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003",
        [],
        "image",
        [0.0],
        "p",
        "m",
        "v",
        "hash",
    )
    assert EmbeddingJob.from_json(job.to_json()) == job
    data = json.loads(
        (Path(__file__).parents[1] / "docs/search-evaluation/fixed-v1.json").read_text()
    )
    assert len(data["queries"]) == 10
    assert {q["language"] for q in data["queries"]} == {"zh", "en"}


def test_search_v1_degrades_to_empty_without_legacy_fallback(monkeypatch):
    import services.api.main as api

    monkeypatch.setattr(
        api, "embed_query", lambda _: (_ for _ in ()).throw(QueryEmbeddingUnavailable("offline"))
    )
    response = api.semantic_search_v1(
        api.SemanticSearchRequest(query="person"),
        db=object(),
        principal=api.Principal("test", "reader", frozenset({"*"})),
    )
    assert response.degraded is True
    assert response.method == "semantic-unavailable"
    assert response.items == []


def test_search_evidence_is_proxied_through_event_intelligence(monkeypatch):
    import asyncio

    import services.api.main as api
    from nanexus.event_intelligence_client import EvidenceContent

    calls = []

    class Client:
        def __init__(self, *args, **kwargs):
            calls.append((args, kwargs))

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def evidence(self, job_id, evidence_id):
            calls.append((job_id, evidence_id))
            return EvidenceContent(b"image", "image/jpeg")

    monkeypatch.setattr(api, "EventIntelligenceClient", Client)
    response = asyncio.run(
        api.semantic_search_evidence(
            "00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"
        )
    )
    assert response.body == b"image"
    assert response.headers["cache-control"] == "private, no-store"
    assert len(calls) == 2
