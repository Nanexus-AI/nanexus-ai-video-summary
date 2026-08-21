from datetime import datetime
from types import SimpleNamespace
def legacy_events(fixture: dict) -> list[SimpleNamespace]:
    events = []
    for item in fixture["legacy_events"]:
        values = dict(item)
        values["start_time"] = datetime.fromisoformat(values["start_time"])
        values["end_time"] = datetime.fromisoformat(values["end_time"]) if values.get("end_time") else None
        events.append(SimpleNamespace(**values))
    return events
