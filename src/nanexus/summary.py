from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from nanexus.config import get_settings
from nanexus.event_intelligence_client import ReviewDetail
from nanexus.llm import chat_completion
from nanexus.models import DailySummary, Event, Summary

RULE_VERSION = "rule-v1"
PROMPT_VERSION = "daily-security-v1"


@dataclass(frozen=True)
class ReviewContext:
    subject_id: str
    source_entity_id: str
    lifecycle: str
    site_id: str
    camera_id: str | None
    camera_name: str | None
    timezone: str
    started_at: datetime
    ended_at: datetime
    labels: tuple[str, ...]
    zones: tuple[str, ...]
    object_keys: tuple[str, ...]
    claim_ids: tuple[str, ...]
    caption: str | None
    tags: tuple[str, ...]
    high_quality_claim: bool
    decision_outcome: str | None
    feedback_verdict: str | None

    @property
    def duration_seconds(self) -> int:
        return max(0, int((self.ended_at - self.started_at).total_seconds()))


def _caption_text(value: dict[str, Any]) -> str | None:
    for key in ("text", "caption"):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def aggregate_reviews(details: list[ReviewDetail], default_timezone: str) -> list[ReviewContext]:
    """Collapse public Review DTOs to one context per canonical ReviewItem."""
    selected: dict[str, ReviewDetail] = {}
    for detail in details:
        if detail.review_item_id is None:
            continue
        key = str(detail.review_item_id)
        current = selected.get(key)
        rank = (detail.lifecycle == "ended", detail.last_occurred_at, detail.source_revision)
        current_rank = (
            current.lifecycle == "ended",
            current.last_occurred_at,
            current.source_revision,
        ) if current else None
        if current_rank is None or rank > current_rank:
            selected[key] = detail

    contexts: list[ReviewContext] = []
    for subject_id, detail in selected.items():
        claims = [claim for item in detail.enrichments for claim in item.claims]
        usable = [
            claim for claim in claims
            if not claim.abstained and not claim.evidence_unavailable
        ]
        captions = [
            (claim, _caption_text(claim.value))
            for claim in usable if claim.predicate == "caption"
        ]
        captions = [(claim, text) for claim, text in captions if text]
        best_caption = max(
            captions, key=lambda item: (item[0].confidence or 0.0, str(item[0].id)),
            default=(None, None),
        )
        tag_values: set[str] = set()
        for claim in usable:
            if claim.predicate != "tags":
                continue
            values = claim.value.get("tags", [])
            if isinstance(values, list):
                tag_values.update(str(value) for value in values if value)
        decision = max(detail.decisions, key=lambda item: item.revision, default=None)
        started_at = detail.start_at or detail.first_occurred_at
        ended_at = detail.end_at or detail.last_occurred_at
        contexts.append(
            ReviewContext(
                subject_id=subject_id,
                source_entity_id=detail.source_entity_id,
                lifecycle=detail.lifecycle,
                site_id=detail.site_id or "default",
                camera_id=str(detail.camera_id) if detail.camera_id else None,
                camera_name=detail.camera_name,
                timezone=detail.camera_timezone or default_timezone,
                started_at=started_at,
                ended_at=ended_at,
                labels=tuple(sorted(set(detail.labels))),
                zones=tuple(sorted(set(detail.zones))),
                object_keys=tuple(sorted({item.object_key for item in detail.objects})),
                claim_ids=tuple(sorted(str(claim.id) for claim in claims)),
                caption=best_caption[1],
                tags=tuple(sorted(tag_values)),
                high_quality_claim=bool(
                    best_caption[0] and (best_caption[0].confidence or 0.0) >= 0.5
                ),
                decision_outcome=decision.outcome if decision else None,
                feedback_verdict=detail.feedback.verdict if detail.feedback else None,
            )
        )
    return sorted(contexts, key=lambda item: (item.started_at, item.subject_id))


def importance_score(review: ReviewContext) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    decision_weights = {"escalate": 100, "send": 60, "suppress": -20, "no_action": 0}
    if review.decision_outcome:
        value = decision_weights.get(review.decision_outcome, 0)
        score += value
        reasons.append(f"decision:{review.decision_outcome}:{value:+d}")
    feedback_weights = {"important": 80, "not_important": -50, "false_positive": -100, "uncertain": 0}
    if review.feedback_verdict:
        value = feedback_weights.get(review.feedback_verdict, 0)
        score += value
        reasons.append(f"feedback:{review.feedback_verdict}:{value:+d}")
    label_weights = {"package": 30, "person": 25, "vehicle": 15, "dog": 5, "cat": 5}
    for label in review.labels:
        value = label_weights.get(label.lower(), 0)
        score += value
        if value:
            reasons.append(f"label:{label}:{value:+d}")
    if review.zones:
        score += 10
        reasons.append("zone:+10")
    duration_points = min(review.duration_seconds // 30, 20)
    score += duration_points
    if duration_points:
        reasons.append(f"duration:{duration_points:+d}")
    local_hour = review.started_at.astimezone(ZoneInfo(review.timezone)).hour
    if local_hour >= 22 or local_hour < 6:
        score += 20
        reasons.append("night:+20")
    if review.high_quality_claim:
        score += 20
        reasons.append("claim:+20")
    return score, reasons


def _duplicate_key(review: ReviewContext) -> tuple[str | None, tuple[str, ...], tuple[str, ...], str]:
    caption = re.sub(r"\W+", " ", (review.caption or "").lower()).strip()
    return review.camera_id, review.labels, review.zones, caption


def build_rule_summary_context(
    day: date, timezone: str, reviews: list[ReviewContext], *, highlight_limit: int = 10
) -> dict[str, Any]:
    """Create deterministic structured content and compress equivalent reviews."""
    label_counts = Counter(label for review in reviews for label in review.labels)
    camera_counts = Counter(review.camera_name or review.camera_id or "unknown" for review in reviews)
    grouped: dict[tuple[str | None, tuple[str, ...], tuple[str, ...], str], list[ReviewContext]] = {}
    for review in reviews:
        grouped.setdefault(_duplicate_key(review), []).append(review)
    highlights: list[dict[str, Any]] = []
    for group in grouped.values():
        ranked = sorted(
            group,
            key=lambda item: (-importance_score(item)[0], item.started_at, item.subject_id),
        )
        representative = ranked[0]
        score, reasons = importance_score(representative)
        highlights.append(
            {
                "subject_id": representative.subject_id,
                "source_subject_ids": sorted(item.subject_id for item in group),
                "claim_ids": sorted({claim for item in group for claim in item.claim_ids}),
                "repeat_count": len(group),
                "score": score,
                "score_reasons": reasons,
                "time": representative.started_at.astimezone(ZoneInfo(timezone)).isoformat(),
                "camera": representative.camera_name or representative.camera_id,
                "labels": list(representative.labels),
                "zones": list(representative.zones),
                "duration_seconds": representative.duration_seconds,
                "caption": representative.caption,
                "decision_outcome": representative.decision_outcome,
                "feedback_verdict": representative.feedback_verdict,
            }
        )
    highlights.sort(key=lambda item: (-item["score"], item["time"], item["subject_id"]))
    return {
        "schema_version": "summary-context-v1",
        "local_date": day.isoformat(),
        "timezone": timezone,
        "review_count": len(reviews),
        "unique_highlight_count": len(highlights),
        "by_label": dict(sorted(label_counts.items())),
        "by_camera": dict(sorted(camera_counts.items())),
        "highlights": highlights[:highlight_limit],
        "source_subject_ids": sorted(review.subject_id for review in reviews),
        "source_claim_ids": sorted({claim for review in reviews for claim in review.claim_ids}),
    }


def render_rule_summary_v1(context: dict[str, Any]) -> str:
    day = context["local_date"]
    count = context["review_count"]
    if count == 0:
        return f"{day}: no reviews recorded."
    labels = ", ".join(f"{key}={value}" for key, value in context["by_label"].items()) or "none"
    lines = [
        f"Summary for {day} ({context['timezone']})",
        f"Reviews: {count}",
        f"By label: {labels}",
        "Highlights:",
    ]
    for item in context["highlights"]:
        local_time = datetime.fromisoformat(item["time"]).strftime("%H:%M")
        description = item["caption"] or "/".join(item["labels"]) or "review"
        repeated = f" (x{item['repeat_count']})" if item["repeat_count"] > 1 else ""
        lines.append(f"- [{local_time}] {item['camera'] or 'unknown'}: {description}{repeated}")
    return "\n".join(lines)


def render_llm_summary_v1(
    context: dict[str, Any],
    *,
    completion: Callable[..., str | None] = chat_completion,
    max_input_chars: int = 16_000,
    max_tokens: int = 700,
    max_cost_micros: int = 25_000,
    input_cost_per_million_micros: int = 1_000_000,
    output_cost_per_million_micros: int = 10_000_000,
) -> tuple[str | None, dict[str, Any]]:
    serialized = json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    estimated_input_tokens = (len(serialized) + 3) // 4
    estimated_max_cost_micros = (
        estimated_input_tokens * input_cost_per_million_micros
        + max_tokens * output_cost_per_million_micros
        + 999_999
    ) // 1_000_000
    settings = get_settings()
    invocation: dict[str, Any] = {
        "prompt_version": PROMPT_VERSION,
        "provider": "openai-compatible",
        "model": settings.llm_model,
        "started_at": datetime.now(tz=UTC).isoformat(),
        "input_characters": len(serialized),
        "estimated_input_tokens": estimated_input_tokens,
        "max_input_characters": max_input_chars,
        "max_output_tokens": max_tokens,
        "estimated_max_cost_micros": estimated_max_cost_micros,
        "max_cost_micros": max_cost_micros,
        "status": "failed",
    }
    if len(serialized) > max_input_chars:
        invocation["error_code"] = "input_budget_exceeded"
        invocation["completed_at"] = datetime.now(tz=UTC).isoformat()
        return None, invocation
    if estimated_max_cost_micros > max_cost_micros:
        invocation["error_code"] = "cost_budget_exceeded"
        invocation["completed_at"] = datetime.now(tz=UTC).isoformat()
        return None, invocation
    messages = [
        {
            "role": "system",
            "content": (
                "Summarize only the supplied structured security Review context. "
                "Do not invent facts. Be concise and preserve notable times and cameras."
            ),
        },
        {"role": "user", "content": serialized},
    ]
    result = completion(messages, temperature=0.2, max_tokens=max_tokens)
    invocation["status"] = "succeeded" if result else "failed"
    if not result:
        invocation["error_code"] = "llm_unavailable"
    invocation["completed_at"] = datetime.now(tz=UTC).isoformat()
    return result, invocation


def queue_summary_generation(
    db: Session,
    *,
    day: date,
    timezone: str,
    site_id: str,
    camera_id: str | None,
    mode: str,
) -> Summary:
    """Create or return the idempotent observable generation record."""
    settings = get_settings()
    generator = "llm" if mode == "llm" else "rule"
    model_version = settings.llm_model if generator == "llm" else settings.summary_rule_version
    prompt_version = settings.summary_prompt_version if generator == "llm" else "none"
    filters = [
        Summary.summary_type == "daily",
        Summary.local_date == day,
        Summary.timezone == timezone,
        Summary.site_id == site_id,
        Summary.generator == generator,
        Summary.model_version == model_version,
        Summary.prompt_version == prompt_version,
    ]
    filters.append(Summary.camera_id.is_(None) if camera_id is None else Summary.camera_id == camera_id)
    existing = db.scalar(select(Summary).where(*filters))
    if existing is not None:
        return existing
    summary = Summary(
        summary_type="daily",
        local_date=day,
        timezone=timezone,
        site_id=site_id,
        camera_id=camera_id,
        content="",
        structured_content={"schema_version": "summary-context-v1"},
        source_subject_ids=[],
        generator=generator,
        model_version=model_version,
        prompt_version=prompt_version,
        status="queued",
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def complete_summary_generation(
    db: Session, summary: Summary, reviews: list[ReviewContext]
) -> Summary:
    """Generate from structured Review context and atomically activate the result."""
    settings = get_settings()
    context = build_rule_summary_context(summary.local_date, summary.timezone, reviews)
    rule_content = render_rule_summary_v1(context)
    content = rule_content
    effective_generator = "rule"
    invocation: dict[str, Any] | None = None
    if summary.generator == "llm":
        llm_content, invocation = render_llm_summary_v1(
            context,
            max_input_chars=settings.summary_llm_max_input_chars,
            max_tokens=settings.summary_llm_max_tokens,
            max_cost_micros=settings.summary_llm_max_cost_micros,
            input_cost_per_million_micros=(
                settings.summary_llm_input_cost_per_million_micros
            ),
            output_cost_per_million_micros=(
                settings.summary_llm_output_cost_per_million_micros
            ),
        )
        if llm_content:
            content = llm_content
            effective_generator = "llm"
        else:
            effective_generator = "rule-fallback"
    context["generation"] = {
        "requested_generator": summary.generator,
        "effective_generator": effective_generator,
        "rule_version": settings.summary_rule_version,
        "model_version": summary.model_version,
        "prompt_version": summary.prompt_version,
        "invocation": invocation,
    }
    summary.content = content
    summary.structured_content = context
    summary.source_subject_ids = context["source_subject_ids"]
    summary.status = "ready"
    now = datetime.now(tz=UTC)
    supersede_filters = [
        Summary.id != summary.id,
        Summary.summary_type == summary.summary_type,
        Summary.local_date == summary.local_date,
        Summary.timezone == summary.timezone,
        Summary.site_id == summary.site_id,
        Summary.status == "ready",
        Summary.superseded_at.is_(None),
    ]
    supersede_filters.append(
        Summary.camera_id.is_(None)
        if summary.camera_id is None
        else Summary.camera_id == summary.camera_id
    )
    for previous in db.scalars(select(Summary).where(*supersede_filters)).all():
        previous.superseded_at = now
        db.add(previous)
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def fail_summary_generation(db: Session, summary: Summary, error: Exception) -> None:
    summary.status = "failed"
    summary.structured_content = {
        **(summary.structured_content or {}),
        "error": {"code": type(error).__name__, "message": str(error)[:500]},
    }
    db.add(summary)
    db.commit()


def compare_legacy_and_review_summaries(
    *,
    day: date,
    timezone: str,
    legacy_events: list[Any],
    review_details: list[ReviewDetail],
) -> dict[str, Any]:
    """Fixed-fixture migration metrics; never used by the serving path."""
    legacy_start, legacy_end = day_bounds(day)
    local_start, local_end = local_day_bounds(day, timezone)
    legacy_in_day = [
        event for event in legacy_events if legacy_start <= event.start_time < legacy_end
    ]
    raw_subjects = [
        str(detail.review_item_id)
        for detail in review_details
        if detail.review_item_id is not None
    ]
    reviews = [
        review
        for review in aggregate_reviews(review_details, timezone)
        if local_start <= review.started_at < local_end
    ]
    structured = build_rule_summary_context(day, timezone, reviews)
    content = render_rule_summary_v1(structured)
    return {
        "schema_version": "summary-comparison-v1",
        "legacy": {
            "row_count": len(legacy_in_day),
            "duplicate_count": len(legacy_in_day)
            - len({event.frigate_id for event in legacy_in_day}),
            "covered_ids": sorted(event.frigate_id for event in legacy_in_day),
            "utc_bounds": [legacy_start.isoformat(), legacy_end.isoformat()],
        },
        "review_v1": {
            "raw_count": len(raw_subjects),
            "review_count": len(reviews),
            "duplicate_count": len(raw_subjects) - len(set(raw_subjects)),
            "covered_subject_ids": structured["source_subject_ids"],
            "utc_bounds": [local_start.isoformat(), local_end.isoformat()],
            "highlight_subject_ids": [
                item["subject_id"] for item in structured["highlights"]
            ],
            "output_sha256": hashlib.sha256(content.encode()).hexdigest(),
        },
    }


def day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=UTC)
    end = start + timedelta(days=1)
    return start, end


def local_day_bounds(day: date, timezone: str) -> tuple[datetime, datetime]:
    """Convert a site's local half-open day to UTC, preserving DST semantics."""
    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as error:
        raise ValueError(f"unknown timezone: {timezone}") from error
    local_start = datetime.combine(day, time.min, tzinfo=zone)
    local_end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=zone)
    return local_start.astimezone(UTC), local_end.astimezone(UTC)


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
