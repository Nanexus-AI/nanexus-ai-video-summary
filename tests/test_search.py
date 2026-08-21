import pytest
from nanexus.search import search_events
from .helpers import legacy_events
class _Scalars:
    def __init__(self, values): self._values = values
    def all(self): return self._values
class KeywordSession:
    def __init__(self, values): self.values = values
    def scalars(self, _statement): return _Scalars(self.values)
@pytest.mark.parametrize("query,indexes", [("person", [2, 0]), ("driveway", [1]), ("package", [0]), ("no-match", [])])
def test_keyword_fallback_preserves_ranked_results(monkeypatch, migration_fixture, query, indexes):
    events = legacy_events(migration_fixture)
    monkeypatch.setattr("nanexus.search.get_vision_pipeline", lambda: type("P", (), {"mode": "stub"})())
    found, scores, method = search_events(KeywordSession([events[i] for i in indexes]), query, limit=3)
    assert [event.frigate_id for event in found] == migration_fixture["expected"]["search"][query]
    assert scores == []
    assert method == "keyword-stub"
