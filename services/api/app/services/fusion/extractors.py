# AGNIDRISHTI API — Phase 7 Pure Feature Extractors
"""
Pure, side-effect-free extractor functions for each evidence group.
Maps existing, verified upstream objects into canonical fusion_v1 feature dictionaries.

Rules:
- Strictly maps existing attributes. Does not recompute upstream algorithms.
- Strictly preserves NULL / None. Does NOT impute zeros or averages.
- Preserves exact 0-100 scale for Persistence Index.
- Preserves industrial NONE with valid coverage as real information (counts=0, distance=None).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.fusion.validator import (
    sanitize_value,
    validate_landcover_fractions,
    validate_sentinel_leakage,
)


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Safely get attribute from object or dictionary."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return sanitize_value(float(v))
    except (ValueError, TypeError):
        return None


def _to_int(v: Any, default: int | None = None) -> int | None:
    if v is None:
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        return default


def _to_str(v: Any, default: str | None = None) -> str | None:
    if v is None:
        return default
    return str(v)


def extract_thermal_features(obs: Any) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """
    Extract Phase 1 Thermal Observable features.
    Returns (features_dict, group_status, provenance_dict).
    """
    features: dict[str, Any] = {
        "thermal_frp": _to_float(_get_attr(obs, "frp")),
        "thermal_brightness_ti4": _to_float(_get_attr(obs, "bright_ti4")),
        "thermal_brightness_ti5": _to_float(_get_attr(obs, "bright_ti5")),
        "thermal_scan": _to_float(_get_attr(obs, "scan")),
        "thermal_track": _to_float(_get_attr(obs, "track")),
        "thermal_daynight": _to_str(_get_attr(obs, "daynight")),
        "thermal_satellite": _to_str(_get_attr(obs, "satellite")),
        "thermal_instrument": _to_str(_get_attr(obs, "instrument")),
        "thermal_confidence": _to_str(_get_attr(obs, "confidence_normalized", _get_attr(obs, "confidence"))),
        "thermal_latitude": _to_float(_get_attr(obs, "latitude")),
        "thermal_longitude": _to_float(_get_attr(obs, "longitude")),
    }

    provenance = {
        "provider": _get_attr(obs, "provider", "NASA FIRMS"),
        "source_product": _get_attr(obs, "source_product"),
        "acquisition_time_utc": (
            _get_attr(obs, "acquisition_time_utc").isoformat()
            if hasattr(_get_attr(obs, "acquisition_time_utc"), "isoformat")
            else str(_get_attr(obs, "acquisition_time_utc"))
        ),
    }

    group_status = "AVAILABLE"
    return features, group_status, provenance


def extract_temporal_features(profile: Any) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """
    Extract Phase 3 Temporal Persistence features.
    Returns (features_dict, group_status, provenance_dict).
    """
    if profile is None:
        features = {
            "temporal_persistence_index": None,
            "temporal_persistence_class": None,
            "temporal_active_days_7d": None,
            "temporal_active_days_30d": None,
            "temporal_active_weeks_30d": None,
            "temporal_span_days_30d": None,
            "temporal_coverage_ratio_30d": None,
            "temporal_detection_count_30d": None,
        }
        return features, "UNAVAILABLE", {"algorithm_version": None}

    p_class = _to_str(_get_attr(profile, "persistence_class"))
    p_index = _to_int(_get_attr(profile, "persistence_index"))

    features = {
        "temporal_persistence_index": p_index,  # Canonical 0-100 scale preserved
        "temporal_persistence_class": p_class,
        "temporal_active_days_7d": _to_int(_get_attr(profile, "active_days_7d"), 0),
        "temporal_active_days_30d": _to_int(_get_attr(profile, "active_days_30d"), 0),
        "temporal_active_weeks_30d": _to_int(_get_attr(profile, "active_weeks_30d"), 0),
        "temporal_span_days_30d": _to_float(_get_attr(profile, "temporal_span_days_30d")),
        "temporal_coverage_ratio_30d": _to_float(_get_attr(profile, "history_coverage_ratio_30d")),
        "temporal_detection_count_30d": _to_int(_get_attr(profile, "raw_detection_count_30d"), 0),
    }

    group_status = "PARTIAL" if p_class == "INSUFFICIENT_HISTORY" else "AVAILABLE"

    provenance = {
        "algorithm_version": _get_attr(profile, "algorithm_version", "temporal_persistence_v1"),
        "radius_m": _get_attr(profile, "radius_m", 750.0),
    }

    return features, group_status, provenance


def extract_industrial_features(profile: Any) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """
    Extract Phase 4 Industrial Context features.
    Returns (features_dict, group_status, provenance_dict).
    """
    if profile is None:
        features = {
            "industrial_context_class": None,
            "industrial_coverage_status": "UNAVAILABLE",
            "industrial_nearest_distance_m": None,
            "industrial_inside_area": None,
            "industrial_nearest_category": None,
            "industrial_feature_count_500m": None,
            "industrial_feature_count_1km": None,
            "industrial_feature_count_5km": None,
            "industrial_has_flare_nearby": None,
            "industrial_has_chimney_nearby": None,
            "industrial_has_refinery_nearby": None,
            "industrial_has_power_plant_nearby": None,
        }
        return features, "UNAVAILABLE", {"algorithm_version": None}

    cov_status = str(_get_attr(profile, "coverage_status", "UNAVAILABLE"))
    if cov_status == "UNAVAILABLE":
        features = {
            "industrial_context_class": str(_get_attr(profile, "context_class", "NONE")),
            "industrial_coverage_status": "UNAVAILABLE",
            "industrial_nearest_distance_m": None,
            "industrial_inside_area": False,
            "industrial_nearest_category": None,
            "industrial_feature_count_500m": None,
            "industrial_feature_count_1km": None,
            "industrial_feature_count_5km": None,
            "industrial_has_flare_nearby": False,
            "industrial_has_chimney_nearby": False,
            "industrial_has_refinery_nearby": False,
            "industrial_has_power_plant_nearby": False,
        }
        return features, "UNAVAILABLE", {"algorithm_version": _get_attr(profile, "algorithm_version")}

    # Valid coverage (ADEQUATE or SPARSE)
    nearest_dist = _get_attr(profile, "nearest_industrial_distance_m")
    features = {
        "industrial_context_class": str(_get_attr(profile, "context_class")),
        "industrial_coverage_status": cov_status,
        "industrial_nearest_distance_m": sanitize_value(float(nearest_dist)) if nearest_dist is not None else None,
        "industrial_inside_area": bool(_get_attr(profile, "inside_industrial_area", False)),
        "industrial_nearest_category": _get_attr(profile, "nearest_feature_category"),
        "industrial_feature_count_500m": int(_get_attr(profile, "feature_count_500m", 0)),
        "industrial_feature_count_1km": int(_get_attr(profile, "feature_count_1km", 0)),
        "industrial_feature_count_5km": int(_get_attr(profile, "feature_count_5km", 0)),
        "industrial_has_flare_nearby": bool(_get_attr(profile, "has_flare_nearby", False)),
        "industrial_has_chimney_nearby": bool(_get_attr(profile, "has_chimney_nearby", False)),
        "industrial_has_refinery_nearby": bool(_get_attr(profile, "has_refinery_nearby", False)),
        "industrial_has_power_plant_nearby": bool(_get_attr(profile, "has_power_plant_nearby", False)),
    }

    provenance = {
        "algorithm_version": _get_attr(profile, "algorithm_version", "industrial_context_v1"),
        "nearest_feature_osm_uid": _get_attr(profile, "nearest_feature_osm_uid"),
    }

    return features, "AVAILABLE", provenance


def extract_land_cover_features(profile: Any) -> tuple[dict[str, Any], str, dict[str, Any], list[str]]:
    """
    Extract Phase 5 Land Cover (ESA WorldCover) features.
    Returns (features_dict, group_status, provenance_dict, quality_flags).
    """
    flags: list[str] = []
    if profile is None:
        features = {
            "landcover_point_code": None,
            "landcover_point_class": None,
            "landcover_context_class": None,
            "landcover_coverage_status": "UNAVAILABLE",
            "landcover_dominant_class_500m": None,
            "landcover_dominant_fraction_500m": None,
            "landcover_tree_fraction_500m": None,
            "landcover_shrub_fraction_500m": None,
            "landcover_grass_fraction_500m": None,
            "landcover_cropland_fraction_500m": None,
            "landcover_builtup_fraction_500m": None,
            "landcover_bare_fraction_500m": None,
            "landcover_water_fraction_500m": None,
            "landcover_wetland_fraction_500m": None,
        }
        return features, "UNAVAILABLE", {"product_version": None}, flags

    cov_status = str(_get_attr(profile, "coverage_status", "UNAVAILABLE"))
    if cov_status == "UNAVAILABLE":
        features = {
            "landcover_point_code": None,
            "landcover_point_class": None,
            "landcover_context_class": None,
            "landcover_coverage_status": "UNAVAILABLE",
            "landcover_dominant_class_500m": None,
            "landcover_dominant_fraction_500m": None,
            "landcover_tree_fraction_500m": None,
            "landcover_shrub_fraction_500m": None,
            "landcover_grass_fraction_500m": None,
            "landcover_cropland_fraction_500m": None,
            "landcover_builtup_fraction_500m": None,
            "landcover_bare_fraction_500m": None,
            "landcover_water_fraction_500m": None,
            "landcover_wetland_fraction_500m": None,
        }
        return features, "UNAVAILABLE", {"product_version": _get_attr(profile, "source_product")}, flags

    def _f(key: str) -> float | None:
        v = _get_attr(profile, key)
        return sanitize_value(float(v)) if v is not None else None

    features = {
        "landcover_point_code": _get_attr(profile, "point_class_code"),
        "landcover_point_class": _get_attr(profile, "point_class_name"),
        "landcover_context_class": _get_attr(profile, "context_class"),
        "landcover_coverage_status": cov_status,
        "landcover_dominant_class_500m": _get_attr(profile, "dominant_class_500m"),
        "landcover_dominant_fraction_500m": _f("dominant_fraction_500m"),
        "landcover_tree_fraction_500m": _f("tree_cover_fraction_500m"),
        "landcover_shrub_fraction_500m": _f("shrubland_fraction_500m"),
        "landcover_grass_fraction_500m": _f("grassland_fraction_500m"),
        "landcover_cropland_fraction_500m": _f("cropland_fraction_500m"),
        "landcover_builtup_fraction_500m": _f("built_up_fraction_500m"),
        "landcover_bare_fraction_500m": _f("bare_sparse_fraction_500m"),
        "landcover_water_fraction_500m": _f("water_fraction_500m"),
        "landcover_wetland_fraction_500m": _f("wetland_fraction_500m"),
    }

    # Validate fraction sum
    fractions_to_check = {
        "tree": features["landcover_tree_fraction_500m"],
        "shrub": features["landcover_shrub_fraction_500m"],
        "grass": features["landcover_grass_fraction_500m"],
        "cropland": features["landcover_cropland_fraction_500m"],
        "builtup": features["landcover_builtup_fraction_500m"],
        "bare": features["landcover_bare_fraction_500m"],
        "water": features["landcover_water_fraction_500m"],
        "wetland": features["landcover_wetland_fraction_500m"],
    }
    is_valid_sum, frac_sum, warning_msg = validate_landcover_fractions(fractions_to_check)
    if not is_valid_sum and warning_msg:
        flags.append(warning_msg)

    group_status = "AVAILABLE" if cov_status == "COMPLETE" else "PARTIAL"

    provenance = {
        "product_version": _get_attr(profile, "source_product", "ESA_WorldCover_10m_2021_v200"),
        "algorithm_version": _get_attr(profile, "algorithm_version", "land_cover_v1"),
        "source_year": 2021,
    }

    return features, group_status, provenance, flags


def extract_sentinel_features(
    profile: Any,
    firms_acquisition_time: datetime,
) -> tuple[dict[str, Any], str, dict[str, Any], list[str]]:
    """
    Extract Phase 6 Sentinel-2 L2A context features.
    Enforces strict temporal leakage prevention: if scene_time > firms_acquisition_time,
    Sentinel group is excluded.
    Preserves strict NULLs for CLOUD_LIMITED observations.
    Returns (features_dict, group_status, provenance_dict, quality_flags).
    """
    flags: list[str] = []
    empty_features = {
        "sentinel_quality_status": None,
        "sentinel_provider_status": "NOT_EVALUATED",
        "sentinel_scene_age_days": None,
        "sentinel_valid_fraction_250m": None,
        "sentinel_cloud_fraction_250m": None,
        "sentinel_b04_median_250m": None,
        "sentinel_b08_median_250m": None,
        "sentinel_b11_median_250m": None,
        "sentinel_b12_median_250m": None,
        "sentinel_ndvi_median_250m": None,
        "sentinel_ndmi_median_250m": None,
        "sentinel_nbr_median_250m": None,
        "sentinel_b11_p90_250m": None,
        "sentinel_b12_p90_250m": None,
    }

    if profile is None:
        return empty_features, "NOT_EVALUATED", {"scene_id": None}, flags

    scene_time = _get_attr(profile, "sentinel_scene_time")
    # Leakage check: Sentinel scene must not be in the future relative to the fire event!
    is_valid_leakage, leak_msg = validate_sentinel_leakage(firms_acquisition_time, scene_time)
    if not is_valid_leakage:
        flags.append(leak_msg or "Temporal leakage detected")
        empty_features["sentinel_provider_status"] = "LEAKAGE_REJECTED"
        return empty_features, "UNAVAILABLE", {"scene_id": _get_attr(profile, "sentinel_scene_id")}, flags

    quality = str(_get_attr(profile, "quality_status", "UNAVAILABLE"))
    provider = str(_get_attr(profile, "provider_status", "UNAVAILABLE"))

    def _f(key: str) -> float | None:
        v = _get_attr(profile, key)
        return sanitize_value(float(v)) if v is not None else None

    if quality == "CLOUD_LIMITED":
        features = {
            "sentinel_quality_status": "CLOUD_LIMITED",
            "sentinel_provider_status": provider,
            "sentinel_scene_age_days": _f("sentinel_scene_age_days"),
            "sentinel_valid_fraction_250m": _f("sentinel_valid_fraction_250m"),
            "sentinel_cloud_fraction_250m": _f("sentinel_cloud_fraction_250m"),
            # Spectral indices MUST REMAIN NULL - do NOT fabricate 0.0!
            "sentinel_b04_median_250m": None,
            "sentinel_b08_median_250m": None,
            "sentinel_b11_median_250m": None,
            "sentinel_b12_median_250m": None,
            "sentinel_ndvi_median_250m": None,
            "sentinel_ndmi_median_250m": None,
            "sentinel_nbr_median_250m": None,
            "sentinel_b11_p90_250m": None,
            "sentinel_b12_p90_250m": None,
        }
        group_status = "CLOUD_LIMITED"
    elif quality in ("EXCELLENT", "GOOD", "LIMITED"):
        features = {
            "sentinel_quality_status": quality,
            "sentinel_provider_status": provider,
            "sentinel_scene_age_days": _f("sentinel_scene_age_days"),
            "sentinel_valid_fraction_250m": _f("sentinel_valid_fraction_250m"),
            "sentinel_cloud_fraction_250m": _f("sentinel_cloud_fraction_250m"),
            "sentinel_b04_median_250m": _f("sentinel_b04_median_250m"),
            "sentinel_b08_median_250m": _f("sentinel_b08_median_250m"),
            "sentinel_b11_median_250m": _f("sentinel_b11_median_250m"),
            "sentinel_b12_median_250m": _f("sentinel_b12_median_250m"),
            "sentinel_ndvi_median_250m": _f("sentinel_ndvi_median_250m"),
            "sentinel_ndmi_median_250m": _f("sentinel_ndmi_median_250m"),
            "sentinel_nbr_median_250m": _f("sentinel_nbr_median_250m"),
            "sentinel_b11_p90_250m": _f("sentinel_b11_p90_250m"),
            "sentinel_b12_p90_250m": _f("sentinel_b12_p90_250m"),
        }
        group_status = "AVAILABLE"
    else:
        features = {
            "sentinel_quality_status": quality,
            "sentinel_provider_status": provider,
            "sentinel_scene_age_days": None,
            "sentinel_valid_fraction_250m": None,
            "sentinel_cloud_fraction_250m": None,
            "sentinel_b04_median_250m": None,
            "sentinel_b08_median_250m": None,
            "sentinel_b11_median_250m": None,
            "sentinel_b12_median_250m": None,
            "sentinel_ndvi_median_250m": None,
            "sentinel_ndmi_median_250m": None,
            "sentinel_nbr_median_250m": None,
            "sentinel_b11_p90_250m": None,
            "sentinel_b12_p90_250m": None,
        }
        group_status = "UNAVAILABLE"

    provenance = {
        "scene_id": _get_attr(profile, "sentinel_scene_id"),
        "scene_time": (
            scene_time.isoformat()
            if hasattr(scene_time, "isoformat")
            else str(scene_time) if scene_time is not None else None
        ),
        "algorithm_version": _get_attr(profile, "algorithm_version", "sentinel_context_v1"),
    }

    return features, group_status, provenance, flags
