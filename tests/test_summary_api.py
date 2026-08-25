from datetime import UTC, date, datetime
from uuid import UUID

from nanexus.models import Summary
from nanexus.queue import SummaryJob
from nanexus.schemas import SummaryRebuildV1Request
from services.api import main as api


def ready_summary() -> Summary:
    return Summary(
        id=UUID("00000000-0000-0000-0000-000000000501"),
        summary_type="daily",
        local_date=date(2026, 8, 20),
        timezone="America/Toronto",
        site_id="home",
        camera_id=None,
        content="precomputed",
        structured_content={"schema_version": "summary-context-v1"},
        source_subject_ids=["00000000-0000-0000-0000-000000000502"],
        generator="rule",
        model_version="rule-v1",
        prompt_version="none",
        status="ready",
        created_at=datetime(2026, 8, 21, tzinfo=UTC),
    )


class FakeDB:
    def __init__(self, summary: Summary | None = None):
        self.summary = summary
        self.commits = 0

    def scalar(self, _statement):
        return self.summary

    def get(self, _model, _identifier):
        return self.summary

    def add(self, _value):
        pass

    def commit(self):
        self.commits += 1


def test_summary_v1_reads_precomputed_result_without_generation(monkeypatch) -> None:
    summary = ready_summary()
    response = api.summary_v1(
        date(2026, 8, 20), "America/Toronto", "home", None, FakeDB(summary),
        api.Principal("test", "reader", frozenset({"*"})),
    )
    assert response.summary is not None
    assert response.summary.content == "precomputed"
    assert response.summary.source_subject_ids == summary.source_subject_ids


def test_rebuild_v1_only_enqueues_and_exposes_job_status(monkeypatch) -> None:
    summary = ready_summary()
    summary.status = "queued"
    queued = []

    class FakeQueue:
        def enqueue_summary(self, job):
            queued.append(job)

    monkeypatch.setattr(api, "queue_summary_generation", lambda *_args, **_kwargs: summary)
    monkeypatch.setattr(api, "AIQueue", FakeQueue)
    db = FakeDB(summary)
    response = api.rebuild_summary_v1(
        SummaryRebuildV1Request(
            local_date=date(2026, 8, 20),
            timezone="America/Toronto",
            site_id="home",
            mode="rule",
        ),
        db,
        api.Principal("test", "admin", frozenset({"*"})),
    )
    assert response.id == summary.id
    assert response.status == "queued"
    assert queued[0].summary_id == str(summary.id)
    assert queued[0].timezone == "America/Toronto"
    assert db.commits == 1


def test_summary_job_round_trip_keeps_site_timezone_and_generation_id() -> None:
    job = SummaryJob(
        summary_id="00000000-0000-0000-0000-000000000601",
        summary_date="2026-08-20",
        camera=None,
        mode="rule",
        timezone="America/Toronto",
        site_id="home",
    )
    assert SummaryJob.from_json(job.to_json()) == job
