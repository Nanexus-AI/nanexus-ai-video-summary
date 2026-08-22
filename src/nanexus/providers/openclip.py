"""Local OpenCLIP zero-shot enrichment Provider.

This module deliberately performs no heavy imports at module import time.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import threading
from io import BytesIO
from typing import Any, Callable, TypeVar

from nanexus.providers.base import (
    AnalysisResult,
    ModelIdentity,
    Provider,
    ProviderAbstained,
    ProviderError,
    ProviderHealth,
    ResourceRequirements,
)

LABEL_SET_VERSION = "security-camera-en-v1"
ZERO_SHOT_LABELS = (
    "person",
    "person wearing red clothes",
    "person wearing blue clothes",
    "person wearing black clothes",
    "delivery person",
    "package on the ground",
    "delivery truck",
    "black SUV",
    "white car",
    "red car",
    "dog",
    "cat",
    "person carrying a cardboard box",
    "person at the front door",
    "vehicle in the driveway",
)
T = TypeVar("T")


class OpenCLIPProvider(Provider):
    """Image/text embeddings and zero-shot labels, not a caption/VLM model."""

    def __init__(self, *, model: str, pretrained: str, device: str = "auto") -> None:
        self.model_name = model
        self.pretrained = pretrained
        self.requested_device = device
        self._model: Any = None
        self._preprocess: Any = None
        self._tokenizer: Any = None
        self._device: str | None = None
        self._runtime_version = "unloaded"
        self._load_lock = threading.Lock()
        self._failed = False

    @property
    def identity(self) -> ModelIdentity:
        device = self._device or self.requested_device
        version = f"{self.pretrained}+{LABEL_SET_VERSION}+{device}+{self._runtime_version}"
        return ModelIdentity(
            provider="openclip",
            model=self.model_name,
            model_version=version[:255],
            pretrained_variant=self.pretrained,
            device=device,
            label_set_version=LABEL_SET_VERSION,
        )

    @property
    def resources(self) -> ResourceRequirements:
        return ResourceRequirements(
            preferred_device=self.requested_device,
            minimum_memory_mb=2048,
            external_network_required=False,
        )

    @property
    def health(self) -> ProviderHealth:
        if self._failed:
            return ProviderHealth.FAILED
        if self._model is None:
            return ProviderHealth.NOT_READY
        return ProviderHealth.HEALTHY

    def _load(self) -> None:
        if self._model is not None:
            return
        with self._load_lock:
            if self._model is not None:
                return
            try:
                import open_clip
                import torch

                device = self.requested_device
                if device == "auto":
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                model, _, preprocess = open_clip.create_model_and_transforms(
                    self.model_name, pretrained=self.pretrained
                )
                model.eval()
                model.to(device)
                self._model = model
                self._preprocess = preprocess
                self._tokenizer = open_clip.get_tokenizer(self.model_name)
                self._device = device
                self._runtime_version = getattr(open_clip, "__version__", "unknown")
            except Exception as error:
                self._failed = True
                raise ProviderError(
                    "model_load_failed", type(error).__name__, retryable=False
                ) from error

    @staticmethod
    def _decode_image(image: bytes) -> Any:
        try:
            from PIL import Image, UnidentifiedImageError

            candidate = Image.open(BytesIO(image))
            candidate.verify()
            return Image.open(BytesIO(image)).convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as error:
            raise ProviderAbstained(
                "image_decode_failed", "Evidence is not a decodable image"
            ) from error

    async def _bounded(self, operation: Callable[[], T], timeout_seconds: float) -> T:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(operation), timeout=timeout_seconds
            )
        except TimeoutError as error:
            raise ProviderError(
                "model_timeout", "OpenCLIP operation timed out", retryable=True
            ) from error

    async def warmup(self, *, timeout_seconds: float) -> None:
        await self._bounded(self._load, timeout_seconds)

    def _image_features(self, image: bytes) -> Any:
        decoded = self._decode_image(image)
        self._load()
        import torch

        tensor = self._preprocess(decoded).unsqueeze(0).to(self._device)
        with torch.no_grad():
            features = self._model.encode_image(tensor)
            return features / features.norm(dim=-1, keepdim=True)

    async def embed_image(
        self, image: bytes, *, timeout_seconds: float
    ) -> tuple[float, ...]:
        features = await self._bounded(
            lambda: self._image_features(image), timeout_seconds
        )
        return tuple(features[0].detach().cpu().tolist())

    async def embed_text(
        self, text: str, *, timeout_seconds: float
    ) -> tuple[float, ...]:
        if not text.strip():
            raise ProviderAbstained("empty_text", "Text embedding input is empty")

        def infer() -> tuple[float, ...]:
            self._load()
            import torch

            with torch.no_grad():
                features = self._model.encode_text(
                    self._tokenizer([text]).to(self._device)
                )
                features = features / features.norm(dim=-1, keepdim=True)
            return tuple(features[0].detach().cpu().tolist())

        return await self._bounded(infer, timeout_seconds)

    async def analyze_image(
        self, image: bytes, *, timeout_seconds: float
    ) -> AnalysisResult:
        def infer() -> AnalysisResult:
            image_features = self._image_features(image)
            import torch

            with torch.no_grad():
                text_features = self._model.encode_text(
                    self._tokenizer(list(ZERO_SHOT_LABELS)).to(self._device)
                )
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                probabilities = (100 * image_features @ text_features.T).softmax(dim=-1)[0]
                top = torch.topk(probabilities, k=3)
            tags = tuple(ZERO_SHOT_LABELS[index] for index in top.indices.tolist())
            confidence = float(top.values[0].item())
            embedding = tuple(image_features[0].detach().cpu().tolist())
            material = json.dumps(
                {
                    "identity": self.identity.model_version,
                    "tags": tags,
                    "confidence": round(confidence, 8),
                    "embedding": [round(value, 8) for value in embedding],
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
            return AnalysisResult(
                summary="OpenCLIP zero-shot labels: " + ", ".join(tags),
                tags=tags,
                confidence=confidence,
                image_embedding=embedding,
                result_hash=hashlib.sha256(material).hexdigest(),
            )

        return await self._bounded(infer, timeout_seconds)
