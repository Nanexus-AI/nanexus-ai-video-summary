from datetime import datetime
from zoneinfo import ZoneInfo

def test_migration_fixture_covers_required_synthetic_cases(migration_fixture):
    reviews = migration_fixture["reviews"]
    assert {review["kind"] for review in reviews} >= {"person", "vehicle"}
    assert any(len(review["object_ids"]) > 1 for review in reviews)
    assert any(review["evidence"]["available"] for review in reviews)
    assert any(not review["evidence"]["available"] for review in reviews)
    duplicate = migration_fixture["duplicate_update_case"]
    assert len(duplicate["payload_indexes"]) > duplicate["expected_legacy_rows"]
    utc = datetime.fromisoformat(reviews[0]["start_time"].replace("Z", "+00:00"))
    assert utc.date().isoformat() == "2026-08-20"
    assert utc.astimezone(ZoneInfo("America/Toronto")).date().isoformat() == "2026-08-19"
