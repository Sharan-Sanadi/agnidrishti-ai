# AGNIDRISHTI API — Thermal Observation ORM Model
"""
SQLAlchemy ORM model for normalized NASA FIRMS thermal observations in PostGIS.
Enforces EPSG:4326, POINT(lng lat) coordinate convention, and deterministic firms_* IDs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ThermalObservationModel(Base):
    """
    Canonical PostGIS storage model for satellite thermal detections.
    Authoritative spatial representation is geom (geometry(Point, 4326)).
    """

    __tablename__ = "thermal_observations"

    # Deterministic observation identifier from Phase 1 parser (e.g. firms_3eb7c881d569bc525e95)
    observation_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        index=True,
        comment="Deterministic SHA-256 derived observation ID",
    )

    # Geographic coordinates (kept for high-throughput serialization, synchronized with geom)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Authoritative PostGIS Geometry (Point, SRID 4326) - POINT(longitude latitude)
    geom = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    # Observation acquisition timestamp in UTC
    acquisition_time_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Satellite and instrument provenance
    satellite: Mapped[str] = mapped_column(String(32), nullable=False)
    instrument: Mapped[str] = mapped_column(String(32), nullable=False)
    source_product: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="NASA FIRMS")

    # Confidence: raw upstream value and normalized semantic string
    confidence_raw: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_normalized: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Sensor measurements (nullable if unavailable from satellite product)
    frp: Mapped[float | None] = mapped_column(Float, nullable=True)
    bright_ti4: Mapped[float | None] = mapped_column(Float, nullable=True)
    bright_ti5: Mapped[float | None] = mapped_column(Float, nullable=True)
    scan: Mapped[float | None] = mapped_column(Float, nullable=True)
    track: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Orbit and processing metadata
    daynight: Mapped[str | None] = mapped_column(String(1), nullable=True)
    firms_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Ingestion audit and idempotency tracking
    first_ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    ingestion_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Raw payload for traceability (strictly sanitized: NO API keys or URLs)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Record timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        Index(
            "idx_thermal_obs_source_acq",
            "source_product",
            "acquisition_time_utc",
        ),
        CheckConstraint(
            "latitude >= -90.0 AND latitude <= 90.0",
            name="chk_obs_latitude_range",
        ),
        CheckConstraint(
            "longitude >= -180.0 AND longitude <= 180.0",
            name="chk_obs_longitude_range",
        ),
    )
