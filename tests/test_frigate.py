from datetime import UTC
from nanexus.config import get_settings
from nanexus.frigate import parse_frigate_event

def test_parse_new_event_builds_legacy_fields(monkeypatch, migration_fixture):
    monkeypatch.setenv("FRIGATE_BASE_URL", "http://frigate.test")
    get_settings.cache_clear()
    parsed = parse_frigate_event(migration_fixture["source_payloads"][0])
    assert parsed is not None
    assert parsed["frigate_id"] == "evt-person-001"
    assert parsed["camera"] == "front_door"
    assert parsed["label"] == "person"
    assert parsed["start_time"].tzinfo is UTC
    assert parsed["snapshot_uri"] == "fixture://snapshots/person-001.jpg"

def test_parse_update_and_reject_invalid_payload(migration_fixture):
    parsed = parse_frigate_event(migration_fixture["source_payloads"][2])
    assert parsed is not None
    assert parsed["frigate_id"] == "evt-person-001"
    assert parsed["end_time"] is not None
    assert parse_frigate_event({"type": "unknown", "after": {}}) is None
    assert parse_frigate_event({"type": "new", "after": {"id": "missing-fields"}}) is None
