from datetime import datetime
from nanexus.schemas import EventOut, SearchResponse, TimelineResponse
def test_api_schema_serialization_matches_timeline_baseline(migration_fixture):
    events = []
    for raw in migration_fixture["legacy_events"]:
        values = dict(raw)
        values["start_time"] = datetime.fromisoformat(values["start_time"])
        values["end_time"] = datetime.fromisoformat(values["end_time"]) if values["end_time"] else None
        events.append(EventOut.model_validate(values))
    assert TimelineResponse(total=len(events), items=events).model_dump(mode="json") == migration_fixture["expected"]["timeline"]
    assert SearchResponse(query="person", method="keyword-stub", total=0, items=[]).model_dump() == {"query": "person", "method": "keyword-stub", "total": 0, "items": []}
