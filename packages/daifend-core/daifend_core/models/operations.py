from sqlalchemy import String, Text, DateTime, Float, JSON, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from .base import Base, TimestampMixin, _uuid


class TelemetryEventRecord(Base, TimestampMixin):
    __tablename__ = "telemetry_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ThreatIntelRecord(Base, TimestampMixin):
    __tablename__ = "threat_intel"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    signature: Mapped[str] = mapped_column(String(512), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    surface: Mapped[str] = mapped_column(String(32), nullable=False)
    intel_metadata: Mapped[dict | None] = mapped_column("metadata", JSON)


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open")
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    category: Mapped[str | None] = mapped_column(String(64), index=True)
    detail: Mapped[dict | None] = mapped_column(JSON)


class VectorSource(Base, TimestampMixin):
    """Registered vector store target per tenant (Qdrant collection, Pinecone index, etc.)."""

    __tablename__ = "vector_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    backend: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    collection_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSON)
    source_reputation: Mapped[float] = mapped_column(Float, default=1.0)


class MemorySnapshot(Base, TimestampMixin):
    """Baseline embedding centroid + fingerprint for drift comparison."""

    __tablename__ = "memory_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    vector_source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("vector_sources.id"), index=True
    )
    collection_id: Mapped[str | None] = mapped_column(String(128), index=True)
    centroid: Mapped[list] = mapped_column(JSON, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    point_count: Mapped[int] = mapped_column(Integer, default=0)
    scan_id: Mapped[str | None] = mapped_column(String(64), index=True)


class MemoryIntegrityReport(Base, TimestampMixin):
    __tablename__ = "memory_integrity_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    collection_id: Mapped[str | None] = mapped_column(String(128))
    scan_id: Mapped[str | None] = mapped_column(String(64), index=True)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    integrity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    poisoning_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    semantic_drift: Mapped[float] = mapped_column(Float, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    vector_backend: Mapped[str | None] = mapped_column(String(32))
    detail: Mapped[dict] = mapped_column(JSON, nullable=False)


class VectorMetadata(Base, TimestampMixin):
    __tablename__ = "vector_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    qdrant_collection: Mapped[str] = mapped_column(String(128), nullable=False)
    point_id: Mapped[str] = mapped_column(String(128), nullable=False)
    trust_weight: Mapped[float] = mapped_column(Float, default=1.0)
    labels: Mapped[dict | None] = mapped_column(JSON)
    connector_type: Mapped[str | None] = mapped_column(String(32))
    namespace: Mapped[str | None] = mapped_column(String(256))
    quarantined: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource: Mapped[str] = mapped_column(String(256), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)


class AgentRegistryEntry(Base, TimestampMixin):
    __tablename__ = "agent_registry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False)
    policy_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    containment_state: Mapped[str] = mapped_column(String(32), default="normal")
