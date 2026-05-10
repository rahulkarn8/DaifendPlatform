"""memory integrity production schema

Revision ID: 002
Revises: 001
Create Date: 2026-05-09

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vector_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("backend", sa.String(32), nullable=False, index=True),
        sa.Column("collection_ref", sa.String(512), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("source_reputation", sa.Float(), server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_vector_sources_tenant", "vector_sources", ["tenant_id"])

    op.create_table(
        "memory_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("vector_source_id", sa.String(36), sa.ForeignKey("vector_sources.id")),
        sa.Column("collection_id", sa.String(128), index=True),
        sa.Column("centroid", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("fingerprint", sa.String(128), nullable=False),
        sa.Column("point_count", sa.Integer(), server_default="0"),
        sa.Column("scan_id", sa.String(64), index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_memory_snapshots_tenant", "memory_snapshots", ["tenant_id"])

    op.add_column(
        "incidents",
        sa.Column("category", sa.String(64), nullable=True),
    )
    op.add_column(
        "incidents",
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_incidents_category", "incidents", ["category"])

    op.add_column(
        "memory_integrity_reports",
        sa.Column("scan_id", sa.String(64), nullable=True),
    )
    op.add_column(
        "memory_integrity_reports",
        sa.Column("integrity_score", sa.Float(), server_default="0", nullable=False),
    )
    op.add_column(
        "memory_integrity_reports",
        sa.Column(
            "poisoning_probability", sa.Float(), server_default="0", nullable=False
        ),
    )
    op.add_column(
        "memory_integrity_reports",
        sa.Column("vector_backend", sa.String(32), nullable=True),
    )
    op.create_index("ix_memory_reports_scan", "memory_integrity_reports", ["scan_id"])

    op.add_column(
        "vector_metadata",
        sa.Column("connector_type", sa.String(32), nullable=True),
    )
    op.add_column(
        "vector_metadata",
        sa.Column("namespace", sa.String(256), nullable=True),
    )
    op.add_column(
        "vector_metadata",
        sa.Column("quarantined", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index("ix_vector_quarantined", "vector_metadata", ["quarantined"])


def downgrade() -> None:
    op.drop_index("ix_vector_quarantined", table_name="vector_metadata")
    op.drop_column("vector_metadata", "quarantined")
    op.drop_column("vector_metadata", "namespace")
    op.drop_column("vector_metadata", "connector_type")

    op.drop_index("ix_memory_reports_scan", table_name="memory_integrity_reports")
    op.drop_column("memory_integrity_reports", "vector_backend")
    op.drop_column("memory_integrity_reports", "poisoning_probability")
    op.drop_column("memory_integrity_reports", "integrity_score")
    op.drop_column("memory_integrity_reports", "scan_id")

    op.drop_index("ix_incidents_category", table_name="incidents")
    op.drop_column("incidents", "detail")
    op.drop_column("incidents", "category")

    op.drop_index("ix_memory_snapshots_tenant", table_name="memory_snapshots")
    op.drop_table("memory_snapshots")

    op.drop_index("ix_vector_sources_tenant", table_name="vector_sources")
    op.drop_table("vector_sources")
