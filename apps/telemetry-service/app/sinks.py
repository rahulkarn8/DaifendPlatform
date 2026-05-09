"""Durable telemetry sinks: ClickHouse (analytics) + Kafka/Redpanda (stream bus)."""

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
DEFAULT_TENANT_ID = os.environ.get("DEFAULT_TENANT_ID", "default")

_kafka_producer: Any = None


async def _clickhouse_insert(batch: list[dict[str, Any]], tenant_id: str) -> None:
    if not CLICKHOUSE_ENABLED:
        return
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
        return
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
    except Exception:
        logger.exception("ClickHouse insert error")


async def _kafka_send(batch: list[dict[str, Any]], tenant_id: str) -> None:
    global _kafka_producer
    if not KAFKA_BOOTSTRAP:
        return
    try:
        from aiokafka import AIOKafkaProducer
    except ImportError:
        return
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
    except Exception:
        logger.exception("Kafka publish error")


async def sink_telemetry_batch(
    batch: list[dict[str, Any]],
    tenant_id: str | None = None,
) -> None:
    tid = tenant_id or DEFAULT_TENANT_ID
    await _clickhouse_insert(batch, tid)
    await _kafka_send(batch, tid)
