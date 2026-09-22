"""Heavy-model boundary used by Search API over HTTP."""

from fastapi import FastAPI, HTTPException
from nanexus.config import get_settings
from nanexus.providers import ProviderError, create_provider
from pydantic import BaseModel, Field

settings = get_settings()
app = FastAPI(title="Nanexus Embedding Model Service", version="1.0")
provider = create_provider(settings)


class EmbedTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class EmbedResponse(BaseModel):
    vector: list[float]
    dimensions: int
    provider: str
    model: str
    model_version: str


@app.on_event("startup")
async def startup():
    await provider.warmup(timeout_seconds=settings.model_timeout_seconds)


@app.get("/health")
async def health():
    identity = provider.identity
    payload = {
        "status": "ok" if provider.ready else "not_ready",
        "provider": identity.provider,
        "model": identity.model,
        "device": identity.device,
    }
    payload.update(provider.runtime_capabilities())
    return payload


@app.post("/v1/embeddings/text", response_model=EmbedResponse)
async def embed_text(body: EmbedTextRequest):
    try:
        vector = await provider.embed_text(
            body.text, timeout_seconds=settings.model_timeout_seconds
        )
    except ProviderError as error:
        raise HTTPException(
            status_code=503 if error.retryable else 422, detail=error.code
        ) from error
    identity = provider.identity
    return EmbedResponse(
        vector=list(vector),
        dimensions=len(vector),
        provider=identity.provider,
        model=identity.model,
        model_version=identity.model_version,
    )
