# AGNIDRISHTI API — Thermal Industrial Context Profile Database Model
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IndustrialContextProfileModel(Base):
    """
    Cached industrial infrastructure context profile for a thermal observation.
    Maintains metric distance, spatial containment, context class, and full-envelope coverage state.
    """

    __tablename__ = "thermal_industrial_context_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    observation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("thermal_observations.observation_id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    radius_m: Mapped[float] = mapped_column(Float, nullable=False, default=5000.0)
    context_class: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # STRONG, MODERATE, WEAK, NONE, UNAVAILABLE
    coverage_status: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # ADEQUATE, PARTIAL, MISSING, FAILED

    nearest_industrial_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_feature_osm_uid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nearest_feature_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nearest_feature_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nearest_feature_geometry_quality: Mapped[str | None] = mapped_column(String(32), nullable=True)

    nearest_flare_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_chimney_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_refinery_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_power_plant_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_industrial_area_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)

    inside_industrial_area: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    feature_count_500m: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    feature_count_1km: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    feature_count_2km: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    feature_count_5km: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    has_flare_nearby: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_chimney_nearby: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_refinery_nearby: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_power_plant_nearby: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    evidence_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    algorithm_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    osm_snapshot_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<IndustrialContextProfileModel(observation_id={self.observation_id}, class={self.context_class}, distance={self.nearest_industrial_distance_m})>"
