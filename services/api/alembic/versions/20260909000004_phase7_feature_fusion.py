"""Phase 7 Feature Fusion Intelligence Profile

Revision ID: 20260909000004
Revises: 20260909000003
Create Date: 2026-09-09 21:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260909000004"
down_revision: str | None = "20260909000003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "thermal_feature_fusion_profiles" not in existing_tables:
        op.create_table(
            "thermal_feature_fusion_profiles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("observation_id", sa.String(length=64), nullable=False),
            sa.Column("schema_version", sa.String(length=32), server_default="fusion_v1", nullable=False),
            sa.Column("schema_hash", sa.String(length=64), nullable=False),
            sa.Column("source_fingerprint", sa.String(length=64), nullable=False),
            sa.Column("fusion_status", sa.String(length=32), nullable=False),
            sa.Column("total_group_count", sa.Integer(), server_default="5", nullable=False),
            sa.Column("evaluated_group_count", sa.Integer(), nullable=False),
            sa.Column("usable_group_count", sa.Integer(), nullable=False),
            sa.Column("expected_feature_count", sa.Integer(), nullable=False),
            sa.Column("non_null_feature_count", sa.Integer(), nullable=False),
            sa.Column("feature_coverage_fraction", sa.Float(), nullable=False),
            sa.Column("feature_vector", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("group_status", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("quality_flags", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
            sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["observation_id"],
                ["thermal_observations.observation_id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("observation_id", "schema_version", name="uq_fusion_observation_schema"),
        )
        op.create_index(
            "idx_fusion_observation_id",
            "thermal_feature_fusion_profiles",
            ["observation_id"],
            unique=False,
        )
        op.create_index(
            "idx_fusion_status",
            "thermal_feature_fusion_profiles",
            ["fusion_status"],
            unique=False,
        )
        op.create_index(
            "idx_fusion_schema_version",
            "thermal_feature_fusion_profiles",
            ["schema_version"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("idx_fusion_schema_version", table_name="thermal_feature_fusion_profiles")
    op.drop_index("idx_fusion_status", table_name="thermal_feature_fusion_profiles")
    op.drop_index("idx_fusion_observation_id", table_name="thermal_feature_fusion_profiles")
    op.drop_table("thermal_feature_fusion_profiles")
