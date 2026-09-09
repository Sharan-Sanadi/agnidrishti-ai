"""Phase 4 Industrial Context Intelligence and OSM Infrastructure Feature Storage

Revision ID: 20260909000001
Revises: 20260908000002
Create Date: 2026-09-09 00:00:00.000000

"""
from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260909000001"
down_revision: str | None = "20260908000002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Create osm_industrial_features table if not present
    if "osm_industrial_features" not in existing_tables:
        op.create_table(
            "osm_industrial_features",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("osm_uid", sa.String(length=64), nullable=False),
            sa.Column("osm_type", sa.String(length=16), nullable=False),
            sa.Column("osm_id", sa.BigInteger(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=True),
            sa.Column("operator", sa.String(length=255), nullable=True),
            sa.Column("feature_category", sa.String(length=64), nullable=False),
            sa.Column("thermal_relevance", sa.String(length=32), nullable=False),
            sa.Column("industrial_tag", sa.String(length=64), nullable=True),
            sa.Column("man_made_tag", sa.String(length=64), nullable=True),
            sa.Column("power_tag", sa.String(length=64), nullable=True),
            sa.Column("plant_source", sa.String(length=64), nullable=True),
            sa.Column("landuse", sa.String(length=64), nullable=True),
            sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
            sa.Column(
                "geom",
                geoalchemy2.types.Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False),
                nullable=False,
            ),
            sa.Column("geometry_quality", sa.String(length=32), nullable=False),
            sa.Column("osm_version", sa.Integer(), nullable=True),
            sa.Column("osm_element_timestamp", sa.DateTime(timezone=True), nullable=True),
            sa.Column("source_provider", sa.String(length=32), nullable=False, server_default="OVERPASS_API"),
            sa.Column("first_ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("last_refreshed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("osm_uid"),
        )
        op.create_index("idx_osm_features_osm_uid", "osm_industrial_features", ["osm_uid"])
        op.create_index("idx_osm_features_category", "osm_industrial_features", ["feature_category"])
        op.execute(
            "CREATE INDEX idx_osm_features_geom ON osm_industrial_features USING GiST (geom)"
        )

    # 2. Create osm_context_coverage table if not present
    if "osm_context_coverage" not in existing_tables:
        op.create_table(
            "osm_context_coverage",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("coverage_id", sa.String(length=64), nullable=False),
            sa.Column("query_hash", sa.String(length=64), nullable=False),
            sa.Column(
                "bbox_geom",
                geoalchemy2.types.Geometry(geometry_type="POLYGON", srid=4326, spatial_index=False),
                nullable=False,
            ),
            sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("osm_base_timestamp", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("feature_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("coverage_id"),
        )
        op.create_index("idx_osm_coverage_coverage_id", "osm_context_coverage", ["coverage_id"])
        op.create_index("idx_osm_coverage_query_hash", "osm_context_coverage", ["query_hash"])
        op.execute(
            "CREATE INDEX idx_osm_coverage_geom ON osm_context_coverage USING GiST (bbox_geom)"
        )

    # 3. Create thermal_industrial_context_profiles table if not present
    if "thermal_industrial_context_profiles" not in existing_tables:
        op.create_table(
            "thermal_industrial_context_profiles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("observation_id", sa.String(length=64), nullable=False),
            sa.Column("radius_m", sa.Float(), nullable=False, server_default="5000.0"),
            sa.Column("context_class", sa.String(length=32), nullable=False),
            sa.Column("coverage_status", sa.String(length=32), nullable=False),
            sa.Column("nearest_industrial_distance_m", sa.Float(), nullable=True),
            sa.Column("nearest_feature_osm_uid", sa.String(length=64), nullable=True),
            sa.Column("nearest_feature_name", sa.String(length=255), nullable=True),
            sa.Column("nearest_feature_category", sa.String(length=64), nullable=True),
            sa.Column("nearest_feature_geometry_quality", sa.String(length=32), nullable=True),
            sa.Column("nearest_flare_distance_m", sa.Float(), nullable=True),
            sa.Column("nearest_chimney_distance_m", sa.Float(), nullable=True),
            sa.Column("nearest_refinery_distance_m", sa.Float(), nullable=True),
            sa.Column("nearest_power_plant_distance_m", sa.Float(), nullable=True),
            sa.Column("nearest_industrial_area_distance_m", sa.Float(), nullable=True),
            sa.Column("inside_industrial_area", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("feature_count_500m", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("feature_count_1km", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("feature_count_2km", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("feature_count_5km", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("has_flare_nearby", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("has_chimney_nearby", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("has_refinery_nearby", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("has_power_plant_nearby", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("evidence_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
            sa.Column("algorithm_version", sa.String(length=32), nullable=False, server_default="1.0.0"),
            sa.Column("osm_snapshot_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["observation_id"], ["thermal_observations.observation_id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("observation_id"),
        )
        op.create_index("idx_industrial_profiles_obs_id", "thermal_industrial_context_profiles", ["observation_id"])


def downgrade() -> None:
    op.drop_table("thermal_industrial_context_profiles")
    op.drop_table("osm_context_coverage")
    op.drop_table("osm_industrial_features")
