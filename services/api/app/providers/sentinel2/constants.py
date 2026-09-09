# AGNIDRISHTI API — Phase 6 Sentinel-2 Constants and Classifications
"""
Authoritative constants, enumerations, quality thresholds, and SCL masking definitions
for Phase 6 Sentinel-2 Level-2A Optical/SWIR Satellite Context Intelligence.
"""

from __future__ import annotations

from enum import StrEnum


class SentinelProviderStatus(StrEnum):
    """Execution status of Sentinel-2 retrieval pipeline."""
    AVAILABLE = "AVAILABLE"
    CLOUD_LIMITED = "CLOUD_LIMITED"
    NO_SCENE = "NO_SCENE"
    NOT_EVALUATED = "NOT_EVALUATED"
    RATE_LIMITED = "RATE_LIMITED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    ERROR = "ERROR"


class SentinelQualityStatus(StrEnum):
    """Local pixel validity quality category based on SCL and dataMask within ROI."""
    EXCELLENT = "EXCELLENT"      # valid_fraction >= 0.80
    GOOD = "GOOD"                # valid_fraction >= 0.60
    LIMITED = "LIMITED"          # valid_fraction >= 0.40
    CLOUD_LIMITED = "CLOUD_LIMITED"  # valid_fraction < 0.40
    UNAVAILABLE = "UNAVAILABLE"  # 0 valid pixels


class SentinelTemporalQuality(StrEnum):
    """Scene age relative to NASA FIRMS thermal observation timestamp."""
    FRESH = "FRESH"              # <= 5 days prior
    RECENT = "RECENT"            # > 5 and <= 15 days prior
    OLDER_CONTEXT = "OLDER_CONTEXT"  # > 15 and <= 30 days prior



# ─── Local Quality Thresholds ───
QUALITY_THRESHOLD_EXCELLENT = 0.80
QUALITY_THRESHOLD_GOOD = 0.60
QUALITY_THRESHOLD_LIMITED = 0.40

# ─── Temporal Quality Thresholds (Days) ───
TEMPORAL_THRESHOLD_FRESH_DAYS = 5.0
TEMPORAL_THRESHOLD_RECENT_DAYS = 15.0
TEMPORAL_THRESHOLD_MAX_LOOKBACK_DAYS = 30.0

# ─── Scene Classification Layer (SCL) Official Codes ───
SCL_NO_DATA = 0
SCL_SATURATED_OR_DEFECTIVE = 1
SCL_DARK_AREA_PIXELS = 2
SCL_CLOUD_SHADOWS = 3
SCL_VEGETATION = 4
SCL_NOT_VEGETATED = 5
SCL_WATER = 6
SCL_UNCLASSIFIED = 7
SCL_CLOUD_MEDIUM_PROBABILITY = 8
SCL_CLOUD_HIGH_PROBABILITY = 9
SCL_THIN_CIRRUS = 10
SCL_SNOW_OR_ICE = 11

# SCL codes considered INVALID for optical/SWIR surface analytics
# Note: Snow/Ice (11) is tracked explicitly; Clouds, shadows, cirrus, defects are masked.
INVALID_SCL_CODES: frozenset[int] = frozenset({
    SCL_NO_DATA,
    SCL_SATURATED_OR_DEFECTIVE,
    SCL_CLOUD_SHADOWS,
    SCL_UNCLASSIFIED,
    SCL_CLOUD_MEDIUM_PROBABILITY,
    SCL_CLOUD_HIGH_PROBABILITY,
    SCL_THIN_CIRRUS,
})

CLOUD_SCL_CODES: frozenset[int] = frozenset({
    SCL_CLOUD_MEDIUM_PROBABILITY,
    SCL_CLOUD_HIGH_PROBABILITY,
    SCL_THIN_CIRRUS,
    SCL_UNCLASSIFIED,
})

CLOUD_SHADOW_SCL_CODES: frozenset[int] = frozenset({
    SCL_CLOUD_SHADOWS,
})

SNOW_SCL_CODES: frozenset[int] = frozenset({
    SCL_SNOW_OR_ICE,
})

# ─── Geometric and Analytical Parameters ───
ANALYTICAL_RADII_METERS: tuple[float, ...] = (100.0, 250.0, 500.0)
PRIMARY_RADIUS_METERS: float = 250.0
ANALYTICAL_RESOLUTION_M: float = 20.0
SENTINEL_COLLECTION_NAME: str = "sentinel-2-l2a"
DEFAULT_ALGORITHM_VERSION: str = "sentinel2_context_v1"
