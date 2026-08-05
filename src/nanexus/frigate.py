from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from nanexus.config import get_settings


def _ts_to_datetime(value: float | int | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(float(value), tz=UTC)


def parse_frigate_event(payload: dict[str, Any]) -> dict[str, Any] | None:
    """
    Normalize Frigate MQTT event payloads into DB fields.

    Supports both:
    - { "type": "new"|"update"|"end", "after": {...} }
    - bare event objects with id/camera/label/start_time
    """
    event = payload.get("after") or payload.get("before") or payload
    if not isinstance(event, dict):
        return None

    frigate_id = event.get("id") or payload.get("id")
    camera = event.get("camera")
    label = event.get("label")
    if not frigate_id or not camera or not label:
        return None

    # Prefer "new" and "end"; still accept bare payloads / updates for demo.
    event_type = payload.get("type")
    if event_type not in (None, "new", "update", "end"):
        return None

    settings = get_settings()
    base = settings.frigate_base_url.rstrip("/")
    has_snapshot = bool(event.get("has_snapshot"))
    has_clip = bool(event.get("has_clip"))

    snapshot_uri = event.get("snapshot_uri")
    clip_uri = event.get("clip_uri")
    if not snapshot_uri and has_snapshot:
        snapshot_uri = f"{base}/api/events/{frigate_id}/snapshot.jpg"
    if not clip_uri and has_clip:
        clip_uri = f"{base}/api/events/{frigate_id}/clip.mp4"

    start = _ts_to_datetime(event.get("start_time"))
    if start is None:
        start = datetime.now(tz=UTC)

    return {
        "frigate_id": str(frigate_id),
        "camera": str(camera),
        "label": str(label),
        "sub_label": event.get("sub_label"),
        "start_time": start,
        "end_time": _ts_to_datetime(event.get("end_time")),
        "snapshot_uri": snapshot_uri,
        "clip_uri": clip_uri,
        "raw_payload": payload,
    }
