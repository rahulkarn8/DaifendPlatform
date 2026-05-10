from __future__ import annotations

import ast
import logging
import os
import re
from typing import Any

from daifend_memory.connectors.base import VectorConnector
from daifend_memory.vector_types import VectorRecord

logger = logging.getLogger(__name__)

_VEC_BRACKET = re.compile(r"^\s*\[(.*)\]\s*$", re.DOTALL)


def _parse_pgvector_text(val: str) -> list[float]:
    """Parse pgvector textual representation to floats."""
    val = val.strip()
    m = _VEC_BRACKET.match(val)
    if m:
        inner = m.group(1).strip()
        if not inner:
            return []
        try:
            parsed = ast.literal_eval("[" + inner + "]")
            if isinstance(parsed, list):
                return [float(x) for x in parsed]
        except (SyntaxError, ValueError, TypeError):
            pass
    parts = val.replace("[", "").replace("]", "").split(",")
    return [float(p.strip()) for p in parts if p.strip()]


class PgVectorConnector(VectorConnector):
    backend_id = "pgvector"

    def __init__(
        self,
        dsn: str,
        table: str,
        id_column: str = "id",
        embedding_column: str = "embedding",
        payload_columns: str | None = None,
    ) -> None:
        self._dsn = dsn
        self._table = table
        self._id_col = id_column
        self._emb_col = embedding_column
        self._payload_cols = (
            [c.strip() for c in payload_columns.split(",") if c.strip()]
            if payload_columns
            else []
        )

    def _connect(self):
        import psycopg

        return psycopg.connect(self._dsn)

    def fetch_vectors(
        self,
        collection: str,
        *,
        limit: int = 512,
        namespace: str | None = None,
        filter_payload: dict[str, Any] | None = None,
    ) -> list[VectorRecord]:
        _ = namespace
        table = (collection.strip() if collection else None) or self._table
        extra_select = ""
        if self._payload_cols:
            extra_select = ", " + ", ".join(f'"{c}"' for c in self._payload_cols)

        where = ""
        params: list[Any] = []
        if filter_payload:
            parts = []
            for k, v in filter_payload.items():
                parts.append(f'"{k}" = %s')
                params.append(v)
            if parts:
                where = " WHERE " + " AND ".join(parts)

        sql = (
            f'SELECT "{self._id_col}"::text, "{self._emb_col}"::text {extra_select} '
            f'FROM "{table}"{where} LIMIT %s'
        )
        params.append(limit)

        records: list[VectorRecord] = []
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    for row in cur.fetchall():
                        pid = row[0]
                        raw_vec = row[1]
                        if raw_vec is None:
                            continue
                        vec = _parse_pgvector_text(str(raw_vec))
                        if not vec:
                            continue
                        payload: dict[str, Any] = {}
                        for i, col in enumerate(self._payload_cols):
                            if 2 + i < len(row) and row[2 + i] is not None:
                                payload[col] = row[2 + i]
                        rep = 1.0
                        if isinstance(payload.get("source_reputation"), (int, float)):
                            rep = float(payload["source_reputation"])
                        records.append(
                            VectorRecord(
                                point_id=str(pid),
                                vector=vec,
                                payload=payload,
                                source_reputation=max(0.0, min(1.0, rep)),
                            )
                        )
        except Exception as exc:
            logger.exception("pgvector fetch failed: %s", exc)
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
        if not point_ids:
            return
        table = os.environ.get("PGVECTOR_TABLE", self._table)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f'DELETE FROM "{table}" WHERE "{self._id_col}"::text = ANY(%s)',
                    (point_ids,),
                )
            conn.commit()

    def health(self) -> dict[str, Any]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return {"ok": True, "backend": self.backend_id, "table": self._table}
        except Exception as exc:
            return {"ok": False, "backend": self.backend_id, "error": str(exc)}


def connector_from_env() -> PgVectorConnector | None:
    dsn = os.environ.get("PGVECTOR_DSN", "").strip()
    table = os.environ.get("PGVECTOR_TABLE", "").strip()
    if not dsn or not table:
        return None
    return PgVectorConnector(
        dsn=dsn,
        table=table,
        id_column=os.environ.get("PGVECTOR_ID_COLUMN", "id"),
        embedding_column=os.environ.get("PGVECTOR_EMBEDDING_COLUMN", "embedding"),
        payload_columns=os.environ.get("PGVECTOR_PAYLOAD_COLUMNS", ""),
    )
