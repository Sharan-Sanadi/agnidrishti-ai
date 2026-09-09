# AGNIDRISHTI API — Land Cover Schemas
"""
Pydantic schemas and DTOs for Phase 5 Land-Cover Intelligence API endpoints.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LandCoverProfileResponse(BaseModel):
    """Client-facing DTO for Phase 5 Land-Cover Intelligence profile."""

    observation_id: str = Field(..., description="Canonical FIRMS observation identifier")
    provider: str = Field("ESA_WORLDCOVER", description="Land cover dataset provider")
    product_name: str = Field("ESA WorldCover 10 m 2021", description="Authoritative dataset name")
    product_version: str = Field("v200", description="Product version")
    source_year: int = Field(2021, description="Dataset baseline year")
    algorithm_version: str = Field("land_cover_v1", description="Algorithm version")

    # Point-level pixel sample
    point_class_code: int = Field(..., description="Raster class code at coordinate (e.g. 40)")
    point_class_name: str = Field(..., description="Canonical class name (e.g. CROPLAND)")
    point_tile_id: str = Field(..., description="Originating WorldCover 3x3 tile ID")

    # Context & Coverage
    context_class: str = Field(..., description="Deterministic Context V1 class")
    coverage_status: str = Field(..., description="COMPLETE, PARTIAL, or UNAVAILABLE")

    # Multi-scale Dominant Classes
    dominant_class_250m: str
    dominant_fraction_250m: float
    dominant_class_500m: str
    dominant_fraction_500m: float
    dominant_class_1000m: str
    dominant_fraction_1000m: float

    # Detailed distributions (valid-pixel fractions per class)
    class_distribution_250m: dict[str, float]
    class_distribution_500m: dict[str, float]
    class_distribution_1000m: dict[str, float]

    # Pixel count & validity metrics
    valid_pixel_count_250m: int
    valid_pixel_count_500m: int
    valid_pixel_count_1000m: int
    valid_fraction_250m: float
    valid_fraction_500m: float
    valid_fraction_1000m: float

    # Direct 500m fractions for Phase-7 feature fusion
    cropland_fraction_500m: float = 0.0
    tree_cover_fraction_500m: float = 0.0
    built_up_fraction_500m: float = 0.0
    grassland_fraction_500m: float = 0.0
    water_fraction_500m: float = 0.0
    shrubland_fraction_500m: float = 0.0
    wetland_fraction_500m: float = 0.0
    bare_sparse_fraction_500m: float = 0.0
    mangrove_fraction_500m: float = 0.0
    moss_lichen_fraction_500m: float = 0.0
    snow_ice_fraction_500m: float = 0.0

    tiles_used: list[str]
    sampled_at: datetime


class BatchLandCoverRequest(BaseModel):
    """Request payload for batch land-cover evaluation. Max 500 IDs enforced."""

    observation_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="List of canonical observation IDs (maximum 500)",
    )


class BatchLandCoverResponse(BaseModel):
    """Batch land-cover profiles keyed by canonical observation ID."""

    total_requested: int
    count: int
    profiles: dict[str, LandCoverProfileResponse]


class LandCoverSyncRequest(BaseModel):
    """Controlled sync/precomputation request for land cover."""

    observation_ids: list[str] | None = Field(
        None, description="Optional explicit observation IDs to compute. If None, uses top stored observations."
    )
    limit: int = Field(1500, ge=1, le=2000, description="Max observations to process if observation_ids is None")
    force_recompute: bool = Field(False, description="Recompute even if profile is already cached in database")


class LandCoverSyncResponse(BaseModel):
    """Execution summary report for land-cover sync operation."""

    status: str
    total_requested: int
    cached_profiles_reused: int
    profiles_computed: int
    profiles_unavailable: int
    unique_tiles_required: list[str]
    tile_cache_hits: int
    remote_tile_downloads: int
    duration_seconds: float
