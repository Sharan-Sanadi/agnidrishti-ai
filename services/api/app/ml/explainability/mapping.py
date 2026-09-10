# AGNIDRISHTI API — Phase 9 Feature Mapping & Display Registry
"""
Mapping utilities connecting transformed sklearn pipeline features to human-readable
fusion_v1 raw evidence features. Provides display name registry, unit formatting,
missing indicator aggregation, one-hot category grouping, and multi-modal evidence group rollups.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.compose import ColumnTransformer

from app.ml.explainability.constants import (
    CONTRIBUTION_HIGH,
    CONTRIBUTION_LOW,
    CONTRIBUTION_MEDIUM,
    DIRECTION_NEUTRAL,
    DIRECTION_OPPOSES,
    DIRECTION_SUPPORTS,
    DIRECTION_TOLERANCE,
)
from app.ml.explainability.schemas import (
    FeatureContributionItem,
    GroupContributionItem,
)
from app.services.fusion.feature_registry import fusion_v1_registry

# -----------------------------------------------------------------------------
# Safe Human-Readable Feature Display Registry
# -----------------------------------------------------------------------------
FEATURE_DISPLAY_NAMES: dict[str, str] = {
    # Thermal (Phase 1)
    "thermal_frp": "Fire Radiative Power",
    "thermal_brightness_ti4": "VIIRS I-4 Thermal Brightness",
    "thermal_brightness_ti5": "VIIRS I-5 Thermal Brightness",
    "thermal_scan": "Sensor Along-Scan Pixel Dimension",
    "thermal_track": "Sensor Along-Track Pixel Dimension",
    "thermal_daynight": "Satellite Solar Cycle (Day/Night)",
    "thermal_satellite": "Observing Satellite Platform",
    "thermal_instrument": "Observing Instrument",
    "thermal_confidence": "Thermal Detection Confidence Tier",
    # Temporal (Phase 3)
    "temporal_persistence_index": "Temporal Persistence Index",
    "temporal_persistence_class": "Persistence Archetype Class",
    "temporal_active_days_7d": "Active Hotspot Days (Last 7D)",
    "temporal_active_days_30d": "Active Hotspot Days (Last 30D)",
    "temporal_active_weeks_30d": "Active Hotspot Weeks (Last 30D)",
    "temporal_span_days_30d": "Temporal Observation Span (30D)",
    "temporal_coverage_ratio_30d": "Temporal Coverage Ratio (30D)",
    "temporal_detection_count_30d": "Total Cluster Detections (30D)",
    # Industrial (Phase 4)
    "industrial_coverage_status": "Industrial Coverage Evaluation",
    "industrial_nearest_distance_m": "Nearest Industrial Feature Distance",
    "industrial_inside_area": "Inside Industrial Boundary",
    "industrial_nearest_category": "Nearest Industrial Category",
    "industrial_feature_count_500m": "Industrial Features within 500m",
    "industrial_feature_count_1km": "Industrial Features within 1km",
    "industrial_feature_count_5km": "Industrial Features within 5km",
    "industrial_has_flare_nearby": "Proximity to Gas Flare",
    "industrial_has_chimney_nearby": "Proximity to Industrial Chimney",
    "industrial_has_refinery_nearby": "Proximity to Oil/Gas Refinery",
    "industrial_has_power_plant_nearby": "Proximity to Thermal Power Plant",
    # Land Cover (Phase 5)
    "landcover_point_code": "WorldCover Point Pixel Code",
    "landcover_coverage_status": "Land Cover Coverage Evaluation",
    "landcover_dominant_fraction_500m": "Dominant Land Cover Fraction (500m)",
    "landcover_tree_fraction_500m": "Tree Canopy Fraction (500m)",
    "landcover_shrub_fraction_500m": "Shrubland Fraction (500m)",
    "landcover_grass_fraction_500m": "Grassland Fraction (500m)",
    "landcover_cropland_fraction_500m": "Cropland Coverage Fraction (500m)",
    "landcover_builtup_fraction_500m": "Built-up Land Fraction (500m)",
    "landcover_bare_fraction_500m": "Bare Soil / Sand Fraction (500m)",
    "landcover_water_fraction_500m": "Water Body Fraction (500m)",
    "landcover_wetland_fraction_500m": "Herbaceous Wetland Fraction (500m)",
    # Sentinel-2 (Phase 6)
    "sentinel_quality_status": "Sentinel-2 Spectral Scene Quality",
    "sentinel_provider_status": "Sentinel-2 Provider Query Status",
    "sentinel_scene_age_days": "Sentinel-2 Prior Scene Age",
    "sentinel_valid_fraction_250m": "Sentinel-2 Clear Valid Pixels (250m)",
    "sentinel_cloud_fraction_250m": "Sentinel-2 Cloud Mask Fraction (250m)",
    "sentinel_b04_median_250m": "Sentinel-2 B04 Red Reflectance (250m)",
    "sentinel_b08_median_250m": "Sentinel-2 B08 NIR Reflectance (250m)",
    "sentinel_b11_median_250m": "Sentinel-2 B11 SWIR1 Reflectance (250m)",
    "sentinel_b12_median_250m": "Sentinel-2 B12 SWIR2 Reflectance (250m)",
    "sentinel_ndvi_median_250m": "Sentinel-2 NDVI Vegetation Index (250m)",
    "sentinel_ndmi_median_250m": "Sentinel-2 NDMI Moisture Index (250m)",
    "sentinel_nbr_median_250m": "Sentinel-2 NBR Normalized Burn Ratio (250m)",
    "sentinel_b11_p90_250m": "Sentinel-2 B11 90th Percentile (250m)",
    "sentinel_b12_p90_250m": "Sentinel-2 B12 90th Percentile (250m)",
}


def get_feature_display_name(feature_name: str) -> str:
    """Return formatted display name or clean fallback."""
    if feature_name in FEATURE_DISPLAY_NAMES:
        return FEATURE_DISPLAY_NAMES[feature_name]
    spec = fusion_v1_registry.get_spec(feature_name)
    if spec:
        return spec.name.replace("_", " ").title()
    return feature_name.replace("_", " ").title()


def get_feature_unit(feature_name: str) -> str:
    """Return unit string from fusion_v1 registry."""
    spec = fusion_v1_registry.get_spec(feature_name)
    if spec and spec.unit:
        return spec.unit
    return ""


def get_feature_group(feature_name: str) -> str:
    """Return evidence group from fusion_v1 registry."""
    spec = fusion_v1_registry.get_spec(feature_name)
    if spec and spec.group:
        return spec.group
    return "UNKNOWN"


def format_raw_value(feature_name: str, raw_val: Any, unit: str = "") -> str:
    """
    Format source value into human-readable representation with appropriate units.
    Avoids printing raw unhelpful floats like 'x_47 = -1.9364' or '0' for missing data.
    """
    if raw_val is None:
        return "Unavailable"

    if isinstance(raw_val, bool):
        return "Yes" if raw_val else "No"

    if isinstance(raw_val, float):
        if "fraction" in feature_name or "ratio" in feature_name:
            pct = round(raw_val * 100.0, 1)
            return f"{pct}%"
        if unit == "MW":
            return f"{raw_val:.1f} MW"
        if unit.lower() in ("kelvin", "k"):
            return f"{raw_val:.1f} K"
        if unit.lower() in ("m", "meters"):
            if raw_val >= 1000:
                return f"{raw_val / 1000.0:.2f} km"
            return f"{round(raw_val)} m"
        if unit.lower() in ("km", "kilometers"):
            return f"{raw_val:.2f} km"
        if "index" in feature_name or "nbr" in feature_name or "ndvi" in feature_name or "ndmi" in feature_name:
            return f"{raw_val:.3f}"
        return f"{raw_val:.2f} {unit}".strip()

    if isinstance(raw_val, int):
        if unit:
            return f"{raw_val} {unit}"
        return str(raw_val)

    if isinstance(raw_val, str):
        return raw_val.replace("_", " ").title()

    return str(raw_val)


def build_raw_feature_map(
    preprocessor: ColumnTransformer,
    ordered_features: list[str],
) -> dict[str, list[int]]:
    """
    Construct exact mapping from each raw feature name to the list of column
    indices in the transformed feature matrix X_trans.
    Handles:
    - Numeric values (accounting for features dropped by SimpleImputer when
      all training values were NaN)
    - Imputer missingness indicators (SimpleImputer add_indicator=True)
    - OneHotEncoder categories (sparse_output=False)
    """
    raw_to_transformed: dict[str, list[int]] = {f: [] for f in ordered_features}
    current_col = 0

    for name, pipe, cols in preprocessor.transformers_:
        if name == "remainder" or not hasattr(pipe, "named_steps"):
            continue

        steps = pipe.named_steps
        if name == "num":
            num_cols = list(cols)
            imputer = steps.get("imputer")

            # Detect which input columns the imputer dropped (all-NaN during fit).
            # SimpleImputer sets statistics_ to NaN for features it cannot impute
            # and removes them from the output.

            dropped_input_indices: set[int] = set()
            if imputer is not None and hasattr(imputer, "statistics_"):
                for local_idx, stat_val in enumerate(imputer.statistics_):
                    try:
                        if np.isnan(stat_val):
                            dropped_input_indices.add(local_idx)
                    except (TypeError, ValueError):
                        pass

            # 1. Imputed numeric values: one column per surviving numeric input column
            for local_idx, col_spec in enumerate(num_cols):
                if local_idx in dropped_input_indices:
                    continue  # This feature was dropped by the imputer
                feat_name = ordered_features[col_spec] if isinstance(col_spec, int) else col_spec
                raw_to_transformed[feat_name].append(current_col)
                current_col += 1

            # 2. Missing indicator columns
            if imputer is not None and getattr(imputer, "indicator_", None) is not None:
                indicator_features = getattr(imputer.indicator_, "features_", [])
                for ind_col_idx in indicator_features:
                    parent_feat_name = (
                        ordered_features[num_cols[ind_col_idx]]
                        if isinstance(num_cols[ind_col_idx], int)
                        else num_cols[ind_col_idx]
                    )
                    raw_to_transformed[parent_feat_name].append(current_col)
                    current_col += 1

        elif name == "cat":
            cat_cols = list(cols)
            encoder = steps.get("encoder")
            if encoder is not None and hasattr(encoder, "categories_"):
                for c_idx, col_spec in enumerate(cat_cols):
                    feat_name = ordered_features[col_spec] if isinstance(col_spec, int) else col_spec
                    n_cats = len(encoder.categories_[c_idx])
                    for _ in range(n_cats):
                        raw_to_transformed[feat_name].append(current_col)
                        current_col += 1

    return raw_to_transformed


def aggregate_group_contributions(
    raw_contributions: list[FeatureContributionItem],
) -> dict[str, GroupContributionItem]:
    """
    Aggregate raw feature contributions into multi-modal evidence groups:
    THERMAL, TEMPORAL, INDUSTRIAL, LAND_COVER, SENTINEL.
    Computes group sums, display relative strengths, and contribution levels.
    """
    groups = ("THERMAL", "TEMPORAL", "INDUSTRIAL", "LAND_COVER", "SENTINEL")
    group_sums: dict[str, float] = {g: 0.0 for g in groups}
    group_counts: dict[str, int] = {g: 0 for g in groups}

    for item in raw_contributions:
        g = item.feature_group
        if g in group_sums:
            group_sums[g] += item.contribution
            group_counts[g] += 1

    total_abs_contribution = sum(abs(v) for v in group_sums.values())
    max_abs_contribution = max((abs(v) for v in group_sums.values()), default=0.0)

    result: dict[str, GroupContributionItem] = {}
    for g in groups:
        val = group_sums[g]
        abs_val = abs(val)

        # Direction
        if val > DIRECTION_TOLERANCE:
            direction = DIRECTION_SUPPORTS
        elif val < -DIRECTION_TOLERANCE:
            direction = DIRECTION_OPPOSES
        else:
            direction = DIRECTION_NEUTRAL

        # Relative strength share (display-only)
        rel_strength = (
            round((abs_val / total_abs_contribution) * 100.0, 1)
            if total_abs_contribution > 0
            else 0.0
        )

        # Contribution level (magnitude relative to max group)
        if max_abs_contribution > 0:
            ratio = abs_val / max_abs_contribution
            if ratio >= 0.50:
                level = CONTRIBUTION_HIGH
            elif ratio >= 0.15:
                level = CONTRIBUTION_MEDIUM
            else:
                level = CONTRIBUTION_LOW
        else:
            level = CONTRIBUTION_LOW

        result[g] = GroupContributionItem(
            group=g,
            total_contribution=round(val, 4),
            relative_strength=rel_strength,
            direction=direction,
            contribution_level=level,
            feature_count=group_counts[g],
        )

    return result
