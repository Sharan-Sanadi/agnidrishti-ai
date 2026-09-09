"""Phase 5 Land-Cover Intelligence with ESA WorldCover 2021 v200

Revision ID: 20260909000002
Revises: 20260909000001
Create Date: 2026-09-09 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260909000002"
down_revision: str | None = "20260909000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "thermal_land_cover_profiles" not in existing_tables:
        op.create_table(
            "thermal_land_cover_profiles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("observation_id", sa.String(length=64), nullable=False),
            sa.Column("provider", sa.String(length=64), server_default="ESA_WORLDCOVER", nullable=False),
            sa.Column("product_name", sa.String(length=64), server_default="ESA WorldCover 10 m 2021", nullable=False),
            sa.Column("product_version", sa.String(length=32), server_default="v200", nullable=False),
            sa.Column("source_year", sa.Integer(), server_default="2021", nullable=False),
            sa.Column("algorithm_version", sa.String(length=64), server_default="land_cover_v1", nullable=False),
            sa.Column("point_class_code", sa.Integer(), nullable=False),
            sa.Column("point_class_name", sa.String(length=64), nullable=False),
            sa.Column("point_tile_id", sa.String(length=32), nullable=False),
            sa.Column("context_class", sa.String(length=64), nullable=False),
            sa.Column("coverage_status", sa.String(length=32), nullable=False),
            sa.Column("dominant_class_250m", sa.String(length=64), nullable=False),
            sa.Column("dominant_fraction_250m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("dominant_class_500m", sa.String(length=64), nullable=False),
            sa.Column("dominant_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("dominant_class_1000m", sa.String(length=64), nullable=False),
            sa.Column("dominant_fraction_1000m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("class_distribution_250m", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("class_distribution_500m", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("class_distribution_1000m", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("valid_pixel_count_250m", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("valid_pixel_count_500m", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("valid_pixel_count_1000m", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("valid_fraction_250m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("valid_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("valid_fraction_1000m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("tree_cover_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("shrubland_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("grassland_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("cropland_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("built_up_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("bare_sparse_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("snow_ice_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("water_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("wetland_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("mangrove_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("moss_lichen_fraction_500m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("tiles_used", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("sampled_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(
                ["observation_id"],
                ["thermal_observations.observation_id"],
                name="fk_thermal_lc_profile_observation_id",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id", name="pk_thermal_land_cover_profiles"),
            sa.UniqueConstraint(
                "observation_id",
                "provider",
                "product_version",
                "algorithm_version",
                name="uq_thermal_lc_profile_identity",
            ),
        )

        op.create_index(
            "idx_thermal_lc_observation_id",
            "thermal_land_cover_profiles",
            ["observation_id"],
            unique=False,
        )
        op.create_index(
            "idx_thermal_lc_context_class",
            "thermal_land_cover_profiles",
            ["context_class"],
            unique=False,
        )
        op.create_index(
            "idx_thermal_lc_coverage_status",
            "thermal_land_cover_profiles",
            ["coverage_status"],
            unique=False,
        )
        op.create_index(
            "idx_thermal_lc_product_version",
            "thermal_land_cover_profiles",
            ["product_version"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "thermal_land_cover_profiles" in existing_tables:
        op.drop_table("thermal_land_cover_profiles")
