import json

import pytest
from fastapi import HTTPException

from nanexus.auth import _static_principal
from nanexus.compatibility import evaluate_event_capability
from nanexus.config import Settings


def test_production_fails_closed_without_identity_files() -> None:
    settings = Settings(
        deployment_mode="production",
        auth_mode="development",
        public_base_url="https://summary.example",
        event_intelligence_public_url="https://events.example",
    )
    with pytest.raises(RuntimeError, match="refuses development"):
        settings.validate_runtime()


def test_static_identity_binds_owner_role_and_site(tmp_path) -> None:
    path = tmp_path / "identities.json"
    path.write_text(
        json.dumps({"tokens": [{"token": "secret", "owner_id": "alice", "role": "user", "sites": ["home"]}]}),
        encoding="utf-8",
    )
    principal = _static_principal("secret", str(path))
    assert principal and principal.owner_id == "alice"
    principal.require("user", site_id="home")
    with pytest.raises(HTTPException) as denied:
        principal.require("user", site_id="other")
    assert denied.value.status_code == 403


@pytest.mark.parametrize(
    "mutation",
    [
        {"api_versions": ["0.9"]},
        {"canonical_schema_versions": []},
        {"processor_contract_versions": ["2.0"]},
        {"capability_contract_version": "2.0"},
    ],
)
def test_incompatible_event_capability_is_rejected(mutation) -> None:
    payload = {
        "capability_contract_version": "1.0",
        "api_versions": ["1.0"],
        "canonical_schema_versions": ["1.0"],
        "processor_contract_versions": ["1.0"],
        "future_unknown_field": True,
    }
    payload.update(mutation)
    assert not evaluate_event_capability(payload, Settings()).compatible


def test_compatible_capability_tolerates_unknown_fields() -> None:
    payload = {
        "capability_contract_version": "1.0",
        "api_versions": ["1.0"],
        "canonical_schema_versions": ["1.0"],
        "processor_contract_versions": ["1.0"],
        "future_unknown_field": {"safe": True},
    }
    assert evaluate_event_capability(payload, Settings()).compatible


def test_credentials_are_not_present_in_public_capability_schema() -> None:
    from nanexus.schemas import ClientCapabilitiesV1

    schema = json.dumps(ClientCapabilitiesV1.model_json_schema()).lower()
    assert "token" not in schema and "internal_url" not in schema and "prompt" not in schema
