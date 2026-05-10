"""Shared synchronous SQLAlchemy session for services that are not async (gateway, auth)."""

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_engine = None
_factory: sessionmaker[Session] | None = None


def _normalize_database_url(url: str) -> str:
    url = url.strip()
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg://" + url.split("postgresql+asyncpg://", 1)[1]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.split("postgresql://", 1)[1]
    return url


def sync_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return _normalize_database_url(url)
    from daifend_core.settings import ServiceSettings

    return _normalize_database_url(ServiceSettings().postgres_url)


def get_sync_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(sync_database_url(), pool_pre_ping=True)
    return _engine


def get_sync_session_factory() -> sessionmaker[Session]:
    global _factory
    if _factory is None:
        _factory = sessionmaker(
            bind=get_sync_engine(), autoflush=False, autocommit=False
        )
    return _factory


@contextmanager
def sync_session_scope() -> Generator[Session, None, None]:
    fac = get_sync_session_factory()
    session = fac()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
