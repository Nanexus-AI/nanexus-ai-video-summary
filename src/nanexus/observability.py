from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nanexus.config import get_settings
from nanexus.models import ChatMessage, Summary
from nanexus.queue import AIQueue


def snapshot(db: Session, queue: AIQueue | None = None) -> dict[str, Any]:
    queue = queue or AIQueue()
    client = queue._client
    settings = get_settings()
    now = datetime.now(tz=UTC)
    latest_summary = db.scalar(select(func.max(Summary.created_at)))
    freshness = max(0.0, (now - latest_summary).total_seconds()) if latest_summary else None
    return {
        "job_backlog": {
            "embedding": client.llen(settings.embedding_queue_key),
            "summary": client.llen(settings.summary_queue_key),
            "chat": client.llen(settings.chat_queue_key),
        },
        "retry_total": int(client.get("nanexus:metrics:retry_total") or 0),
        "dlq_count": client.llen(settings.embedding_dlq_key),
        "dlq_recent_error": client.get("nanexus:metrics:dlq_recent_error"),
        "model_latency_seconds": float(client.get("nanexus:metrics:model_latency_seconds") or 0),
        "model_error_total": int(client.get("nanexus:metrics:model_error_total") or 0),
        "token_total": int(db.scalar(select(func.sum(ChatMessage.input_tokens))) or 0),
        "cost_micros_total": int(db.scalar(select(func.sum(ChatMessage.cost_micros))) or 0),
        "search_latency_seconds": float(client.get("nanexus:metrics:search_latency_seconds") or 0),
        "summary_freshness_seconds": freshness,
        "worker_heartbeats": {
            name: client.get(f"nanexus:heartbeat:{name}")
            for name in ("embedding", "enrichment", "summary", "chat")
        },
    }


def prometheus(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for queue_name, value in data["job_backlog"].items():
        lines.append(f'nanexus_job_backlog{{queue="{queue_name}"}} {value}')
    for name in ("retry_total", "dlq_count", "model_latency_seconds", "model_error_total", "token_total", "cost_micros_total", "search_latency_seconds"):
        lines.append(f"nanexus_{name} {data[name]}")
    freshness = data["summary_freshness_seconds"]
    if freshness is not None:
        lines.append(f"nanexus_summary_freshness_seconds {freshness}")
    return "\n".join(lines) + "\n"
