"""
Enterprise NATS ingress: durable subscribe, exponential reconnect, tenant propagation on events.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from typing import TYPE_CHECKING, Any

from nats.aio.client import Client as NATS

from app.ingest_config import nats_subjects

if TYPE_CHECKING:
    import socketio

logger = logging.getLogger(__name__)


def _normalize_batch(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Accept either { events: [...] } or a single event object."""
    if "events" in payload and isinstance(payload["events"], list):
        events = payload["events"]
    else:
        events = [payload]
    tenant_id = payload.get("tenantId") or payload.get("tenant_id")
    out: list[dict[str, Any]] = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        e = dict(ev)
        if tenant_id and "tenantId" not in e and "tenant_id" not in e:
            e["tenantId"] = tenant_id
        e.setdefault("source", "nats")
        out.append(e)
    return out


async def enterprise_nats_loop(
    sio: socketio.AsyncServer,
    nats_url: str,
    sink_batch,
) -> None:
    backoff = 1.0
    max_backoff = 60.0
    subjects = nats_subjects()

    while True:
        nc: NATS | None = None
        try:
            nc = NATS()
            await nc.connect(servers=[nats_url], reconnect_time_wait=min(backoff, 10))
            backoff = 1.0
            logger.info("telemetry enterprise NATS connected; subjects=%s", subjects)

            async def handler(msg) -> None:
                try:
                    payload = json.loads(msg.data.decode())
                    batch = _normalize_batch(payload)
                    if not batch:
                        return
                    await sio.emit("telemetry:batch", batch)
                    await sink_batch(batch)
                except Exception as exc:
                    logger.exception("enterprise NATS handler error: %s", exc)

            subs = []
            for subj in subjects:
                s = await nc.subscribe(subj, cb=handler)
                subs.append(s)

            while nc.is_connected:
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("NATS enterprise loop error: %s", exc)
        finally:
            if nc is not None:
                try:
                    await nc.drain()
                except Exception:
                    pass

        jitter = random.uniform(0, 0.5)
        await asyncio.sleep(backoff + jitter)
        backoff = min(max_backoff, backoff * 2)
