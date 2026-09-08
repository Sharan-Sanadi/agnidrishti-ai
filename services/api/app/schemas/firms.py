# AGNIDRISHTI API — NASA FIRMS Schemas
"""
Domain models and DTOs for NASA FIRMS satellite thermal observations.

CRITICAL GIS CONVENTION:
  GeoJSON coordinates use [longitude, latitude] — NOT [latitude, longitude].
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.constants import (
    LAT_MAX,
    LAT_MIN,
    LNG_MAX,
    LNG_MIN,
)


class BoundingBox(BaseModel):
    """Geographic bounding box with strict spatial validation."""

    west: float = Field(..., ge=LNG_MIN, le=LNG_MAX, description="Western longitude")
    south: float = Field(..., ge=LAT_MIN, le=LAT_MAX, description="Southern latitude")
    east: float = Field(..., ge=LNG_MIN, le=LNG_MAX, description="Eastern longitude")
    north: float = Field(..., ge=LAT_MIN, le=LAT_MAX, description="Northern latitude")

    @model_validator(mode="after")
    def validate_bounds(self) -> BoundingBox:
        if self.south >= self.north:
            raise ValueError(f"South latitude ({self.south}) must be strictly less than north latitude ({self.north}).")
        if self.west >= self.east:
            raise ValueError(
                f"West longitude ({self.west}) must be strictly less than east longitude ({self.east}). "
                "Antimeridian crossing is not supported in Phase 1."
            )
        return self

    def to_firms_area(self) -> str:
        """Format bounding box for NASA FIRMS Area API: west,south,east,north."""
        return f"{self.west:.4f},{self.south:.4f},{self.east:.4f},{self.north:.4f}"

    def to_dict(self) -> dict[str, float]:
        return {
            "west": self.west,
            "south": self.south,
            "east": self.east,
            "north": self.north,
        }


class ThermalObservation(BaseModel):
    """
    Canonical Phase 1 observation DTO.
    Preserves raw satellite observation data without premature classification.
    """

    id: str = Field(..., description="Stable deterministic observation identifier")
    latitude: float = Field(..., ge=LAT_MIN, le=LAT_MAX, description="WGS84 latitude")
    longitude: float = Field(..., ge=LNG_MIN, le=LNG_MAX, description="WGS84 longitude")

    acquisition_time_utc: datetime = Field(..., description="Observation UTC timestamp")

    satellite: str = Field(..., description="Satellite platform (e.g. N20, N21, SNPP)")
    instrument: str = Field(..., description="Sensor instrument (e.g. VIIRS, MODIS)")
    source: str = Field(..., description="FIRMS source product (e.g. VIIRS_NOAA20_NRT)")

    confidence: str = Field(..., description="Raw detection confidence (e.g. 'l', 'n', 'h' or 'nominal')")
    frp: float | None = Field(None, ge=0.0, description="Fire Radiative Power in MW")

    bright_ti4: float | None = Field(None, description="Brightness temperature TI4 (Kelvin)")
    bright_ti5: float | None = Field(None, description="Brightness temperature TI5 (Kelvin)")

    scan: float | None = Field(None, ge=0.0, description="Along-scan pixel resolution (km)")
    track: float | None = Field(None, ge=0.0, description="Along-track pixel resolution (km)")

    daynight: str | None = Field(None, description="'D' for Day, 'N' for Night")
    firms_version: str | None = Field(None, description="FIRMS processing collection/version")

    ingestion_time_utc: datetime = Field(..., description="System ingestion timestamp (UTC)")
    geojson: dict[str, Any] = Field(
        default_factory=dict,
        description="GeoJSON Point geometry: { type: 'Point', coordinates: [lng, lat] }",
    )


class FIRMSHotspotsResponse(BaseModel):
    """Standardized response envelope for NASA FIRMS observations."""

    mode: str = Field(default="live", description="Application data mode ('live')")
    provider: str = Field(default="NASA FIRMS", description="Upstream satellite data provider")
    sources: list[str] = Field(..., description="Satellite source feeds included")
    requested_bbox: dict[str, float] = Field(..., description="Geographic bounding box queried")
    day_range: int = Field(..., description="Day range queried (1-5)")
    requested_date: str | None = Field(None, description="Specific acquisition date queried (if any)")
    fetched_at: datetime = Field(..., description="Timestamp of fetch from NASA or cache")
    data_status: str = Field(default="fresh", description="'fresh' or 'stale' (if served from fallback cache)")
    count: int = Field(..., description="Number of valid thermal observations returned")
    rejected_count: int = Field(default=0, description="Number of invalid/malformed records skipped")
    partial: bool = Field(default=False, description="True if one or more requested sources failed but others succeeded")
    successful_sources: list[str] = Field(..., description="Sources successfully fetched and parsed")
    failed_sources: list[str] = Field(default_factory=list, description="Sources that failed upstream")
    observations: list[ThermalObservation] = Field(..., description="List of canonical thermal observations")


class FIRMSAvailabilityItem(BaseModel):
    """Data availability record for a specific sensor."""

    data_id: str
    min_date: str
    max_date: str


class FIRMSAvailabilityResponse(BaseModel):
    """Response envelope for NASA FIRMS data availability preflight."""

    provider: str = "NASA FIRMS"
    items: list[FIRMSAvailabilityItem]
    checked_at: datetime
