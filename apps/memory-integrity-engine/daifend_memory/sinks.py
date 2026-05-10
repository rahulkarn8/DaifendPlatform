"""NATS + ClickHouse sinks for memory integrity telemetry."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def publish_nats_memory_event(tenant_id: str, subject_suffix: str, payload: dict) -> None:
    url = os.environ.get("NATS_URL", "").strip()
    if not url:
        return
    try:
        import nats

        nc = await nats.connect(url)
        subj = os.environ.get("NATS_MEMORY_SUBJECT_PREFIX", "daifend.memory")
        await nc.publish(
            f"{subj}.{subject_suffix}",
            json.dumps({"tenantId": tenant_id, **payload}).encode(),
        )
        await nc.drain()
    except Exception as exc:
        logger.warning("NATS publish failed: %s", exc)


def clickhouse_insert_drift_row(
    tenant_id: str,
    scan_id: str | None,
    drift: float,
    trust: float,
    poisoning_p: float,
    fingerprint: str,
    backend: str | None,
) -> None:
    base = os.environ.get("CLICKHOUSE_HTTP_URL", "").strip()
    if not base:
        from daifend_core.settings import ServiceSettings

        base = ServiceSettings().clickhouse_url.rstrip("/")
    if not base:
        return
    row = {
        "ts_ms": int(__import__("time").time() * 1000),
        "tenant_id": tenant_id,
        "scan_id": scan_id or "",
        "semantic_drift": drift,
        "trust_score": trust,
        "poisoning_probability": poisoning_p,
        "fingerprint": fingerprint,
        "vector_backend": backend or "",
    }
    try:
        sql = """INSERT INTO daifend.drift_metrics FORMAT JSONEachRow"""
        body = json.dumps(row) + "\n"
        r = httpx.post(
            f"{base.rstrip('/')}/",
            params={"query": sql},
            content=body,
            headers={"Content-Type": "text/plain"},
            timeout=5.0,
        )
        r.raise_for_status()
    except Exception as exc:
        logger.warning("ClickHouse drift insert failed: %s", exc)


def clickhouse_insert_retrieval_row(
    tenant_id: str,
    scan_id: str | None,
    retrieval_anomaly: float,
    anomalous_count: int,
) -> None:
    base = os.environ.get("CLICKHOUSE_HTTP_URL", "").strip()
    if not base:
        from daifend_core.settings import ServiceSettings

        base = ServiceSettings().clickhouse_url.rstrip("/")
    if not base:
        return
    row = {
        "ts_ms": int(__import__("time").time() * 1000),
        "tenant_id": tenant_id,
        "scan_id": scan_id or "",
        "retrieval_anomaly_score": retrieval_anomaly,
        "anomalous_vector_count": anomalous_count,
    }
    try:
        sql = """INSERT INTO daifend.retrieval_events FORMAT JSONEachRow"""
        body = json.dumps(row) + "\n"
        r = httpx.post(
            f"{base.rstrip('/')}/",
            params={"query": sql},
            content=body,
            headers={"Content-Type": "text/plain"},
            timeout=5.0,
        )
        r.raise_for_status()
    except Exception as exc:
        logger.warning("ClickHouse retrieval insert failed: %s", exc)
