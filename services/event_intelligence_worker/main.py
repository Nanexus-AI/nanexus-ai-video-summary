"""External deterministic Processor used by the first cross-repository slice."""

from __future__ import annotations

import asyncio
import logging
import signal
from datetime import UTC, datetime
from uuid import uuid4

from nanexus.config import get_settings
from nanexus.event_intelligence_client import EventIntelligenceClient, EventIntelligenceError
from nanexus.event_intelligence_contracts.enrichment_result import (
    CaptionClaim,
    EnrichmentResult,
    ModelInvocationFacts,
    PrivacyRoute,
    ResultError,
    ResultStatus,
    TagsClaim,
)
from nanexus.providers import Provider, ProviderAbstained, ProviderError, create_provider
from nanexus.providers.media import validate_image_evidence

logger = logging.getLogger("event_intelligence_worker")


def _result_error(
    *, job, provider: Provider, started_at: datetime, error: ProviderError
) -> EnrichmentResult:
    completed_at = datetime.now(UTC)
    status = (
        ResultStatus.ABSTAINED
        if isinstance(error, ProviderAbstained)
        else ResultStatus.FAILED
    )
    identity = provider.identity
    return EnrichmentResult(
        job_id=job.job_id,
        idempotency_key=job.idempotency_key,
        contract_version="1.0",
        status=status,
        model_invocation=ModelInvocationFacts(
            invocation_id=uuid4(),
            provider=identity.provider,
            model=identity.model,
            model_version=identity.model_version,
            outcome=status,
            started_at=started_at,
            completed_at=completed_at,
            privacy_route=PrivacyRoute.LOCAL_ONLY,
            external_network_used=False,
        ),
        claims=(),
        errors=(
            ResultError(code=error.code, reason=error.reason, retryable=error.retryable),
        ),
        completed_at=completed_at,
    )


async def process_once(
    client: EventIntelligenceClient, provider: Provider | None = None
) -> bool:
    settings = get_settings()
    provider = provider or create_provider(settings)
    await client.capability()
    job = await client.next_job()
    if job is None:
        return False
    await client.subject(job.job_id)
    evidence_ref = job.evidence_refs[0]
    started_at = datetime.now(UTC)
    try:
        evidence = await client.evidence(job.job_id, evidence_ref.evidence_id)
        image = validate_image_evidence(
            evidence, maximum_bytes=settings.model_max_image_bytes
        )
        analysis = await provider.analyze_image(
            image, timeout_seconds=settings.model_timeout_seconds
        )
    except ProviderError as error:
        if error.retryable:
            logger.warning(
                "model attempt deferred job_id=%s provider=%s code=%s retryable=true",
                job.job_id,
                provider.identity.provider,
                error.code,
            )
            raise
        result = _result_error(
            job=job, provider=provider, started_at=started_at, error=error
        )
        await client.submit(result)
        logger.info(
            "model attempt audited job_id=%s provider=%s code=%s status=%s",
            job.job_id,
            provider.identity.provider,
            error.code,
            result.status,
        )
        return True

    completed_at = datetime.now(UTC)
    identity = provider.identity
    evidence_ids = (evidence_ref.evidence_id,)
    claims = []
    requested = {item.output_type.value for item in job.requested_outputs}
    if "caption" in requested:
        claims.append(
            CaptionClaim(
                claim_type="caption",
                schema_version="1.0",
                text=analysis.summary,
                confidence=analysis.confidence,
                evidence_ids=evidence_ids,
            )
        )
    if "tags" in requested:
        claims.append(
            TagsClaim(
                claim_type="tags",
                schema_version="1.0",
                tags=analysis.tags,
                confidence=analysis.confidence,
                evidence_ids=evidence_ids,
            )
        )
    result = EnrichmentResult(
        job_id=job.job_id,
        idempotency_key=job.idempotency_key,
        contract_version="1.0",
        status=ResultStatus.SUCCEEDED,
        model_invocation=ModelInvocationFacts(
            invocation_id=uuid4(),
            provider=identity.provider,
            model=identity.model,
            model_version=identity.model_version,
            outcome=ResultStatus.SUCCEEDED,
            started_at=started_at,
            completed_at=completed_at,
            privacy_route=PrivacyRoute.LOCAL_ONLY,
            external_network_used=False,
        ),
        claims=tuple(claims),
        errors=(),
        completed_at=completed_at,
    )
    await client.submit(result)
    logger.info(
        "processor job completed job_id=%s trace_id=%s provider=%s model=%s "
        "pretrained=%s device=%s label_set=%s latency_ms=%d result_hash=%s "
        "evidence_id=%s",
        job.job_id,
        job.trace_id,
        identity.provider,
        identity.model,
        identity.pretrained_variant,
        identity.device,
        identity.label_set_version,
        int((completed_at - started_at).total_seconds() * 1000),
        analysis.result_hash,
        evidence_ref.evidence_id,
    )
    return True


async def run() -> None:
    settings = get_settings()
    provider = create_provider(settings)
    await provider.warmup(timeout_seconds=settings.model_timeout_seconds)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(name, stop.set)
    async with EventIntelligenceClient(
        settings.event_intelligence_url,
        settings.event_intelligence_token,
        timeout_seconds=settings.event_intelligence_timeout_seconds,
    ) as client:
        while not stop.is_set():
            try:
                processed = await process_once(client, provider)
                if not processed:
                    await asyncio.sleep(settings.event_intelligence_poll_seconds)
            except EventIntelligenceError as error:
                logger.warning(
                    "processor request failed code=%s retryable=%s",
                    error.code,
                    error.retryable,
                )
                await asyncio.sleep(
                    settings.event_intelligence_poll_seconds if error.retryable else 5.0
                )
            except ProviderError as error:
                logger.warning(
                    "provider failed code=%s retryable=%s", error.code, error.retryable
                )
                await asyncio.sleep(settings.event_intelligence_poll_seconds)


def main() -> None:
    logging.basicConfig(level=get_settings().log_level)
    asyncio.run(run())


if __name__ == "__main__":
    main()
