# AGNIDRISHTI API — Industrial Context & OSM Schemas
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# Context Class: mapped industrial evidence strength
ContextClass = Literal["STRONG", "MODERATE", "WEAK", "NONE", "UNAVAILABLE"]
CoverageStatus = Literal["ADEQUATE", "PARTIAL", "MISSING", "FAILED"]
GeometryQuality = Literal["EXACT_POINT", "EXACT_LINE", "EXACT_POLYGON", "CENTER_FALLBACK"]

IndustrialCategory = Literal[
    "FLARE",
    "CHIMNEY",
    "REFINERY",
    "INDUSTRIAL_WORKS",
    "THERMAL_POWER_PLANT",
    "OTHER_POWER_PLANT",
    "INDUSTRIAL_AREA",
    "STORAGE_TANK",
    "OTHER_INDUSTRIAL",
]


class NearestFeatureDTO(BaseModel):
    osm_uid: str = Field(..., description="Unique OSM Identifier e.g. node/123, way/456")
    name: str | None = Field(None, description="Feature name if available")
    operator: str | None = Field(None, description="Operator name if available")
    feature_category: IndustrialCategory
    geometry_quality: GeometryQuality
    distance_m: float = Field(..., ge=0, description="Metric distance in meters")
    inside_industrial_area: bool = Field(False, description="True if point is contained inside polygon")


class IndustrialContextProfileDTO(BaseModel):
    observation_id: str
    radius_m: float = Field(5000.0, description="Context radius used (default 5000m)")
    context_class: ContextClass
    coverage_status: CoverageStatus

    nearest_industrial_distance_m: float | None = Field(None, description="Metric distance to nearest feature")
    nearest_feature: NearestFeatureDTO | None = None

    nearest_flare_distance_m: float | None = None
    nearest_chimney_distance_m: float | None = None
    nearest_refinery_distance_m: float | None = None
    nearest_power_plant_distance_m: float | None = None
    nearest_industrial_area_distance_m: float | None = None

    inside_industrial_area: bool = False

    industrial_feature_count_500m: int = 0
    industrial_feature_count_1km: int = 0
    industrial_feature_count_2km: int = 0
    industrial_feature_count_5km: int = 0

    has_flare_nearby: bool = False
    has_chimney_nearby: bool = False
    has_refinery_nearby: bool = False
    has_power_plant_nearby: bool = False

    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    algorithm_version: str = "1.0.0"
    osm_snapshot_at: datetime | None = None
    calculated_at: datetime


class BatchIndustrialContextRequest(BaseModel):
    observation_ids: list[str] = Field(..., max_length=500, description="List of thermal observation IDs (max 500)")


class BatchIndustrialContextResponse(BaseModel):
    total_requested: int
    profiles: dict[str, IndustrialContextProfileDTO]


class OSMSyncRequest(BaseModel):
    west: float = Field(..., ge=-180.0, le=180.0)
    south: float = Field(..., ge=-90.0, le=90.0)
    east: float = Field(..., ge=-180.0, le=180.0)
    north: float = Field(..., ge=-90.0, le=90.0)
    force_refresh: bool = False


class OSMSyncResponse(BaseModel):
    coverage_id: str
    status: CoverageStatus
    feature_count: int
    features_ingested: int
    completed_at: datetime | None = None
    expires_at: datetime


class OSMFeatureGeoJSON(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: dict[str, Any]
    properties: dict[str, Any]


class OSMFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[OSMFeatureGeoJSON]
    total_count: int
