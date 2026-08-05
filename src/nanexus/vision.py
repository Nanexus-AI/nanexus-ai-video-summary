from __future__ import annotations

import hashlib
import logging
import threading
from dataclasses import dataclass
from io import BytesIO

from nanexus.config import get_settings

logger = logging.getLogger(__name__)

# Zero-shot prompts for security-camera style captions (OpenCLIP).
ZERO_SHOT_LABELS = [
    "a person",
    "a person wearing red clothes",
    "a person wearing blue clothes",
    "a person wearing black clothes",
    "a delivery person",
    "a package on the ground",
    "a UPS delivery truck",
    "an Amazon delivery van",
    "a black SUV",
    "a white car",
    "a red car",
    "a dog",
    "a cat",
    "someone carrying a cardboard box",
    "a person at the front door",
    "a vehicle in the driveway",
]


@dataclass
class VisionResult:
    caption: str
    embedding: list[float]
    tags: list[str]
    model: str


def stub_embedding(seed: str, dim: int) -> list[float]:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    values: list[float] = []
    while len(values) < dim:
        for b in digest:
            values.append((b / 255.0) * 2 - 1)
            if len(values) >= dim:
                break
        digest = hashlib.sha256(digest).digest()
    norm = sum(v * v for v in values) ** 0.5 or 1.0
    return [v / norm for v in values]


def stub_caption(camera: str, label: str, sub_label: str | None) -> str:
    where = camera.replace("_", " ")
    detail = sub_label or label
    return f"Stub vision: {detail} near {where}"


class VisionPipeline:
    """OpenCLIP image/text embeddings + zero-shot caption tags."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._lock = threading.Lock()
        self._model = None
        self._preprocess = None
        self._tokenizer = None
        self._device = None
        self._loaded = False

    @property
    def mode(self) -> str:
        return self._settings.ai_mode.lower()

    def ensure_loaded(self) -> None:
        if self.mode == "stub":
            return
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            self._load_openclip()
            self._loaded = True

    def _load_openclip(self) -> None:
        import open_clip
        import torch

        settings = self._settings
        device = settings.ai_device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(
            "loading OpenCLIP model=%s pretrained=%s device=%s",
            settings.openclip_model,
            settings.openclip_pretrained,
            device,
        )
        model, _, preprocess = open_clip.create_model_and_transforms(
            settings.openclip_model,
            pretrained=settings.openclip_pretrained,
        )
        model.eval()
        model.to(device)
        self._model = model
        self._preprocess = preprocess
        self._tokenizer = open_clip.get_tokenizer(settings.openclip_model)
        self._device = device
        logger.info("OpenCLIP ready on %s", device)

    def embed_text(self, text: str) -> list[float]:
        if self.mode == "stub":
            return stub_embedding(f"text:{text}", self._settings.embedding_dim)

        self.ensure_loaded()
        import torch

        assert self._model is not None and self._tokenizer is not None
        tokens = self._tokenizer([text])
        with torch.no_grad():
            tokens = tokens.to(self._device)
            features = self._model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
        return features[0].detach().cpu().tolist()

    def analyze_image(
        self,
        image_bytes: bytes | None,
        *,
        camera: str,
        label: str,
        sub_label: str | None,
    ) -> VisionResult:
        if self.mode == "stub" or image_bytes is None:
            seed = f"{camera}:{label}:{sub_label}:{len(image_bytes or b'')}"
            tags = [label]
            if sub_label:
                tags.append(sub_label)
            if image_bytes is None and self.mode != "stub":
                caption = f"{stub_caption(camera, label, sub_label)} (snapshot missing)"
                model = "stub-fallback"
            else:
                caption = stub_caption(camera, label, sub_label)
                model = "stub"
            return VisionResult(
                caption=caption,
                embedding=stub_embedding(seed, self._settings.embedding_dim),
                tags=tags,
                model=model,
            )

        self.ensure_loaded()
        from PIL import Image
        import torch

        assert self._model is not None and self._preprocess is not None and self._tokenizer is not None

        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image_input = self._preprocess(image).unsqueeze(0).to(self._device)

        with torch.no_grad():
            image_features = self._model.encode_image(image_input)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            text_tokens = self._tokenizer(ZERO_SHOT_LABELS).to(self._device)
            text_features = self._model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            probs = (100.0 * image_features @ text_features.T).softmax(dim=-1)[0]

        topk = torch.topk(probs, k=min(3, len(ZERO_SHOT_LABELS)))
        tags: list[str] = [label]
        if sub_label:
            tags.append(str(sub_label))
        top_labels: list[str] = []
        for idx, score in zip(topk.indices.tolist(), topk.values.tolist()):
            name = ZERO_SHOT_LABELS[idx]
            top_labels.append(f"{name} ({score:.0%})")
            short = name.removeprefix("a ").removeprefix("an ")
            if short not in tags:
                tags.append(short)

        where = camera.replace("_", " ")
        subject = sub_label or label
        caption = (
            f"{subject} near {where}; "
            f"OpenCLIP sees: {', '.join(top_labels)}"
        )
        embedding = image_features[0].detach().cpu().tolist()
        model_name = f"openclip:{self._settings.openclip_model}/{self._settings.openclip_pretrained}"
        return VisionResult(caption=caption, embedding=embedding, tags=tags, model=model_name)


_pipeline: VisionPipeline | None = None
_pipeline_lock = threading.Lock()


def get_vision_pipeline() -> VisionPipeline:
    global _pipeline
    if _pipeline is None:
        with _pipeline_lock:
            if _pipeline is None:
                _pipeline = VisionPipeline()
    return _pipeline
