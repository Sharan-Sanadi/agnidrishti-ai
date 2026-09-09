# AGNIDRISHTI API — Sentinel-2 L2A Provider Package
"""
Sentinel-2 Level-2A optical/SWIR context provider using the Copernicus Data Space Ecosystem.
"""

from app.providers.sentinel2.auth import CDSEAuthError, CDSETokenProvider, get_cdse_token_provider
from app.providers.sentinel2.catalog import CDSECatalogClient, CDSECatalogError
from app.providers.sentinel2.constants import (
    ANALYTICAL_RADII_METERS,
    ANALYTICAL_RESOLUTION_M,
    INVALID_SCL_CODES,
    PRIMARY_RADIUS_METERS,
    SENTINEL_COLLECTION_NAME,
    SentinelProviderStatus,
    SentinelQualityStatus,
    SentinelTemporalQuality,
)
from app.providers.sentinel2.process import CDSEProcessClient, CDSEProcessError

__all__ = [
    "CDSEAuthError",
    "CDSECatalogClient",
    "CDSECatalogError",
    "CDSEProcessClient",
    "CDSEProcessError",
    "CDSETokenProvider",
    "get_cdse_token_provider",
    "SentinelProviderStatus",
    "SentinelQualityStatus",
    "SentinelTemporalQuality",
    "INVALID_SCL_CODES",
    "ANALYTICAL_RADII_METERS",
    "PRIMARY_RADIUS_METERS",
    "ANALYTICAL_RESOLUTION_M",
    "SENTINEL_COLLECTION_NAME",
]
