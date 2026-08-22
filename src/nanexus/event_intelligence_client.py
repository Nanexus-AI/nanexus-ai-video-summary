"""HTTP client for the public Event Intelligence Processor API v1."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, ValidationError

from nanexus.event_intelligence_contracts import Capability, EnrichmentResult, ProcessorJob

logger = logging.getLogger(__name__)


class SubjectMetadata(BaseModel):
    subject_type: str
    subject_id: UUID
    subject_revision: str
    lifecycle: str
    labels: list[str]
    zones: list[str]
    camera: str | None


@dataclass(frozen=True)
class EventIntelligenceError(Exception):
    code: str
    message: str
    retryable: bool
    status_code: int | None = None

    def __str__(self) -> str:
        return self.message


class IncompatibleContractError(EventIntelligenceError):
    pass


class EventIntelligenceClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout_seconds: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout_seconds),
            transport=transport,
            headers={"Authorization": f"Bearer {token}"},
        )

    async def __aenter__(self) -> "EventIntelligenceClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = await self._client.request(method, path, **kwargs)
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise EventIntelligenceError(
                "event_intelligence_unavailable", type(error).__name__, True
            ) from error
        if response.is_error:
            retryable = response.status_code in {408, 429, 502, 503, 504}
            raise EventIntelligenceError(
                f"http_{response.status_code}",
                f"Event Intelligence request failed ({response.status_code})",
                retryable,
                response.status_code,
            )
        return response

    async def health(self) -> bool:
        response = await self._request("GET", "/api/v1/health")
        return response.json().get("status") == "ok"

    async def capability(self) -> Capability:
        response = await self._request("GET", "/api/v1/processor/capabilities")
        try:
            capability = Capability.model_validate(response.json())
        except ValidationError as error:
            raise IncompatibleContractError(
                "invalid_capability", "Capability response is not v1 compatible", False
            ) from error
        required = (
            "1.0" in capability.processor_contract_versions
            and "1.0" in capability.enrichment_result_versions
            and capability.claim_writeback
            and capability.model_invocation
        )
        if not required:
            raise IncompatibleContractError(
                "missing_capability", "Required Processor v1 capabilities are unavailable", False
            )
        return capability

    async def next_job(self) -> ProcessorJob | None:
        response = await self._request("GET", "/api/v1/processor/jobs/next")
        if response.json() is None:
            return None
        try:
            return ProcessorJob.model_validate(response.json())
        except ValidationError as error:
            raise IncompatibleContractError(
                "incompatible_job", "Processor Job is not v1 compatible", False
            ) from error

    async def subject(self, job_id: UUID) -> SubjectMetadata:
        response = await self._request("GET", f"/api/v1/processor/jobs/{job_id}/subject")
        return SubjectMetadata.model_validate(response.json())

    async def evidence(self, job_id: UUID, evidence_id: UUID) -> bytes:
        response = await self._request(
            "GET", f"/api/v1/processor/jobs/{job_id}/evidence/{evidence_id}"
        )
        return response.content

    async def submit(self, result: EnrichmentResult) -> bool:
        response = await self._request(
            "POST",
            f"/api/v1/processor/jobs/{result.job_id}/result",
            json=result.model_dump(mode="json"),
            headers={"X-Trace-ID": str(result.job_id)},
        )
        return bool(response.json()["accepted"])
