"""Phase 6 Sentinel-2 L2A Optical/SWIR Satellite Context Intelligence

Revision ID: 20260909000003
Revises: 20260909000002
Create Date: 2026-09-09 18:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260909000003"
down_revision: str | None = "20260909000002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "thermal_sentinel_context_profiles" not in existing_tables:
        op.create_table(
            "thermal_sentinel_context_profiles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("observation_id", sa.String(length=64), nullable=False),
            sa.Column("provider", sa.String(length=64), server_default="CDSE", nullable=False),
            sa.Column("collection", sa.String(length=64), server_default="sentinel-2-l2a", nullable=False),
            sa.Column("scene_id", sa.String(length=128), nullable=True),
            sa.Column("product_id", sa.String(length=128), nullable=True),
            sa.Column("satellite_platform", sa.String(length=32), nullable=True),
            sa.Column("scene_acquisition_time_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("target_firms_time_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("scene_age_hours", sa.Float(), nullable=True),
            sa.Column("scene_age_days", sa.Float(), nullable=True),
            sa.Column("temporal_quality", sa.String(length=32), nullable=True),
            sa.Column("catalogue_cloud_cover", sa.Float(), nullable=True),
            sa.Column("local_valid_fraction", sa.Float(), nullable=True),
            sa.Column("local_cloud_fraction", sa.Float(), nullable=True),
            sa.Column("local_cloud_shadow_fraction", sa.Float(), nullable=True),
            sa.Column("local_snow_fraction", sa.Float(), nullable=True),
            sa.Column("quality_status", sa.String(length=32), nullable=False),
            sa.Column("provider_status", sa.String(length=32), nullable=False),
            sa.Column("analytical_resolution_m", sa.Float(), server_default="20.0", nullable=False),
            # Point-level features
            sa.Column("point_is_valid", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("point_scl", sa.Integer(), nullable=True),
            sa.Column("point_b04", sa.Float(), nullable=True),
            sa.Column("point_b08", sa.Float(), nullable=True),
            sa.Column("point_b11", sa.Float(), nullable=True),
            sa.Column("point_b12", sa.Float(), nullable=True),
            sa.Column("point_ndvi", sa.Float(), nullable=True),
            sa.Column("point_ndmi", sa.Float(), nullable=True),
            sa.Column("point_nbr", sa.Float(), nullable=True),
            # Neighborhood multi-scale distributions
            sa.Column("stats_100m", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("stats_250m", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("stats_500m", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            # Phase-7 explicit feature fusion columns
            sa.Column("sentinel_scene_age_days", sa.Float(), nullable=True),
            sa.Column("sentinel_valid_fraction_250m", sa.Float(), nullable=True),
            sa.Column("sentinel_b04_median_250m", sa.Float(), nullable=True),
            sa.Column("sentinel_b08_median_250m", sa.Float(), nullable=True),
            sa.Column("sentinel_b11_median_250m", sa.Float(), nullable=True),
            sa.Column("sentinel_b12_median_250m", sa.Float(), nullable=True),
            sa.Column("sentinel_ndvi_median_250m", sa.Float(), nullable=True),
            sa.Column("sentinel_ndmi_median_250m", sa.Float(), nullable=True),
            sa.Column("sentinel_nbr_median_250m", sa.Float(), nullable=True),
            sa.Column("sentinel_b11_p90_250m", sa.Float(), nullable=True),
            sa.Column("sentinel_b12_p90_250m", sa.Float(), nullable=True),
            # Metadata & Timestamps
            sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("algorithm_version", sa.String(length=32), server_default="sentinel2_context_v1", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            # Primary key, foreign key, unique constraint
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["observation_id"],
                ["thermal_observations.observation_id"],
                ondelete="CASCADE",
                name="fk_sentinel_obs_id",
            ),
            sa.UniqueConstraint("observation_id", "algorithm_version", name="uq_obs_sentinel_alg_version"),
        )

        op.create_index(
            "idx_sentinel_profile_obs_id",
            "thermal_sentinel_context_profiles",
            ["observation_id"],
            unique=False,
        )
        op.create_index(
            "idx_sentinel_profile_quality",
            "thermal_sentinel_context_profiles",
            ["quality_status"],
            unique=False,
        )
        op.create_index(
            "idx_sentinel_profile_scene_id",
            "thermal_sentinel_context_profiles",
            ["scene_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "thermal_sentinel_context_profiles" in existing_tables:
        op.drop_index("idx_sentinel_profile_scene_id", table_name="thermal_sentinel_context_profiles")
        op.drop_index("idx_sentinel_profile_quality", table_name="thermal_sentinel_context_profiles")
        op.drop_index("idx_sentinel_profile_obs_id", table_name="thermal_sentinel_context_profiles")
        op.drop_table("thermal_sentinel_context_profiles")
