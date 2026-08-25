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


def test_subject_link_redirects_to_public_review_boundary() -> None:
    subject_id = uuid4()
    response = open_subject_v1(subject_id)
    assert response.status_code == 307
    assert response.headers["location"].endswith(f"/api/v1/events/{subject_id}")
