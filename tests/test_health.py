from nanexus.config import Settings
from nanexus.schemas import HealthResponse
from services.api import main as api


LEGACY_HEALTH_FIELDS = (
    "status",
    "database",
    "redis",
    "ai_mode",
    "summary_mode",
    "chat_mode",
)


class _FakeDB:
    def execute(self, _statement):
        return None


class _FakeQueue:
    def ping(self):
        return True


def _health(monkeypatch, **overrides) -> HealthResponse:
    monkeypatch.setattr(api, "settings", Settings(_env_file=None, **overrides))
    monkeypatch.setattr(api, "AIQueue", _FakeQueue)
    return api.health(_FakeDB())


def test_health_reports_stub_provider_independently_of_legacy_ai_mode(monkeypatch) -> None:
    response = _health(monkeypatch, ai_mode="openclip", model_provider="stub")
    payload = response.model_dump()
    assert payload["ai_mode"] == "openclip"
    assert payload["model_provider"] == "stub"


def test_health_reports_openclip_provider_independently_of_requested_device(
    monkeypatch,
) -> None:
    for requested_device in ("cpu", "cuda", "auto"):
        response = _health(
            monkeypatch,
            ai_mode="stub",
            model_provider="openclip",
            ai_device=requested_device,
        )
        payload = response.model_dump()
        assert payload["model_provider"] == "openclip"
        assert payload["ai_mode"] == "stub"
        assert "device" not in payload
        assert "cuda_available" not in payload


def test_health_keeps_legacy_ai_mode_and_stable_existing_fields(monkeypatch) -> None:
    response = _health(monkeypatch)
    payload = response.model_dump()
    for name in LEGACY_HEALTH_FIELDS:
        assert name in payload
    assert payload["ai_mode"] == "openclip"
    assert payload["summary_mode"] == "rule"
    assert payload["chat_mode"] == "extractive"
    assert payload["model_provider"] == "stub"
    assert set(payload) == set(LEGACY_HEALTH_FIELDS) | {"model_provider"}


def test_health_schema_marks_ai_mode_legacy_and_keeps_serialization_stable() -> None:
    schema = HealthResponse.model_json_schema()
    properties = schema["properties"]
    assert properties["ai_mode"]["deprecated"] is True
    assert "legacy" in properties["ai_mode"]["description"].lower()
    assert "MODEL_PROVIDER" in properties["model_provider"]["description"]
    required = set(schema["required"])
    assert set(LEGACY_HEALTH_FIELDS) <= required
    assert "model_provider" in required
    dumped = HealthResponse(
        status="ok",
        database=True,
        redis=True,
        ai_mode="openclip",
        summary_mode="rule",
        chat_mode="extractive",
        model_provider="stub",
    ).model_dump()
    assert list(dumped)[:6] == list(LEGACY_HEALTH_FIELDS)
    assert dumped["model_provider"] == "stub"
