"""Deterministic local Provider used by default and for fallback tests."""

import hashlib

from nanexus.providers.base import (
    AnalysisResult,
    ModelIdentity,
    Provider,
    ProviderHealth,
    ResourceRequirements,
)


def stub_embedding(seed: bytes, dimensions: int) -> tuple[float, ...]:
    digest = hashlib.sha256(seed).digest()
    values: list[float] = []
    while len(values) < dimensions:
        values.extend((value / 255.0) * 2 - 1 for value in digest)
        digest = hashlib.sha256(digest).digest()
    values = values[:dimensions]
    norm = sum(value * value for value in values) ** 0.5 or 1.0
    return tuple(value / norm for value in values)


class StubProvider(Provider):
    def __init__(self, *, dimensions: int = 512) -> None:
        self._dimensions = dimensions

    @property
    def identity(self) -> ModelIdentity:
        return ModelIdentity(
            provider="nanexus",
            model="deterministic-stub",
            model_version="1.0+stub-labels-v1+cpu",
            pretrained_variant="builtin",
            device="cpu",
            label_set_version="stub-labels-v1",
        )

    @property
    def resources(self) -> ResourceRequirements:
        return ResourceRequirements(preferred_device="cpu", minimum_memory_mb=16)

    @property
    def health(self) -> ProviderHealth:
        return ProviderHealth.HEALTHY

    async def warmup(self, *, timeout_seconds: float) -> None:
        del timeout_seconds

    async def analyze_image(
        self, image: bytes, *, timeout_seconds: float
    ) -> AnalysisResult:
        del timeout_seconds
        material = b"stub-result:" + image
        return AnalysisResult(
            summary="Zero-shot stub enrichment for the selected snapshot",
            tags=("activity",),
            confidence=1.0,
            image_embedding=stub_embedding(b"image:" + image, self._dimensions),
            result_hash=hashlib.sha256(material).hexdigest(),
        )

    async def embed_image(
        self, image: bytes, *, timeout_seconds: float
    ) -> tuple[float, ...]:
        del timeout_seconds
        return stub_embedding(b"image:" + image, self._dimensions)

    async def embed_text(
        self, text: str, *, timeout_seconds: float
    ) -> tuple[float, ...]:
        del timeout_seconds
        return stub_embedding(b"text:" + text.encode(), self._dimensions)
