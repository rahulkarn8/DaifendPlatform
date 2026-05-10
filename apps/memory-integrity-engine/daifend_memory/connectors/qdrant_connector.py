from __future__ import annotations

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from daifend_memory.connectors.base import VectorConnector
from daifend_memory.vector_types import VectorRecord

logger = logging.getLogger(__name__)


class QdrantConnector(VectorConnector):
    backend_id = "qdrant"

    def __init__(self, url: str, timeout: float = 30.0) -> None:
        self._client = QdrantClient(url=url.rstrip("/"), timeout=timeout)

    def fetch_vectors(
        self,
        collection: str,
        *,
        limit: int = 512,
        namespace: str | None = None,
        filter_payload: dict[str, Any] | None = None,
    ) -> list[VectorRecord]:
        flt: Filter | None = None
        if filter_payload:
            must = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_payload.items()
                if isinstance(v, (str, int, float, bool))
            ]
            if must:
                flt = Filter(must=must)

        records: list[VectorRecord] = []
        offset = None
        while len(records) < limit:
            batch_limit = min(128, limit - len(records))
            points, offset = self._client.scroll(
                collection_name=collection,
                scroll_filter=flt,
                limit=batch_limit,
                offset=offset,
                with_vectors=True,
                with_payload=True,
            )
            if not points:
                break
            for p in points:
                vec = p.vector
                if isinstance(vec, dict):
                    # named vectors — take first
                    vec = next(iter(vec.values()))
                if vec is None:
                    continue
                rep = 1.0
                if p.payload and isinstance(p.payload.get("source_reputation"), (int, float)):
                    rep = float(p.payload["source_reputation"])
                text = ""
                if p.payload:
                    for key in ("text", "content", "chunk", "body", "document"):
                        if key in p.payload and isinstance(p.payload[key], str):
                            text = p.payload[key]
                            break
                pr = dict(p.payload or {})
                if text:
                    pr["_extracted_text"] = text
                records.append(
                    VectorRecord(
                        point_id=str(p.id),
                        vector=list(map(float, vec)),
                        payload=pr,
                        source_reputation=max(0.0, min(1.0, rep)),
                    )
                )
            if offset is None:
                break
        return records[:limit]

    def delete_points(
        self,
        collection: str,
        point_ids: list[str],
        *,
        namespace: str | None = None,
    ) -> None:
        _ = namespace
        if not point_ids:
            return
        from qdrant_client.models import PointIdsList

        self._client.delete(
            collection_name=collection,
            points_selector=PointIdsList(points=point_ids),
        )

    def health(self) -> dict[str, Any]:
        try:
            cols = self._client.get_collections()
            return {
                "ok": True,
                "backend": self.backend_id,
                "collections": [c.name for c in cols.collections],
            }
        except Exception as exc:
            logger.warning("Qdrant health failed: %s", exc)
            return {"ok": False, "backend": self.backend_id, "error": str(exc)}
