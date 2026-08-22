import asyncio
import sys

import pytest

from nanexus.providers.base import ProviderAbstained, ProviderError, ProviderHealth
from nanexus.providers.openclip import LABEL_SET_VERSION, OpenCLIPProvider


def test_openclip_is_lazy_and_identifies_zero_shot_label_set() -> None:
    sys.modules.pop("open_clip", None)
    sys.modules.pop("torch", None)
    provider = OpenCLIPProvider(model="ViT-B-32", pretrained="openai", device="cpu")
    assert provider.health is ProviderHealth.NOT_READY
    assert provider.identity.label_set_version == LABEL_SET_VERSION
    assert provider.identity.pretrained_variant == "openai"
    assert "open_clip" not in sys.modules
    assert "torch" not in sys.modules


def test_invalid_image_abstains_without_loading_model() -> None:
    provider = OpenCLIPProvider(model="ViT-B-32", pretrained="openai", device="cpu")
    with pytest.raises(ProviderAbstained, match="decodable") as caught:
        provider._decode_image(b"not-an-image")
    assert caught.value.code == "image_decode_failed"
    assert provider.health is ProviderHealth.NOT_READY


def test_empty_text_abstains() -> None:
    async def check() -> None:
        provider = OpenCLIPProvider(model="ViT-B-32", pretrained="openai")
        with pytest.raises(ProviderAbstained) as caught:
            await provider.embed_text(" ", timeout_seconds=1)
        assert caught.value.code == "empty_text"

    asyncio.run(check())


def test_timeout_is_retryable() -> None:
    async def check() -> None:
        provider = OpenCLIPProvider(model="ViT-B-32", pretrained="openai")

        def slow() -> None:
            import time

            time.sleep(0.05)

        with pytest.raises(ProviderError) as caught:
            await provider._bounded(slow, 0.001)
        assert caught.value.code == "model_timeout"
        assert caught.value.retryable

    asyncio.run(check())
