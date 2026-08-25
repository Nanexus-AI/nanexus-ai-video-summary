from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from nanexus.config import Settings


@dataclass(frozen=True)
class CompatibilityStatus:
    compatible: bool
    reason: str | None = None


def evaluate_event_capability(payload: dict[str, Any], settings: Settings) -> CompatibilityStatus:
    required = {
        "capability_contract_version": settings.expected_capability_version,
        "api_versions": settings.expected_event_api_version,
        "canonical_schema_versions": settings.expected_canonical_schema_version,
        "processor_contract_versions": settings.expected_processor_contract_version,
    }
    for field, expected in required.items():
        actual = payload.get(field)
        accepted = actual == expected if isinstance(actual, str) else expected in (actual or [])
        if not accepted:
            return CompatibilityStatus(False, f"incompatible {field}")
    return CompatibilityStatus(True)


def check_event_intelligence(settings: Settings) -> CompatibilityStatus:
    headers = {"Authorization": f"Bearer {settings.event_intelligence_token}"}
    try:
        response = httpx.get(
            f"{settings.event_intelligence_url.rstrip('/')}/api/v1/processor/capabilities",
            headers=headers,
            timeout=settings.event_intelligence_timeout_seconds,
        )
        response.raise_for_status()
        return evaluate_event_capability(response.json(), settings)
    except (httpx.HTTPError, ValueError, TypeError):
        return CompatibilityStatus(False, "event intelligence capability unavailable")
