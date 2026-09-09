# AGNIDRISHTI API — ESA WorldCover 2021 v200 Provider
"""
ESA WorldCover 10 m 2021 v200 analytical raster intelligence provider.
"""

from app.providers.worldcover.client import WorldCoverClient, get_worldcover_client
from app.providers.worldcover.constants import (
    ALGORITHM_VERSION,
    NATIVE_CRS,
    NOMINAL_RESOLUTION_M,
    PRODUCT_NAME,
    PRODUCT_VERSION,
    PROVIDER_NAME,
    SOURCE_YEAR,
    WORLDCOVER_CLASSES,
    WORLDCOVER_LABELS,
    LandCoverContextClass,
    LandCoverCoverageStatus,
    get_class_label,
    get_class_name,
)
from app.providers.worldcover.raster import WorldCoverRasterProcessor
from app.providers.worldcover.schemas import (
    ObservationLandCoverAnalysis,
    PointLandCoverSample,
    ScaleLandCoverDistribution,
)
from app.providers.worldcover.tile_resolver import (
    build_worldcover_url,
    format_tile_id,
    format_worldcover_filename,
    parse_tile_id,
    resolve_neighborhood_tiles,
    resolve_point_tile,
)

__all__ = [
    "ALGORITHM_VERSION",
    "NATIVE_CRS",
    "NOMINAL_RESOLUTION_M",
    "PRODUCT_NAME",
    "PRODUCT_VERSION",
    "PROVIDER_NAME",
    "SOURCE_YEAR",
    "WORLDCOVER_CLASSES",
    "WORLDCOVER_LABELS",
    "LandCoverContextClass",
    "LandCoverCoverageStatus",
    "ObservationLandCoverAnalysis",
    "PointLandCoverSample",
    "ScaleLandCoverDistribution",
    "WorldCoverClient",
    "WorldCoverRasterProcessor",
    "build_worldcover_url",
    "format_tile_id",
    "format_worldcover_filename",
    "get_class_label",
    "get_class_name",
    "get_worldcover_client",
    "parse_tile_id",
    "resolve_neighborhood_tiles",
    "resolve_point_tile",
]
