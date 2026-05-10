"""enterprise quotas and security policies

Revision ID: 003
Revises: 002
Create Date: 2026-05-10

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenant_quotas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("telemetry_events_per_day", sa.Integer(), server_default="1000000"),
        sa.Column("api_requests_per_minute", sa.Integer(), server_default="6000"),
        sa.Column("memory_scans_per_hour", sa.Integer(), server_default="120"),
        sa.Column("hard_enforce", sa.Boolean(), server_default="false"),
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
    op.create_index("ix_tenant_quotas_tenant", "tenant_quotas", ["tenant_id"])

    op.create_table(
        "security_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("policy_type", sa.String(64), nullable=False, index=True),
        sa.Column("body", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("opa_bundle_ref", sa.String(512)),
        sa.Column("version", sa.Integer(), server_default="1"),
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
    op.create_index("ix_security_policies_tenant", "security_policies", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_security_policies_tenant", table_name="security_policies")
    op.drop_table("security_policies")
    op.drop_index("ix_tenant_quotas_tenant", table_name="tenant_quotas")
    op.drop_table("tenant_quotas")
