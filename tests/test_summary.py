import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from nanexus.event_intelligence_client import ReviewDetail
from nanexus.models import Summary
from nanexus.summary import (
    aggregate_reviews,
    build_rule_summary_context,
    compare_legacy_and_review_summaries,
    importance_score,
    local_day_bounds,
    render_llm_summary_v1,
    render_rule_summary,
    render_rule_summary_v1,
)

from .helpers import legacy_events


def test_rule_summary_is_deterministic(migration_fixture):
    assert render_rule_summary(date(2026, 8, 20), legacy_events(migration_fixture)) == migration_fixture["expected"]["rule_summary"]

def test_rule_summary_empty_day():
    assert render_rule_summary(date(2026, 8, 20), []) == "2026-08-20: no events recorded."


@pytest.mark.parametrize(
    ("day", "timezone", "expected_start", "expected_end"),
    [
        (
            date(2026, 8, 20),
            "UTC",
            datetime(2026, 8, 20, tzinfo=UTC),
            datetime(2026, 8, 21, tzinfo=UTC),
        ),
        (
            date(2026, 8, 20),
            "America/Toronto",
            datetime(2026, 8, 20, 4, tzinfo=UTC),
            datetime(2026, 8, 21, 4, tzinfo=UTC),
        ),
        (
            date(2026, 3, 8),
            "America/Toronto",
            datetime(2026, 3, 8, 5, tzinfo=UTC),
            datetime(2026, 3, 9, 4, tzinfo=UTC),
        ),
        (
            date(2026, 11, 1),
            "America/Toronto",
            datetime(2026, 11, 1, 4, tzinfo=UTC),
            datetime(2026, 11, 2, 5, tzinfo=UTC),
        ),
    ],
)
def test_local_day_bounds_include_dst(
    day: date, timezone: str, expected_start: datetime, expected_end: datetime
) -> None:
    assert local_day_bounds(day, timezone) == (expected_start, expected_end)


def test_local_day_bounds_reject_unknown_timezone() -> None:
    with pytest.raises(ValueError, match="unknown timezone"):
        local_day_bounds(date(2026, 8, 20), "Mars/Olympus")


def test_summary_model_is_application_owned_and_versioned() -> None:
    assert Summary.__tablename__ == "summaries"
    assert {column.name for column in Summary.__table__.columns} == {
        "id", "summary_type", "local_date", "timezone", "site_id", "camera_id",
        "content", "structured_content", "source_subject_ids", "generator",
        "model_version", "prompt_version", "status", "created_at", "superseded_at",
    }


def review_detail(
    subject: str,
    *,
    lifecycle: str = "ended",
    minute: int = 0,
    caption: str | None = "Person at the front door",
    confidence: float = 0.9,
    outcome: str = "send",
    feedback: str | None = None,
) -> ReviewDetail:
    claim_id = f"00000000-0000-0000-0001-{int(subject):012d}"
    return ReviewDetail.model_validate(
        {
            "id": f"00000000-0000-0000-0002-{int(subject):012d}",
            "review_item_id": f"00000000-0000-0000-0003-{int(subject):012d}",
            "source_instance_id": "00000000-0000-0000-0000-000000000010",
            "source_namespace": "frigate.review",
            "source_entity_id": f"review-{subject}",
            "source_revision": "2" if lifecycle == "ended" else "1",
            "lifecycle": lifecycle,
            "occurred_at": f"2026-08-20T12:{minute:02d}:00Z",
            "start_at": f"2026-08-20T12:{minute:02d}:00Z",
            "end_at": f"2026-08-20T12:{minute:02d}:45Z",
            "labels": ["person"],
            "zones": ["porch"],
            "camera_id": "00000000-0000-0000-0000-000000000020",
            "camera_name": "Front",
            "site_id": "home",
            "camera_timezone": "America/Toronto",
            "first_occurred_at": f"2026-08-20T12:{minute:02d}:00Z",
            "last_occurred_at": f"2026-08-20T12:{minute:02d}:45Z",
            "objects": [
                {"object_key": "person-1", "label": "person"},
                {"object_key": "person-1", "label": "person"},
            ],
            "enrichments": [
                {
                    "job_id": "00000000-0000-0000-0000-000000000030",
                    "status": "succeeded",
                    "subject_revision": "2",
                    "claims": [] if caption is None else [
                        {
                            "id": claim_id,
                            "predicate": "caption",
                            "value": {"text": caption},
                            "confidence": confidence,
                            "producer_type": "caption",
                            "producer_version": "1",
                        }
                    ],
                }
            ],
            "decisions": [
                {
                    "id": "00000000-0000-0000-0000-000000000040",
                    "revision": 1,
                    "outcome": outcome,
                }
            ],
            "feedback": {"verdict": feedback} if feedback else None,
        }
    )


def test_review_aggregation_deduplicates_subject_objects_and_prefers_ended() -> None:
    active = review_detail("1", lifecycle="active", caption=None)
    ended = review_detail("1", lifecycle="ended")
    contexts = aggregate_reviews([active, ended], "UTC")
    assert len(contexts) == 1
    assert contexts[0].lifecycle == "ended"
    assert contexts[0].object_keys == ("person-1",)
    assert contexts[0].caption == "Person at the front door"
    assert contexts[0].timezone == "America/Toronto"


def test_review_aggregation_degrades_without_claim_or_evidence() -> None:
    detail = review_detail("2", caption=None)
    context = aggregate_reviews([detail], "UTC")[0]
    assert context.caption is None
    assert context.claim_ids == ()
    structured = build_rule_summary_context(date(2026, 8, 20), "America/Toronto", [context])
    assert structured["review_count"] == 1
    assert render_rule_summary_v1(structured).endswith("Front: person")


def test_importance_rules_are_explainable_and_feedback_dominates() -> None:
    important = aggregate_reviews([review_detail("3", feedback="important")], "UTC")[0]
    false_positive = aggregate_reviews(
        [review_detail("4", feedback="false_positive")], "UTC"
    )[0]
    high_score, reasons = importance_score(important)
    low_score, _ = importance_score(false_positive)
    assert high_score > low_score
    assert "feedback:important:+80" in reasons
    assert "decision:send:+60" in reasons


def test_rule_summary_compresses_duplicates_and_is_stable() -> None:
    contexts = aggregate_reviews(
        [review_detail("5", minute=1), review_detail("6", minute=2)], "UTC"
    )
    first = build_rule_summary_context(date(2026, 8, 20), "America/Toronto", contexts)
    second = build_rule_summary_context(date(2026, 8, 20), "America/Toronto", list(reversed(contexts)))
    assert first == second
    assert first["review_count"] == 2
    assert first["unique_highlight_count"] == 1
    assert first["highlights"][0]["repeat_count"] == 2
    assert len(first["source_subject_ids"]) == 2


def test_llm_summary_consumes_only_structured_context_and_honors_budgets() -> None:
    calls = []

    def completion(messages, **kwargs):
        calls.append((messages, kwargs))
        return "LLM result"

    context = build_rule_summary_context(date(2026, 8, 20), "UTC", [])
    result, invocation = render_llm_summary_v1(
        context, completion=completion, max_input_chars=10_000, max_tokens=123
    )
    assert result == "LLM result"
    assert invocation["status"] == "succeeded"
    assert calls[0][1]["max_tokens"] == 123
    assert "snapshot" not in calls[0][0][1]["content"].lower()
    assert invocation["estimated_max_cost_micros"] <= invocation["max_cost_micros"]
    assert invocation["model"]
    assert invocation["completed_at"]

    fallback, failed = render_llm_summary_v1(
        context, completion=completion, max_input_chars=1
    )
    assert fallback is None
    assert failed["error_code"] == "input_budget_exceeded"

    cost_fallback, cost_failed = render_llm_summary_v1(
        context, completion=completion, max_input_chars=10_000, max_cost_micros=0
    )
    assert cost_fallback is None
    assert cost_failed["error_code"] == "cost_budget_exceeded"


def test_fixed_fixture_compares_legacy_and_review_summary_behavior(migration_fixture) -> None:
    comparison_fixture = json.loads(
        (Path(__file__).parent / "fixtures" / "summary-comparison.v1.json").read_text()
    )

    def at(detail: ReviewDetail, value: str) -> ReviewDetail:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return detail.model_copy(
            update={
                "occurred_at": timestamp,
                "start_at": timestamp,
                "end_at": timestamp,
                "first_occurred_at": timestamp,
                "last_occurred_at": timestamp,
            }
        )

    details = [
        at(
            review_detail(
                item["subject"],
                lifecycle=item["lifecycle"],
                caption=item["caption"],
                outcome=item["outcome"],
            ),
            item["timestamp"],
        )
        for item in comparison_fixture["review_cases"]
    ]
    result = compare_legacy_and_review_summaries(
        day=date.fromisoformat(comparison_fixture["local_date"]),
        timezone=comparison_fixture["timezone"],
        legacy_events=legacy_events(migration_fixture),
        review_details=details,
    )
    assert result["legacy"] == {
        "row_count": 3,
        "duplicate_count": 0,
        "covered_ids": ["evt-person-001", "evt-person-utc-boundary", "evt-vehicle-001"],
        "utc_bounds": ["2026-08-20T00:00:00+00:00", "2026-08-21T00:00:00+00:00"],
    }
    assert result["review_v1"] == comparison_fixture["expected_review_v1"]
