from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from daifend_core.observability import instrument_fastapi
from daifend_core.service_gate import require_internal_service_token
from daifend_memory.analysis import analyze_memory_integrity
from daifend_memory.connectors.factory import build_connector
from daifend_memory.persistence import (
    audit,
    create_incident,
    list_incidents,
    list_reports,
    load_snapshot_centroid,
    save_integrity_report,
    save_snapshot,
)
from daifend_memory.semantic_pipeline import run_semantic_integrity_pipeline
from daifend_memory.sinks import (
    clickhouse_insert_drift_row,
    clickhouse_insert_retrieval_row,
    publish_nats_memory_event,
)
from daifend_memory.telemetry_fanout import fanout

logger = logging.getLogger(__name__)

app = FastAPI(title="Daifend Memory Integrity Engine", version="0.4.0")

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")

SCAN_COUNTER = Counter(
    "daifend_memory_scans_total", "Memory integrity scans", ["status"]
)
ANALYZE_HIST = Histogram(
    "daifend_memory_analyze_seconds", "Analyze / scan pipeline duration"
)

_scans: dict[str, dict[str, Any]] = {}


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


class ScanStartRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(validation_alias="tenantId")
    vector_backend: str = Field(validation_alias="vectorBackend")
    collection: str
    limit: int = Field(default=512, ge=2, le=10_000)
    namespace: str | None = None
    baseline_snapshot_id: str | None = Field(
        default=None, validation_alias="baselineSnapshotId"
    )
    persist_baseline: bool = Field(default=False, validation_alias="persistBaseline")


class RollbackRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(validation_alias="tenantId")
    vector_backend: str = Field(validation_alias="vectorBackend")
    collection: str
    point_ids: list[str] = Field(validation_alias="pointIds")
    namespace: str | None = None
    quarantine_only: bool = Field(default=False, validation_alias="quarantineOnly")


def _analyze_result_response(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "trustScore": result["trustScore"],
        "integrityScore": result.get("integrityScore"),
        "poisoningProbability": result.get("poisoningProbability"),
        "semanticDrift": result["semanticDrift"],
        "semanticDriftMax": result.get("semanticDriftMax"),
        "poisonedClusterRisk": result["poisonedClusterRisk"],
        "clusterImbalance": result.get("clusterImbalance"),
        "silhouetteScore": result.get("silhouetteScore"),
        "retrievalAnomalyScore": result.get("retrievalAnomalyScore"),
        "anomalousIndices": result["anomalousIndices"],
        "anomalousPointIds": result.get("anomalousPointIds"),
        "promptInjectionSignals": result["promptInjectionSignals"],
        "fingerprint": result["fingerprint"],
        "recommendedActions": result["recommendedActions"],
        "centroid": result.get("centroid"),
        "vectorCount": result.get("vectorCount"),
        "embeddingDim": result.get("embeddingDim"),
    }


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
        "version": "0.4.0",
        "status": "ok",
        "qdrantConfigured": qc is not None,
        "qdrantReachable": qdrant_ok,
    }


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


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

    try:
        result = analyze_memory_integrity(
            body.embeddings,
            baseline_centroid=body.baseline_centroid,
            text_samples=body.text_samples,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    if os.environ.get("MEMORY_PERSIST_ANALYZE", "").lower() in ("1", "true", "yes"):
        try:
            save_integrity_report(
                tenant,
                body.collection_id,
                scan_id=None,
                backend="inline",
                result=result,
            )
        except Exception as exc:
            logger.warning("persist analyze failed: %s", exc)

    return _analyze_result_response(result)


def _publish_nats_blocking(tenant_id: str, suffix: str, payload: dict) -> None:
    try:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                publish_nats_memory_event(tenant_id, suffix, payload)
            )
        finally:
            loop.close()
    except Exception as exc:
        logger.warning("NATS sync publish failed: %s", exc)


def _run_scan_sync(
    scan_id: str,
    tenant_id: str,
    backend: str,
    collection: str,
    limit: int,
    namespace: str | None,
    baseline_snapshot_id: str | None,
    persist_baseline: bool,
) -> None:
    with ANALYZE_HIST.time():
        _scans[scan_id] = {"status": "running", "tenantId": tenant_id}
        try:
            connector = build_connector(backend)
            records = connector.fetch_vectors(
                collection, limit=limit, namespace=namespace
            )
            if len(records) < 2:
                raise ValueError(
                    f"need at least 2 vectors from backend; got {len(records)}"
                )

            baseline = None
            if baseline_snapshot_id:
                baseline = load_snapshot_centroid(baseline_snapshot_id, tenant_id)
            result = run_semantic_integrity_pipeline(
                records, baseline, extra_texts=None
            )
            report_id = save_integrity_report(
                tenant_id,
                collection,
                scan_id,
                backend,
                result,
            )
            if persist_baseline:
                save_snapshot(
                    tenant_id,
                    collection,
                    scan_id,
                    result["centroid"],
                    result["fingerprint"],
                    int(result["vectorCount"]),
                )

            clickhouse_insert_drift_row(
                tenant_id,
                scan_id,
                float(result["semanticDrift"]),
                float(result["trustScore"]),
                float(result.get("poisoningProbability", 0)),
                str(result["fingerprint"]),
                backend,
            )
            clickhouse_insert_retrieval_row(
                tenant_id,
                scan_id,
                float(result.get("retrievalAnomalyScore", 0)),
                len(result.get("anomalousIndices", [])),
            )

            fanout.publish(
                tenant_id,
                {
                    "type": "memory.scan.completed",
                    "scanId": scan_id,
                    "trustScore": result["trustScore"],
                    "integrityScore": result.get("integrityScore"),
                    "poisoningProbability": result.get("poisoningProbability"),
                    "semanticDrift": result["semanticDrift"],
                    "fingerprint": result["fingerprint"],
                    "reportId": report_id,
                },
            )

            if float(result.get("poisoningProbability", 0)) > 0.55:
                try:
                    create_incident(
                        tenant_id,
                        title="Elevated AI memory poisoning probability",
                        severity="high",
                        category="memory_integrity",
                        detail={
                            "scanId": scan_id,
                            "reportId": report_id,
                            "poisoningProbability": result.get("poisoningProbability"),
                            "trustScore": result["trustScore"],
                        },
                    )
                except Exception as exc:
                    logger.warning("incident create failed: %s", exc)

            audit(
                tenant_id,
                None,
                "memory.scan.completed",
                f"scan:{scan_id}",
                f"report={report_id}",
            )

            _publish_nats_blocking(
                tenant_id,
                "scan.completed",
                {
                    "scanId": scan_id,
                    "reportId": report_id,
                    "trustScore": result["trustScore"],
                    "poisoningProbability": result.get("poisoningProbability"),
                    "fingerprint": result["fingerprint"],
                },
            )

            _scans[scan_id] = {
                "status": "completed",
                "tenantId": tenant_id,
                "reportId": report_id,
                "summary": {
                    "trustScore": result["trustScore"],
                    "semanticDrift": result["semanticDrift"],
                    "poisoningProbability": result.get("poisoningProbability"),
                },
            }
            SCAN_COUNTER.labels(status="completed").inc()
        except Exception as exc:
            logger.exception("scan %s failed", scan_id)
            _scans[scan_id] = {"status": "failed", "tenantId": tenant_id, "error": str(exc)}
            SCAN_COUNTER.labels(status="failed").inc()
            fanout.publish(
                tenant_id,
                {"type": "memory.scan.failed", "scanId": scan_id, "error": str(exc)},
            )


async def _run_scan_task(
    scan_id: str,
    tenant_id: str,
    backend: str,
    collection: str,
    limit: int,
    namespace: str | None,
    baseline_snapshot_id: str | None,
    persist_baseline: bool,
):
    await run_in_threadpool(
        _run_scan_sync,
        scan_id,
        tenant_id,
        backend,
        collection,
        limit,
        namespace,
        baseline_snapshot_id,
        persist_baseline,
    )


@app.post(
    "/v1/scan/start",
    dependencies=[Depends(require_internal_service_token)],
)
async def scan_start(
    body: ScanStartRequest,
    background: BackgroundTasks,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
):
    tenant = x_tenant_id or body.tenant_id
    if x_tenant_id and x_tenant_id != body.tenant_id:
        raise HTTPException(status_code=400, detail="tenant mismatch")

    scan_id = str(uuid.uuid4())
    _scans[scan_id] = {"status": "queued", "tenantId": tenant}
    SCAN_COUNTER.labels(status="queued").inc()
    background.add_task(
        _run_scan_task,
        scan_id,
        tenant,
        body.vector_backend,
        body.collection,
        body.limit,
        body.namespace,
        body.baseline_snapshot_id,
        body.persist_baseline,
    )
    return {"scanId": scan_id, "status": "queued"}


@app.get(
    "/v1/scan/{scan_id}/status",
    dependencies=[Depends(require_internal_service_token)],
)
def scan_status(
    scan_id: str,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
):
    row = _scans.get(scan_id)
    if not row:
        raise HTTPException(status_code=404, detail="unknown scan")
    if x_tenant_id and row.get("tenantId") != x_tenant_id:
        raise HTTPException(status_code=403, detail="forbidden")
    return row


@app.get(
    "/v1/memory/reports",
    dependencies=[Depends(require_internal_service_token)],
)
def memory_reports(
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    limit: int = 20,
):
    return {"reports": list_reports(x_tenant_id, limit=limit)}


@app.get(
    "/v1/memory/feed",
    dependencies=[Depends(require_internal_service_token)],
)
def memory_feed(
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    since: float | None = None,
):
    return {"events": fanout.recent(x_tenant_id, since_ts=since)}


@app.get(
    "/v1/incidents/list",
    dependencies=[Depends(require_internal_service_token)],
)
def incidents_list(
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    limit: int = 50,
):
    return {"incidents": list_incidents(x_tenant_id, limit=limit)}


@app.post(
    "/v1/rollback/initiate",
    dependencies=[Depends(require_internal_service_token)],
)
async def rollback_initiate(
    body: RollbackRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
):
    tenant = x_tenant_id or body.tenant_id
    if x_tenant_id and x_tenant_id != body.tenant_id:
        raise HTTPException(status_code=400, detail="tenant mismatch")

    def _rollback():
        connector = build_connector(body.vector_backend)
        if body.quarantine_only:
            audit(
                tenant,
                None,
                "memory.rollback.quarantine_marked",
                body.collection,
                ",".join(body.point_ids[:20]),
            )
            return {"mode": "quarantine_marked", "pointCount": len(body.point_ids)}
        connector.delete_points(
            body.collection, body.point_ids, namespace=body.namespace
        )
        audit(
            tenant,
            None,
            "memory.rollback.deleted",
            body.collection,
            f"count={len(body.point_ids)}",
        )
        return {"mode": "deleted", "pointCount": len(body.point_ids)}

    try:
        out = await run_in_threadpool(_rollback)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    fanout.publish(
        tenant,
        {
            "type": "memory.rollback",
            "collection": body.collection,
            **out,
        },
    )
    await publish_nats_memory_event(
        tenant,
        "rollback",
        {"collection": body.collection, **out},
    )
    return out


instrument_fastapi(app, "daifend-memory-integrity-engine")
