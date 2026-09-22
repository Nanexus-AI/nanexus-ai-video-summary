from uuid import uuid4

from services.api.main import client_capabilities_v1, open_subject_v1


def test_capabilities_are_versioned_and_do_not_expose_secrets() -> None:
    capability = client_capabilities_v1()
    assert capability.api_version == "v1"
    assert capability.subject_reference == "uuid"
    assert capability.chat.asynchronous is True
    assert capability.legacy_fallback_available is True
    serialized = capability.model_dump_json().lower()
    assert "token" not in serialized
    assert "event-intelligence:8000" not in serialized


def test_subject_link_redirects_to_public_review_item_boundary() -> None:
    from nanexus.public_paths import event_intelligence_review_item_url
    from services.api.main import settings

    subject_id = uuid4()
    response = open_subject_v1(subject_id)
    assert response.status_code == 307
    location = response.headers["location"]
    assert location == event_intelligence_review_item_url(
        settings.event_intelligence_public_url, subject_id
    )
    assert location.endswith(f"/api/v1/review-items/{subject_id}")
    assert "/api/v1/events/" not in location
    assert "processor" not in location
    assert "token" not in location.lower()


def test_search_and_chat_subject_paths_share_video_summary_boundary() -> None:
    from nanexus.public_paths import SUBJECT_PATH_TEMPLATE, subject_path
    from nanexus.schemas import ChatMessageV1Out
    from nanexus.models import ChatMessage
    from datetime import UTC, datetime

    subject_id = "00000000-0000-0000-0000-000000000801"
    assert subject_path(subject_id) == f"/api/v1/subjects/{subject_id}"
    assert SUBJECT_PATH_TEMPLATE == "/api/v1/subjects/{subject_id}"
    message = ChatMessage(
        id=uuid4(),
        conversation_id=1,
        owner_id="alice",
        role="assistant",
        content="answer",
        related_subject_ids=[subject_id],
        degraded=False,
        created_at=datetime.now(UTC),
    )
    citations = ChatMessageV1Out.model_validate(message).citations
    assert citations[0]["review_path"] == subject_path(subject_id)
    # Capabilities advertise the same Video Summary subject boundary.
    assert client_capabilities_v1().subject_path_template == SUBJECT_PATH_TEMPLATE
