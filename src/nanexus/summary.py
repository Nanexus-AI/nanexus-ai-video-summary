from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta
from datetime import UTC

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from nanexus.models import DailySummary, Event


def day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=UTC)
    end = start + timedelta(days=1)
    return start, end


def build_rule_summary(db: Session, day: date, camera: str | None = None) -> DailySummary:
    start, end = day_bounds(day)
    stmt: Select[tuple[Event]] = select(Event).where(
        Event.start_time >= start,
        Event.start_time < end,
    )
    if camera:
        stmt = stmt.where(Event.camera == camera)
    stmt = stmt.order_by(Event.start_time.asc())
    events = list(db.scalars(stmt).all())

    if not events:
        content = f"{day.isoformat()}: no events recorded."
    else:
        by_label = Counter(e.label for e in events)
        by_camera = Counter(e.camera for e in events)
        lines = [
            f"Summary for {day.isoformat()}",
            f"Total events: {len(events)}",
            "By label: " + ", ".join(f"{k}={v}" for k, v in by_label.most_common()),
            "By camera: " + ", ".join(f"{k}={v}" for k, v in by_camera.most_common()),
            "",
            "Highlights:",
        ]
        for event in events[:20]:
            caption = event.caption or f"{event.label} detected"
            ts = event.start_time.astimezone(UTC).strftime("%H:%M")
            lines.append(f"- [{ts}] {event.camera}: {caption}")
        if len(events) > 20:
            lines.append(f"... and {len(events) - 20} more events")
        content = "\n".join(lines)

    stmt = select(DailySummary).where(DailySummary.summary_date == day)
    if camera is None:
        stmt = stmt.where(DailySummary.camera.is_(None))
    else:
        stmt = stmt.where(DailySummary.camera == camera)
    existing = db.scalar(stmt)
    if existing:
        existing.content = content
        existing.event_count = len(events)
        existing.model = "rule-v0"
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    summary = DailySummary(
        summary_date=day,
        camera=camera,
        content=content,
        model="rule-v0",
        event_count=len(events),
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def fallback_summary_text(db: Session, day: date) -> str:
    start, end = day_bounds(day)
    count = db.scalar(
        select(func.count()).select_from(Event).where(
            Event.start_time >= start,
            Event.start_time < end,
        )
    )
    return f"No precomputed summary for {day.isoformat()}. Events today: {count or 0}."
