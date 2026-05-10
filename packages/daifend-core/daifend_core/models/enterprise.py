from sqlalchemy import String, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, _uuid


class TenantQuota(Base, TimestampMixin):
    __tablename__ = "tenant_quotas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    telemetry_events_per_day: Mapped[int] = mapped_column(Integer, default=1_000_000)
    api_requests_per_minute: Mapped[int] = mapped_column(Integer, default=6000)
    memory_scans_per_hour: Mapped[int] = mapped_column(Integer, default=120)
    hard_enforce: Mapped[bool] = mapped_column(Boolean, default=False)


class SecurityPolicy(Base, TimestampMixin):
    __tablename__ = "security_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    body: Mapped[dict] = mapped_column(JSON, nullable=False)
    opa_bundle_ref: Mapped[str | None] = mapped_column(String(512))
    version: Mapped[int] = mapped_column(Integer, default=1)
