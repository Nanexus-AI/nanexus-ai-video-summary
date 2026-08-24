from datetime import date, datetime

from nanexus.schemas import (
    EventOut,
    SearchResponse,
    SummaryRebuildV1Request,
    TimelineResponse,
)


def test_api_schema_serialization_matches_timeline_baseline(migration_fixture):
    events = []
    for raw in migration_fixture["legacy_events"]:
        values = dict(raw)
        values["start_time"] = datetime.fromisoformat(values["start_time"])
        values["end_time"] = datetime.fromisoformat(values["end_time"]) if values["end_time"] else None
        events.append(EventOut.model_validate(values))
    assert TimelineResponse(total=len(events), items=events).model_dump(mode="json") == migration_fixture["expected"]["timeline"]
    assert SearchResponse(query="person", method="keyword-stub", total=0, items=[]).model_dump() == {"query": "person", "method": "keyword-stub", "total": 0, "items": []}


def test_summary_rebuild_v1_is_async_only_and_version_scoped() -> None:
    request = SummaryRebuildV1Request(
        local_date=date(2026, 8, 20),
        timezone="America/Toronto",
        site_id="home",
        mode="llm",
    )
    assert request.model_dump() == {
        "local_date": date(2026, 8, 20),
        "timezone": "America/Toronto",
        "site_id": "home",
        "camera_id": None,
        "mode": "llm",
    }
    assert "sync" not in SummaryRebuildV1Request.model_fields
