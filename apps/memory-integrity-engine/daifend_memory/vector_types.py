"""Shared types for vector connector I/O."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VectorRecord:
    """One point from a vector database."""

    point_id: str
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)
    source_reputation: float = 1.0
