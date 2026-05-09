"""
Telemetry ingress: NATS (optional) + Socket.IO fan-out for the Daifend web console.

Demo mode (no NATS): generates the same event families as the legacy Node mock server.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
from typing import Any

import socketio
from fastapi import FastAPI
from nats.aio.client import Client as NATS

from app.sinks import sink_telemetry_batch
from daifend_core.observability import instrument_fastapi

NATS_URL = os.environ.get("NATS_URL", "nats://127.0.0.1:4222")
PORT = int(os.environ.get("TELEMETRY_PORT", "4001"))
ORIGINS = os.environ.get(
    "TELEMETRY_ORIGINS",
    "http://127.0.0.1:3000,http://localhost:3000",
).split(",")

fastapi_app = FastAPI(title="Daifend Telemetry Service", version="0.2.0")
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=ORIGINS,
    transports=["websocket", "polling"],
)
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

memory_trust = 93.6
drift = 0.08
poisoned = 0
rag_integrity = 96.2
active_agents = 7


def _clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def _jitter(base: float, amount: float) -> float:
    return base + (random.random() * 2 - 1) * amount


def _pick(xs: list[Any]) -> Any:
    return random.choice(xs)


def _build_batch_sync() -> list[dict[str, Any]]:
    global memory_trust, drift, poisoned, rag_integrity, active_agents
    import time

    ts = int(time.time() * 1000)
    drift = _clamp(_jitter(drift, 0.01), 0, 1)
    memory_trust = _clamp(_jitter(memory_trust, 0.25) - drift * 0.15, 0, 100)
    rag_integrity = _clamp(_jitter(rag_integrity, 0.22) - drift * 0.1, 0, 100)
    poisoned = int(_clamp(_jitter(float(poisoned), 0.2), 0, 250))
    active_agents = int(_clamp(_jitter(float(active_agents), 0.35), 0, 64))

    batch: list[dict[str, Any]] = [
        {
            "type": "memory.trust",
            "ts": ts,
            "trustScore": round(memory_trust, 2),
            "driftScore": round(drift, 3),
            "poisonedVectors": poisoned,
        },
        {
            "type": "rag.integrity",
            "ts": ts,
            "integrityScore": round(rag_integrity, 2),
            "injectionAttempts": int(_clamp(_jitter(2, 2), 0, 22)),
            "maliciousDocsQuarantined": int(_clamp(_jitter(1, 1), 0, 10)),
        },
        {
            "type": "agent.runtime",
            "ts": ts,
            "activeAgents": active_agents,
            "unsafeToolAttempts": int(_clamp(_jitter(1, 2), 0, 28)),
            "containmentActions": int(_clamp(_jitter(1, 1.5), 0, 10)),
        },
    ]
    if random.random() < 0.42:
        batch.append(
            {
                "type": "threat.attempt",
                "ts": ts,
                "signature": _pick(
                    [
                        "PromptInjection:ContextOverride",
                        "EmbeddingPoison:GradientFlip",
                        "AgentToolMisuse:ShellPivot",
                        "RAG:RetrieverBypass",
                    ]
                ),
                "severity": _pick(["low", "medium", "high", "critical"]),
                "surface": _pick(["rag", "memory", "agent", "model", "identity"]),
            }
        )
    return batch


_tick_started = False


@fastapi_app.get("/health")
def health():
    global _tick_started
    if not _tick_started:
        _tick_started = True
        sio.start_background_task(tick_loop)
    return {"service": "telemetry-service", "status": "ok"}


@sio.event
async def connect(sid, environ):
    global _tick_started
    if not _tick_started:
        _tick_started = True
        sio.start_background_task(tick_loop)

    import time

    await sio.emit(
        "telemetry:hello",
        {
            "serverTime": int(time.time() * 1000),
            "streams": ["telemetry:batch"],
            "mode": "live",
        },
        room=sid,
    )


@sio.on("simulation:spike")
async def simulation_spike(sid, data):  # type: ignore[misc]
    global drift, poisoned, memory_trust, rag_integrity
    intensity = float((data or {}).get("intensity") or 0.7)
    k = _clamp(intensity, 0, 1)
    drift = _clamp(drift + 0.08 * k, 0, 1)
    poisoned = int(_clamp(poisoned + 18 * k, 0, 500))
    memory_trust = _clamp(memory_trust - 3.5 * k, 0, 100)
    rag_integrity = _clamp(rag_integrity - 3.0 * k, 0, 100)
    import time

    spike_batch = [
        {
            "type": "healing.action",
            "ts": int(time.time() * 1000),
            "action": "isolate_vector_segment",
            "incidentId": f"INC-{str(int(time.time()))[-6:]}",
            "progress": 0.12,
        }
    ]
    await sio.emit("telemetry:batch", spike_batch)
    try:
        await sink_telemetry_batch(spike_batch)
    except Exception:
        pass


async def tick_loop():
    nc: NATS | None = None
    try:
        nc = NATS()
        await nc.connect(servers=[NATS_URL], connect_timeout=2)
    except Exception:
        nc = None

    while True:
        batch = _build_batch_sync()
        await sio.emit("telemetry:batch", batch)
        if nc and nc.is_connected:
            try:
                await nc.publish(
                    "daifend.telemetry.raw",
                    json.dumps({"events": batch}).encode(),
                )
            except Exception:
                pass
        try:
            await sink_telemetry_batch(batch)
        except Exception:
            pass
        await asyncio.sleep(0.9)


instrument_fastapi(fastapi_app, "daifend-telemetry-service")
