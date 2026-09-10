# AGNIDRISHTI API — Phase 9 Mapping Unit Tests
"""
Tests for preprocessing-aware feature mapping, raw-to-transformed column mapping,
missingness indicators, one-hot category aggregation, and multi-modal group rollups.
"""

from __future__ import annotations

from app.ml.classification.registry import model_registry
from app.ml.explainability.constants import (
    CONTRIBUTION_HIGH,
    DIRECTION_NEUTRAL,
    DIRECTION_OPPOSES,
    DIRECTION_SUPPORTS,
)
from app.ml.explainability.mapping import (
    aggregate_group_contributions,
    build_raw_feature_map,
    format_raw_value,
    get_feature_display_name,
    get_feature_group,
    get_feature_unit,
)
from app.ml.explainability.schemas import FeatureContributionItem


def test_build_raw_feature_map_completeness():
    """Verify that all 96 transformed feature columns map to the 53 raw features."""
    pipeline = model_registry.model
    manifest = model_registry.manifest
    assert pipeline is not None
    assert manifest is not None

    preprocessor = pipeline.named_steps["preprocessor"]
    ordered_features = manifest.ordered_features
    assert len(ordered_features) == 53

    raw_to_trans = build_raw_feature_map(preprocessor, ordered_features)
    assert len(raw_to_trans) == 53

    all_mapped_indices = []
    for feat_name, indices in raw_to_trans.items():
        assert isinstance(indices, list)
        all_mapped_indices.extend(indices)

    # 96 total transformed features
    assert len(all_mapped_indices) == 96
    assert len(set(all_mapped_indices)) == 96  # strictly unique, no collisions
    assert set(all_mapped_indices) == set(range(96))  # complete 0..95 span


def test_missing_indicator_aggregation():
    """Verify that features with missing indicators map both value and indicator columns."""
    pipeline = model_registry.model
    manifest = model_registry.manifest
    preprocessor = pipeline.named_steps["preprocessor"]
    raw_to_trans = build_raw_feature_map(preprocessor, manifest.ordered_features)

    # Features like nearest_industrial_distance_m have missing indicators
    ind_dist_indices = raw_to_trans["industrial_nearest_distance_m"]
    assert len(ind_dist_indices) == 2  # 1 value col + 1 missing indicator col

    # Sentinel NDVI also had missingness
    ndvi_indices = raw_to_trans["sentinel_ndvi_median_250m"]
    assert len(ndvi_indices) == 2


def test_one_hot_category_aggregation():
    """Verify that one-hot categorical features map all their categories to the parent raw feature."""
    pipeline = model_registry.model
    manifest = model_registry.manifest
    preprocessor = pipeline.named_steps["preprocessor"]
    raw_to_trans = build_raw_feature_map(preprocessor, manifest.ordered_features)

    # Day/Night has 2 categories: D, N
    daynight_indices = raw_to_trans["thermal_daynight"]
    assert len(daynight_indices) == 2

    # Persistence class has 4 categories: ISOLATED, OCCASIONAL, PERSISTENT, RECURRING
    persist_indices = raw_to_trans["temporal_persistence_class"]
    assert len(persist_indices) == 4


def test_format_raw_value_formatting():
    """Verify human-readable source value formatting with units and edge cases."""
    assert format_raw_value("thermal_frp", 45.678, "MW") == "45.7 MW"
    assert format_raw_value("thermal_brightness_ti4", 320.45, "Kelvin") == "320.4 K"
    assert format_raw_value("industrial_nearest_distance_m", 596.2, "m") == "596 m"
    assert format_raw_value("industrial_nearest_distance_m", 2500.0, "m") == "2.50 km"
    assert format_raw_value("landcover_cropland_fraction_500m", 0.742) == "74.2%"
    assert format_raw_value("sentinel_ndvi_median_250m", 0.4567) == "0.457"
    assert format_raw_value("industrial_has_flare_nearby", True) == "Yes"
    assert format_raw_value("industrial_has_flare_nearby", False) == "No"
    assert format_raw_value("industrial_nearest_category", "INDUSTRIAL_AREA") == "Industrial Area"
    assert format_raw_value("sentinel_ndvi_median_250m", None) == "Unavailable"


def test_feature_display_name_and_metadata():
    """Verify display names and groups for core features."""
    assert get_feature_display_name("thermal_frp") == "Fire Radiative Power"
    assert get_feature_group("thermal_frp") == "THERMAL"
    assert get_feature_unit("thermal_frp") == "MW"

    assert get_feature_display_name("industrial_nearest_distance_m") == "Nearest Industrial Feature Distance"
    assert get_feature_group("industrial_nearest_distance_m") == "INDUSTRIAL"
    assert get_feature_unit("industrial_nearest_distance_m") == "meters"


def test_aggregate_group_contributions():
    """Verify multi-modal group aggregation sums, directions, and levels."""
    sample_items = [
        FeatureContributionItem(
            feature_name="thermal_frp",
            display_name="Fire Radiative Power",
            feature_group="THERMAL",
            raw_value=50.0,
            display_value="50.0 MW",
            unit="MW",
            contribution=1.5,
            relative_strength=30.0,
            direction=DIRECTION_SUPPORTS,
            rank=1,
        ),
        FeatureContributionItem(
            feature_name="industrial_nearest_distance_m",
            display_name="Nearest Industrial Distance",
            feature_group="INDUSTRIAL",
            raw_value=300.0,
            display_value="300 m",
            unit="m",
            contribution=2.5,
            relative_strength=50.0,
            direction=DIRECTION_SUPPORTS,
            rank=2,
        ),
        FeatureContributionItem(
            feature_name="landcover_cropland_fraction_500m",
            display_name="Cropland Fraction",
            feature_group="LAND_COVER",
            raw_value=0.8,
            display_value="80.0%",
            unit="",
            contribution=-1.0,
            relative_strength=20.0,
            direction=DIRECTION_OPPOSES,
            rank=1,
        ),
    ]

    groups = aggregate_group_contributions(sample_items)
    assert "THERMAL" in groups
    assert "INDUSTRIAL" in groups
    assert "LAND_COVER" in groups
    assert "TEMPORAL" in groups
    assert "SENTINEL" in groups

    assert groups["INDUSTRIAL"].total_contribution == 2.5
    assert groups["INDUSTRIAL"].direction == DIRECTION_SUPPORTS
    assert groups["INDUSTRIAL"].contribution_level == CONTRIBUTION_HIGH

    assert groups["LAND_COVER"].total_contribution == -1.0
    assert groups["LAND_COVER"].direction == DIRECTION_OPPOSES

    assert groups["TEMPORAL"].total_contribution == 0.0
    assert groups["TEMPORAL"].direction == DIRECTION_NEUTRAL
