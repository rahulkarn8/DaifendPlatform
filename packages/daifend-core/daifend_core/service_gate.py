"""Optional enforcement: only the gateway (or mesh) may call engine HTTP APIs."""

from __future__ import annotations

import os

from fastapi import Header, HTTPException


def require_internal_service_token(
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> None:
    """
    When ``ENGINE_REQUIRE_INTERNAL_TOKEN`` is true and ``INTERNAL_SERVICE_TOKEN`` is set,
    reject requests without a matching ``X-Internal-Token``.

    In a service mesh, combine with network policies and drop the header at the sidecar
    once mTLS identity replaces shared secrets.
    """
    required = os.environ.get("ENGINE_REQUIRE_INTERNAL_TOKEN", "").lower() in (
        "1",
        "true",
        "yes",
    )
    expected = os.environ.get("INTERNAL_SERVICE_TOKEN", "").strip()
    if not required:
        return
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="ENGINE_REQUIRE_INTERNAL_TOKEN set but INTERNAL_SERVICE_TOKEN is empty",
        )
    if x_internal_token != expected:
        raise HTTPException(status_code=403, detail="invalid_or_missing_service_token")
