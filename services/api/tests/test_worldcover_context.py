# AGNIDRISHTI API — ESA WorldCover Context V1 Classifier Unit Tests
"""
Verifies deterministic Phase-5 Context V1 classification rules:
- 500m Dominance >= 0.60 maps to <CLASS>_DOMINANT
- Dominance < 0.60 maps to MIXED
- UNAVAILABLE coverage maps to UNAVAILABLE
- Does not infer fire cause or hazard probability.
"""

from app.providers.worldcover.constants import (
    DOMINANCE_THRESHOLD,
    WorldCoverContextClass,
    WorldCoverCoverageStatus,
)
from app.providers.worldcover.raster import WorldCoverRasterProcessor


def test_cropland_dominant_classification():
    """Verify cropland fraction >= 0.60 maps to CROPLAND_DOMINANT."""
    context = WorldCoverRasterProcessor.classify_context_v1(
        dominant_class="CROPLAND",
        dominant_fraction=0.80,
        coverage_status=WorldCoverCoverageStatus.COMPLETE,
        valid_fraction=0.99,
    )
    assert context == WorldCoverContextClass.CROPLAND_DOMINANT


def test_built_up_dominant_classification():
    """Verify built-up fraction >= 0.60 maps to BUILT_UP_DOMINANT."""
    context = WorldCoverRasterProcessor.classify_context_v1(
        dominant_class="BUILT_UP",
        dominant_fraction=0.70,
        coverage_status=WorldCoverCoverageStatus.COMPLETE,
        valid_fraction=0.95,
    )
    assert context == WorldCoverContextClass.BUILT_UP_DOMINANT


def test_tree_cover_dominant_classification():
    """Verify tree cover fraction >= 0.60 maps to TREE_COVER_DOMINANT."""
    context = WorldCoverRasterProcessor.classify_context_v1(
        dominant_class="TREE_COVER",
        dominant_fraction=0.65,
        coverage_status=WorldCoverCoverageStatus.COMPLETE,
        valid_fraction=0.98,
    )
    assert context == WorldCoverContextClass.TREE_COVER_DOMINANT


def test_mixed_classification_below_threshold():
    """Verify when no class reaches 0.60, context is classified as MIXED."""
    # 40% Cropland, 35% Built-up, 25% Grassland -> highest is Cropland at 0.40 < 0.60
    context = WorldCoverRasterProcessor.classify_context_v1(
        dominant_class="CROPLAND",
        dominant_fraction=0.40,
        coverage_status=WorldCoverCoverageStatus.COMPLETE,
        valid_fraction=0.95,
    )
    assert context == WorldCoverContextClass.MIXED


def test_exact_threshold_boundary():
    """Verify boundary condition at exactly 0.60 dominance."""
    assert DOMINANCE_THRESHOLD == 0.60

    # Exactly 0.60 -> DOMINANT
    context_at_threshold = WorldCoverRasterProcessor.classify_context_v1(
        dominant_class="GRASSLAND",
        dominant_fraction=0.60,
        coverage_status=WorldCoverCoverageStatus.COMPLETE,
        valid_fraction=0.90,
    )
    assert context_at_threshold == WorldCoverContextClass.GRASSLAND_DOMINANT

    # Just below 0.60 (0.5999) -> MIXED
    context_below_threshold = WorldCoverRasterProcessor.classify_context_v1(
        dominant_class="GRASSLAND",
        dominant_fraction=0.5999,
        coverage_status=WorldCoverCoverageStatus.COMPLETE,
        valid_fraction=0.90,
    )
    assert context_below_threshold == WorldCoverContextClass.MIXED


def test_all_class_dominant_mappings():
    """Verify mapping table for every official WorldCover class."""
    expected_mappings = {
        "TREE_COVER": WorldCoverContextClass.TREE_COVER_DOMINANT,
        "SHRUBLAND": WorldCoverContextClass.SHRUBLAND_DOMINANT,
        "GRASSLAND": WorldCoverContextClass.GRASSLAND_DOMINANT,
        "CROPLAND": WorldCoverContextClass.CROPLAND_DOMINANT,
        "BUILT_UP": WorldCoverContextClass.BUILT_UP_DOMINANT,
        "BARE_SPARSE_VEGETATION": WorldCoverContextClass.BARE_SPARSE_DOMINANT,
        "SNOW_AND_ICE": WorldCoverContextClass.SNOW_ICE_DOMINANT,
        "PERMANENT_WATER": WorldCoverContextClass.WATER_DOMINANT,
        "HERBACEOUS_WETLAND": WorldCoverContextClass.WETLAND_DOMINANT,
        "MANGROVES": WorldCoverContextClass.MANGROVE_DOMINANT,
        "MOSS_AND_LICHEN": WorldCoverContextClass.MOSS_LICHEN_DOMINANT,
    }

    for class_name, expected_context in expected_mappings.items():
        ctx = WorldCoverRasterProcessor.classify_context_v1(
            dominant_class=class_name,
            dominant_fraction=0.85,
            coverage_status=WorldCoverCoverageStatus.COMPLETE,
            valid_fraction=1.0,
        )
        assert ctx == expected_context


def test_unavailable_coverage_status():
    """Verify UNAVAILABLE coverage status always produces UNAVAILABLE context."""
    context = WorldCoverRasterProcessor.classify_context_v1(
        dominant_class="CROPLAND",
        dominant_fraction=0.90,
        coverage_status=WorldCoverCoverageStatus.UNAVAILABLE,
        valid_fraction=0.0,
    )
    assert context == WorldCoverContextClass.UNAVAILABLE
