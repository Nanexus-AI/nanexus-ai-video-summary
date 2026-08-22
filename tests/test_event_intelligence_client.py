import asyncio
import functools

def async_test(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return asyncio.run(function(*args, **kwargs))
    return wrapper

import copy
import json
from pathlib import Path

import httpx
import pytest

from nanexus.event_intelligence_client import (
    EventIntelligenceClient,
    EventIntelligenceError,
    IncompatibleContractError,
)
from services.event_intelligence_worker.main import process_once

FIXTURE = json.loads(
    (Path(__file__).parent / "contracts" / "fixtures" / "contract-v1.json").read_text()
)


@async_test
async def test_client_checks_capability_and_rejects_incompatible_version() -> None:
    payload = copy.deepcopy(FIXTURE["capability"])
    payload["processor_contract_versions"] = ["1.0"]

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer secret"
        return httpx.Response(200, json=payload)

    async with EventIntelligenceClient(
        "http://ei", "secret", transport=httpx.MockTransport(handler)
    ) as client:
        assert (await client.capability()).claim_writeback

    payload["claim_writeback"] = False
    async with EventIntelligenceClient(
        "http://ei", "secret", transport=httpx.MockTransport(handler)
    ) as client:
        with pytest.raises(IncompatibleContractError) as caught:
            await client.capability()
        assert caught.value.retryable is False


@async_test
async def test_client_classifies_permission_and_transient_failures() -> None:
    async def denied(_: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"detail": "denied"})

    async with EventIntelligenceClient(
        "http://ei", "secret", transport=httpx.MockTransport(denied)
    ) as client:
        with pytest.raises(EventIntelligenceError) as caught:
            await client.next_job()
        assert caught.value.code == "http_403"
        assert caught.value.retryable is False

    async def unavailable(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    async with EventIntelligenceClient(
        "http://ei", "secret", transport=httpx.MockTransport(unavailable)
    ) as client:
        with pytest.raises(EventIntelligenceError) as caught:
            await client.next_job()
        assert caught.value.retryable is True


@async_test
async def test_stub_worker_completes_public_contract_loop() -> None:
    submitted = []
    job = FIXTURE["processor_job"]
    capability = FIXTURE["capability"]

    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/capabilities"):
            return httpx.Response(200, json=capability)
        if path.endswith("/jobs/next"):
            return httpx.Response(200, json=job)
        if path.endswith("/subject"):
            return httpx.Response(
                200,
                json={
                    "subject_type": "review_item",
                    "subject_id": job["subject_id"],
                    "subject_revision": job["subject_revision"],
                    "lifecycle": "ended",
                    "labels": ["person"],
                    "zones": ["porch"],
                    "camera": "front_yard",
                },
            )
        if "/evidence/" in path:
            return httpx.Response(200, content=b"fixture-image", headers={"content-type": "image/jpeg"})
        if path.endswith("/result"):
            submitted.append(json.loads(request.content))
            return httpx.Response(
                200,
                json={"job_id": job["job_id"], "status": "succeeded", "accepted": True},
            )
        raise AssertionError(path)

    async with EventIntelligenceClient(
        "http://ei", "secret", transport=httpx.MockTransport(handler)
    ) as client:
        assert await process_once(client)
    assert submitted[0]["claims"][0]["text"] == "person observed at front_yard"
    assert submitted[0]["model_invocation"]["external_network_used"] is False
