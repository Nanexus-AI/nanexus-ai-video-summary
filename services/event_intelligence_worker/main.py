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
    ResultStatus,
)

logger = logging.getLogger("event_intelligence_worker")


async def process_once(client: EventIntelligenceClient) -> bool:
    await client.capability()
    job = await client.next_job()
    if job is None:
        return False
    subject = await client.subject(job.job_id)
    for evidence in job.evidence_refs:
        await client.evidence(job.job_id, evidence.evidence_id)
    now = datetime.now(UTC)
    label = subject.labels[0] if subject.labels else "activity"
    camera = subject.camera or "unknown"
    result = EnrichmentResult(
        job_id=job.job_id,
        idempotency_key=job.idempotency_key,
        contract_version="1.0",
        status=ResultStatus.SUCCEEDED,
        model_invocation=ModelInvocationFacts(
            invocation_id=uuid4(),
            provider="nanexus-video-summary",
            model="deterministic-stub",
            model_version="1.0",
            outcome=ResultStatus.SUCCEEDED,
            started_at=now,
            completed_at=now,
            privacy_route=PrivacyRoute.LOCAL_ONLY,
            external_network_used=False,
        ),
        claims=(
            CaptionClaim(
                claim_type="caption",
                schema_version="1.0",
                text=f"{label} observed at {camera}",
                confidence=1.0,
                evidence_ids=tuple(item.evidence_id for item in job.evidence_refs),
            ),
        ),
        errors=(),
        completed_at=now,
    )
    await client.submit(result)
    logger.info("processor job completed job_id=%s trace_id=%s", job.job_id, job.trace_id)
    return True


async def run() -> None:
    settings = get_settings()
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
                processed = await process_once(client)
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


def main() -> None:
    logging.basicConfig(level=get_settings().log_level)
    asyncio.run(run())


if __name__ == "__main__":
    main()
