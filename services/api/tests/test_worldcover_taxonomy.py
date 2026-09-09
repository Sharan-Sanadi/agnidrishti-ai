# AGNIDRISHTI API — ESA WorldCover Taxonomy Unit Tests
"""
Verifies exact official ESA WorldCover 10 m 2021 v200 class codes and taxonomical mappings.
"""

from app.providers.worldcover.constants import (
    OFFICIAL_CLASS_NAMES,
    WORLDCOVER_CLASSES,
    WorldCoverClass,
    WorldCoverContextClass,
    WorldCoverCoverageStatus,
    get_class_name,
    is_valid_class_code,
)


def test_official_11_class_codes():
    """Verify all 11 official ESA WorldCover 2021 v200 class codes exist and map correctly."""
    expected_mappings = {
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

    assert len(WORLDCOVER_CLASSES) == 11

    for code, expected_name in expected_mappings.items():
        assert is_valid_class_code(code) is True
        assert get_class_name(code) == expected_name
        assert OFFICIAL_CLASS_NAMES[code] == expected_name


def test_enum_values():
    """Verify WorldCoverClass enum members correspond to official codes."""
    assert WorldCoverClass.TREE_COVER.value == 10
    assert WorldCoverClass.SHRUBLAND.value == 20
    assert WorldCoverClass.GRASSLAND.value == 30
    assert WorldCoverClass.CROPLAND.value == 40
    assert WorldCoverClass.BUILT_UP.value == 50
    assert WorldCoverClass.BARE_SPARSE_VEGETATION.value == 60
    assert WorldCoverClass.SNOW_AND_ICE.value == 70
    assert WorldCoverClass.PERMANENT_WATER.value == 80
    assert WorldCoverClass.HERBACEOUS_WETLAND.value == 90
    assert WorldCoverClass.MANGROVES.value == 95
    assert WorldCoverClass.MOSS_AND_LICHEN.value == 100


def test_unexpected_codes_and_nodata():
    """Verify invalid codes, 0 (nodata), and 255 map to UNKNOWN_CODE and are not valid classes."""
    invalid_codes = [0, 15, 45, 99, 101, 255, -1]

    for code in invalid_codes:
        assert is_valid_class_code(code) is False
        assert get_class_name(code) == "UNKNOWN_CODE"


def test_coverage_status_and_context_enums():
    """Verify Coverage Status and Context V1 enum members."""
    assert WorldCoverCoverageStatus.COMPLETE.value == "COMPLETE"
    assert WorldCoverCoverageStatus.PARTIAL.value == "PARTIAL"
    assert WorldCoverCoverageStatus.UNAVAILABLE.value == "UNAVAILABLE"

    assert WorldCoverContextClass.CROPLAND_DOMINANT.value == "CROPLAND_DOMINANT"
    assert WorldCoverContextClass.BUILT_UP_DOMINANT.value == "BUILT_UP_DOMINANT"
    assert WorldCoverContextClass.TREE_COVER_DOMINANT.value == "TREE_COVER_DOMINANT"
    assert WorldCoverContextClass.MIXED.value == "MIXED"
    assert WorldCoverContextClass.UNAVAILABLE.value == "UNAVAILABLE"
