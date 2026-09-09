# AGNIDRISHTI API — Land Cover Profile ORM Model
"""
SQLAlchemy ORM model for storing/caching Phase 5 ESA WorldCover 2021 v200 profiles.
Linked to canonical thermal_observations by observation_id.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
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


class ThermalLandCoverProfileModel(Base):
    """
    Derived Phase 5 Land-Cover Intelligence Profile.
    Stores multi-scale circular metric composition and Context V1 classification.
    """

    __tablename__ = "thermal_land_cover_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    observation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("thermal_observations.observation_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Provenance metadata
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="ESA_WORLDCOVER")
    product_name: Mapped[str] = mapped_column(
        String(64), nullable=False, default="ESA WorldCover 10 m 2021"
    )
    product_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v200")
    source_year: Mapped[int] = mapped_column(Integer, nullable=False, default=2021)
    algorithm_version: Mapped[str] = mapped_column(
        String(64), nullable=False, default="land_cover_v1"
    )

    # Point-level pixel sample
    point_class_code: Mapped[int] = mapped_column(Integer, nullable=False)
    point_class_name: Mapped[str] = mapped_column(String(64), nullable=False)
    point_tile_id: Mapped[str] = mapped_column(String(32), nullable=False)

    # Primary Explainable Context & Coverage Status
    context_class: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    coverage_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    # Multi-scale Dominant Classes and Fractions
    dominant_class_250m: Mapped[str] = mapped_column(String(64), nullable=False)
    dominant_fraction_250m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    dominant_class_500m: Mapped[str] = mapped_column(String(64), nullable=False)
    dominant_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    dominant_class_1000m: Mapped[str] = mapped_column(String(64), nullable=False)
    dominant_fraction_1000m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Detailed distributions as JSONB
    class_distribution_250m: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    class_distribution_500m: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    class_distribution_1000m: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Pixel count metrics
    valid_pixel_count_250m: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_pixel_count_500m: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_pixel_count_1000m: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    valid_fraction_250m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    valid_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    valid_fraction_1000m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Explicit 500m fraction columns for Phase-7 Feature Fusion readiness
    tree_cover_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    shrubland_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    grassland_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cropland_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    built_up_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    bare_sparse_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    snow_ice_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    water_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    wetland_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mangrove_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    moss_lichen_fraction_500m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Intersecting tiles used
    tiles_used: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    sampled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint(
            "observation_id",
            "provider",
            "product_version",
            "algorithm_version",
            name="uq_thermal_lc_profile_identity",
        ),
        Index("idx_thermal_lc_observation_id", "observation_id"),
        Index("idx_thermal_lc_context_class", "context_class"),
        Index("idx_thermal_lc_coverage_status", "coverage_status"),
        Index("idx_thermal_lc_product_version", "product_version"),
    )
