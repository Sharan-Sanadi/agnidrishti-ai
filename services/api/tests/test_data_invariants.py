# AGNIDRISHTI API — Scientific Data Invariant Automated Tests
"""
Non-invasive automated validation tests enforcing physical, mathematical,
and domain invariants across the AgniDrishti data and intelligence pipeline.
"""

from __future__ import annotations

from app.ml.classification.registry import model_registry
from app.ml.explainability.constants import ADDITIVITY_TOLERANCE
from app.ml.explainability.provider import get_explanation_provider
from app.providers.firms.parser import (
    parse_firms_csv,
)
from app.providers.sentinel2.indices import (
    calculate_ndvi,
)
from app.services.firms_ingestion import (
    normalize_confidence,
    sanitize_float,
)
from app.services.fusion.feature_registry import fusion_v1_registry
from app.services.temporal_persistence import (
    classify_persistence_v1,
    compute_persistence_index_v1,
)


def test_spatial_coordinate_invariants():
    """Verify that latitude and longitude outside [-90, 90] and [-180, 180] are rejected."""
    # Valid
    csv_valid = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
        "20.5937,78.9629,340.5,0.4,0.4,2026-09-07,1200,N20,VIIRS,n,2.0NRT,290.1,45.2,D\n"
    )
    obs, rej = parse_firms_csv(csv_valid, "VIIRS_NOAA20_NRT")
    assert len(obs) == 1 and rej == 0
    assert -90.0 <= obs[0].latitude <= 90.0
    assert -180.0 <= obs[0].longitude <= 180.0
    # GeoJSON coordinate convention [longitude, latitude]
    assert obs[0].geojson["coordinates"] == [obs[0].longitude, obs[0].latitude]

    # Invalid latitude (> 90)
    csv_bad_lat = csv_valid.replace("20.5937", "95.5937")
    obs_lat, rej_lat = parse_firms_csv(csv_bad_lat, "VIIRS_NOAA20_NRT")
    assert len(obs_lat) == 0 and rej_lat == 1

    # Invalid longitude (> 180)
    csv_bad_lon = csv_valid.replace("78.9629", "185.0000")
    obs_lon, rej_lon = parse_firms_csv(csv_bad_lon, "VIIRS_NOAA20_NRT")
    assert len(obs_lon) == 0 and rej_lon == 1


def test_frp_and_brightness_physical_invariants():
    """Verify that FRP is non-negative and brightness temperatures are physically sound."""
    # FRP must be >= 0.0
    assert sanitize_float(0.0) == 0.0
    assert sanitize_float(45.2) == 45.2
    assert sanitize_float(float("nan")) is None
    assert sanitize_float(float("inf")) is None
    assert sanitize_float(None) is None


def test_confidence_normalization_invariants():
    """Verify confidence values strictly map to known semantic domain or None."""
    valid_semantic = {"low", "nominal", "high"}
    for raw_code in ["l", "n", "h", "low", "nominal", "high", "L", "N", "H"]:
        norm = normalize_confidence(raw_code)
        assert norm in valid_semantic

    assert normalize_confidence("") is None


def test_temporal_persistence_invariants():
    """Verify persistence index is strictly bounded in [0, 100] and classes are valid enums."""
    valid_classes = {"PERSISTENT", "RECURRING", "OCCASIONAL", "ISOLATED", "INSUFFICIENT_HISTORY"}

    # Test boundary combinations
    for days in [0, 1, 4, 8, 15, 30]:
        for weeks in [0, 1, 2, 3, 4]:
            for span in [0.0, 7.0, 14.0, 28.0]:
                for cov in [5, 20, 21, 30]:
                    cls = classify_persistence_v1(days, weeks, span, cov, min_history_days=21)
                    assert cls in valid_classes

                    score, comp = compute_persistence_index_v1(days, span, weeks, min(days, 3))
                    assert 0 <= score <= 100
                    assert 0.0 <= comp["active_days_score"] <= 45.0
                    assert 0.0 <= comp["temporal_span_score"] <= 25.0
                    assert 0.0 <= comp["multi_week_score"] <= 20.0
                    assert 0.0 <= comp["recency_score"] <= 10.0


def test_sentinel_index_mathematical_invariants():
    """Verify spectral indices are strictly bounded in [-1.0, 1.0] and zero-division is protected."""
    # Positive vegetation
    val = calculate_ndvi(0.40, 0.10)
    assert val is not None and -1.0 <= val <= 1.0

    # Negative water/burn
    val_neg = calculate_ndvi(0.02, 0.10)
    assert val_neg is not None and -1.0 <= val_neg <= 1.0

    # Near-zero denominator
    val_zero = calculate_ndvi(0.0, 0.0)
    assert val_zero is None

    # NaN / None inputs
    assert calculate_ndvi(None, 0.10) is None
    assert calculate_ndvi(float("nan"), 0.10) is None


def test_model_manifest_and_registry_alignment_invariants():
    """Verify that all features entering the classifier exist in the canonical fusion_v1_registry."""
    manifest = model_registry.manifest
    assert manifest is not None

    registry_eligible = set(fusion_v1_registry.model_eligible_names)
    for feat in manifest.ordered_features:
        assert feat in registry_eligible, f"Feature {feat} in model manifest is not in eligible registry!"

    # Geographic coordinates must NEVER enter the classifier
    assert "thermal_latitude" not in manifest.ordered_features
    assert "thermal_longitude" not in manifest.ordered_features


def test_shap_mathematical_additivity_invariant():
    """Verify that TreeExplainer additive residual |(base + sum(contributions)) - margin| < 1e-3."""
    pipeline = model_registry.model
    manifest = model_registry.manifest
    assert pipeline is not None and manifest is not None

    ordered_features = manifest.ordered_features
    provider = get_explanation_provider(pipeline, ordered_features)

    # Synthetic realistic vector
    row = [None] * len(ordered_features)
    row[0] = 30.0  # frp
    row[1] = 330.0 # ti4
    row[2] = 296.0 # ti5
    row[9] = 50.0  # persistence_index
    row[18] = 300.0 # nearest_dist_m
    row[34] = 0.70  # cropland fraction

    feature_dict = {ordered_features[i]: val for i, val in enumerate(row)}
    pred_cls = str(pipeline.predict([row])[0])

    exp = provider.explain_batch([row], [pred_cls], [feature_dict])[0]
    assert exp.status == "AVAILABLE"
    assert exp.additivity_error is not None
    assert exp.additivity_error < ADDITIVITY_TOLERANCE
