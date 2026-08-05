from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from nanexus.config import get_settings
from nanexus.llm import chat_completion
from nanexus.models import DailySummary, Event


def day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=UTC)
    end = start + timedelta(days=1)
    return start, end


def load_day_events(db: Session, day: date, camera: str | None = None) -> list[Event]:
    start, end = day_bounds(day)
    stmt: Select[tuple[Event]] = select(Event).where(
        Event.start_time >= start,
        Event.start_time < end,
    )
    if camera:
        stmt = stmt.where(Event.camera == camera)
    stmt = stmt.order_by(Event.start_time.asc())
    return list(db.scalars(stmt).all())


def render_rule_summary(day: date, events: list[Event]) -> str:
    if not events:
        return f"{day.isoformat()}: no events recorded."

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
    for event in events[:30]:
        caption = event.caption or f"{event.label} detected"
        ts = event.start_time.astimezone(UTC).strftime("%H:%M")
        lines.append(f"- [{ts}] {event.camera}: {caption}")
    if len(events) > 30:
        lines.append(f"... and {len(events) - 30} more events")
    return "\n".join(lines)


def render_llm_summary(day: date, events: list[Event]) -> str | None:
    if not events:
        return f"{day.isoformat()}: no events recorded."

    bullets = []
    for event in events[:40]:
        caption = event.caption or f"{event.label} detected"
        ts = event.start_time.astimezone(UTC).strftime("%H:%M")
        bullets.append(f"- [{ts}] {event.camera} / {event.label}: {caption}")
    context = "\n".join(bullets)
    messages = [
        {
            "role": "system",
            "content": (
                "You summarize home security camera events for a homeowner. "
                "Be concise, factual, and structured with short sections: Overview, "
                "Notable events, By camera. Do not invent details not present in the list."
            ),
        },
        {
            "role": "user",
            "content": f"Date: {day.isoformat()}\nEvents ({len(events)}):\n{context}",
        },
    ]
    return chat_completion(messages, temperature=0.2, max_tokens=700)


def upsert_summary(
    db: Session,
    *,
    day: date,
    camera: str | None,
    content: str,
    model: str,
    event_count: int,
) -> DailySummary:
    stmt = select(DailySummary).where(DailySummary.summary_date == day)
    if camera is None:
        stmt = stmt.where(DailySummary.camera.is_(None))
    else:
        stmt = stmt.where(DailySummary.camera == camera)
    existing = db.scalar(stmt)
    if existing:
        existing.content = content
        existing.event_count = event_count
        existing.model = model
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    summary = DailySummary(
        summary_date=day,
        camera=camera,
        content=content,
        model=model,
        event_count=event_count,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def build_daily_summary(
    db: Session,
    day: date,
    camera: str | None = None,
    *,
    mode: str | None = None,
) -> DailySummary:
    """Build and persist a daily summary. mode: rule | llm (falls back to rule)."""
    settings = get_settings()
    mode = (mode or settings.summary_mode).lower()
    events = load_day_events(db, day, camera)

    model = "rule-v0"
    content = render_rule_summary(day, events)
    if mode == "llm":
        llm_text = render_llm_summary(day, events)
        if llm_text:
            content = llm_text
            model = f"llm:{settings.llm_model}"

    return upsert_summary(
        db,
        day=day,
        camera=camera,
        content=content,
        model=model,
        event_count=len(events),
    )


# Backward-compatible alias used by older scripts/API.
def build_rule_summary(db: Session, day: date, camera: str | None = None) -> DailySummary:
    return build_daily_summary(db, day, camera, mode="rule")


def fallback_summary_text(db: Session, day: date) -> str:
    start, end = day_bounds(day)
    count = db.scalar(
        select(func.count()).select_from(Event).where(
            Event.start_time >= start,
            Event.start_time < end,
        )
    )
    return f"No precomputed summary for {day.isoformat()}. Events today: {count or 0}."
