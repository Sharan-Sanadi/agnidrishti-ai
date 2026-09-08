"""Phase 3 Temporal Persistence Intelligence and Dataset Coverage

Revision ID: 20260908000002
Revises: 20260908000001
Create Date: 2026-09-08 18:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260908000002"
down_revision: str | None = "20260908000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create firms_data_coverage table
    op.create_table(
        "firms_data_coverage",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_product", sa.String(length=64), nullable=False),
        sa.Column("coverage_date", sa.Date(), nullable=False),
        sa.Column("west", sa.Float(), nullable=False),
        sa.Column("south", sa.Float(), nullable=False),
        sa.Column("east", sa.Float(), nullable=False),
        sa.Column("north", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("fetched_count", sa.Integer(), nullable=False),
        sa.Column("valid_count", sa.Integer(), nullable=False),
        sa.Column("upserted_count", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_product",
            "coverage_date",
            "west",
            "south",
            "east",
            "north",
            name="uq_coverage_source_date_bbox",
        ),
    )
    op.create_index(
        "idx_firms_coverage_query",
        "firms_data_coverage",
        ["coverage_date", "source_product"],
        unique=False,
    )

    # 2. Create persistence_profiles table
    op.create_table(
        "persistence_profiles",
        sa.Column("observation_id", sa.String(length=64), nullable=False),
        sa.Column("algorithm_version", sa.String(length=64), nullable=False),
        sa.Column("analysis_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("radius_m", sa.Float(), nullable=False),
        sa.Column("raw_detection_count_7d", sa.Integer(), nullable=False),
        sa.Column("raw_detection_count_30d", sa.Integer(), nullable=False),
        sa.Column("active_days_7d", sa.Integer(), nullable=False),
        sa.Column("active_days_30d", sa.Integer(), nullable=False),
        sa.Column("active_weeks_30d", sa.Integer(), nullable=False),
        sa.Column("first_seen_30d", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_30d", sa.DateTime(timezone=True), nullable=True),
        sa.Column("temporal_span_days_30d", sa.Float(), nullable=False),
        sa.Column("history_coverage_days_7d", sa.Integer(), nullable=False),
        sa.Column("history_coverage_days_30d", sa.Integer(), nullable=False),
        sa.Column("history_coverage_ratio_30d", sa.Float(), nullable=False),
        sa.Column("persistence_index", sa.Integer(), nullable=False),
        sa.Column("persistence_class", sa.String(length=32), nullable=False),
        sa.Column("explanation", sa.String(length=512), nullable=False),
        sa.Column("explanation_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["observation_id"],
            ["thermal_observations.observation_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("observation_id"),
    )
    op.create_index(
        "idx_persistence_class_index",
        "persistence_profiles",
        ["persistence_class", "persistence_index"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_persistence_class_index", table_name="persistence_profiles")
    op.drop_table("persistence_profiles")
    op.drop_index("idx_firms_coverage_query", table_name="firms_data_coverage")
    op.drop_table("firms_data_coverage")
