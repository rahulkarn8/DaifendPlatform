"""Optional OPA policy check and JWT permission enforcement."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


async def opa_authorize_request(request: Request, tenant_id: str, claims: dict[str, Any]) -> None:
    base = os.environ.get("OPA_URL", "").strip().rstrip("/")
    if not base:
        return
    path_parts = [p for p in request.url.path.strip("/").split("/") if p]
    payload = {
        "input": {
            "tenantId": tenant_id,
            "method": request.method,
            "path": path_parts,
            "sub": claims.get("sub"),
            "permissions": claims.get("permissions") or [],
        }
    }
    try:
        kw = {"timeout": 3.0}
        async with httpx.AsyncClient(**kw) as client:
            r = await client.post(f"{base}/v1/data/daifend/gateway/allow", json=payload)
        if r.status_code != 200:
            logger.warning("OPA non-200: %s", r.status_code)
            return
        body = r.json()
        res = body.get("result")
        if res is True:
            return
        if isinstance(res, dict) and res.get("allow") is True:
            return
        raise HTTPException(status_code=403, detail="opa_denied")
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("OPA check failed-open: %s", exc)


def require_permissions(claims: dict[str, Any], any_of: list[str]) -> None:
    if claims.get("sub") == "internal":
        return
    perms = claims.get("permissions")
    if isinstance(perms, str):
        perms = [p.strip() for p in perms.split() if p.strip()]
    if not isinstance(perms, list):
        perms = []
    scope = str(claims.get("scope", ""))
    merged = set(perms) | set(scope.split())
    if "*" in merged or "admin" in merged:
        return
    if any(p in merged for p in any_of):
        return
    raise HTTPException(status_code=403, detail="insufficient_permissions")
