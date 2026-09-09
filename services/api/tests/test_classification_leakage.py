# AGNIDRISHTI API — Phase 8 Leakage & Spatial Grouping Tests
"""
Unit tests validating feature exclusion, anti-circularity guardrails (Strategy A),
and spatial group segregation across splits.
"""

from __future__ import annotations

from app.ml.classification.constants import (
    FORBIDDEN_MODEL_FEATURES,
    STRATEGY_A_EXCLUDED_CATEGORICALS,
)
from app.ml.classification.dataset import (
    DatasetRecord,
    audit_leakage,
    compute_spatial_group,
    get_model_feature_names,
)
from app.ml.classification.splitting import audit_group_leakage, split_grouped_dataset


def test_forbidden_features_excluded_from_model_matrix() -> None:
    """Ensure identifiers, timestamps, and raw coordinates are never in model features."""
    feature_names = get_model_feature_names(strategy_a=True)
    for forbidden in FORBIDDEN_MODEL_FEATURES:
        assert forbidden not in feature_names, f"Forbidden feature '{forbidden}' found in model features!"


def test_strategy_a_circular_categoricals_excluded() -> None:
    """Ensure weak-label defining categoricals are strictly excluded under Strategy A."""
    feature_names = get_model_feature_names(strategy_a=True)
    for cat in STRATEGY_A_EXCLUDED_CATEGORICALS:
        assert cat not in feature_names, f"Strategy A circular categorical '{cat}' found in model features!"


def test_audit_leakage_detector() -> None:
    """audit_leakage must detect forbidden and circular keys if injected."""
    clean_matrix = [{"thermal_frp": 15.2, "thermal_brightness": 320.5}]
    assert audit_leakage(clean_matrix, strategy_a=True) == []

    dirty_matrix = [{"thermal_frp": 15.2, "latitude": 28.5, "observation_id": "firms_123"}]
    detected = audit_leakage(dirty_matrix, strategy_a=True)
    assert "latitude" in detected
    assert "observation_id" in detected


def test_spatial_grouped_split_zero_leakage() -> None:
    """Ensure no spatial grid cell is shared between train, validation, and test splits."""
    records = []
    # Create 20 groups with 5 observations each
    for g_idx in range(20):
        lat = 20.0 + (g_idx * 0.05)
        lon = 78.0 + (g_idx * 0.05)
        grp = compute_spatial_group(lat, lon)
        for obs_idx in range(5):
            records.append(
                DatasetRecord(
                    observation_id=f"obs_{g_idx}_{obs_idx}",
                    features={"thermal_frp": 10.0 + obs_idx},
                    label="INDUSTRIAL_THERMAL_CONTEXT" if g_idx % 2 == 0 else "AGRICULTURAL_THERMAL_CONTEXT",
                    label_provenance="WEAK_HIGH_CONFIDENCE",
                    spatial_group=grp,
                )
            )

    train, val, test = split_grouped_dataset(records, test_size=0.20, val_size=0.20, random_state=42)
    assert len(train) > 0
    assert len(val) > 0
    assert len(test) > 0

    leakage = audit_group_leakage(train, val, test)
    assert leakage["train_val_overlap"] == 0
    assert leakage["train_test_overlap"] == 0
    assert leakage["val_test_overlap"] == 0
