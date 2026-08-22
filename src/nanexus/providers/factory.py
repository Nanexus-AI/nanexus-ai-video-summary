"""Configuration-driven Provider selection with cloud providers disabled."""

from nanexus.config import Settings
from nanexus.providers.base import Provider
from nanexus.providers.stub import StubProvider


def create_provider(settings: Settings) -> Provider:
    if settings.model_provider == "stub":
        return StubProvider(dimensions=settings.embedding_dim)
    if settings.model_provider == "openclip":
        from nanexus.providers.openclip import OpenCLIPProvider

        return OpenCLIPProvider(
            model=settings.openclip_model,
            pretrained=settings.openclip_pretrained,
            device=settings.ai_device,
        )
    raise ValueError("MODEL_PROVIDER must be 'stub' or 'openclip'")
