from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from daifend_core.observability import instrument_fastapi
from daifend_core.service_gate import require_internal_service_token
from daifend_memory.analysis import analyze_memory_integrity

logger = logging.getLogger(__name__)

app = FastAPI(title="Daifend Memory Integrity Engine", version="0.2.0")

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")


def _qdrant() -> Any | None:
    try:
        from qdrant_client import QdrantClient

        return QdrantClient(url=QDRANT_URL, timeout=3.0)
    except Exception as exc:
        logger.debug("Qdrant client unavailable: %s", exc)
        return None


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(validation_alias="tenantId")
    embeddings: list[list[float]]
    baseline_centroid: list[float] | None = Field(
        default=None, validation_alias="baselineCentroid"
    )
    text_samples: list[str] | None = Field(
        default=None, validation_alias="textSamples"
    )
    collection_id: str | None = Field(default=None, validation_alias="collectionId")


@app.get("/health")
def health():
    qc = _qdrant()
    qdrant_ok: bool | None = None
    if qc is not None:
        try:
            qc.get_collections()
            qdrant_ok = True
        except Exception:
            qdrant_ok = False
    return {
        "service": "memory-integrity-engine",
        "status": "ok",
        "qdrantConfigured": qc is not None,
        "qdrantReachable": qdrant_ok,
    }


@app.get(
    "/v1/qdrant/status",
    dependencies=[Depends(require_internal_service_token)],
)
def qdrant_status():
    qc = _qdrant()
    if qc is None:
        return {"available": False, "reason": "qdrant_client_not_installed_or_invalid_url"}
    try:
        cols = qc.get_collections()
        names = [c.name for c in cols.collections]
        return {"available": True, "url": QDRANT_URL, "collections": names}
    except Exception as exc:
        return {"available": False, "url": QDRANT_URL, "error": str(exc)}


@app.post(
    "/v1/analyze",
    dependencies=[Depends(require_internal_service_token)],
)
def analyze(
    body: AnalyzeRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
):
    tenant = x_tenant_id or body.tenant_id
    if x_tenant_id and x_tenant_id != body.tenant_id:
        raise HTTPException(status_code=400, detail="tenant mismatch")
    _ = tenant

    try:
        result = analyze_memory_integrity(
            body.embeddings,
            baseline_centroid=body.baseline_centroid,
            text_samples=body.text_samples,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return {
        "trustScore": result["trustScore"],
        "semanticDrift": result["semanticDrift"],
        "poisonedClusterRisk": result["poisonedClusterRisk"],
        "anomalousIndices": result["anomalousIndices"],
        "promptInjectionSignals": result["promptInjectionSignals"],
        "fingerprint": result["fingerprint"],
        "recommendedActions": result["recommendedActions"],
    }


instrument_fastapi(app, "daifend-memory-integrity-engine")
