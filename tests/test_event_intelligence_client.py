import asyncio
import functools

def async_test(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return asyncio.run(function(*args, **kwargs))
    return wrapper

import copy
from io import BytesIO
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
from nanexus.providers.stub import StubProvider
from nanexus.providers.base import (
    AnalysisResult,
    ModelIdentity,
    Provider,
    ProviderError,
    ProviderHealth,
    ResourceRequirements,
)


def fixture_image() -> bytes:
    from PIL import Image

    output = BytesIO()
    Image.new("RGB", (2, 2), "red").save(output, format="JPEG")
    return output.getvalue()

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
            return httpx.Response(
                200, content=fixture_image(), headers={"content-type": "image/jpeg"}
            )
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
        assert await process_once(client, StubProvider())
    assert submitted[0]["claims"][0]["text"].startswith("Zero-shot stub")
    assert submitted[0]["claims"][1]["tags"] == ["activity"]
    assert submitted[0]["model_invocation"]["external_network_used"] is False


class RetryProvider(Provider):
    @property
    def identity(self):
        return ModelIdentity("test", "retry", "1.0", "fixture", "cpu", "labels-v1")

    @property
    def resources(self):
        return ResourceRequirements("cpu", 1)

    @property
    def health(self):
        return ProviderHealth.HEALTHY

    async def warmup(self, *, timeout_seconds):
        pass

    async def analyze_image(self, image, *, timeout_seconds):
        raise ProviderError("model_timeout", "timed out", retryable=True)

    async def embed_image(self, image, *, timeout_seconds):
        return ()

    async def embed_text(self, text, *, timeout_seconds):
        return ()


@async_test
async def test_retryable_model_failure_does_not_submit_or_lose_job() -> None:
    job = FIXTURE["processor_job"]
    submitted = False

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal submitted
        path = request.url.path
        if path.endswith("/capabilities"):
            return httpx.Response(200, json=FIXTURE["capability"])
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
                    "zones": [],
                    "camera": "front_yard",
                },
            )
        if "/evidence/" in path:
            return httpx.Response(
                200, content=fixture_image(), headers={"content-type": "image/jpeg"}
            )
        if path.endswith("/result"):
            submitted = True
        raise AssertionError(path)

    async with EventIntelligenceClient(
        "http://ei", "secret", transport=httpx.MockTransport(handler)
    ) as client:
        with pytest.raises(ProviderError, match="timed out"):
            await process_once(client, RetryProvider())
    assert submitted is False


@async_test
async def test_decode_failure_submits_auditable_abstention() -> None:
    job = FIXTURE["processor_job"]
    submitted = []

    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/capabilities"):
            return httpx.Response(200, json=FIXTURE["capability"])
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
                    "labels": [],
                    "zones": [],
                    "camera": None,
                },
            )
        if "/evidence/" in path:
            return httpx.Response(
                200, content=b"invalid", headers={"content-type": "image/jpeg"}
            )
        if path.endswith("/result"):
            submitted.append(json.loads(request.content))
            return httpx.Response(
                200,
                json={"job_id": job["job_id"], "status": "abstained", "accepted": True},
            )
        raise AssertionError(path)

    async with EventIntelligenceClient(
        "http://ei", "secret", transport=httpx.MockTransport(handler)
    ) as client:
        assert await process_once(client, StubProvider())
    assert submitted[0]["status"] == "abstained"
    assert submitted[0]["errors"][0]["code"] == "image_decode_failed"
