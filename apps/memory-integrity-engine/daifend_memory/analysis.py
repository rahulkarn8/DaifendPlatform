"""
Production-oriented memory integrity analysis (numpy-backed).

Optional upgrade path: swap embedding source to sentence-transformers / enterprise models.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

import numpy as np

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.I),
    re.compile(r"disregard\s+(the\s+)?(above|system)", re.I),
    re.compile(r"<\s*/?\s*system\s*>", re.I),
    re.compile(r"you\s+are\s+now\s+(DAN|unrestricted)", re.I),
    re.compile(r"sudo\s+mode", re.I),
    re.compile(r"developer\s+message\s*:", re.I),
]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)
    return float(np.dot(a, b) / denom)


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    return 1.0 - _cosine_similarity(a, b)


def _fingerprint_vectors(embeddings: np.ndarray) -> str:
    flat = np.ascontiguousarray(embeddings, dtype=np.float64).ravel()
    digest = hashlib.sha256(flat.tobytes()).hexdigest()[:32]
    return digest


def _prompt_injection_score(text: str) -> tuple[float, list[str]]:
    reasons: list[str] = []
    hits = 0
    for pat in _INJECTION_PATTERNS:
        if pat.search(text):
            hits += 1
            reasons.append(f"pattern:{pat.pattern[:48]}")
    # crude entropy spike heuristic for obfuscated payloads
    ent = _shannon_entropy(text)
    if ent > 4.8 and len(text) > 120:
        hits += 1
        reasons.append("high_entropy")
    score = min(1.0, hits * 0.25 + max(0.0, (ent - 4.2) * 0.08))
    return score, reasons


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    from collections import Counter

    c = Counter(s)
    n = len(s)
    return float(-sum((cnt / n) * np.log2(cnt / n) for cnt in c.values()))


def analyze_memory_integrity(
    embeddings: list[list[float]],
    baseline_centroid: list[float] | None = None,
    text_samples: list[str] | None = None,
) -> dict[str, Any]:
    if len(embeddings) < 2:
        raise ValueError("At least two embeddings are required for integrity analysis")

    m = np.asarray(embeddings, dtype=np.float64)
    if m.ndim != 2:
        raise ValueError("embeddings must be a 2-D matrix")

    centroid = m.mean(axis=0)
    if baseline_centroid is not None:
        baseline = np.asarray(baseline_centroid, dtype=np.float64)
        if baseline.shape != centroid.shape:
            raise ValueError("baseline_centroid dimension mismatch")
    else:
        baseline = centroid

    dists = np.array([_cosine_distance(row, baseline) for row in m])
    drift = float(np.mean(dists))
    std = float(np.std(dists) + 1e-9)
    z = (dists - np.mean(dists)) / std
    # z ≈ 2.0 catches orthogonal / cluster-outliers in small batches (enterprise tuning per tenant)
    anomalous_indices = [int(i) for i in np.where(np.abs(z) >= 2.0 - 1e-6)[0]]

    # cluster isolation: fraction of points far from bulk
    poison_risk = float(np.mean(dists > np.percentile(dists, 85)))

    trust = float(max(0.0, min(100.0, 100.0 * (1.0 - min(1.0, drift * 1.8 + poison_risk * 0.35)))))

    injection_signals: list[dict[str, Any]] = []
    if text_samples:
        for i, sample in enumerate(text_samples):
            score, reasons = _prompt_injection_score(sample)
            if score > 0.01:
                injection_signals.append(
                    {"sampleIndex": i, "score": round(score, 4), "reasons": reasons}
                )

    fingerprint = _fingerprint_vectors(m)

    actions: list[str] = []
    if anomalous_indices:
        actions.append("quarantine_anomalous_vector_segments")
    if poison_risk > 0.25:
        actions.append("trigger_embedding_rebaseline")
    if drift > 0.22:
        actions.append("schedule_memory_rollback_review")
    if injection_signals:
        actions.append("enable_prompt_firewall_and_audit_chain")

    return {
        "trustScore": round(trust, 2),
        "semanticDrift": round(drift, 4),
        "poisonedClusterRisk": round(poison_risk, 4),
        "anomalousIndices": anomalous_indices,
        "promptInjectionSignals": injection_signals,
        "fingerprint": fingerprint,
        "recommendedActions": actions,
    }
