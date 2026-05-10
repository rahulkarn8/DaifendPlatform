"""In-memory ring buffer of recent memory-integrity events per tenant (for polling / future SSE)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Any

_MAX = 128


class TelemetryFanout:
    def __init__(self) -> None:
        self._buf: dict[str, deque[dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=_MAX)
        )
        self._lock = Lock()

    def publish(self, tenant_id: str, event: dict[str, Any]) -> None:
        payload = {"ts": time.time(), **event}
        with self._lock:
            self._buf[tenant_id].append(payload)

    def recent(self, tenant_id: str, since_ts: float | None = None) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._buf.get(tenant_id, ()))
        if since_ts is None:
            return items
        return [e for e in items if e.get("ts", 0) > since_ts]


fanout = TelemetryFanout()
