from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from nanexus.config import get_settings
from nanexus.llm import chat_completion
from nanexus.models import Conversation, DailySummary, Event
from nanexus.search import search_events
from nanexus.summary import day_bounds

# Common aliases users type in Swagger / chat UI.
_CAMERA_ALIASES = {
    "front yard": "front_yard",
    "frontyard": "front_yard",
    "前院": "front_yard",
    "前门": "front_door",
    "front door": "front_door",
    "frontdoor": "front_door",
    "drive way": "driveway",
    "车道": "driveway",
    "车库": "garage",
    "后院": "backyard",
    "back yard": "backyard",
}


def _norm_key(value: str) -> str:
    return value.strip().lower().replace("-", " ").replace("_", " ")


def resolve_camera(db: Session, camera: str | None) -> str | None:
    """Normalize camera input like 'front yard' / '前院' to DB id 'front_yard'."""
    if not camera:
        return None
    raw = camera.strip()
    if not raw:
        return None

    alias = _CAMERA_ALIASES.get(_norm_key(raw))
    if alias:
        return alias

    known = list(db.scalars(select(Event.camera).distinct()).all())
    # Exact match first.
    for name in known:
        if name == raw:
            return name
    # Space/underscore-insensitive match against known cameras.
    target = _norm_key(raw)
    for name in known:
        if _norm_key(name) == target:
            return name
    # Soft contains match: "front yard" vs "front_yard_cam"
    for name in known:
        if target in _norm_key(name) or _norm_key(name) in target:
            return name
    return raw


def _format_event_line(event: Event) -> str:
    ts = event.start_time.astimezone(UTC).strftime("%Y-%m-%d %H:%M")
    caption = event.caption or f"{event.label} detected"
    return f"[event:{event.id}] [{ts}] {event.camera}/{event.label}: {caption}"


def retrieve_context(
    db: Session,
    question: str,
    *,
    camera: str | None = None,
    limit: int = 8,
) -> tuple[list[Event], list[DailySummary], str]:
    """Retrieve events + recent summaries for RAG."""
    camera = resolve_camera(db, camera)
    since = datetime.now(tz=UTC) - timedelta(days=get_settings().chat_lookback_days)
    events, _scores, method = search_events(
        db,
        question,
        limit=limit,
        camera=camera,
        since=since,
    )
    # Always include today's summary if present.
    today = datetime.now(tz=UTC).date()
    summaries = list(
        db.scalars(
            select(DailySummary)
            .where(DailySummary.summary_date >= today - timedelta(days=2))
            .order_by(DailySummary.summary_date.desc())
            .limit(3)
        ).all()
    )
    if camera:
        summaries = [s for s in summaries if s.camera in (None, camera)]

    # If semantic search returns nothing, fall back to today's timeline.
    if not events:
        start, end = day_bounds(today)
        stmt = select(Event).where(Event.start_time >= start, Event.start_time < end)
        if camera:
            stmt = stmt.where(Event.camera == camera)
        events = list(db.scalars(stmt.order_by(Event.start_time.desc()).limit(limit)).all())
        method = "timeline-today"

    return events, summaries, method


def answer_extractive(question: str, events: list[Event], summaries: list[DailySummary]) -> str:
    lines = [f"Question: {question}", "", "Retrieved context:"]
    if summaries:
        lines.append("Daily summaries:")
        for s in summaries:
            cam = s.camera or "all cameras"
            lines.append(f"- {s.summary_date} ({cam}, {s.event_count} events):")
            for part in s.content.splitlines()[:8]:
                lines.append(f"  {part}")
    if events:
        lines.append("Related events:")
        for event in events:
            lines.append(f"- {_format_event_line(event)}")
    else:
        lines.append("No matching events found in the lookback window.")

    lines.extend(
        [
            "",
            "Answer:",
            _heuristic_answer(question, events, summaries),
        ]
    )
    return "\n".join(lines)


def _heuristic_answer(
    question: str,
    events: list[Event],
    summaries: list[DailySummary],
) -> str:
    q = question.lower()
    if not events and not summaries:
        return "I could not find related events or summaries. Try a broader query or import more Frigate events."

    if events:
        by_label: dict[str, int] = {}
        by_camera: dict[str, int] = {}
        for e in events:
            by_label[e.label] = by_label.get(e.label, 0) + 1
            by_camera[e.camera] = by_camera.get(e.camera, 0) + 1
        top = events[0]
        label_bits = ", ".join(f"{k}×{v}" for k, v in sorted(by_label.items(), key=lambda x: -x[1]))
        cam_bits = ", ".join(f"{k}×{v}" for k, v in sorted(by_camera.items(), key=lambda x: -x[1]))
        tip = top.caption or f"{top.label} at {top.camera}"
        if any(w in q for w in ("how many", "多少", "count", "几")):
            return f"I found {len(events)} related events ({label_bits}) across {cam_bits}."
        return (
            f"I found {len(events)} related events ({label_bits}). "
            f"Most relevant: {tip}."
        )

    s = summaries[0]
    return f"Based on the {s.summary_date} summary ({s.event_count} events): {s.content.splitlines()[0]}"


def answer_with_llm(question: str, events: list[Event], summaries: list[DailySummary]) -> str | None:
    context_parts: list[str] = []
    for s in summaries:
        context_parts.append(
            f"SUMMARY date={s.summary_date} camera={s.camera or 'all'} events={s.event_count}\n{s.content}"
        )
    for event in events:
        context_parts.append(_format_event_line(event))
    context = "\n".join(context_parts) if context_parts else "No context."
    messages = [
        {
            "role": "system",
            "content": (
                "You are a home security assistant with access to Frigate event captions "
                "and daily summaries. Answer only from the provided context. "
                "Cite event ids like [event:123] when relevant. If unsure, say so."
            ),
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        },
    ]
    return chat_completion(messages, temperature=0.2, max_tokens=500)


def run_chat(
    db: Session,
    question: str,
    *,
    conversation_id: int | None = None,
    camera: str | None = None,
    user_id: str = "local",
) -> tuple[Conversation, str, list[int], str]:
    settings = get_settings()
    camera = resolve_camera(db, camera)
    events, summaries, method = retrieve_context(db, question, camera=camera)
    related_ids = [e.id for e in events]

    mode = settings.chat_mode.lower()
    answer = None
    used = "extractive"
    if mode == "llm":
        answer = answer_with_llm(question, events, summaries)
        if answer:
            used = f"llm:{settings.llm_model}"
    if not answer:
        answer = answer_extractive(question, events, summaries)
        used = f"extractive/{method}"

    if conversation_id:
        conv = db.get(Conversation, conversation_id)
        if not conv:
            raise ValueError("conversation not found")
    else:
        conv = Conversation(user_id=user_id, title=question[:80], messages=[], related_event_ids=[])
        db.add(conv)
        db.flush()

    messages: list[dict[str, Any]] = list(conv.messages or [])
    messages.append({"role": "user", "content": question, "ts": datetime.now(tz=UTC).isoformat()})
    messages.append(
        {
            "role": "assistant",
            "content": answer,
            "ts": datetime.now(tz=UTC).isoformat(),
            "method": used,
            "related_event_ids": related_ids,
        }
    )
    conv.messages = messages
    flag_modified(conv, "messages")
    # Merge related ids
    existing = set(conv.related_event_ids or [])
    existing.update(related_ids)
    conv.related_event_ids = sorted(existing)
    flag_modified(conv, "related_event_ids")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv, answer, related_ids, used
