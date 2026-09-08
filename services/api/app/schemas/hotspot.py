# AGNIDRISHTI API — Hotspot Schema
"""
Core domain contract for thermal detections.

CRITICAL GIS CONVENTION:
  GeoJSON coordinates use [longitude, latitude] — NOT [latitude, longitude].
  This is documented in app/core/constants.py and must be respected everywhere.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.constants import LAT_MAX, LAT_MIN, LNG_MAX, LNG_MIN


class HotspotBase(BaseModel):
    """Core thermal detection fields."""

    latitude: float = Field(..., ge=LAT_MIN, le=LAT_MAX, description="WGS84 latitude")
    longitude: float = Field(..., ge=LNG_MIN, le=LNG_MAX, description="WGS84 longitude")
    acquired_at: datetime = Field(..., description="Detection timestamp (UTC)")
    source: str = Field(default="NASA_FIRMS", description="Data source identifier")
    satellite: str | None = Field(None, description="Satellite platform, e.g. MODIS, VIIRS")
    frp_mw: float | None = Field(None, ge=0.0, description="Fire Radiative Power in MW")
    brightness_ti4: float | None = Field(None, description="Brightness temperature TI4 (K)")
    brightness_ti5: float | None = Field(None, description="Brightness temperature TI5 (K)")
    confidence: str | None = Field(
        None,
        description="Detection confidence from source (low/nominal/high or 0-100)",
    )
    day_night: str | None = Field(None, description="D=day, N=night")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional source fields")


class HotspotCreate(HotspotBase):
    """Schema for creating a new hotspot record."""

    pass


class HotspotRead(HotspotBase):
    """Schema returned from the API — includes id and GeoJSON geometry."""

    id: str = Field(..., description="Unique hotspot identifier (UUID)")
    geojson: dict[str, Any] | None = Field(
        None,
        description="GeoJSON Point geometry: { type: 'Point', coordinates: [lng, lat] }",
    )

    @field_validator("geojson", mode="before")
    @classmethod
    def build_geojson(cls, v: Any, info: Any) -> dict[str, Any] | None:
        """Auto-build GeoJSON if not provided."""
        if v is not None:
            return v
        data = info.data
        if "longitude" in data and "latitude" in data:
            return {
                "type": "Point",
                "coordinates": [data["longitude"], data["latitude"]],  # [lng, lat]
            }
        return None


class HotspotListResponse(BaseModel):
    """Response for listing hotspots."""

    hotspots: list[HotspotRead]
    total: int
    analysis_mode: str = "fixture"
