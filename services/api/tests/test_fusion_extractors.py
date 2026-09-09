# AGNIDRISHTI API — Phase 7 Feature Extractors and Validation Unit Tests
"""
Pure unit tests verifying feature extraction, missingness semantics, scale invariants,
leakage prevention, and source fingerprinting.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.services.fusion.extractors import (
    extract_industrial_features,
    extract_land_cover_features,
    extract_sentinel_features,
    extract_temporal_features,
    extract_thermal_features,
)
from app.services.fusion.fingerprint import compute_source_fingerprint


def test_thermal_extraction() -> None:
    now = datetime.now(UTC)
    mock_obs = {
        "frp": 12.5,
        "bright_ti4": 345.2,
        "bright_ti5": 298.1,
        "scan": 0.38,
        "track": 0.36,
        "daynight": "N",
        "satellite": "N20",
        "instrument": "VIIRS",
        "confidence_normalized": "nominal",
        "latitude": 21.45,
        "longitude": 84.12,
        "provider": "NASA FIRMS",
        "source_product": "VIIRS_NOAA20_NRT",
        "acquisition_time_utc": now,
    }

    features, status, prov = extract_thermal_features(mock_obs)
    assert status == "AVAILABLE"
    assert features["thermal_frp"] == 12.5
    assert features["thermal_daynight"] == "N"
    assert features["thermal_latitude"] == 21.45
    assert features["thermal_longitude"] == 84.12
    assert prov["source_product"] == "VIIRS_NOAA20_NRT"


def test_temporal_persistence_scale_invariant() -> None:
    # CRITICAL: persistence_index 100 must remain 100, NOT 1.0 or 1
    mock_pers = {
        "persistence_index": 100,
        "persistence_class": "PERSISTENT",
        "active_days_7d": 7,
        "active_days_30d": 24,
        "active_weeks_30d": 4,
        "temporal_span_days_30d": 28.5,
        "history_coverage_ratio_30d": 1.0,
        "raw_detection_count_30d": 52,
        "algorithm_version": "temporal_persistence_v1",
        "radius_m": 750.0,
    }

    features, status, prov = extract_temporal_features(mock_pers)
    assert status == "AVAILABLE"
    assert features["temporal_persistence_index"] == 100
    assert isinstance(features["temporal_persistence_index"], int)
    assert features["temporal_persistence_class"] == "PERSISTENT"
    assert features["temporal_active_days_30d"] == 24


def test_temporal_insufficient_history_partial() -> None:
    # INSUFFICIENT_HISTORY must preserve index and category without setting index to 0
    mock_pers = {
        "persistence_index": 16,
        "persistence_class": "INSUFFICIENT_HISTORY",
        "active_days_7d": 1,
        "active_days_30d": 1,
        "active_weeks_30d": 1,
        "temporal_span_days_30d": 0.0,
        "history_coverage_ratio_30d": 0.03,
        "raw_detection_count_30d": 1,
        "algorithm_version": "temporal_persistence_v1",
    }

    features, status, _ = extract_temporal_features(mock_pers)
    assert status == "PARTIAL"
    assert features["temporal_persistence_class"] == "INSUFFICIENT_HISTORY"
    assert features["temporal_persistence_index"] == 16


def test_industrial_none_with_adequate_coverage() -> None:
    # Industrial NONE with valid coverage: counts are 0, distance is None, status is AVAILABLE
    mock_ind = {
        "context_class": "NONE",
        "coverage_status": "ADEQUATE",
        "nearest_industrial_distance_m": None,
        "inside_industrial_area": False,
        "nearest_feature_category": None,
        "feature_count_500m": 0,
        "feature_count_1km": 0,
        "feature_count_5km": 0,
        "has_flare_nearby": False,
        "has_chimney_nearby": False,
        "has_refinery_nearby": False,
        "has_power_plant_nearby": False,
        "algorithm_version": "industrial_context_v1",
    }

    features, status, _ = extract_industrial_features(mock_ind)
    assert status == "AVAILABLE"
    assert features["industrial_context_class"] == "NONE"
    assert features["industrial_coverage_status"] == "ADEQUATE"
    assert features["industrial_nearest_distance_m"] is None
    assert features["industrial_feature_count_500m"] == 0
    assert features["industrial_feature_count_5km"] == 0


def test_industrial_unavailable_remains_unavailable() -> None:
    mock_ind = {
        "context_class": "NONE",
        "coverage_status": "UNAVAILABLE",
        "nearest_industrial_distance_m": None,
        "inside_industrial_area": False,
        "feature_count_500m": None,
    }

    features, status, _ = extract_industrial_features(mock_ind)
    assert status == "UNAVAILABLE"
    assert features["industrial_coverage_status"] == "UNAVAILABLE"
    assert features["industrial_feature_count_500m"] is None


def test_sentinel_cloud_limited_null_spectral_values() -> None:
    # CLOUD_LIMITED: spectral indices must remain strictly None, not 0.0
    now = datetime.now(UTC)
    scene_time = now - timedelta(days=2)
    mock_s2 = {
        "quality_status": "CLOUD_LIMITED",
        "provider_status": "CLOUD_LIMITED",
        "sentinel_scene_time": scene_time,
        "sentinel_scene_id": "S2A_MSIL2A_TEST",
        "sentinel_scene_age_days": 2.0,
        "sentinel_valid_fraction_250m": 0.15,
        "sentinel_cloud_fraction_250m": 0.85,
        "algorithm_version": "sentinel_context_v1",
    }

    features, status, prov, flags = extract_sentinel_features(mock_s2, firms_acquisition_time=now)
    assert status == "CLOUD_LIMITED"
    assert features["sentinel_quality_status"] == "CLOUD_LIMITED"
    assert features["sentinel_ndvi_median_250m"] is None
    assert features["sentinel_ndmi_median_250m"] is None
    assert features["sentinel_nbr_median_250m"] is None
    assert features["sentinel_b04_median_250m"] is None
    assert len(flags) == 0


def test_sentinel_future_leakage_rejection() -> None:
    # Sentinel scene time > FIRMS detection time MUST be rejected as temporal leakage
    firms_time = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    future_scene_time = firms_time + timedelta(hours=3)  # In the future!

    mock_s2 = {
        "quality_status": "EXCELLENT",
        "provider_status": "AVAILABLE",
        "sentinel_scene_time": future_scene_time,
        "sentinel_scene_id": "S2A_FUTURE_LEAK",
        "sentinel_ndvi_median_250m": 0.45,
    }

    features, status, _, flags = extract_sentinel_features(mock_s2, firms_acquisition_time=firms_time)
    assert status == "UNAVAILABLE"
    assert features["sentinel_provider_status"] == "LEAKAGE_REJECTED"
    assert features["sentinel_ndvi_median_250m"] is None
    assert any("TEMPORAL LEAKAGE DETECTED" in flag for flag in flags)


def test_land_cover_fraction_sum() -> None:
    mock_lc = {
        "point_class_code": 40,
        "point_class_name": "CROPLAND",
        "context_class": "CROPLAND_DOMINANT",
        "coverage_status": "COMPLETE",
        "dominant_class_500m": "CROPLAND",
        "dominant_fraction_500m": 0.80,
        "tree_cover_fraction_500m": 0.10,
        "shrubland_fraction_500m": 0.05,
        "grassland_fraction_500m": 0.05,
        "cropland_fraction_500m": 0.80,
        "built_up_fraction_500m": 0.0,
        "bare_sparse_fraction_500m": 0.0,
        "water_fraction_500m": 0.0,
        "wetland_fraction_500m": 0.0,
        "source_product": "ESA_WorldCover_10m_2021_v200",
        "algorithm_version": "land_cover_v1",
    }

    features, status, prov, flags = extract_land_cover_features(mock_lc)
    assert status == "AVAILABLE"
    assert features["landcover_point_class"] == "CROPLAND"
    assert features["landcover_cropland_fraction_500m"] == 0.80
    assert len(flags) == 0


def test_source_fingerprint_stability_and_sensitivity() -> None:
    vec1 = {"feat_a": 1.0, "feat_b": "X", "feat_c": None}
    statuses = {"THERMAL": "AVAILABLE", "TEMPORAL": "AVAILABLE"}
    versions = {"algo_a": "v1"}

    fp1 = compute_source_fingerprint(vec1, statuses, versions)
    fp2 = compute_source_fingerprint(dict(vec1), dict(statuses), dict(versions))
    assert fp1 == fp2, "Fingerprint must be deterministic"

    # One feature changes
    vec2 = {"feat_a": 1.1, "feat_b": "X", "feat_c": None}
    fp3 = compute_source_fingerprint(vec2, statuses, versions)
    assert fp3 != fp1, "Fingerprint must change when feature changes"

    # Status changes
    statuses_changed = {"THERMAL": "AVAILABLE", "TEMPORAL": "PARTIAL"}
    fp4 = compute_source_fingerprint(vec1, statuses_changed, versions)
    assert fp4 != fp1, "Fingerprint must change when status changes"
