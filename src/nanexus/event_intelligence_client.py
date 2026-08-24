"""HTTP client for the public Event Intelligence Processor API v1."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, Field, ValidationError

from nanexus.event_intelligence_contracts import (
    Capability,
    EnrichmentResult,
    ProcessorJob,
)

logger = logging.getLogger(__name__)


class SubjectMetadata(BaseModel):
    subject_type: str
    subject_id: UUID
    subject_revision: str
    lifecycle: str
    labels: list[str]
    zones: list[str]
    camera: str | None
    site: str | None = None
    occurred_at: datetime | None = None


@dataclass(frozen=True)
class EvidenceContent:
    content: bytes
    content_type: str


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


class SubmitReceipt(BaseModel):
    job_id: UUID
    status: str
    accepted: bool
    claim_ids: list[UUID] = []
    evidence_ids: list[UUID] = []


class EventListItem(BaseModel):
    id: UUID
    lifecycle: str


class EventListPage(BaseModel):
    items: list[EventListItem]
    total: int
    limit: int
    offset: int


class ReviewObject(BaseModel):
    object_key: str
    label: str


class ReviewClaim(BaseModel):
    id: UUID
    predicate: str
    value: dict[str, Any]
    confidence: float | None = None
    abstained: bool = False
    evidence_unavailable: bool = False
    producer_type: str
    producer_version: str
    evidence_ids: list[UUID] = Field(default_factory=list)


class ReviewEnrichment(BaseModel):
    job_id: UUID
    status: str
    subject_revision: str
    claims: list[ReviewClaim] = Field(default_factory=list)


class ReviewDecision(BaseModel):
    id: UUID
    revision: int
    outcome: str
    confidence: float | None = None
    degraded: bool = False


class ReviewFeedback(BaseModel):
    verdict: str


class ReviewDetail(BaseModel):
    id: UUID
    review_item_id: UUID | None = None
    source_instance_id: UUID
    source_namespace: str
    source_entity_id: str
    source_revision: str
    lifecycle: str
    occurred_at: datetime
    start_at: datetime | None = None
    end_at: datetime | None = None
    labels: list[str] = Field(default_factory=list)
    zones: list[str] = Field(default_factory=list)
    camera_id: UUID | None = None
    camera_name: str | None = None
    site_id: str | None = None
    camera_timezone: str | None = None
    first_occurred_at: datetime
    last_occurred_at: datetime
    objects: list[ReviewObject] = Field(default_factory=list)
    enrichments: list[ReviewEnrichment] = Field(default_factory=list)
    decisions: list[ReviewDecision] = Field(default_factory=list)
    feedback: ReviewFeedback | None = None


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

    async def __aenter__(self) -> EventIntelligenceClient:
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

    async def evidence(self, job_id: UUID, evidence_id: UUID) -> EvidenceContent:
        response = await self._request(
            "GET", f"/api/v1/processor/jobs/{job_id}/evidence/{evidence_id}"
        )
        return EvidenceContent(
            content=response.content,
            content_type=response.headers.get("content-type", "").split(";", 1)[0].strip().lower(),
        )

    async def submit(self, result: EnrichmentResult) -> SubmitReceipt:
        response = await self._request(
            "POST",
            f"/api/v1/processor/jobs/{result.job_id}/result",
            json=result.model_dump(mode="json"),
            headers={"X-Trace-ID": str(result.job_id)},
        )
        return SubmitReceipt.model_validate(response.json())

    async def review_details(
        self, *, occurred_from: datetime, occurred_to: datetime
    ) -> list[ReviewDetail]:
        """Read deduplicated Review contexts through Event Intelligence API v1 only."""
        offset = 0
        details: list[ReviewDetail] = []
        while True:
            response = await self._request(
                "GET",
                "/api/v1/events",
                params={
                    "event_kind": "review",
                    "occurred_from": occurred_from.isoformat(),
                    "occurred_to": occurred_to.isoformat(),
                    "limit": 100,
                    "offset": offset,
                },
            )
            page = EventListPage.model_validate(response.json())
            for item in page.items:
                detail = await self._request("GET", f"/api/v1/events/{item.id}")
                parsed = ReviewDetail.model_validate(detail.json())
                if parsed.review_item_id is not None:
                    details.append(parsed)
            offset += len(page.items)
            if not page.items or offset >= page.total:
                return details
