from __future__ import annotations

import logging
import os
from typing import Any

from daifend_memory.connectors.base import VectorConnector
from daifend_memory.vector_types import VectorRecord

logger = logging.getLogger(__name__)


class PineconeConnector(VectorConnector):
    backend_id = "pinecone"

    def __init__(self, api_key: str, index_name: str) -> None:
        from pinecone import Pinecone

        self._pc = Pinecone(api_key=api_key)
        self._index_name = index_name
        self._index = self._pc.Index(index_name)

    def fetch_vectors(
        self,
        collection: str,
        *,
        limit: int = 512,
        namespace: str | None = None,
        filter_payload: dict[str, Any] | None = None,
    ) -> list[VectorRecord]:
        _ = collection
        _ = filter_payload
        ns = namespace if namespace is not None else ""
        records: list[VectorRecord] = []
        try:
            # Serverless / modern indexes: list() yields pages of vector IDs
            list_iter = self._index.list(namespace=ns)
            id_buffer: list[str] = []
            for page in list_iter:
                chunk = page if isinstance(page, list) else getattr(page, "vectors", page)
                if hasattr(chunk, "__iter__") and not isinstance(chunk, (str, bytes)):
                    id_buffer.extend(str(x) for x in chunk)
                else:
                    id_buffer.append(str(chunk))
                while len(id_buffer) >= 50 and len(records) < limit:
                    batch = id_buffer[:50]
                    id_buffer = id_buffer[50:]
                    res = self._index.fetch(ids=batch, namespace=ns)
                    for pid, vdata in (res.vectors or {}).items():
                        vec = list(map(float, vdata.values))
                        meta = dict(vdata.metadata or {})
                        rep = 1.0
                        if isinstance(meta.get("source_reputation"), (int, float)):
                            rep = float(meta["source_reputation"])
                        records.append(
                            VectorRecord(
                                point_id=str(pid),
                                vector=vec,
                                payload=meta,
                                source_reputation=max(0.0, min(1.0, rep)),
                            )
                        )
                        if len(records) >= limit:
                            return records
            if id_buffer and len(records) < limit:
                res = self._index.fetch(ids=id_buffer[:limit], namespace=ns)
                for pid, vdata in (res.vectors or {}).items():
                    vec = list(map(float, vdata.values))
                    meta = dict(vdata.metadata or {})
                    rep = 1.0
                    if isinstance(meta.get("source_reputation"), (int, float)):
                        rep = float(meta["source_reputation"])
                    records.append(
                        VectorRecord(
                            point_id=str(pid),
                            vector=vec,
                            payload=meta,
                            source_reputation=max(0.0, min(1.0, rep)),
                        )
                    )
                    if len(records) >= limit:
                        break
        except TypeError:
            # Fallback: query with small random probe (deterministic seed via zero — may fail dim)
            logger.warning("Pinecone list() unavailable; attempting describe + query fallback")
            stats = self._index.describe_index_stats()
            total = int(getattr(stats, "total_vector_count", 0) or 0)
            if total == 0:
                return []
            dim = int(os.environ.get("PINECONE_EMBEDDING_DIM", "384"))
            probe = [0.01 * (i % 7) for i in range(dim)]
            res = self._index.query(
                vector=probe,
                top_k=min(limit, max(1, total)),
                namespace=ns,
                include_metadata=True,
            )
            for m in res.matches or []:
                if m.values:
                    vec = list(map(float, m.values))
                    meta = dict(m.metadata or {})
                    rep = 1.0
                    if isinstance(meta.get("source_reputation"), (int, float)):
                        rep = float(meta["source_reputation"])
                    records.append(
                        VectorRecord(
                            point_id=str(m.id),
                            vector=vec,
                            payload=meta,
                            source_reputation=max(0.0, min(1.0, rep)),
                        )
                    )
        except Exception as exc:
            logger.exception("Pinecone fetch failed: %s", exc)
            raise
        return records[:limit]

    def delete_points(
        self,
        collection: str,
        point_ids: list[str],
        *,
        namespace: str | None = None,
    ) -> None:
        _ = collection
        if not point_ids:
            return
        ns = namespace if namespace is not None else ""
        self._index.delete(ids=point_ids, namespace=ns)

    def health(self) -> dict[str, Any]:
        try:
            stats = self._index.describe_index_stats()
            return {
                "ok": True,
                "backend": self.backend_id,
                "index": self._index_name,
                "total_vector_count": getattr(stats, "total_vector_count", None),
            }
        except Exception as exc:
            return {"ok": False, "backend": self.backend_id, "error": str(exc)}


def connector_from_env() -> PineconeConnector | None:
    key = os.environ.get("PINECONE_API_KEY", "").strip()
    idx = os.environ.get("PINECONE_INDEX", "").strip()
    if not key or not idx:
        return None
    return PineconeConnector(api_key=key, index_name=idx)
