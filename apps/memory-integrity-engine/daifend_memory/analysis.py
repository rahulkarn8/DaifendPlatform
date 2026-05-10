"""Backward-compatible entrypoints delegating to the semantic integrity pipeline."""

from __future__ import annotations

from typing import Any

from daifend_memory.semantic_pipeline import analyze_from_embeddings_only


def analyze_memory_integrity(
    embeddings: list[list[float]],
    baseline_centroid: list[float] | None = None,
    text_samples: list[str] | None = None,
) -> dict[str, Any]:
    return analyze_from_embeddings_only(
        embeddings,
        baseline_centroid=baseline_centroid,
        text_samples=text_samples,
    )
