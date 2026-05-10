from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlparse

from daifend_memory.connectors.base import VectorConnector
from daifend_memory.vector_types import VectorRecord

logger = logging.getLogger(__name__)


class WeaviateConnector(VectorConnector):
    backend_id = "weaviate"

    def __init__(
        self,
        http_url: str,
        class_name: str,
        api_key: str | None = None,
    ) -> None:
        import weaviate

        u = urlparse(http_url)
        host = u.hostname or "localhost"
        port = u.port or (443 if u.scheme == "https" else 8080)
        secure = u.scheme == "https"
        grpc_host = os.environ.get("WEAVIATE_GRPC_HOST", host)
        grpc_port = int(os.environ.get("WEAVIATE_GRPC_PORT", "50051"))
        headers: dict[str, str] | None = None
        if api_key:
            headers = {"Authorization": f"Bearer {api_key}"}

        self._client = weaviate.connect_to_custom(
            http_host=host,
            http_port=port,
            http_secure=secure,
            grpc_host=grpc_host,
            grpc_port=grpc_port,
            headers=headers,
        )
        self._class_name = class_name

    def fetch_vectors(
        self,
        collection: str,
        *,
        limit: int = 512,
        namespace: str | None = None,
        filter_payload: dict[str, Any] | None = None,
    ) -> list[VectorRecord]:
        _ = namespace
        _ = filter_payload
        name = collection or self._class_name
        coll = self._client.collections.get(name)
        records: list[VectorRecord] = []
        try:
            for i, obj in enumerate(coll.iterator(include_vector=True)):
                if i >= limit:
                    break
                vec_raw = obj.vector
                if isinstance(vec_raw, dict):
                    vec = list(map(float, next(iter(vec_raw.values()))))
                elif vec_raw is not None:
                    vec = list(map(float, vec_raw))
                else:
                    continue
                props = dict(obj.properties or {})
                rep = 1.0
                if isinstance(props.get("source_reputation"), (int, float)):
                    rep = float(props["source_reputation"])
                records.append(
                    VectorRecord(
                        point_id=str(obj.uuid),
                        vector=vec,
                        payload=props,
                        source_reputation=max(0.0, min(1.0, rep)),
                    )
                )
        except Exception as exc:
            logger.exception("Weaviate iterator failed: %s", exc)
            raise
        return records

    def delete_points(
        self,
        collection: str,
        point_ids: list[str],
        *,
        namespace: str | None = None,
    ) -> None:
        _ = namespace
        name = collection or self._class_name
        coll = self._client.collections.get(name)
        for pid in point_ids:
            coll.data.delete_by_id(pid)

    def health(self) -> dict[str, Any]:
        try:
            live = self._client.is_ready()
            return {"ok": bool(live), "backend": self.backend_id, "class": self._class_name}
        except Exception as exc:
            return {"ok": False, "backend": self.backend_id, "error": str(exc)}


def connector_from_env() -> WeaviateConnector | None:
    url = os.environ.get("WEAVIATE_URL", "").strip()
    cls = os.environ.get("WEAVIATE_CLASS", "").strip()
    if not url or not cls:
        return None
    key = os.environ.get("WEAVIATE_API_KEY", "").strip() or None
    return WeaviateConnector(http_url=url, class_name=cls, api_key=key)
