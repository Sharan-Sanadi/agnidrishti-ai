# AGNIDRISHTI API — Phase 6 Sentinel-2 API Schemas
"""
Pydantic schemas for Sentinel-2 API requests, responses, batch lookups, and sync operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.providers.sentinel2.constants import (
    SentinelProviderStatus,
    SentinelQualityStatus,
    SentinelTemporalQuality,
)


class RadiusStatsSchema(BaseModel):
    """Reflectance and spectral index statistics for a specific radius."""
    model_config = ConfigDict(extra="ignore")

    radius_m: float
    total_pixel_count: int = 0
    valid_pixel_count: int = 0
    valid_fraction: float = 0.0

    b04_median: float | None = None
    b08_median: float | None = None
    b11_median: float | None = None
    b12_median: float | None = None

    ndvi_median: float | None = None
    ndmi_median: float | None = None
    nbr_median: float | None = None

    ndvi_p10: float | None = None
    ndvi_p90: float | None = None
    ndmi_p10: float | None = None
    ndmi_p90: float | None = None
    nbr_p10: float | None = None
    nbr_p90: float | None = None
    b11_p90: float | None = None
    b12_p90: float | None = None


class SentinelContextProfileResponse(BaseModel):
    """Full Sentinel-2 optical/SWIR context intelligence profile for a thermal observation."""
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    observation_id: str
    provider: str = "CDSE"
    collection: str = "sentinel-2-l2a"
    scene_id: str | None = None
    product_id: str | None = None
    satellite_platform: str | None = None

    scene_acquisition_time_utc: datetime | None = None
    target_firms_time_utc: datetime
    scene_age_hours: float | None = None
    scene_age_days: float | None = None
    temporal_quality: SentinelTemporalQuality | str | None = None

    catalogue_cloud_cover: float | None = None
    local_valid_fraction: float | None = None
    local_cloud_fraction: float | None = None
    local_cloud_shadow_fraction: float | None = None
    local_snow_fraction: float | None = None

    quality_status: SentinelQualityStatus | str
    provider_status: SentinelProviderStatus | str
    analytical_resolution_m: float = 20.0

    point_is_valid: bool = False
    point_scl: int | None = None
    point_b04: float | None = None
    point_b08: float | None = None
    point_b11: float | None = None
    point_b12: float | None = None
    point_ndvi: float | None = None
    point_ndmi: float | None = None
    point_nbr: float | None = None

    stats_100m: dict[str, Any] = Field(default_factory=dict)
    stats_250m: dict[str, Any] = Field(default_factory=dict)
    stats_500m: dict[str, Any] = Field(default_factory=dict)

    # Explicit Phase-7 Feature Fusion Columns
    sentinel_scene_age_days: float | None = None
    sentinel_valid_fraction_250m: float | None = None
    sentinel_b04_median_250m: float | None = None
    sentinel_b08_median_250m: float | None = None
    sentinel_b11_median_250m: float | None = None
    sentinel_b12_median_250m: float | None = None
    sentinel_ndvi_median_250m: float | None = None
    sentinel_ndmi_median_250m: float | None = None
    sentinel_nbr_median_250m: float | None = None
    sentinel_b11_p90_250m: float | None = None
    sentinel_b12_p90_250m: float | None = None

    provenance: dict[str, Any] = Field(default_factory=dict)
    algorithm_version: str = "sentinel2_context_v1"
    processed_at: datetime


class BatchSentinelProfileRequest(BaseModel):
    """Request payload for fetching cached Sentinel-2 profiles in batch."""
    observation_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="List of canonical observation IDs (max 500 per request)",
    )


class BatchSentinelProfileResponse(BaseModel):
    """Response envelope for batch cached Sentinel-2 profiles."""
    total_requested: int
    count: int
    profiles: dict[str, SentinelContextProfileResponse]


class SentinelSyncRequest(BaseModel):
    """Request payload for controlled remote sync/precomputation."""
    observation_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of observation IDs to evaluate (max 50 per sync request)",
    )
    force_refresh: bool = Field(
        default=False,
        description="Whether to overwrite existing cached profiles",
    )


class SentinelSyncResponse(BaseModel):
    """Summary of controlled remote Sentinel synchronization execution."""
    status: str
    total_requested: int
    cached_profiles_reused: int
    profiles_computed: int
    profiles_cloud_limited: int
    profiles_no_scene: int
    profiles_failed: int
    duration_seconds: float
    profiles: dict[str, SentinelContextProfileResponse]
