# AGNIDRISHTI API — Stored Observation Schemas
"""
Pydantic schemas for PostGIS-stored thermal observations and synchronization requests/responses.
Maintains strict frontend compatibility with Phase 1 while exposing storage provenance.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


def validate_finite(val: float | None) -> float | None:
    """Ensure numeric values are finite (no NaN or +/-Infinity)."""
    if val is not None and (math.isnan(val) or math.isinf(val)):
        return None
    return val


class StoredObservationItem(BaseModel):
    """Canonical thermal observation retrieved directly from PostGIS storage."""

    id: str = Field(..., description="Stable deterministic observation ID (firms_*)")
    latitude: float = Field(..., description="WGS84 latitude")
    longitude: float = Field(..., description="WGS84 longitude")
    acquisition_time_utc: datetime = Field(..., description="Observation UTC timestamp")

    satellite: str = Field(..., description="Satellite platform (N20, N21, SNPP)")
    instrument: str = Field(..., description="Sensor instrument (VIIRS, MODIS)")
    source: str = Field(..., description="Sensor product (e.g. VIIRS_NOAA20_NRT)")
    provider: str = Field(default="NASA FIRMS", description="Upstream provider")

    confidence: str = Field(..., description="Raw detection confidence ('l', 'n', 'h', etc.)")
    confidence_normalized: str | None = Field(None, description="Normalized semantic confidence ('low', 'nominal', 'high')")

    frp: float | None = Field(None, description="Fire Radiative Power in MW")
    bright_ti4: float | None = Field(None, description="Brightness temperature TI4 (Kelvin)")
    bright_ti5: float | None = Field(None, description="Brightness temperature TI5 (Kelvin)")

    scan: float | None = Field(None, description="Along-scan pixel resolution (km)")
    track: float | None = Field(None, description="Along-track pixel resolution (km)")

    daynight: str | None = Field(None, description="'D' for Day, 'N' for Night")
    firms_version: str | None = Field(None, description="FIRMS processing collection/version")

    # PostGIS storage provenance metadata
    first_ingested_at: datetime = Field(..., description="First recorded ingestion timestamp (UTC)")
    last_seen_at: datetime = Field(..., description="Most recent ingestion timestamp (UTC)")
    ingestion_count: int = Field(default=1, description="Number of times this physical observation was ingested")
    stored_in_postgis: bool = Field(default=True, description="Indicates record is backed by PostGIS storage")

    geojson: dict[str, Any] = Field(
        default_factory=dict,
        description="GeoJSON Point geometry: { type: 'Point', coordinates: [lng, lat] }",
    )

    _val_frp = field_validator("frp", mode="before")(validate_finite)
    _val_ti4 = field_validator("bright_ti4", mode="before")(validate_finite)
    _val_ti5 = field_validator("bright_ti5", mode="before")(validate_finite)


class StoredObservationsResponse(BaseModel):
    """Standard response envelope for PostGIS stored observations query."""

    mode: str = Field(default="stored", description="Data provenance mode ('stored')")
    storage: str = Field(default="PostGIS", description="Underlying database engine")
    count: int = Field(..., description="Number of observations returned in this page")
    total: int = Field(..., description="Total matching observations in PostGIS for query")
    limit: int = Field(..., description="Result page limit")
    offset: int = Field(..., description="Result page offset")
    bbox: dict[str, float] | None = Field(None, description="Applied bounding box filter")
    observations: list[StoredObservationItem] = Field(..., description="List of stored thermal observations")


class FIRMSSyncRequest(BaseModel):
    """Request payload for triggering NASA FIRMS to PostGIS synchronization."""

    west: float | None = None
    south: float | None = None
    east: float | None = None
    north: float | None = None
    days: int = Field(1, ge=1, le=5, description="Day range to fetch (1-5)")
    sources: list[str] | None = Field(None, description="Sensor feeds to query")
    date: str | None = Field(None, description="Acquisition date (YYYY-MM-DD)")
    force_refresh: bool = Field(False, description="Bypass in-memory cache")


class FIRMSSyncResponse(BaseModel):
    """Response envelope for NASA FIRMS to PostGIS synchronization result."""

    status: str = Field(..., description="Sync status: 'completed', 'partial', or 'failed'")
    run_id: str = Field(..., description="Unique ingestion run audit identifier")
    provider: str = Field(default="NASA FIRMS")
    sources: list[str] = Field(..., description="Requested sources")
    requested_bbox: dict[str, float] = Field(..., description="Requested bounding box")
    day_range: int = Field(...)
    requested_date: str | None = None
    fetched_count: int = Field(..., description="Total records fetched from upstream")
    valid_count: int = Field(..., description="Valid observations parsed")
    rejected_count: int = Field(..., description="Invalid or malformed records skipped")
    upserted_count: int = Field(..., description="Records upserted into PostGIS")
    successful_sources: list[str] = Field(...)
    failed_sources: list[str] = Field(default_factory=list)
    started_at: datetime = Field(...)
    completed_at: datetime | None = None
    error_summary: str | None = None
