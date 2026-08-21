from nanexus.chat import answer_extractive
from .helpers import legacy_events
def test_extractive_chat_count_answer(migration_fixture):
    answer = answer_extractive("How many events?", legacy_events(migration_fixture)[:2], [])
    assert answer == migration_fixture["expected"]["chat"]["how_many_events"]
def test_extractive_chat_empty_context():
    assert "I could not find related events or summaries." in answer_extractive("What happened?", [], [])
