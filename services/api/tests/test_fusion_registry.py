# AGNIDRISHTI API — Phase 7 Feature Registry Tests
"""
Unit tests verifying the canonical fusion_v1 feature registry.
Asserts:
- Total features count (59).
- Model-eligible features count (57).
- Unique feature names and valid types.
- Deterministic canonical ordering.
- Stable SHA-256 schema hash.
- Geographic coordinates excluded from default ML features.
"""

from __future__ import annotations

import pytest

from app.services.fusion.feature_registry import (
    FUSION_V1_FEATURES,
    SCHEMA_VERSION_V1,
    FeatureRegistry,
    fusion_v1_registry,
)


def test_registry_schema_version() -> None:
    assert SCHEMA_VERSION_V1 == "fusion_v1"
    assert fusion_v1_registry.schema_version == "fusion_v1"


def test_registry_feature_counts() -> None:
    # 59 registered features total, 57 model-eligible (lat/lon excluded from ML features)
    assert fusion_v1_registry.total_feature_count == 59
    assert fusion_v1_registry.model_eligible_count == 57
    assert len(fusion_v1_registry.features) == 59


def test_registry_unique_feature_names() -> None:
    names = [f.name for f in fusion_v1_registry.features]
    assert len(names) == len(set(names)), "Feature names must be strictly unique"


def test_registry_canonical_order_stability() -> None:
    # Verify the first 5 and last 5 features to guard against silent reordering
    names = fusion_v1_registry.feature_names
    assert names[0] == "thermal_frp"
    assert names[1] == "thermal_brightness_ti4"
    assert names[2] == "thermal_brightness_ti5"
    assert names[3] == "thermal_scan"
    assert names[4] == "thermal_track"

    # Coordinates are positions 9 and 10
    assert names[9] == "thermal_latitude"
    assert names[10] == "thermal_longitude"

    # Temporal starts at index 11
    assert names[11] == "temporal_persistence_index"

    # Industrial starts at index 19
    assert names[19] == "industrial_context_class"

    # Land Cover starts at index 31
    assert names[31] == "landcover_point_code"

    # Sentinel starts at index 45
    assert names[45] == "sentinel_quality_status"

    # End features
    assert names[-2] == "sentinel_b11_p90_250m"
    assert names[-1] == "sentinel_b12_p90_250m"


def test_registry_schema_hash_determinism() -> None:
    # Recreate registry instance and verify identical SHA-256 hash
    new_reg = FeatureRegistry(FUSION_V1_FEATURES)
    assert new_reg.schema_hash == fusion_v1_registry.schema_hash
    assert len(fusion_v1_registry.schema_hash) == 64


def test_registry_coordinates_excluded_from_model_features() -> None:
    lat_spec = fusion_v1_registry.get_spec("thermal_latitude")
    lon_spec = fusion_v1_registry.get_spec("thermal_longitude")

    assert lat_spec is not None
    assert lon_spec is not None
    assert lat_spec.model_eligible is False
    assert lon_spec.model_eligible is False

    model_names = fusion_v1_registry.model_eligible_names
    assert "thermal_latitude" not in model_names
    assert "thermal_longitude" not in model_names
    assert "thermal_frp" in model_names


def test_registry_duplicate_name_error() -> None:
    # Injecting a duplicate feature spec must raise ValueError
    features_list = list(FUSION_V1_FEATURES)
    features_list.append(FUSION_V1_FEATURES[0])
    with pytest.raises(ValueError, match="Duplicate feature names"):
        FeatureRegistry(tuple(features_list))
