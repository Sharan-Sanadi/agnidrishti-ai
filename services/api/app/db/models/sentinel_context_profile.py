# AGNIDRISHTI API — Sentinel-2 Context Profile Database Model
"""
SQLAlchemy ORM model for storing and caching Phase 6 Sentinel-2 L2A context profiles.
Linked to canonical thermal_observations by observation_id.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ThermalSentinelContextProfileModel(Base):
    """
    Derived Phase 6 Sentinel-2 Satellite Context Intelligence Profile.
    Stores multi-scale metric circular spectral statistics, cloud masking quality,
    point reflectance & indices, and provenance.
    """

    __tablename__ = "thermal_sentinel_context_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    observation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("thermal_observations.observation_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Provider & Collection metadata
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="CDSE")
    collection: Mapped[str] = mapped_column(String(64), nullable=False, default="sentinel-2-l2a")
    scene_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    product_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    satellite_platform: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Timestamps & Temporal Quality (Zero Future Leakage Enforced)
    scene_acquisition_time_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    target_firms_time_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    scene_age_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    scene_age_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    temporal_quality: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Coarse catalogue cloud metadata
    catalogue_cloud_cover: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Local pixel quality within ROI
    local_valid_fraction: Mapped[float | None] = mapped_column(Float, nullable=True)
    local_cloud_fraction: Mapped[float | None] = mapped_column(Float, nullable=True)
    local_cloud_shadow_fraction: Mapped[float | None] = mapped_column(Float, nullable=True)
    local_snow_fraction: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Pipeline & Quality Status
    quality_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    analytical_resolution_m: Mapped[float] = mapped_column(Float, nullable=False, default=20.0)

    # Point-level pixel sample at FIRMS coordinates
    point_is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    point_scl: Mapped[int | None] = mapped_column(Integer, nullable=True)
    point_b04: Mapped[float | None] = mapped_column(Float, nullable=True)
    point_b08: Mapped[float | None] = mapped_column(Float, nullable=True)
    point_b11: Mapped[float | None] = mapped_column(Float, nullable=True)
    point_b12: Mapped[float | None] = mapped_column(Float, nullable=True)
    point_ndvi: Mapped[float | None] = mapped_column(Float, nullable=True)
    point_ndmi: Mapped[float | None] = mapped_column(Float, nullable=True)
    point_nbr: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Multi-scale circular neighborhood statistics (100m, 250m, 500m)
    stats_100m: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    stats_250m: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    stats_500m: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Explicit Phase-7 Feature Fusion Columns (250m primary context)
    sentinel_scene_age_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentinel_valid_fraction_250m: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentinel_b04_median_250m: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentinel_b08_median_250m: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentinel_b11_median_250m: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentinel_b12_median_250m: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentinel_ndvi_median_250m: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentinel_ndmi_median_250m: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentinel_nbr_median_250m: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentinel_b11_p90_250m: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentinel_b12_p90_250m: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Traceability & Provenance (no secret credentials)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    algorithm_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="sentinel2_context_v1"
    )

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
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint("observation_id", "algorithm_version", name="uq_obs_sentinel_alg_version"),
        Index("idx_sentinel_profile_obs_id", "observation_id"),
        Index("idx_sentinel_profile_quality", "quality_status"),
        Index("idx_sentinel_profile_scene_id", "scene_id"),
    )
