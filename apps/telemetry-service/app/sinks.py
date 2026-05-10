"""Durable telemetry sinks: ClickHouse (analytics) + Kafka/Redpanda (stream bus) + DLQ on failure."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

CLICKHOUSE_HTTP = os.environ.get("CLICKHOUSE_HTTP_URL", "http://127.0.0.1:8123").rstrip(
    "/"
)
CLICKHOUSE_ENABLED = os.environ.get("CLICKHOUSE_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
)
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "").strip()
KAFKA_TOPIC = os.environ.get("KAFKA_TELEMETRY_TOPIC", "daifend.telemetry.raw")
KAFKA_DLQ_TOPIC = os.environ.get(
    "KAFKA_TELEMETRY_DLQ_TOPIC", "daifend.telemetry.dlq"
).strip()
DEFAULT_TENANT_ID = os.environ.get("DEFAULT_TENANT_ID", "default")

_kafka_producer: Any = None


async def _clickhouse_insert(batch: list[dict[str, Any]], tenant_id: str) -> bool:
    if not CLICKHOUSE_ENABLED:
        return True
    lines = []
    for ev in batch:
        row = {
            "ts_ms": int(ev.get("ts", 0)),
            "tenant_id": tenant_id,
            "event_type": str(ev.get("type", "")),
            "payload_json": json.dumps(ev, separators=(",", ":")),
        }
        lines.append(json.dumps(row, separators=(",", ":")))
    if not lines:
        return True
    body = "\n".join(lines)
    query = "INSERT INTO daifend.telemetry_events_raw FORMAT JSONEachRow"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(
                f"{CLICKHOUSE_HTTP}/",
                params={"query": query},
                content=body.encode(),
                headers={"Content-Type": "application/json"},
            )
            if r.status_code >= 400:
                logger.warning("ClickHouse insert failed: %s %s", r.status_code, r.text[:200])
                return False
            return True
    except Exception:
        logger.exception("ClickHouse insert error")
        return False


async def _kafka_send(batch: list[dict[str, Any]], tenant_id: str) -> bool:
    global _kafka_producer
    if not KAFKA_BOOTSTRAP:
        return True
    try:
        from aiokafka import AIOKafkaProducer
    except ImportError:
        return True
    payload = json.dumps(
        {"tenantId": tenant_id, "events": batch}, separators=(",", ":")
    ).encode()
    try:
        if _kafka_producer is None:
            _kafka_producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP.split(","),
            )
            await _kafka_producer.start()
        await _kafka_producer.send_and_wait(KAFKA_TOPIC, payload)
        return True
    except Exception:
        logger.exception("Kafka publish error")
        return False


async def _kafka_dlq(
    batch: list[dict[str, Any]],
    tenant_id: str,
    *,
    error: str,
    stage: str,
) -> None:
    global _kafka_producer
    if not KAFKA_BOOTSTRAP or not KAFKA_DLQ_TOPIC:
        return
    try:
        from aiokafka import AIOKafkaProducer
    except ImportError:
        return
    body = json.dumps(
        {
            "tenantId": tenant_id,
            "failedAt": stage,
            "error": error[:2048],
            "events": batch,
        },
        separators=(",", ":"),
    ).encode()
    try:
        if _kafka_producer is None:
            _kafka_producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP.split(","),
            )
            await _kafka_producer.start()
        await _kafka_producer.send_and_wait(KAFKA_DLQ_TOPIC, body)
    except Exception:
        logger.exception("Kafka DLQ publish error")


async def sink_telemetry_batch(
    batch: list[dict[str, Any]],
    tenant_id: str | None = None,
) -> None:
    """Route each event by its tenantId (required in enterprise); fallback only when absent."""
    from collections import defaultdict

    by_tenant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev in batch:
        if not isinstance(ev, dict):
            continue
        tid = (
            ev.get("tenantId")
            or ev.get("tenant_id")
            or tenant_id
            or DEFAULT_TENANT_ID
        )
        by_tenant[str(tid)].append(ev)
    if not by_tenant:
        return
    for tid, evs in by_tenant.items():
        ch_ok = await _clickhouse_insert(evs, tid)
        if not ch_ok:
            await _kafka_dlq(evs, tid, error="clickhouse_insert_failed", stage="clickhouse")
        kafka_ok = await _kafka_send(evs, tid)
        if not kafka_ok:
            await _kafka_dlq(evs, tid, error="kafka_publish_failed", stage="kafka")
