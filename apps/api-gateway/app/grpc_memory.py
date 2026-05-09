"""Optional gRPC client to memory-integrity-engine (lower latency than REST)."""

from __future__ import annotations

import logging
import os
from typing import Any

import grpc

logger = logging.getLogger(__name__)


def analyze_via_grpc(body: dict[str, Any]) -> dict[str, Any]:
    from daifend.v1 import memory_pb2, memory_pb2_grpc

    target = os.environ["MEMORY_GRPC_TARGET"].strip()
    req = memory_pb2.AnalyzeRequest(
        tenant_id=str(body.get("tenantId") or body.get("tenant_id", "")),
        collection_id=str(body.get("collectionId") or body.get("collection_id", "")),
    )
    for row in body.get("embeddings", []):
        v = req.embeddings.add()
        v.values.extend([float(x) for x in row])
    for x in body.get("baselineCentroid") or body.get("baseline_centroid") or []:
        req.baseline_centroid.append(float(x))
    for t in body.get("textSamples") or body.get("text_samples") or []:
        req.text_samples.append(str(t))

    creds = _grpc_channel_credentials()
    if creds:
        channel = grpc.secure_channel(target, creds)
    else:
        channel = grpc.insecure_channel(target)
    try:
        stub = memory_pb2_grpc.MemoryIntegrityStub(channel)
        resp = stub.Analyze(req, timeout=30)
        signals = [
            {
                "sampleIndex": s.sample_index,
                "score": s.score,
                "reasons": list(s.reasons),
            }
            for s in resp.prompt_injection_signals
        ]
        return {
            "trustScore": resp.trust_score,
            "semanticDrift": resp.semantic_drift,
            "poisonedClusterRisk": resp.poisoned_cluster_risk,
            "anomalousIndices": list(resp.anomalous_indices),
            "promptInjectionSignals": signals,
            "fingerprint": resp.fingerprint,
            "recommendedActions": list(resp.recommended_actions),
        }
    finally:
        channel.close()


def _grpc_channel_credentials() -> grpc.ChannelCredentials | None:
    if os.getenv("MEMORY_GRPC_TLS", "").lower() not in ("1", "true", "yes"):
        return None
    ca = os.getenv("MTLS_CA_BUNDLE", "").strip()
    cert = os.getenv("MTLS_CLIENT_CERT", "").strip()
    key = os.getenv("MTLS_CLIENT_KEY", "").strip()
    if ca and cert and key:
        with open(ca, "rb") as fca, open(cert, "rb") as fc, open(key, "rb") as fk:
            return grpc.ssl_channel_credentials(
                root_certificates=fca.read(),
                private_key=fk.read(),
                certificate_chain=fc.read(),
            )
    if ca:
        with open(ca, "rb") as fca:
            return grpc.ssl_channel_credentials(root_certificates=fca.read())
    logger.warning("MEMORY_GRPC_TLS set but MTLS_CA_BUNDLE missing; using insecure")
    return None
