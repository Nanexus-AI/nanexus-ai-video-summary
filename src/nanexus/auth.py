from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path

from fastapi import Header, HTTPException

from nanexus.config import get_settings


@dataclass(frozen=True)
class Principal:
    owner_id: str
    role: str
    sites: frozenset[str]

    def require(self, *roles: str, site_id: str | None = None) -> None:
        if self.role not in roles:
            raise HTTPException(status_code=403, detail="insufficient permission")
        if site_id and "*" not in self.sites and site_id not in self.sites:
            raise HTTPException(status_code=403, detail="site access denied")


def _static_principal(token: str, path: str) -> Principal | None:
    try:
        records = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        raise HTTPException(status_code=503, detail="identity provider unavailable")
    for record in records.get("tokens", []):
        candidate = str(record.get("token", ""))
        if candidate and hmac.compare_digest(candidate, token):
            role = str(record.get("role", "user"))
            if role not in {"reader", "user", "admin"}:
                break
            return Principal(
                owner_id=str(record["owner_id"]),
                role=role,
                sites=frozenset(str(item) for item in record.get("sites", [])),
            )
    return None


def current_principal(
    authorization: str | None = Header(default=None),
    x_nanexus_dev_owner: str | None = Header(default=None),
) -> Principal:
    settings = get_settings()
    if settings.auth_mode == "development":
        owner = x_nanexus_dev_owner or "local"
        return Principal(owner_id=owner, role="admin", sites=frozenset({"*"}))
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="authentication required")
    principal = _static_principal(authorization[7:], settings.auth_tokens_file)
    if principal is None:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return principal


def token_fingerprint(value: str) -> str:
    """Safe correlation helper: never log or return the credential itself."""
    return hashlib.sha256(value.encode()).hexdigest()[:12]
