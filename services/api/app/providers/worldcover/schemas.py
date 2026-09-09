# AGNIDRISHTI API — ESA WorldCover Schemas
"""
Pydantic schemas for internal WorldCover raster sampling and multi-scale distributions.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.providers.worldcover.constants import (
    LandCoverContextClass,
    LandCoverCoverageStatus,
)


class PointLandCoverSample(BaseModel):
    """Exact raster pixel sample at the observation coordinate."""

    code: int = Field(..., description="Raw WorldCover raster class code (e.g. 40)")
    class_name: str = Field(..., description="Canonical class name (e.g. CROPLAND)")
    tile_id: str = Field(..., description="Originating WorldCover 3x3 tile ID")
    is_valid: bool = Field(..., description="True if pixel represents a documented class")


class ScaleLandCoverDistribution(BaseModel):
    """Land cover composition for a circular metric radius."""

    radius_m: float = Field(..., description="Metric radius (250, 500, or 1000 meters)")
    total_pixels: int = Field(..., description="Total pixels evaluated within circular radius")
    valid_pixels: int = Field(..., description="Count of pixels matching official classes")
    invalid_pixels: int = Field(0, description="Count of nodata or out-of-range pixels")
    valid_fraction: float = Field(..., description="Ratio of valid to total pixels (0.0 - 1.0)")
    class_counts: dict[str, int] = Field(default_factory=dict, description="Pixel counts per class")
    class_fractions: dict[str, float] = Field(
        default_factory=dict, description="Valid-pixel land-cover fractions (sum ~ 1.0)"
    )
    dominant_class: str = Field(..., description="Class with highest valid pixel fraction")
    dominant_fraction: float = Field(..., description="Fraction of the dominant class (0.0 - 1.0)")


class ObservationLandCoverAnalysis(BaseModel):
    """Complete multi-scale analytical profile derived from ESA WorldCover raster."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    observation_id: str
    point_sample: PointLandCoverSample
    scale_250m: ScaleLandCoverDistribution
    scale_500m: ScaleLandCoverDistribution
    scale_1000m: ScaleLandCoverDistribution
    context_class: LandCoverContextClass
    coverage_status: LandCoverCoverageStatus
    tiles_used: list[str]
    sampled_at: datetime
    error_detail: str | None = None
