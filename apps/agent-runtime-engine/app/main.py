from __future__ import annotations

import json
import re
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.opa import opa_decide_agent_action
from daifend_core.service_gate import require_internal_service_token

app = FastAPI(title="Daifend Agent Runtime Engine", version="0.2.0")

DEFAULT_POLICY = {
    "version": 1,
    "tools": [
        {"name": "read_file", "allowed": True, "maxArgsBytes": 32_768},
        {"name": "http_request", "allowed": False},
        {"name": "run_shell", "allowed": False},
        {"name": "execute_code", "allowed": False},
    ],
    "denyPatterns": [
        r"rm\s+-rf",
        r"curl\s+.*\|\s*sh",
        r"child_process",
        r"os\.system",
    ],
}


class ValidateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(validation_alias="tenantId")
    agent_id: str = Field(validation_alias="agentId")
    tool_name: str = Field(validation_alias="toolName")
    arguments: dict[str, Any]
    reasoning_step: str | None = Field(default=None, validation_alias="reasoningStep")


def _policy_for_tenant(_tenant_id: str) -> dict[str, Any]:
    return DEFAULT_POLICY


def _args_blob(args: dict[str, Any]) -> str:
    try:
        return json.dumps(args, sort_keys=True)
    except (TypeError, ValueError):
        return str(args)


@app.get("/health")
def health():
    return {"service": "agent-runtime-engine", "status": "ok"}


@app.post(
    "/v1/validate-action",
    dependencies=[Depends(require_internal_service_token)],
)
async def validate_action(
    body: ValidateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
):
    if x_tenant_id and x_tenant_id != body.tenant_id:
        raise HTTPException(status_code=400, detail="tenant mismatch")

    policy = _policy_for_tenant(body.tenant_id)
    violations: list[str] = []
    tool = next(
        (t for t in policy["tools"] if t["name"] == body.tool_name),
        None,
    )
    if tool is None:
        violations.append(f"unknown_tool:{body.tool_name}")
    elif not tool.get("allowed", False):
        violations.append(f"tool_blocked:{body.tool_name}")

    blob = _args_blob(body.arguments)
    max_bytes = (tool or {}).get("maxArgsBytes") or 65_536
    if len(blob.encode()) > max_bytes:
        violations.append("arguments_size_exceeded")

    for pat in policy.get("denyPatterns", []):
        if re.search(pat, blob, re.I):
            violations.append(f"deny_pattern:{pat}")

    if body.reasoning_step:
        for pat in policy.get("denyPatterns", []):
            if re.search(pat, body.reasoning_step, re.I):
                violations.append("reasoning_unsafe")

    opa_payload = {
        "tenant_id": body.tenant_id,
        "agent_id": body.agent_id,
        "tool_name": body.tool_name,
        "arguments": body.arguments,
        "reasoning_step": body.reasoning_step or "",
        "local_violations": violations,
    }
    opa_result = await opa_decide_agent_action(opa_payload)
    if opa_result is not None:
        allowed = bool(opa_result.get("allow"))
        if not allowed:
            violations.append("opa_denied")
    else:
        allowed = len(violations) == 0

    containment = "none"
    if not allowed:
        containment = "hard_block" if any(
            v.startswith("deny_pattern")
            or v.startswith("tool_blocked")
            or v == "opa_denied"
            for v in violations
        ) else "soft_block"

    return {
        "allowed": allowed,
        "violations": violations,
        "containment": containment,
    }
