"""gRPC server for MemoryIntegrity (internal high-throughput path)."""

from __future__ import annotations

import logging
import os
from concurrent import futures

import grpc

from daifend.v1 import memory_pb2, memory_pb2_grpc
from daifend_memory.analysis import analyze_memory_integrity

logger = logging.getLogger(__name__)
GRPC_PORT = int(os.environ.get("GRPC_PORT", "50051"))


class MemoryIntegrityServicer(memory_pb2_grpc.MemoryIntegrityServicer):
    def Analyze(self, request, context):
        try:
            embeddings = [list(v.values) for v in request.embeddings]
            baseline = (
                list(request.baseline_centroid)
                if len(request.baseline_centroid)
                else None
            )
            texts = list(request.text_samples) if len(request.text_samples) else None
            r = analyze_memory_integrity(
                embeddings,
                baseline_centroid=baseline,
                text_samples=texts,
            )
            resp = memory_pb2.AnalyzeResponse(
                trust_score=r["trustScore"],
                semantic_drift=r["semanticDrift"],
                poisoned_cluster_risk=r["poisonedClusterRisk"],
                anomalous_indices=r["anomalousIndices"],
                fingerprint=r["fingerprint"],
                recommended_actions=r["recommendedActions"],
            )
            for sig in r.get("promptInjectionSignals", []):
                p = resp.prompt_injection_signals.add()
                p.sample_index = int(sig.get("sampleIndex", 0))
                p.score = float(sig.get("score", 0))
                p.reasons.extend(sig.get("reasons", []))
            return resp
        except ValueError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except Exception as exc:  # pragma: no cover
            logger.exception("gRPC Analyze failed")
            context.abort(grpc.StatusCode.INTERNAL, str(exc))


def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    memory_pb2_grpc.add_MemoryIntegrityServicer_to_server(
        MemoryIntegrityServicer(), server
    )
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()
    logger.info("MemoryIntegrity gRPC listening on :%s", GRPC_PORT)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
