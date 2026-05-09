"""Optional Open Policy Agent integration (central policy for agent runtime)."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPA_URL = os.environ.get("OPA_URL", "").rstrip("/")


async def opa_decide_agent_action(payload: dict[str, Any]) -> dict[str, Any] | None:
    """
    POST /v1/data/daifend/agent/allow with {"input": ...}.

    Returns {"allow": bool, ...} or None if OPA is disabled / unreachable.
    """
    if not OPA_URL:
        return None
    url = f"{OPA_URL}/v1/data/daifend/agent/allow"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.post(url, json={"input": payload})
            if r.status_code >= 400:
                logger.warning("OPA returned %s: %s", r.status_code, r.text[:200])
                return None
            data = r.json()
            raw = data.get("result")
            if isinstance(raw, dict) and "allow" in raw:
                return raw
            return {"allow": bool(raw)}
    except Exception:
        logger.exception("OPA request failed")
        return None
