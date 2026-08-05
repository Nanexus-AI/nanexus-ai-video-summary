from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx

from nanexus.config import get_settings

logger = logging.getLogger(__name__)


def snapshots_dir() -> Path:
    path = Path(get_settings().snapshots_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def local_snapshot_path(frigate_id: str) -> Path:
    return snapshots_dir() / f"{frigate_id}.jpg"


def fetch_snapshot_bytes(uri: str | None, *, timeout: float = 30.0) -> bytes | None:
    """Load snapshot bytes from http(s), file://, or a local path under snapshots_dir."""
    if not uri:
        return None

    settings = get_settings()
    parsed = urlparse(uri)

    if parsed.scheme in ("http", "https"):
        headers = {}
        if settings.frigate_token:
            headers["Authorization"] = f"Bearer {settings.frigate_token}"
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                resp = client.get(uri, headers=headers)
                resp.raise_for_status()
                return resp.content
        except Exception:
            logger.exception("failed to download snapshot from %s", uri)
            return None

    if parsed.scheme == "file":
        path = Path(unquote(parsed.path))
        if path.is_file():
            return path.read_bytes()
        logger.warning("file snapshot missing: %s", path)
        return None

    # Bare local path or filename under snapshots_dir
    path = Path(uri)
    if not path.is_file():
        path = snapshots_dir() / Path(uri).name
    if path.is_file():
        return path.read_bytes()

    logger.warning("unsupported or missing snapshot uri: %s", uri)
    return None
