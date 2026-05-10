from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from daifend_memory.vector_types import VectorRecord


class VectorConnector(ABC):
    """Pluggable backend: pull embeddings + metadata for integrity analysis."""

    backend_id: str

    @abstractmethod
    def fetch_vectors(
        self,
        collection: str,
        *,
        limit: int = 512,
        namespace: str | None = None,
        filter_payload: dict[str, Any] | None = None,
    ) -> list[VectorRecord]:
        raise NotImplementedError

    @abstractmethod
    def delete_points(
        self,
        collection: str,
        point_ids: list[str],
        *,
        namespace: str | None = None,
    ) -> None:
        """Remove or quarantine vectors (backend-specific)."""

    @abstractmethod
    def health(self) -> dict[str, Any]:
        raise NotImplementedError
