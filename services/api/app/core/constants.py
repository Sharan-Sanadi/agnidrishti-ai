# AGNIDRISHTI API — Domain Constants
"""
Classification taxonomy, source identifiers, and scientific guardrails.
"""

from __future__ import annotations

from enum import StrEnum

# ==============================
# CLASSIFICATION TAXONOMY
# ==============================

class TopLevelClass(StrEnum):
    """Level 1 classification."""
    INDUSTRIAL = "INDUSTRIAL"
    NON_INDUSTRIAL = "NON_INDUSTRIAL"
    UNCERTAIN = "UNCERTAIN"


class IndustrialSubclass(StrEnum):
    """Level 2 — Industrial subclasses."""
    PROBABLE_INDUSTRIAL_FIRE = "PROBABLE_INDUSTRIAL_FIRE"
    PERSISTENT_INDUSTRIAL_THERMAL_SOURCE = "PERSISTENT_INDUSTRIAL_THERMAL_SOURCE"
    FLARE_LIKE_THERMAL_ACTIVITY = "FLARE_LIKE_THERMAL_ACTIVITY"
    MINING_OR_INDUSTRIAL_THERMAL_ACTIVITY = "MINING_OR_INDUSTRIAL_THERMAL_ACTIVITY"
    OTHER_INDUSTRIAL_ANOMALY = "OTHER_INDUSTRIAL_ANOMALY"


class NonIndustrialSubclass(StrEnum):
    """Level 2 — Non-industrial subclasses."""
    FOREST_OR_NATURAL_FIRE = "FOREST_OR_NATURAL_FIRE"
    AGRICULTURAL_BURNING = "AGRICULTURAL_BURNING"
    OTHER_NON_INDUSTRIAL_THERMAL_ACTIVITY = "OTHER_NON_INDUSTRIAL_THERMAL_ACTIVITY"


class UncertainSubclass(StrEnum):
    """Level 2 — Uncertain subclass."""
    UNCERTAIN_THERMAL_ANOMALY = "UNCERTAIN_THERMAL_ANOMALY"


# Union of all subclasses for validation
ALL_SUBCLASSES = (
    list(IndustrialSubclass)
    + list(NonIndustrialSubclass)
    + list(UncertainSubclass)
)


# ==============================
# DATA SOURCE IDENTIFIERS
# ==============================

class DataSource(StrEnum):
    """Known external data sources for traceability."""
    NASA_FIRMS = "NASA_FIRMS"
    OPENSTREETMAP = "OPENSTREETMAP"
    DYNAMIC_WORLD = "DYNAMIC_WORLD"
    ESA_WORLDCOVER = "ESA_WORLDCOVER"
    SENTINEL_2 = "SENTINEL_2"
    FIXTURE = "FIXTURE"


# ==============================
# ANALYSIS MODE
# ==============================

class AnalysisMode(StrEnum):
    """Indicates whether analysis used real or fixture data."""
    FIXTURE = "fixture"
    LIVE = "live"
    DEGRADED = "degraded"


# ==============================
# COORDINATE BOUNDS
# ==============================

LAT_MIN = -90.0
LAT_MAX = 90.0
LNG_MIN = -180.0
LNG_MAX = 180.0

# ==============================
# GeoJSON CONVENTION
# ==============================
# GeoJSON coordinates: [longitude, latitude] — NOT [lat, lng]
# This is a critical convention. Document prominently.
GEOJSON_COORDINATE_ORDER = "GeoJSON uses [longitude, latitude] — NOT [latitude, longitude]"

# ==============================
# NASA FIRMS CONSTANTS & SENSORS
# ==============================

class FIRMSSensor(StrEnum):
    """Supported NASA FIRMS satellite/sensor products."""
    VIIRS_NOAA20_NRT = "VIIRS_NOAA20_NRT"
    VIIRS_NOAA21_NRT = "VIIRS_NOAA21_NRT"
    VIIRS_SNPP_NRT = "VIIRS_SNPP_NRT"  # Kept optional; under NASA data-quality advisory

# Default primary sensors for Phase 1
DEFAULT_FIRMS_SENSORS = [
    FIRMSSensor.VIIRS_NOAA20_NRT,
    FIRMSSensor.VIIRS_NOAA21_NRT,
]

# India Operational Bounding Box (West, South, East, North)
# Covers mainland India + coastal waters
INDIA_DEFAULT_BBOX = (68.0, 6.5, 97.5, 37.5)

# Maximum supported day range by NASA FIRMS Area API
FIRMS_MIN_DAY_RANGE = 1
FIRMS_MAX_DAY_RANGE = 5

# ==============================
# FIRMS ERROR CODES
# ==============================

class FIRMSErrorCode(StrEnum):
    """Structured error codes for FIRMS ingestion."""
    MISSING_FIRMS_KEY = "MISSING_FIRMS_KEY"
    INVALID_BOUNDING_BOX = "INVALID_BOUNDING_BOX"
    INVALID_DAY_RANGE = "INVALID_DAY_RANGE"
    UNSUPPORTED_SOURCE = "UNSUPPORTED_SOURCE"
    FIRMS_AUTH_ERROR = "FIRMS_AUTH_ERROR"
    FIRMS_RATE_LIMITED = "FIRMS_RATE_LIMITED"
    FIRMS_TIMEOUT = "FIRMS_TIMEOUT"
    FIRMS_UPSTREAM_ERROR = "FIRMS_UPSTREAM_ERROR"
    FIRMS_MALFORMED_RESPONSE = "FIRMS_MALFORMED_RESPONSE"
