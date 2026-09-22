"""Public application path construction for Search evidence and Chat citations."""

from datetime import UTC, datetime
from uuid import UUID

from nanexus.models import ChatMessage
from nanexus.public_paths import (
    EVIDENCE_PROXY_PATH_TEMPLATE,
    EVENT_INTELLIGENCE_REVIEW_ITEM_PATH_TEMPLATE,
    SUBJECT_PATH_TEMPLATE,
    evidence_proxy_path,
    evidence_proxy_url,
    event_intelligence_review_item_path,
    event_intelligence_review_item_url,
    subject_path,
)
from nanexus.schemas import ChatMessageV1Out


def test_evidence_proxy_path_matches_implemented_route_without_duplicate_segment():
    job_id = UUID("00000000-0000-0000-0000-0000000000a1")
    evidence_id = UUID("00000000-0000-0000-0000-0000000000a2")
    path = evidence_proxy_path(job_id, evidence_id)
    assert path == f"/api/v1/search/evidence/{job_id}/{evidence_id}"
    assert path.count("/evidence/") == 1
    assert f"/evidence/{job_id}/evidence/" not in path
    assert EVIDENCE_PROXY_PATH_TEMPLATE == "/api/v1/search/evidence/{job_id}/{evidence_id}"


def test_evidence_proxy_url_uses_public_base_without_event_intelligence_host():
    url = evidence_proxy_url(
        "http://video-summary.example:8000/",
        "00000000-0000-0000-0000-0000000000b1",
        "00000000-0000-0000-0000-0000000000b2",
    )
    assert url == (
        "http://video-summary.example:8000/api/v1/search/evidence/"
        "00000000-0000-0000-0000-0000000000b1/"
        "00000000-0000-0000-0000-0000000000b2"
    )
    assert "processor" not in url
    assert url.count("/evidence/") == 1


def test_search_and_chat_share_authoritative_subject_path():
    subject_id = "00000000-0000-0000-0000-0000000000c1"
    assert subject_path(subject_id) == f"/api/v1/subjects/{subject_id}"
    assert SUBJECT_PATH_TEMPLATE == "/api/v1/subjects/{subject_id}"
    assert event_intelligence_review_item_path(subject_id) == (f"/api/v1/review-items/{subject_id}")
    assert EVENT_INTELLIGENCE_REVIEW_ITEM_PATH_TEMPLATE == ("/api/v1/review-items/{review_item_id}")
    assert event_intelligence_review_item_url("https://events.example/", subject_id) == (
        f"https://events.example/api/v1/review-items/{subject_id}"
    )

    message = ChatMessage(
        id=UUID("00000000-0000-0000-0000-0000000000c2"),
        conversation_id=1,
        owner_id="alice",
        role="assistant",
        content="answer",
        related_subject_ids=[subject_id],
        degraded=False,
        created_at=datetime.now(UTC),
    )
    citations = ChatMessageV1Out.model_validate(message).citations
    assert citations == [{"subject_id": subject_id, "review_path": subject_path(subject_id)}]
