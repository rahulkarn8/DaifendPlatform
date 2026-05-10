"""API key verification (SHA-256 of presented secret vs api_keys.key_hash)."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from sqlalchemy import select

from daifend_core.db_sync import sync_session_scope
from daifend_core.models import ApiKey

logger = logging.getLogger(__name__)


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str) -> dict[str, Any] | None:
    """
    Returns claims dict { tenant_id, sub, permissions[], scopes } or None.
    """
    if not raw_key or len(raw_key) < 8:
        return None
    digest = hash_api_key(raw_key.strip())
    try:
        with sync_session_scope() as s:
            row = s.scalar(
                select(ApiKey).where(
                    ApiKey.key_hash == digest,
                    ApiKey.revoked.is_(False),
                )
            )
            if row is None:
                return None
            perms: list[str] = []
            try:
                raw = row.scopes or "[]"
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    perms = [str(x) for x in parsed]
            except Exception:
                perms = []
            return {
                "tenant_id": row.tenant_id,
                "sub": f"apikey:{row.id}",
                "permissions": perms,
                "scope": " ".join(perms) if perms else "telemetry:read",
                "api_key_id": row.id,
            }
    except Exception as exc:
        logger.exception("api key verify failed: %s", exc)
        return None
