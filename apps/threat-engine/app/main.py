from __future__ import annotations

import hashlib
import re
from typing import Any

import numpy as np
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from daifend_core.service_gate import require_internal_service_token

app = FastAPI(title="Daifend Threat & RAG Security Engine", version="0.2.0")

_MALWARE_MARKERS = [
    re.compile(r"ignore\s+all\s+instructions", re.I),
    re.compile(r"base64\s*\(", re.I),
    re.compile(r"eval\s*\(", re.I),
]


@app.get("/health")
def health():
    return {"service": "threat-engine", "status": "ok"}


class RagScanRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(validation_alias="tenantId")
    document_id: str = Field(validation_alias="documentId")
    chunks: list[str]
    embedding_dim: int | None = Field(default=None, validation_alias="embeddingDim")


@app.post(
    "/v1/rag/scan-document",
    dependencies=[Depends(require_internal_service_token)],
)
def scan_document(body: RagScanRequest):
    if not body.chunks:
        raise HTTPException(status_code=422, detail="chunks required")

    unsafe: list[dict[str, Any]] = []
    scores: list[float] = []

    for i, chunk in enumerate(body.chunks):
        s = 0.0
        reasons: list[str] = []
        for pat in _MALWARE_MARKERS:
            if pat.search(chunk):
                s += 0.35
                reasons.append(pat.pattern[:40])
        # semantic poisoning proxy: abnormal character class ratio
        alnum = sum(c.isalnum() for c in chunk)
        ratio = alnum / (len(chunk) + 1e-9)
        if ratio < 0.35 and len(chunk) > 80:
            s += 0.2
            reasons.append("low_alnum_ratio")
        scores.append(min(1.0, s))
        if s > 0.25:
            unsafe.append({"chunkIndex": i, "reason": ";".join(reasons) or "heuristic"})

    integrity = float(max(0.0, 100.0 * (1.0 - np.mean(scores))))
    poisoning = float(min(1.0, np.mean(scores) + 0.1 * len(unsafe)))

    return {
        "integrityScore": round(integrity, 2),
        "poisoningLikelihood": round(poisoning, 4),
        "unsafeContexts": unsafe,
    }


class CorrelateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(validation_alias="tenantId")
    events: list[dict[str, Any]]


@app.post(
    "/v1/threats/correlate",
    dependencies=[Depends(require_internal_service_token)],
)
def correlate(body: CorrelateRequest):
    """Deterministic correlation stub — production pipes Kafka/NATS batches."""
    merged = hashlib.sha256(
        str(body.events).encode(),
        usedforsecurity=False,
    ).hexdigest()[:16]
    return {
        "correlationId": merged,
        "severity": "high" if len(body.events) > 5 else "medium",
        "narrative": f"Correlated {len(body.events)} telemetry signals for tenant {body.tenant_id}",
    }
