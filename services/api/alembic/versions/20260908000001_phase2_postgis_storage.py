"""Phase 2 PostGIS storage and geospatial normalization

Revision ID: 20260908000001
Revises: None
Create Date: 2026-09-08 12:00:00.000000

"""
from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260908000001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enable PostGIS extension safely
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 2. Create thermal_observations table
    op.create_table(
        "thermal_observations",
        sa.Column("observation_id", sa.String(length=64), nullable=False, comment="Deterministic SHA-256 derived observation ID"),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=False,
            ),
            nullable=False,
        ),
        sa.Column("acquisition_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("satellite", sa.String(length=32), nullable=False),
        sa.Column("instrument", sa.String(length=32), nullable=False),
        sa.Column("source_product", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False, server_default="NASA FIRMS"),
        sa.Column("confidence_raw", sa.String(length=32), nullable=False),
        sa.Column("confidence_normalized", sa.String(length=32), nullable=True),
        sa.Column("frp", sa.Float(), nullable=True),
        sa.Column("bright_ti4", sa.Float(), nullable=True),
        sa.Column("bright_ti5", sa.Float(), nullable=True),
        sa.Column("scan", sa.Float(), nullable=True),
        sa.Column("track", sa.Float(), nullable=True),
        sa.Column("daynight", sa.String(length=1), nullable=True),
        sa.Column("firms_version", sa.String(length=32), nullable=True),
        sa.Column("first_ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("ingestion_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("observation_id", name="pk_thermal_observations"),
        sa.CheckConstraint("latitude >= -90.0 AND latitude <= 90.0", name="chk_obs_latitude_range"),
        sa.CheckConstraint("longitude >= -180.0 AND longitude <= 180.0", name="chk_obs_longitude_range"),
    )

    # 3. Create spatial and temporal indexes
    op.create_index(
        "idx_thermal_observations_geom",
        "thermal_observations",
        ["geom"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_index(
        "idx_thermal_observations_acq_utc",
        "thermal_observations",
        ["acquisition_time_utc"],
        unique=False,
    )
    op.create_index(
        "idx_thermal_obs_source_acq",
        "thermal_observations",
        ["source_product", "acquisition_time_utc"],
        unique=False,
    )
    op.create_index(
        "idx_thermal_observations_obs_id",
        "thermal_observations",
        ["observation_id"],
        unique=False,
    )

    # 4. Create ingestion_runs table
    op.create_table(
        "ingestion_runs",
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False, server_default="NASA FIRMS"),
        sa.Column("requested_sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("requested_bbox", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("requested_day_range", sa.Integer(), nullable=False),
        sa.Column("requested_date", sa.String(length=32), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="running"),
        sa.Column("fetched_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("upserted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("successful_sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("failed_sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("run_id", name="pk_ingestion_runs"),
    )
    op.create_index("idx_ingestion_runs_run_id", "ingestion_runs", ["run_id"], unique=False)
    op.create_index("idx_ingestion_runs_started_at", "ingestion_runs", ["started_at"], unique=False)


def downgrade() -> None:
    op.drop_table("ingestion_runs")
    op.drop_table("thermal_observations")
