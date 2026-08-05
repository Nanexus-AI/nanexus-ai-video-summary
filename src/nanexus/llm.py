from __future__ import annotations

import logging
from typing import Any

import httpx

from nanexus.config import get_settings

logger = logging.getLogger(__name__)


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
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        logger.exception("LLM chat completion failed")
        return None
