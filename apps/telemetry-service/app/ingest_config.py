"""Telemetry ingest mode: enterprise (NATS-only, no synthetic batches) vs demo (local sandbox)."""

from __future__ import annotations

import os


def ingest_mode() -> str:
    """
    - enterprise: only forward events received from NATS (or Kafka via bridge); no RNG telemetry.
    - demo: legacy jitter-based batches for local UI sandbox only.
    """
    explicit = os.environ.get("TELEMETRY_INGEST_MODE", "").strip().lower()
    if explicit in ("enterprise", "demo"):
        return explicit
    return (
        "demo"
        if os.environ.get("DAIFEND_ENV", "development").lower() == "development"
        else "enterprise"
    )


def nats_subjects() -> list[str]:
    raw = os.environ.get("TELEMETRY_NATS_SUBJECTS", "").strip()
    if raw:
        return [s.strip() for s in raw.split(",") if s.strip()]
    return [
        "daifend.telemetry.raw",
        "daifend.memory.scan.completed",
        "daifend.memory.scan.failed",
        "daifend.memory.rollback",
    ]
