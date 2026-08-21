from datetime import date
from nanexus.summary import render_rule_summary
from .helpers import legacy_events

def test_rule_summary_is_deterministic(migration_fixture):
    assert render_rule_summary(date(2026, 8, 20), legacy_events(migration_fixture)) == migration_fixture["expected"]["rule_summary"]

def test_rule_summary_empty_day():
    assert render_rule_summary(date(2026, 8, 20), []) == "2026-08-20: no events recorded."
