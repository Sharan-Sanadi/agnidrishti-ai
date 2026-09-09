# AGNIDRISHTI API — ESA WorldCover 2021 v200 Constants and Taxonomy
"""
Official taxonomy, product metadata, and deterministic classification rules
for ESA WorldCover 10 m 2021 v200.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum

# Official Product Metadata
PROVIDER_NAME = "ESA_WORLDCOVER"
PRODUCT_NAME = "ESA WorldCover 10 m 2021"
PRODUCT_VERSION = "v200"
SOURCE_YEAR = 2021
NOMINAL_RESOLUTION_M = 10
ALGORITHM_VERSION = "land_cover_v1"
NATIVE_CRS = "EPSG:4326"


class WorldCoverClass(IntEnum):
    TREE_COVER = 10
    SHRUBLAND = 20
    GRASSLAND = 30
    CROPLAND = 40
    BUILT_UP = 50
    BARE_SPARSE_VEGETATION = 60
    SNOW_AND_ICE = 70
    PERMANENT_WATER = 80
    HERBACEOUS_WETLAND = 90
    MANGROVES = 95
    MOSS_AND_LICHEN = 100


# Official 11 Land-Cover Classes (Map layer)
WORLDCOVER_CLASSES: dict[int, str] = {
    10: "TREE_COVER",
    20: "SHRUBLAND",
    30: "GRASSLAND",
    40: "CROPLAND",
    50: "BUILT_UP",
    60: "BARE_SPARSE_VEGETATION",
    70: "SNOW_AND_ICE",
    80: "PERMANENT_WATER",
    90: "HERBACEOUS_WETLAND",
    95: "MANGROVES",
    100: "MOSS_AND_LICHEN",
}

OFFICIAL_CLASS_NAMES = WORLDCOVER_CLASSES

# Human-readable labels for UI display
WORLDCOVER_LABELS: dict[int, str] = {
    10: "Tree Cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / Sparse Vegetation",
    70: "Snow and Ice",
    80: "Permanent Water",
    90: "Herbaceous Wetland",
    95: "Mangroves",
    100: "Moss and Lichen",
}

# Context V1 Mapping
CONTEXT_DOMINANCE_THRESHOLD = 0.60
DOMINANCE_THRESHOLD = CONTEXT_DOMINANCE_THRESHOLD
MIN_VALID_PIXEL_FRACTION = 0.50


CLASS_CODE_TO_CONTEXT_MAP: dict[int, str] = {
    10: "TREE_COVER_DOMINANT",
    20: "SHRUBLAND_DOMINANT",
    30: "GRASSLAND_DOMINANT",
    40: "CROPLAND_DOMINANT",
    50: "BUILT_UP_DOMINANT",
    60: "BARE_SPARSE_DOMINANT",
    70: "SNOW_ICE_DOMINANT",
    80: "WATER_DOMINANT",
    90: "WETLAND_DOMINANT",
    95: "MANGROVE_DOMINANT",
    100: "MOSS_LICHEN_DOMINANT",
}


class LandCoverCoverageStatus(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


WorldCoverCoverageStatus = LandCoverCoverageStatus


class LandCoverContextClass(StrEnum):
    TREE_COVER_DOMINANT = "TREE_COVER_DOMINANT"
    SHRUBLAND_DOMINANT = "SHRUBLAND_DOMINANT"
    GRASSLAND_DOMINANT = "GRASSLAND_DOMINANT"
    CROPLAND_DOMINANT = "CROPLAND_DOMINANT"
    BUILT_UP_DOMINANT = "BUILT_UP_DOMINANT"
    BARE_SPARSE_DOMINANT = "BARE_SPARSE_DOMINANT"
    SNOW_ICE_DOMINANT = "SNOW_ICE_DOMINANT"
    WATER_DOMINANT = "WATER_DOMINANT"
    WETLAND_DOMINANT = "WETLAND_DOMINANT"
    MANGROVE_DOMINANT = "MANGROVE_DOMINANT"
    MOSS_LICHEN_DOMINANT = "MOSS_LICHEN_DOMINANT"
    MIXED = "MIXED"
    UNAVAILABLE = "UNAVAILABLE"


WorldCoverContextClass = LandCoverContextClass


def get_class_name(code: int) -> str:
    """Return canonical class name or UNKNOWN_CODE."""
    return WORLDCOVER_CLASSES.get(code, "UNKNOWN_CODE")


def is_valid_class_code(code: int) -> bool:
    """Return True if code is one of the official 11 WorldCover class codes."""
    return code in WORLDCOVER_CLASSES


def get_class_label(code: int) -> str:
    """Return human-readable class label."""
    return WORLDCOVER_LABELS.get(code, f"Unknown ({code})")
