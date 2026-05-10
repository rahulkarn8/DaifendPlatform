"""
Deterministic semantic integrity analysis: clustering, centroid drift, outliers, trust scores.

Uses scikit-learn for KMeans and silhouette; numpy for cosine geometry.
Optional sentence-transformers when MEMORY_SENTENCE_TRANSFORMER_MODEL is set (text–vector alignment).
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from daifend_memory.vector_types import VectorRecord

logger = logging.getLogger(__name__)

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.I),
    re.compile(r"disregard\s+(the\s+)?(above|system)", re.I),
    re.compile(r"<\s*/?\s*system\s*>", re.I),
    re.compile(r"you\s+are\s+now\s+(DAN|unrestricted)", re.I),
    re.compile(r"sudo\s+mode", re.I),
    re.compile(r"developer\s+message\s*:", re.I),
    re.compile(r"jailbreak|DAN\s+mode|bypass\s+(safety|filter)", re.I),
    re.compile(r"repeat\s+(the\s+)?(system|hidden)\s+prompt", re.I),
]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b) + 1e-12)
    return float(np.dot(a, b) / denom)


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    return 1.0 - _cosine_similarity(a, b)


def _row_normalize(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / norms


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    from collections import Counter

    c = Counter(s)
    n = len(s)
    return float(-sum((cnt / n) * np.log2(cnt / n) for cnt in c.values()))


def _prompt_injection_score(text: str) -> tuple[float, list[str]]:
    reasons: list[str] = []
    hits = 0
    for pat in _INJECTION_PATTERNS:
        if pat.search(text):
            hits += 1
            reasons.append(f"pattern:{pat.pattern[:40]}")
    ent = _shannon_entropy(text)
    if ent > 4.8 and len(text) > 120:
        hits += 1
        reasons.append("high_entropy_obfuscation")
    score = min(1.0, hits * 0.22 + max(0.0, (ent - 4.2) * 0.07))
    return score, reasons


def _fingerprint_matrix(m: np.ndarray) -> str:
    flat = np.ascontiguousarray(m, dtype=np.float64).ravel()
    return hashlib.sha256(flat.tobytes()).hexdigest()[:32]


def _encode_texts_sentence_transformers(texts: list[str]) -> np.ndarray | None:
    model_name = os.environ.get("MEMORY_SENTENCE_TRANSFORMER_MODEL", "").strip()
    if not model_name:
        return None
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(model_name)
        emb = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return np.asarray(emb, dtype=np.float64)
    except Exception as exc:
        logger.warning("sentence-transformers encode failed: %s", exc)
        return None


def _retrieval_spread_anomaly(
    x_norm: np.ndarray, rng: np.random.Generator
) -> float:
    """Deterministic pseudo-random pair sample of cosine similarities — high spread + low mean = suspicious."""
    n = x_norm.shape[0]
    if n < 4:
        return 0.0
    pairs = max(8, min(64, n * (n - 1) // 4))
    sims: list[float] = []
    for i in range(pairs):
        a = int(rng.integers(0, n))
        b = int(rng.integers(0, n))
        if a == b:
            b = (b + 1) % n
        sims.append(float(np.dot(x_norm[a], x_norm[b])))
    arr = np.array(sims, dtype=np.float64)
    spread = float(np.std(arr))
    mean_sim = float(np.mean(arr))
    # Unusually high spread relative to cohesion indicates retrieval instability
    anomaly = max(0.0, spread - (1.0 - mean_sim) * 0.5)
    return float(min(1.0, anomaly * 2.0))


def run_semantic_integrity_pipeline(
    records: list[VectorRecord],
    baseline_centroid: list[float] | None,
    extra_texts: list[str] | None = None,
    *,
    rng_seed: int = 42,
) -> dict[str, Any]:
    if len(records) < 2:
        raise ValueError("At least two vectors are required for integrity analysis")

    m = np.asarray([r.vector for r in records], dtype=np.float64)
    if m.ndim != 2:
        raise ValueError("embedding matrix must be 2-D")

    x_norm = _row_normalize(m)
    n, dim = x_norm.shape

    centroid = x_norm.mean(axis=0)
    centroid = centroid / (np.linalg.norm(centroid) + 1e-12)

    if baseline_centroid is not None:
        base = np.asarray(baseline_centroid, dtype=np.float64)
        if base.shape[0] != dim:
            raise ValueError("baseline_centroid dimension mismatch")
        base = base / (np.linalg.norm(base) + 1e-12)
    else:
        base = centroid.copy()

    dists = np.array([_cosine_distance(x_norm[i], base) for i in range(n)])
    drift_mean = float(np.mean(dists))
    drift_max = float(np.max(dists))
    std = float(np.std(dists) + 1e-9)
    z = (dists - np.mean(dists)) / std
    anomalous_indices = [int(i) for i in np.where(np.abs(z) >= 2.0)[0]]

    rep = np.array([r.source_reputation for r in records], dtype=np.float64)
    reputation_factor = float(np.clip(np.mean(rep), 0.0, 1.0))

    imbalance = 0.0
    sil_val: float | None = None
    labels = np.zeros(n, dtype=np.int32)
    k = 2
    if n >= 3:
        k = max(2, min(8, n // 3))
        k = min(k, n - 1)
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=rng_seed, max_iter=100)
        labels = kmeans.fit_predict(x_norm)
        cluster_sizes = np.bincount(labels, minlength=k).astype(np.float64)
        cluster_sizes = cluster_sizes[cluster_sizes > 0]
        imbalance = float(np.std(cluster_sizes) / (np.mean(cluster_sizes) + 1e-9))
        if k >= 2 and n > k and len(set(labels)) > 1:
            try:
                sil_val = float(silhouette_score(x_norm, labels, metric="cosine"))
            except Exception:
                sil_val = None

    clustering_quality = (sil_val + 1.0) / 2.0 if sil_val is not None else 0.55

    rng = np.random.default_rng(rng_seed)
    retrieval_anomaly = _retrieval_spread_anomaly(x_norm, rng)

    isolation_risk = float(np.mean(dists > np.percentile(dists, 85)))

    texts: list[str] = []
    if extra_texts:
        texts.extend(extra_texts)
    for r in records:
        for key in ("_extracted_text", "text", "content", "chunk"):
            v = r.payload.get(key)
            if isinstance(v, str) and v.strip():
                texts.append(v)
                break

    injection_signals: list[dict[str, Any]] = []
    max_inj = 0.0
    for i, sample in enumerate(texts):
        score, reasons = _prompt_injection_score(sample)
        max_inj = max(max_inj, score)
        if score > 0.01:
            injection_signals.append(
                {"sampleIndex": i, "score": round(score, 4), "reasons": reasons}
            )

    text_emb = _encode_texts_sentence_transformers(texts) if texts else None
    embedding_alignment_penalty = 0.0
    if text_emb is not None and text_emb.shape[0] == len(texts):
        # Compare each text embedding to global centroid of memory vectors
        for row in text_emb:
            row_n = row / (np.linalg.norm(row) + 1e-12)
            sim = float(np.dot(row_n, centroid))
            if sim < 0.15:
                embedding_alignment_penalty += 0.08
        embedding_alignment_penalty = float(min(1.0, embedding_alignment_penalty))

    outlier_frac = len(anomalous_indices) / float(n)

    poisoning_probability = (
        0.24 * min(1.0, drift_mean * 2.2)
        + 0.18 * min(1.0, outlier_frac * 2.5)
        + 0.14 * min(1.0, imbalance * 0.35)
        + 0.22 * min(1.0, max_inj)
        + 0.12 * min(1.0, retrieval_anomaly)
        + 0.1 * embedding_alignment_penalty
        + 0.08 * min(1.0, drift_max * 1.5)
    )
    poisoning_probability -= 0.12 * (reputation_factor - 0.5)
    if sil_val is not None and sil_val < 0.08:
        poisoning_probability += 0.06
    poisoning_probability = float(np.clip(poisoning_probability, 0.0, 1.0))

    integrity_score = float(
        100.0
        * (1.0 - poisoning_probability * 0.85)
        * (0.45 + 0.55 * clustering_quality)
        * (0.85 + 0.15 * reputation_factor)
    )
    integrity_score = float(np.clip(integrity_score, 0.0, 100.0))

    trust_score = float(
        100.0
        * (
            1.0
            - 0.5 * poisoning_probability
            - 0.22 * min(1.0, max(0.0, drift_mean - 0.06) * 3.0)
            - 0.14 * min(1.0, outlier_frac * 2.0)
            - 0.1 * min(1.0, isolation_risk)
        )
        * (0.9 + 0.1 * reputation_factor)
    )
    trust_score = float(np.clip(trust_score, 0.0, 100.0))

    fingerprint = _fingerprint_matrix(x_norm)

    actions: list[str] = []
    if anomalous_indices:
        actions.append("quarantine_anomalous_vector_segments")
    if isolation_risk > 0.25:
        actions.append("trigger_embedding_rebaseline")
    if drift_mean > 0.18:
        actions.append("schedule_memory_rollback_review")
    if injection_signals:
        actions.append("enable_prompt_firewall_and_audit_chain")
    if retrieval_anomaly > 0.35:
        actions.append("audit_retrieval_pipeline_and_rerankers")
    if poisoning_probability > 0.45:
        actions.append("isolate_namespace_pending_forensics")

    return {
        "trustScore": round(trust_score, 2),
        "integrityScore": round(integrity_score, 2),
        "poisoningProbability": round(poisoning_probability, 4),
        "semanticDrift": round(drift_mean, 4),
        "semanticDriftMax": round(drift_max, 4),
        "poisonedClusterRisk": round(isolation_risk, 4),
        "clusterImbalance": round(imbalance, 4),
        "silhouetteScore": round(sil_val, 4) if sil_val is not None else None,
        "retrievalAnomalyScore": round(retrieval_anomaly, 4),
        "anomalousIndices": anomalous_indices,
        "anomalousPointIds": [records[i].point_id for i in anomalous_indices],
        "promptInjectionSignals": injection_signals,
        "fingerprint": fingerprint,
        "recommendedActions": actions,
        "centroid": centroid.tolist(),
        "reputationFactor": round(reputation_factor, 4),
        "vectorCount": n,
        "embeddingDim": dim,
        "kClusters": k,
    }


def analyze_from_embeddings_only(
    embeddings: list[list[float]],
    baseline_centroid: list[float] | None = None,
    text_samples: list[str] | None = None,
    *,
    rng_seed: int = 42,
) -> dict[str, Any]:
    records = [
        VectorRecord(point_id=str(i), vector=v, payload={}, source_reputation=1.0)
        for i, v in enumerate(embeddings)
    ]
    return run_semantic_integrity_pipeline(
        records,
        baseline_centroid,
        extra_texts=text_samples,
        rng_seed=rng_seed,
    )
