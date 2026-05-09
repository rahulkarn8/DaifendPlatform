"""Outbound HTTP/TLS settings for service-to-service calls (e.g. API gateway → engines)."""

from __future__ import annotations

import os
from typing import Any


def httpx_async_client_kwargs(timeout: float = 30.0) -> dict[str, Any]:
    """
    Build kwargs for ``httpx.AsyncClient``.

    Optional mTLS (mesh / private CA):

    - ``MTLS_CA_BUNDLE`` — PEM file to verify upstream server certs
    - ``MTLS_CLIENT_CERT`` / ``MTLS_CLIENT_KEY`` — client certificate + key for mutual TLS
    """
    kw: dict[str, Any] = {"timeout": timeout}
    ca = os.environ.get("MTLS_CA_BUNDLE", "").strip()
    cert = os.environ.get("MTLS_CLIENT_CERT", "").strip()
    key = os.environ.get("MTLS_CLIENT_KEY", "").strip()
    if ca:
        kw["verify"] = ca
    if cert and key:
        kw["cert"] = (cert, key)
    return kw
