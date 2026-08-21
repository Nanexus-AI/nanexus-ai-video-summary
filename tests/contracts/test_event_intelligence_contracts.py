import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nanexus.event_intelligence_contracts import Capability, EnrichmentResult, ProcessorJob

FIXTURE = json.loads((Path(__file__).parent / "fixtures/contract-v1.json").read_text())

def test_published_fixture_validates_independently() -> None:
    ProcessorJob.model_validate(FIXTURE["processor_job"])
    Capability.model_validate(FIXTURE["capability"])
    for result in FIXTURE["enrichment_results"].values():
        EnrichmentResult.model_validate(result)

def test_consumer_rejects_incompatible_versions() -> None:
    for key, model, payload in (
        ("contract_version", ProcessorJob, FIXTURE["processor_job"]),
        ("contract_version", EnrichmentResult, FIXTURE["enrichment_results"]["succeeded"]),
        ("capability_contract_version", Capability, FIXTURE["capability"]),
    ):
        changed = copy.deepcopy(payload)
        changed[key] = "2.0"
        with pytest.raises(ValidationError):
            model.model_validate(changed)

def test_consumer_rejects_urls_credentials_and_chain_of_thought() -> None:
    cases = (
        (ProcessorJob, FIXTURE["processor_job"], "source_url"),
        (EnrichmentResult, FIXTURE["enrichment_results"]["succeeded"], "chain_of_thought"),
        (Capability, FIXTURE["capability"], "frigate_credential"),
    )
    for model, original, field in cases:
        payload = {**original, field: "forbidden"}
        with pytest.raises(ValidationError, match="Extra inputs"):
            model.model_validate(payload)

def test_local_only_external_network_is_rejected_by_consumer() -> None:
    payload = copy.deepcopy(FIXTURE["enrichment_results"]["succeeded"])
    payload["model_invocation"]["external_network_used"] = True
    with pytest.raises(ValidationError, match="local_only"):
        EnrichmentResult.model_validate(payload)
