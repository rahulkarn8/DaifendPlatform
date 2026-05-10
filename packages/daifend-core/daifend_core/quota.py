"""Tenant API quota: Postgres limits + Redis sliding minute counter."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from sqlalchemy import select

from daifend_core.db_sync import sync_session_scope
from daifend_core.models import TenantQuota

logger = logging.getLogger(__name__)


class QuotaExceeded(Exception):
    def __init__(self, detail: str, status_code: int = 429, headers: dict | None = None):
        self.detail = detail
        self.status_code = status_code
        self.headers = headers or {}


def _default_rpm() -> int:
    return int(os.environ.get("DEFAULT_TENANT_API_RPM", "6000"))


def get_tenant_api_rpm(tenant_id: str) -> int:
    try:
        with sync_session_scope() as s:
            row = s.scalar(
                select(TenantQuota).where(TenantQuota.tenant_id == tenant_id).limit(1)
            )
            if row is not None:
                return int(row.api_requests_per_minute)
    except Exception as exc:
        logger.warning("quota db read failed for %s: %s", tenant_id, exc)
    return _default_rpm()


def check_api_minute_quota(tenant_id: str) -> None:
    """Increment per-tenant per-minute counter; raise QuotaExceeded if over limit."""
    limit = get_tenant_api_rpm(tenant_id)
    redis_url = os.environ.get("REDIS_URL", "").strip()
    minute_key = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    redis_key = f"daifend:quota:api:{tenant_id}:{minute_key}"

    if not redis_url:
        if not hasattr(check_api_minute_quota, "_local"):
            check_api_minute_quota._local = {}  # type: ignore[attr-defined]
        d: dict[str, int] = check_api_minute_quota._local  # type: ignore[attr-defined]
        cur = d.get(redis_key, 0) + 1
        d[redis_key] = cur
        if len(d) > 256:
            d.clear()
        if cur > limit:
            raise QuotaExceeded(
                "tenant_api_quota_exceeded",
                headers={"Retry-After": "60"},
            )
        return

    try:
        import redis

        r = redis.Redis.from_url(redis_url, decode_responses=True)
        pipe = r.pipeline()
        pipe.incr(redis_key)
        pipe.expire(redis_key, 120)
        cur, _ = pipe.execute()
        if int(cur) > limit:
            raise QuotaExceeded(
                "tenant_api_quota_exceeded",
                headers={"Retry-After": "60"},
            )
    except QuotaExceeded:
        raise
    except Exception as exc:
        logger.warning("quota redis failed (fail-open): %s", exc)


def check_memory_scan_hourly_quota(tenant_id: str) -> None:
    hourly_limit = int(os.environ.get("DEFAULT_MEMORY_SCANS_PER_HOUR", "120"))
    try:
        with sync_session_scope() as s:
            row = s.scalar(
                select(TenantQuota).where(TenantQuota.tenant_id == tenant_id).limit(1)
            )
            if row is not None:
                hourly_limit = int(row.memory_scans_per_hour)
    except Exception as exc:
        logger.warning("memory quota db read failed: %s", exc)

    redis_url = os.environ.get("REDIS_URL", "").strip()
    hour_key = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    redis_key = f"daifend:quota:memory_scan:{tenant_id}:{hour_key}"

    if not redis_url:
        return

    try:
        import redis

        r = redis.Redis.from_url(redis_url, decode_responses=True)
        pipe = r.pipeline()
        pipe.incr(redis_key)
        pipe.expire(redis_key, 7200)
        cur, _ = pipe.execute()
        if int(cur) > hourly_limit:
            raise QuotaExceeded(
                "tenant_memory_scan_quota_exceeded",
                status_code=429,
                headers={"Retry-After": "3600"},
            )
    except QuotaExceeded:
        raise
    except Exception as exc:
        logger.warning("memory scan quota redis failed (fail-open): %s", exc)
