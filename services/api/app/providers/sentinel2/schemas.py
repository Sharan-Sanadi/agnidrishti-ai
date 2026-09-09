# AGNIDRISHTI API — Phase 6 Sentinel-2 Internal Schemas
"""
Internal data structures and Pydantic schemas for Sentinel-2 provider operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.providers.sentinel2.constants import (
    SentinelQualityStatus,
)


class SentinelCandidate(BaseModel):
    """Discovered Sentinel-2 Level-2A scene candidate from STAC catalog."""
    model_config = ConfigDict(extra="ignore")

    scene_id: str
    product_id: str | None = None
    satellite_platform: str | None = None
    acquisition_time_utc: datetime
    cloud_cover_percentage: float = 0.0
    bbox: list[float] | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class RadiusSpectralStats(BaseModel):
    """Multi-band reflectance and spectral index statistics for a circular metric radius."""
    model_config = ConfigDict(extra="ignore")

    radius_m: float
    total_pixel_count: int
    valid_pixel_count: int
    valid_fraction: float

    # Reflectance medians (Float32 reflectance 0.0 - 1.0)
    b04_median: float | None = None
    b08_median: float | None = None
    b11_median: float | None = None
    b12_median: float | None = None

    # Spectral index medians
    ndvi_median: float | None = None
    ndmi_median: float | None = None
    nbr_median: float | None = None

    # Percentiles for distribution robustness
    ndvi_p10: float | None = None
    ndvi_p90: float | None = None
    ndmi_p10: float | None = None
    ndmi_p90: float | None = None
    nbr_p10: float | None = None
    nbr_p90: float | None = None
    b11_p90: float | None = None
    b12_p90: float | None = None


class PointSpectralSample(BaseModel):
    """Point-level pixel reflectance and spectral indices directly at observation coordinates."""
    model_config = ConfigDict(extra="ignore")

    is_valid: bool
    scl_code: int | None = None
    scl_name: str | None = None
    b04: float | None = None
    b08: float | None = None
    b11: float | None = None
    b12: float | None = None
    ndvi: float | None = None
    ndmi: float | None = None
    nbr: float | None = None


class SentinelLocalQuality(BaseModel):
    """Local pixel validity assessment within the observation ROI."""
    model_config = ConfigDict(extra="ignore")

    total_pixels: int
    valid_pixels: int
    cloud_pixels: int
    cloud_shadow_pixels: int
    snow_pixels: int
    no_data_pixels: int

    valid_fraction: float
    cloud_fraction: float
    cloud_shadow_fraction: float
    snow_fraction: float
    quality_status: SentinelQualityStatus
