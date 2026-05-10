"""Synchronous PostgreSQL persistence for memory integrity (SQLAlchemy + psycopg)."""

from __future__ import annotations

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from daifend_core.models import (
    AuditLog,
    Incident,
    MemoryIntegrityReport,
    MemorySnapshot,
)

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def _normalize_database_url(url: str) -> str:
    url = url.strip()
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg://" + url.split("postgresql+asyncpg://", 1)[1]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.split("postgresql://", 1)[1]
    return url


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return _normalize_database_url(url)
    from daifend_core.settings import ServiceSettings

    return _normalize_database_url(ServiceSettings().postgres_url)


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(_get_database_url(), pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(), autoflush=False, autocommit=False
        )
    return _SessionLocal


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    fac = get_session_factory()
    session = fac()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def save_integrity_report(
    tenant_id: str,
    collection_id: str | None,
    scan_id: str | None,
    backend: str | None,
    result: dict[str, Any],
) -> str:
    """Persist analysis; returns report id."""
    detail = {k: v for k, v in result.items() if k != "centroid"}
    if "centroid" in result:
        detail["centroid"] = result["centroid"]
    with session_scope() as s:
        row = MemoryIntegrityReport(
            tenant_id=tenant_id,
            collection_id=collection_id,
            scan_id=scan_id,
            trust_score=float(result["trustScore"]),
            integrity_score=float(result.get("integrityScore", result["trustScore"])),
            poisoning_probability=float(result.get("poisoningProbability", 0)),
            semantic_drift=float(result["semanticDrift"]),
            fingerprint=str(result["fingerprint"]),
            vector_backend=backend,
            detail=detail,
        )
        s.add(row)
        s.flush()
        rid = row.id
    return rid


def save_snapshot(
    tenant_id: str,
    collection_id: str | None,
    scan_id: str | None,
    centroid: list[float],
    fingerprint: str,
    point_count: int,
    vector_source_id: str | None = None,
) -> str:
    with session_scope() as s:
        snap = MemorySnapshot(
            tenant_id=tenant_id,
            vector_source_id=vector_source_id,
            collection_id=collection_id,
            centroid=centroid,
            fingerprint=fingerprint,
            point_count=point_count,
            scan_id=scan_id,
        )
        s.add(snap)
        s.flush()
        return snap.id


def load_snapshot_centroid(snapshot_id: str, tenant_id: str) -> list[float] | None:
    with session_scope() as s:
        snap = s.get(MemorySnapshot, snapshot_id)
        if snap is None or snap.tenant_id != tenant_id:
            return None
        return list(snap.centroid) if snap.centroid else None


def list_reports(tenant_id: str, limit: int = 20) -> list[dict[str, Any]]:
    with session_scope() as s:
        q = (
            select(MemoryIntegrityReport)
            .where(MemoryIntegrityReport.tenant_id == tenant_id)
            .order_by(MemoryIntegrityReport.created_at.desc())
            .limit(limit)
        )
        rows = s.scalars(q).all()
        out = []
        for r in rows:
            out.append(
                {
                    "id": r.id,
                    "tenantId": r.tenant_id,
                    "collectionId": r.collection_id,
                    "scanId": r.scan_id,
                    "trustScore": r.trust_score,
                    "integrityScore": r.integrity_score,
                    "poisoningProbability": r.poisoning_probability,
                    "semanticDrift": r.semantic_drift,
                    "fingerprint": r.fingerprint,
                    "vectorBackend": r.vector_backend,
                    "detail": r.detail,
                    "createdAt": r.created_at.isoformat() if r.created_at else None,
                }
            )
        return out


def list_incidents(tenant_id: str, limit: int = 50) -> list[dict[str, Any]]:
    with session_scope() as s:
        q = (
            select(Incident)
            .where(Incident.tenant_id == tenant_id)
            .order_by(Incident.created_at.desc())
            .limit(limit)
        )
        rows = s.scalars(q).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "status": r.status,
                "severity": r.severity,
                "category": r.category,
                "detail": r.detail,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]


def create_incident(
    tenant_id: str,
    title: str,
    severity: str,
    category: str,
    detail: dict[str, Any],
) -> str:
    with session_scope() as s:
        inc = Incident(
            tenant_id=tenant_id,
            title=title,
            status="open",
            severity=severity,
            category=category,
            detail=detail,
        )
        s.add(inc)
        s.flush()
        return inc.id


def audit(
    tenant_id: str,
    actor_id: str | None,
    action: str,
    resource: str,
    detail: str | None = None,
) -> None:
    try:
        with session_scope() as s:
            s.add(
                AuditLog(
                    tenant_id=tenant_id,
                    actor_id=actor_id,
                    action=action,
                    resource=resource,
                    detail=detail,
                )
            )
    except Exception as exc:
        logger.warning("audit log failed: %s", exc)
