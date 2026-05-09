from __future__ import annotations

import uuid

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from daifend_core.service_gate import require_internal_service_token

app = FastAPI(title="Daifend Self-Healing Engine", version="0.2.0")

_workflows: dict[str, dict] = {}


class WorkflowRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(validation_alias="tenantId")
    incident_id: str = Field(validation_alias="incidentId")
    actions: list[str]


@app.get("/health")
def health():
    return {"service": "self-healing-engine", "status": "ok"}


@app.post(
    "/v1/workflows",
    dependencies=[Depends(require_internal_service_token)],
)
def start_workflow(body: WorkflowRequest):
    if not body.actions:
        raise HTTPException(status_code=422, detail="actions required")

    wid = str(uuid.uuid4())
    steps = [{"name": a, "status": "queued"} for a in body.actions]
    _workflows[wid] = {
        "tenantId": body.tenant_id,
        "incidentId": body.incident_id,
        "steps": steps,
        "status": "queued",
    }
    # simulate immediate progression for API contract
    for s in steps:
        s["status"] = "completed"
    _workflows[wid]["status"] = "completed"

    return {
        "workflowId": wid,
        "status": "completed",
        "steps": steps,
    }
