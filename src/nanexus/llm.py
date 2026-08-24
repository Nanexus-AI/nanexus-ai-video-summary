from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from nanexus.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMCompletion:
    content: str
    input_tokens: int | None
    output_tokens: int | None


def llm_configured() -> bool:
    return bool(get_settings().llm_api_key)


def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 800,
) -> str | None:
    """
    OpenAI-compatible Chat Completions call.
    Returns None when LLM is not configured or the request fails.
    """
    result = chat_completion_with_usage(
        messages, temperature=temperature, max_tokens=max_tokens
    )
    return result.content if result else None


def chat_completion_with_usage(
    messages: list[dict[str, str]], *, temperature: float = 0.2, max_tokens: int = 800
) -> LLMCompletion | None:
    settings = get_settings()
    if not settings.llm_api_key:
        return None

    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        usage = data.get("usage", {})
        return LLMCompletion(
            data["choices"][0]["message"]["content"].strip(),
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
    except Exception:
        logger.exception("LLM chat completion failed")
        return None
