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
