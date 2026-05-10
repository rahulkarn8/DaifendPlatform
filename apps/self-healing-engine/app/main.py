from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from daifend_core.service_gate import require_internal_service_token

logger = logging.getLogger(__name__)

app = FastAPI(title="Daifend Self-Healing Engine", version="0.3.0")

MEMORY_INTEGRITY_URL = os.environ.get(
    "MEMORY_INTEGRITY_URL", "http://127.0.0.1:8003"
).rstrip("/")
INTERNAL_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN", "").strip()

_workflows: dict[str, dict] = {}


class WorkflowRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(validation_alias="tenantId")
    incident_id: str = Field(validation_alias="incidentId")
    actions: list[str]
    context: dict[str, Any] | None = None


def _memory_headers(tenant_id: str) -> dict[str, str]:
    h: dict[str, str] = {
        "Content-Type": "application/json",
        "X-Tenant-Id": tenant_id,
    }
    if INTERNAL_TOKEN:
        h["X-Internal-Token"] = INTERNAL_TOKEN
    return h


def _run_memory_rollback(
    tenant_id: str,
    *,
    quarantine_only: bool,
    ctx: dict[str, Any],
) -> dict[str, Any]:
    collection = str(ctx.get("collection") or ctx.get("vectorCollection") or "")
    backend = str(ctx.get("vectorBackend") or "qdrant")
    point_ids = ctx.get("pointIds") or ctx.get("anomalousPointIds") or []
    if not collection or not point_ids:
        raise ValueError("context.collection and context.pointIds required for memory rollback")
    body = {
        "tenantId": tenant_id,
        "vectorBackend": backend,
        "collection": collection,
        "pointIds": [str(x) for x in point_ids],
        "quarantineOnly": quarantine_only,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            f"{MEMORY_INTEGRITY_URL}/v1/rollback/initiate",
            headers=_memory_headers(tenant_id),
            json=body,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"memory rollback HTTP {r.status_code}: {r.text[:500]}")
        return r.json()


def _execute_action(
    tenant_id: str,
    action: str,
    incident_id: str,
    ctx: dict[str, Any] | None,
) -> dict[str, Any]:
    ctx = ctx or {}
    normalized = action.strip().lower().replace(" ", ".")

    if normalized in ("memory.rollback", "memory.rollback.delete", "rollback.embeddings"):
        return _run_memory_rollback(tenant_id, quarantine_only=False, ctx=ctx)
    if normalized in (
        "memory.quarantine",
        "memory.rollback.quarantine",
        "quarantine.vectors",
    ):
        return _run_memory_rollback(tenant_id, quarantine_only=True, ctx=ctx)

    if normalized in ("noop", "audit.log"):
        return {"mode": "noop", "action": action}

    raise ValueError(f"unsupported action: {action}")


@app.get("/health")
def health():
    return {"service": "self-healing-engine", "status": "ok", "version": "0.3.0"}


@app.get("/ready")
def ready():
    return {"ready": True}


@app.post(
    "/v1/workflows",
    dependencies=[Depends(require_internal_service_token)],
)
def start_workflow(body: WorkflowRequest):
    if not body.actions:
        raise HTTPException(status_code=422, detail="actions required")

    wid = str(uuid.uuid4())
    steps_out: list[dict[str, Any]] = []
    overall = "completed"

    for a in body.actions:
        step = {"name": a, "status": "queued", "detail": None}
        try:
            result = _execute_action(body.tenant_id, a, body.incident_id, body.context)
            step["status"] = "completed"
            step["detail"] = result
        except Exception as exc:
            logger.exception("workflow step failed")
            step["status"] = "failed"
            step["detail"] = {"error": str(exc)}
            overall = "failed"
            steps_out.append(step)
            break
        steps_out.append(step)

    _workflows[wid] = {
        "tenantId": body.tenant_id,
        "incidentId": body.incident_id,
        "steps": steps_out,
        "status": overall,
    }

    return {
        "workflowId": wid,
        "status": overall,
        "steps": steps_out,
    }
