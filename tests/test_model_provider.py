import asyncio

import pytest

from nanexus.config import Settings
from nanexus.providers import ProviderHealth, create_provider
from nanexus.providers.stub import StubProvider


def test_stub_provider_contract_is_structured_and_deterministic() -> None:
    async def check() -> None:
        provider = StubProvider(dimensions=8)
        first = await provider.analyze_image(b"fixture", timeout_seconds=1)
        assert provider.health is ProviderHealth.HEALTHY
        assert provider.ready
        assert not provider.resources.external_network_required
        assert first == await provider.analyze_image(b"fixture", timeout_seconds=1)
        assert len(first.image_embedding) == 8
        assert first.result_hash

    asyncio.run(check())


def test_provider_factory_defaults_to_stub_and_rejects_unknown() -> None:
    settings = Settings(_env_file=None, model_provider="stub")
    assert isinstance(create_provider(settings), StubProvider)
    with pytest.raises(ValueError, match="MODEL_PROVIDER"):
        create_provider(Settings(_env_file=None, model_provider="cloud"))


def test_provider_calls_are_cancellable() -> None:
    async def check() -> None:
        task = asyncio.create_task(StubProvider().embed_text("person", timeout_seconds=1))
        assert await task

    asyncio.run(check())
