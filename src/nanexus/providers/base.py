"""Transport-neutral provider contract used by isolated model workers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class ProviderHealth(StrEnum):
    HEALTHY = "healthy"
    NOT_READY = "not_ready"
    FAILED = "failed"


@dataclass(frozen=True)
class ModelIdentity:
    provider: str
    model: str
    model_version: str
    pretrained_variant: str
    device: str
    label_set_version: str


@dataclass(frozen=True)
class ResourceRequirements:
    preferred_device: str
    minimum_memory_mb: int
    external_network_required: bool = False


@dataclass(frozen=True)
class AnalysisResult:
    """Zero-shot output. ``summary`` is intentionally not a VLM caption."""

    summary: str
    tags: tuple[str, ...]
    confidence: float | None
    image_embedding: tuple[float, ...]
    result_hash: str


class ProviderError(RuntimeError):
    def __init__(self, code: str, reason: str, *, retryable: bool) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason
        self.retryable = retryable


class ProviderAbstained(ProviderError):
    def __init__(self, code: str, reason: str) -> None:
        super().__init__(code, reason, retryable=False)


class Provider(ABC):
    @property
    @abstractmethod
    def identity(self) -> ModelIdentity: ...

    @property
    @abstractmethod
    def resources(self) -> ResourceRequirements: ...

    @property
    @abstractmethod
    def health(self) -> ProviderHealth: ...

    @property
    def ready(self) -> bool:
        return self.health is ProviderHealth.HEALTHY

    def runtime_capabilities(self) -> dict[str, object]:
        identity = self.identity
        return {
            "provider": identity.provider,
            "model": identity.model,
            "device": identity.device,
            "requested_device": identity.device,
            "cuda_available": False,
            "torch_cuda_build": None,
        }

    @abstractmethod
    async def warmup(self, *, timeout_seconds: float) -> None: ...

    @abstractmethod
    async def analyze_image(
        self, image: bytes, *, timeout_seconds: float
    ) -> AnalysisResult: ...

    @abstractmethod
    async def embed_image(
        self, image: bytes, *, timeout_seconds: float
    ) -> tuple[float, ...]: ...

    @abstractmethod
    async def embed_text(
        self, text: str, *, timeout_seconds: float
    ) -> tuple[float, ...]: ...
