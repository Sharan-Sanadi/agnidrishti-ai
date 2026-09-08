# AGNIDRISHTI API — Analysis Aggregate Schema
"""
HotspotAnalysis: the single most important contract in Agnidrishti.
This aggregate drives the hotspot detail panel in the frontend.
The backend exposes this so the web app does NOT manually combine
five unrelated response shapes.

Pipeline: DETECT → UNDERSTAND → CLASSIFY → EXPLAIN → MONITOR
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.classification import Classification
from app.schemas.common import DataQuality, DataSourceInfo
from app.schemas.hotspot import HotspotRead

# ==============================
# CONTEXT SUB-SCHEMAS
# ==============================

class ThermalContext(BaseModel):
    """Thermal-specific analysis context."""

    frp_mw: float | None = None
    brightness_ti4: float | None = None
    brightness_ti5: float | None = None
    brightness_delta: float | None = Field(None, description="TI4 - TI5 delta")
    day_night: str | None = None
    detection_confidence: str | None = None


class TemporalContext(BaseModel):
    """Repeated hotspot / persistence analysis."""

    detection_count: int = Field(default=0, description="Total detections at this location")
    persistence_score: float | None = Field(
        None, ge=0.0, le=1.0, description="0=transient, 1=persistent"
    )
    first_detected: datetime | None = None
    last_detected: datetime | None = None
    historical_frp_mean: float | None = None
    historical_frp_std: float | None = None
    frp_deviation: float | None = Field(None, description="Current FRP deviation from baseline")


class IndustrialContext(BaseModel):
    """Industrial infrastructure proximity context."""

    nearest_industrial_facility: dict[str, Any] | None = None
    distance_to_nearest_m: float | None = Field(None, description="Distance in meters")
    industrial_facilities_500m: int = 0
    industrial_facilities_1km: int = 0
    industrial_facilities_5km: int = 0
    industrial_zone: bool = False
    infrastructure_types: list[str] = Field(default_factory=list)


class LandCoverContext(BaseModel):
    """Land cover composition around the hotspot."""

    dominant_class: str | None = None
    built_area_ratio: float | None = Field(None, ge=0.0, le=1.0)
    vegetation_ratio: float | None = Field(None, ge=0.0, le=1.0)
    crop_ratio: float | None = Field(None, ge=0.0, le=1.0)
    water_ratio: float | None = Field(None, ge=0.0, le=1.0)
    bare_ratio: float | None = Field(None, ge=0.0, le=1.0)
    source: str | None = None


class SatelliteContext(BaseModel):
    """Satellite observation metadata."""

    has_recent_imagery: bool = False
    latest_image_date: datetime | None = None
    cloud_cover_pct: float | None = None
    satellite_platform: str | None = None
    scene_id: str | None = None


# ==============================
# ANALYSIS AGGREGATE
# ==============================

class HotspotAnalysis(BaseModel):
    """
    THE core aggregate object for Agnidrishti.
    Combines all contextual layers into a single response.
    """

    hotspot: HotspotRead
    thermal_context: ThermalContext
    temporal_context: TemporalContext
    industrial_context: IndustrialContext
    landcover_context: LandCoverContext
    satellite_context: SatelliteContext
    classification: Classification
    anomaly_score: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall anomaly score 0.0–1.0",
    )
    warnings: list[str] = Field(default_factory=list)
    data_sources: list[DataSourceInfo] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)
    analysis_mode: str = Field(
        default="fixture",
        description="fixture / live / degraded — NEVER pretend fixtures are real AI predictions",
    )
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class AnalyzeRequest(BaseModel):
    """Request body for the analyze endpoint."""

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
