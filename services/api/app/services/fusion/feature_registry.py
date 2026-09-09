# AGNIDRISHTI API — Phase 7 Feature Registry
"""
Central feature registry for Phase 7 Feature Fusion (fusion_v1).
Defines the canonical, versioned, machine-readable schema for all evidence features
assembled from Phases 1-6.

Strict scientific constraints:
- Canonical deterministic ordering.
- Explicit types, units, nullability, and source provenance.
- Model eligibility flag (geographic coordinates excluded from default ML features).
- Deterministic SHA-256 schema hash for strict compatibility verification.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Literal

SCHEMA_VERSION_V1 = "fusion_v1"

EvidenceGroup = Literal["THERMAL", "TEMPORAL", "INDUSTRIAL", "LAND_COVER", "SENTINEL"]
FeatureDtype = Literal["float", "int", "str", "bool"]


@dataclass(frozen=True)
class FeatureSpec:
    """Specification of an individual fused feature."""

    name: str
    group: EvidenceGroup
    source_phase: str
    source_field: str
    dtype: FeatureDtype
    unit: str
    nullable: bool
    model_eligible: bool
    description: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


# Canonical ordered list of features in fusion_v1
FUSION_V1_FEATURES: tuple[FeatureSpec, ...] = (
    # =========================================================================
    # Group 1: THERMAL (Phase 1 / NASA FIRMS)
    # =========================================================================
    FeatureSpec(
        name="thermal_frp",
        group="THERMAL",
        source_phase="phase1",
        source_field="frp",
        dtype="float",
        unit="MW",
        nullable=False,
        model_eligible=True,
        description="Fire Radiative Power in Megawatts from NASA FIRMS VIIRS/MODIS sensor.",
    ),
    FeatureSpec(
        name="thermal_brightness_ti4",
        group="THERMAL",
        source_phase="phase1",
        source_field="bright_ti4",
        dtype="float",
        unit="Kelvin",
        nullable=False,
        model_eligible=True,
        description="VIIRS I-4 thermal channel brightness temperature (3.74 um) in Kelvin.",
    ),
    FeatureSpec(
        name="thermal_brightness_ti5",
        group="THERMAL",
        source_phase="phase1",
        source_field="bright_ti5",
        dtype="float",
        unit="Kelvin",
        nullable=False,
        model_eligible=True,
        description="VIIRS I-5 thermal channel brightness temperature (11.45 um) in Kelvin.",
    ),
    FeatureSpec(
        name="thermal_scan",
        group="THERMAL",
        source_phase="phase1",
        source_field="scan",
        dtype="float",
        unit="km",
        nullable=False,
        model_eligible=True,
        description="Along-scan pixel footprint spatial dimension in kilometers.",
    ),
    FeatureSpec(
        name="thermal_track",
        group="THERMAL",
        source_phase="phase1",
        source_field="track",
        dtype="float",
        unit="km",
        nullable=False,
        model_eligible=True,
        description="Along-track pixel footprint spatial dimension in kilometers.",
    ),
    FeatureSpec(
        name="thermal_daynight",
        group="THERMAL",
        source_phase="phase1",
        source_field="daynight",
        dtype="str",
        unit="category",
        nullable=False,
        model_eligible=True,
        description="Day ('D') or Night ('N') solar illumination condition at acquisition.",
    ),
    FeatureSpec(
        name="thermal_satellite",
        group="THERMAL",
        source_phase="phase1",
        source_field="satellite",
        dtype="str",
        unit="category",
        nullable=False,
        model_eligible=True,
        description="Satellite platform identifier (e.g. 'N20', 'N21', 'Terra', 'Aqua').",
    ),
    FeatureSpec(
        name="thermal_instrument",
        group="THERMAL",
        source_phase="phase1",
        source_field="instrument",
        dtype="str",
        unit="category",
        nullable=False,
        model_eligible=True,
        description="Thermal sensor instrument name (e.g. 'VIIRS', 'MODIS').",
    ),
    FeatureSpec(
        name="thermal_confidence",
        group="THERMAL",
        source_phase="phase1",
        source_field="confidence_normalized",
        dtype="str",
        unit="category",
        nullable=False,
        model_eligible=True,
        description="Normalized detection confidence category ('nominal', 'low', 'high').",
    ),
    FeatureSpec(
        name="thermal_latitude",
        group="THERMAL",
        source_phase="phase1",
        source_field="latitude",
        dtype="float",
        unit="degrees",
        nullable=False,
        model_eligible=False,
        description="Geographic latitude (WGS84). Excluded from model features to prevent spatial memorization.",
    ),
    FeatureSpec(
        name="thermal_longitude",
        group="THERMAL",
        source_phase="phase1",
        source_field="longitude",
        dtype="float",
        unit="degrees",
        nullable=False,
        model_eligible=False,
        description="Geographic longitude (WGS84). Excluded from model features to prevent spatial memorization.",
    ),

    # =========================================================================
    # Group 2: TEMPORAL (Phase 3 / Temporal Persistence)
    # =========================================================================
    FeatureSpec(
        name="temporal_persistence_index",
        group="TEMPORAL",
        source_phase="phase3",
        source_field="persistence_index",
        dtype="int",
        unit="0_100",
        nullable=False,
        model_eligible=True,
        description="Temporal persistence index on canonical 0-100 integer scale within 750m buffer.",
    ),
    FeatureSpec(
        name="temporal_persistence_class",
        group="TEMPORAL",
        source_phase="phase3",
        source_field="persistence_class",
        dtype="str",
        unit="category",
        nullable=False,
        model_eligible=True,
        description="Recurrence classification ('PERSISTENT', 'RECURRING', 'EPISODIC', 'ISOLATED', 'INSUFFICIENT_HISTORY').",
    ),
    FeatureSpec(
        name="temporal_active_days_7d",
        group="TEMPORAL",
        source_phase="phase3",
        source_field="active_days_7d",
        dtype="int",
        unit="count",
        nullable=False,
        model_eligible=True,
        description="Distinct active UTC calendar days with thermal detection within 7-day lookback.",
    ),
    FeatureSpec(
        name="temporal_active_days_30d",
        group="TEMPORAL",
        source_phase="phase3",
        source_field="active_days_30d",
        dtype="int",
        unit="count",
        nullable=False,
        model_eligible=True,
        description="Distinct active UTC calendar days with thermal detection within 30-day lookback.",
    ),
    FeatureSpec(
        name="temporal_active_weeks_30d",
        group="TEMPORAL",
        source_phase="phase3",
        source_field="active_weeks_30d",
        dtype="int",
        unit="count",
        nullable=False,
        model_eligible=True,
        description="Distinct active ISO calendar weeks with thermal detection within 30-day lookback.",
    ),
    FeatureSpec(
        name="temporal_span_days_30d",
        group="TEMPORAL",
        source_phase="phase3",
        source_field="temporal_span_days_30d",
        dtype="float",
        unit="days",
        nullable=False,
        model_eligible=True,
        description="Temporal span in days between first and last detection within 30-day window.",
    ),
    FeatureSpec(
        name="temporal_coverage_ratio_30d",
        group="TEMPORAL",
        source_phase="phase3",
        source_field="history_coverage_ratio_30d",
        dtype="float",
        unit="ratio_0_1",
        nullable=False,
        model_eligible=True,
        description="Ratio of available FIRMS coverage days in the 30-day history window (0.0 to 1.0).",
    ),
    FeatureSpec(
        name="temporal_detection_count_30d",
        group="TEMPORAL",
        source_phase="phase3",
        source_field="raw_detection_count_30d",
        dtype="int",
        unit="count",
        nullable=False,
        model_eligible=True,
        description="Total raw thermal hotspot detection count within 750m in 30-day lookback.",
    ),

    # =========================================================================
    # Group 3: INDUSTRIAL (Phase 4 / Industrial Context)
    # =========================================================================
    FeatureSpec(
        name="industrial_context_class",
        group="INDUSTRIAL",
        source_phase="phase4",
        source_field="context_class",
        dtype="str",
        unit="category",
        nullable=False,
        model_eligible=True,
        description="Industrial proximity context strength ('NONE', 'WEAK', 'MODERATE', 'STRONG', 'DIRECT_OVERLAY').",
    ),
    FeatureSpec(
        name="industrial_coverage_status",
        group="INDUSTRIAL",
        source_phase="phase4",
        source_field="coverage_status",
        dtype="str",
        unit="category",
        nullable=False,
        model_eligible=True,
        description="OpenStreetMap industrial feature coverage quality ('ADEQUATE', 'SPARSE', 'UNAVAILABLE').",
    ),
    FeatureSpec(
        name="industrial_nearest_distance_m",
        group="INDUSTRIAL",
        source_phase="phase4",
        source_field="nearest_industrial_distance_m",
        dtype="float",
        unit="meters",
        nullable=True,
        model_eligible=True,
        description="Geodesic distance in meters to nearest OSM industrial feature (NULL if none within 5km).",
    ),
    FeatureSpec(
        name="industrial_inside_area",
        group="INDUSTRIAL",
        source_phase="phase4",
        source_field="inside_industrial_area",
        dtype="bool",
        unit="boolean",
        nullable=False,
        model_eligible=True,
        description="True if thermal coordinate falls strictly inside an OSM industrial landuse/site polygon.",
    ),
    FeatureSpec(
        name="industrial_nearest_category",
        group="INDUSTRIAL",
        source_phase="phase4",
        source_field="nearest_feature_category",
        dtype="str",
        unit="category",
        nullable=True,
        model_eligible=True,
        description="OSM primary category tag of nearest industrial feature (NULL if none within 5km).",
    ),
    FeatureSpec(
        name="industrial_feature_count_500m",
        group="INDUSTRIAL",
        source_phase="phase4",
        source_field="feature_count_500m",
        dtype="int",
        unit="count",
        nullable=False,
        model_eligible=True,
        description="Count of verified OSM industrial infrastructure features within 500m radius.",
    ),
    FeatureSpec(
        name="industrial_feature_count_1km",
        group="INDUSTRIAL",
        source_phase="phase4",
        source_field="feature_count_1km",
        dtype="int",
        unit="count",
        nullable=False,
        model_eligible=True,
        description="Count of verified OSM industrial infrastructure features within 1km radius.",
    ),
    FeatureSpec(
        name="industrial_feature_count_5km",
        group="INDUSTRIAL",
        source_phase="phase4",
        source_field="feature_count_5km",
        dtype="int",
        unit="count",
        nullable=False,
        model_eligible=True,
        description="Count of verified OSM industrial infrastructure features within 5km radius.",
    ),
    FeatureSpec(
        name="industrial_has_flare_nearby",
        group="INDUSTRIAL",
        source_phase="phase4",
        source_field="has_flare_nearby",
        dtype="bool",
        unit="boolean",
        nullable=False,
        model_eligible=True,
        description="True if an industrial flare stack is mapped within 5km radius.",
    ),
    FeatureSpec(
        name="industrial_has_chimney_nearby",
        group="INDUSTRIAL",
        source_phase="phase4",
        source_field="has_chimney_nearby",
        dtype="bool",
        unit="boolean",
        nullable=False,
        model_eligible=True,
        description="True if an industrial chimney or smokestack is mapped within 5km radius.",
    ),
    FeatureSpec(
        name="industrial_has_refinery_nearby",
        group="INDUSTRIAL",
        source_phase="phase4",
        source_field="has_refinery_nearby",
        dtype="bool",
        unit="boolean",
        nullable=False,
        model_eligible=True,
        description="True if an oil/gas refinery or chemical processing plant is mapped within 5km radius.",
    ),
    FeatureSpec(
        name="industrial_has_power_plant_nearby",
        group="INDUSTRIAL",
        source_phase="phase4",
        source_field="has_power_plant_nearby",
        dtype="bool",
        unit="boolean",
        nullable=False,
        model_eligible=True,
        description="True if an electric power plant is mapped within 5km radius.",
    ),

    # =========================================================================
    # Group 4: LAND_COVER (Phase 5 / ESA WorldCover 10m)
    # =========================================================================
    FeatureSpec(
        name="landcover_point_code",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="point_class_code",
        dtype="int",
        unit="code",
        nullable=True,
        model_eligible=True,
        description="ESA WorldCover 2021 10m pixel class code at thermal coordinate (e.g. 10, 20, 30, 40, 50).",
    ),
    FeatureSpec(
        name="landcover_point_class",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="point_class_name",
        dtype="str",
        unit="category",
        nullable=True,
        model_eligible=True,
        description="ESA WorldCover class name at point (e.g. 'CROPLAND', 'BUILT_UP', 'TREE_COVER').",
    ),
    FeatureSpec(
        name="landcover_context_class",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="context_class",
        dtype="str",
        unit="category",
        nullable=True,
        model_eligible=True,
        description="Dominant neighborhood land cover context category in 500m buffer.",
    ),
    FeatureSpec(
        name="landcover_coverage_status",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="coverage_status",
        dtype="str",
        unit="category",
        nullable=False,
        model_eligible=True,
        description="ESA WorldCover tile coverage status ('COMPLETE', 'PARTIAL', 'UNAVAILABLE').",
    ),
    FeatureSpec(
        name="landcover_dominant_class_500m",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="dominant_class_500m",
        dtype="str",
        unit="category",
        nullable=True,
        model_eligible=True,
        description="Dominant land cover class name within 500m circular buffer.",
    ),
    FeatureSpec(
        name="landcover_dominant_fraction_500m",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="dominant_fraction_500m",
        dtype="float",
        unit="ratio_0_1",
        nullable=True,
        model_eligible=True,
        description="Area fraction occupied by the dominant land cover class in 500m buffer.",
    ),
    FeatureSpec(
        name="landcover_tree_fraction_500m",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="tree_cover_fraction_500m",
        dtype="float",
        unit="ratio_0_1",
        nullable=True,
        model_eligible=True,
        description="Tree cover area fraction (Class 10) within 500m circular buffer.",
    ),
    FeatureSpec(
        name="landcover_shrub_fraction_500m",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="shrubland_fraction_500m",
        dtype="float",
        unit="ratio_0_1",
        nullable=True,
        model_eligible=True,
        description="Shrubland area fraction (Class 20) within 500m circular buffer.",
    ),
    FeatureSpec(
        name="landcover_grass_fraction_500m",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="grassland_fraction_500m",
        dtype="float",
        unit="ratio_0_1",
        nullable=True,
        model_eligible=True,
        description="Grassland area fraction (Class 30) within 500m circular buffer.",
    ),
    FeatureSpec(
        name="landcover_cropland_fraction_500m",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="cropland_fraction_500m",
        dtype="float",
        unit="ratio_0_1",
        nullable=True,
        model_eligible=True,
        description="Cropland area fraction (Class 40) within 500m circular buffer.",
    ),
    FeatureSpec(
        name="landcover_builtup_fraction_500m",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="built_up_fraction_500m",
        dtype="float",
        unit="ratio_0_1",
        nullable=True,
        model_eligible=True,
        description="Built-up / urban area fraction (Class 50) within 500m circular buffer.",
    ),
    FeatureSpec(
        name="landcover_bare_fraction_500m",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="bare_sparse_fraction_500m",
        dtype="float",
        unit="ratio_0_1",
        nullable=True,
        model_eligible=True,
        description="Bare / sparse vegetation fraction (Class 60) within 500m circular buffer.",
    ),
    FeatureSpec(
        name="landcover_water_fraction_500m",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="water_fraction_500m",
        dtype="float",
        unit="ratio_0_1",
        nullable=True,
        model_eligible=True,
        description="Permanent open water fraction (Class 80) within 500m circular buffer.",
    ),
    FeatureSpec(
        name="landcover_wetland_fraction_500m",
        group="LAND_COVER",
        source_phase="phase5",
        source_field="wetland_fraction_500m",
        dtype="float",
        unit="ratio_0_1",
        nullable=True,
        model_eligible=True,
        description="Herbaceous wetland fraction (Class 90) within 500m circular buffer.",
    ),

    # =========================================================================
    # Group 5: SENTINEL (Phase 6 / Copernicus Sentinel-2 L2A)
    # =========================================================================
    FeatureSpec(
        name="sentinel_quality_status",
        group="SENTINEL",
        source_phase="phase6",
        source_field="quality_status",
        dtype="str",
        unit="category",
        nullable=True,
        model_eligible=True,
        description="Sentinel-2 observational quality assessment ('EXCELLENT', 'GOOD', 'LIMITED', 'CLOUD_LIMITED', 'UNAVAILABLE').",
    ),
    FeatureSpec(
        name="sentinel_provider_status",
        group="SENTINEL",
        source_phase="phase6",
        source_field="provider_status",
        dtype="str",
        unit="category",
        nullable=False,
        model_eligible=True,
        description="Sentinel provider retrieval status ('AVAILABLE', 'CLOUD_LIMITED', 'PROVIDER_UNAVAILABLE', 'NO_SCENE', 'RATE_LIMITED').",
    ),
    FeatureSpec(
        name="sentinel_scene_age_days",
        group="SENTINEL",
        source_phase="phase6",
        source_field="sentinel_scene_age_days",
        dtype="float",
        unit="days",
        nullable=True,
        model_eligible=True,
        description="Elapsed days between Sentinel-2 scene acquisition and FIRMS detection (scene_time <= firms_time).",
    ),
    FeatureSpec(
        name="sentinel_valid_fraction_250m",
        group="SENTINEL",
        source_phase="phase6",
        source_field="sentinel_valid_fraction_250m",
        dtype="float",
        unit="ratio_0_1",
        nullable=True,
        model_eligible=True,
        description="Cloud-free and shadow-free valid SCL pixel fraction within 250m buffer.",
    ),
    FeatureSpec(
        name="sentinel_cloud_fraction_250m",
        group="SENTINEL",
        source_phase="phase6",
        source_field="sentinel_cloud_fraction_250m",
        dtype="float",
        unit="ratio_0_1",
        nullable=True,
        model_eligible=True,
        description="Cloud pixel fraction within 250m circular buffer.",
    ),
    FeatureSpec(
        name="sentinel_b04_median_250m",
        group="SENTINEL",
        source_phase="phase6",
        source_field="sentinel_b04_median_250m",
        dtype="float",
        unit="reflectance",
        nullable=True,
        model_eligible=True,
        description="Sentinel-2 Band 4 (Red, 665 nm) median surface reflectance in 250m buffer.",
    ),
    FeatureSpec(
        name="sentinel_b08_median_250m",
        group="SENTINEL",
        source_phase="phase6",
        source_field="sentinel_b08_median_250m",
        dtype="float",
        unit="reflectance",
        nullable=True,
        model_eligible=True,
        description="Sentinel-2 Band 8 (NIR, 842 nm) median surface reflectance in 250m buffer.",
    ),
    FeatureSpec(
        name="sentinel_b11_median_250m",
        group="SENTINEL",
        source_phase="phase6",
        source_field="sentinel_b11_median_250m",
        dtype="float",
        unit="reflectance",
        nullable=True,
        model_eligible=True,
        description="Sentinel-2 Band 11 (SWIR-1, 1610 nm) median surface reflectance in 250m buffer.",
    ),
    FeatureSpec(
        name="sentinel_b12_median_250m",
        group="SENTINEL",
        source_phase="phase6",
        source_field="sentinel_b12_median_250m",
        dtype="float",
        unit="reflectance",
        nullable=True,
        model_eligible=True,
        description="Sentinel-2 Band 12 (SWIR-2, 2190 nm) median surface reflectance in 250m buffer.",
    ),
    FeatureSpec(
        name="sentinel_ndvi_median_250m",
        group="SENTINEL",
        source_phase="phase6",
        source_field="sentinel_ndvi_median_250m",
        dtype="float",
        unit="index_minus1_to_1",
        nullable=True,
        model_eligible=True,
        description="Normalized Difference Vegetation Index (NDVI) median in 250m buffer (vegetation density/vigor).",
    ),
    FeatureSpec(
        name="sentinel_ndmi_median_250m",
        group="SENTINEL",
        source_phase="phase6",
        source_field="sentinel_ndmi_median_250m",
        dtype="float",
        unit="index_minus1_to_1",
        nullable=True,
        model_eligible=True,
        description="Normalized Difference Moisture Index (NDMI) median in 250m buffer (canopy moisture/stress).",
    ),
    FeatureSpec(
        name="sentinel_nbr_median_250m",
        group="SENTINEL",
        source_phase="phase6",
        source_field="sentinel_nbr_median_250m",
        dtype="float",
        unit="index_minus1_to_1",
        nullable=True,
        model_eligible=True,
        description="Normalized Burn Ratio (NBR) median in 250m buffer (burn severity and fire scars).",
    ),
    FeatureSpec(
        name="sentinel_b11_p90_250m",
        group="SENTINEL",
        source_phase="phase6",
        source_field="sentinel_b11_p90_250m",
        dtype="float",
        unit="reflectance",
        nullable=True,
        model_eligible=True,
        description="Sentinel-2 SWIR-1 (B11) 90th percentile reflectance (detects sub-pixel high-temperature emitters).",
    ),
    FeatureSpec(
        name="sentinel_b12_p90_250m",
        group="SENTINEL",
        source_phase="phase6",
        source_field="sentinel_b12_p90_250m",
        dtype="float",
        unit="reflectance",
        nullable=True,
        model_eligible=True,
        description="Sentinel-2 SWIR-2 (B12) 90th percentile reflectance (detects sub-pixel high-temperature emitters).",
    ),
)


class FeatureRegistry:
    """Singleton-style accessor and validator for feature registry."""

    def __init__(self, features: tuple[FeatureSpec, ...] = FUSION_V1_FEATURES) -> None:
        self._features = features
        self._name_to_spec: dict[str, FeatureSpec] = {f.name: f for f in features}
        if len(self._name_to_spec) != len(features):
            duplicates = [f.name for f in features if list(features).count(f) > 1]
            raise ValueError(f"Duplicate feature names detected in registry: {duplicates}")

        # Compute deterministic schema hash
        self._schema_hash = self._compute_schema_hash()

    def _compute_schema_hash(self) -> str:
        """Compute SHA-256 hash over canonical JSON representation of all features."""
        canonical_repr = [
            {
                "name": f.name,
                "group": f.group,
                "source_phase": f.source_phase,
                "source_field": f.source_field,
                "dtype": f.dtype,
                "unit": f.unit,
                "nullable": f.nullable,
                "model_eligible": f.model_eligible,
            }
            for f in self._features
        ]
        serialized = json.dumps(canonical_repr, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @property
    def schema_version(self) -> str:
        return SCHEMA_VERSION_V1

    @property
    def schema_hash(self) -> str:
        return self._schema_hash

    @property
    def total_feature_count(self) -> int:
        return len(self._features)

    @property
    def model_eligible_count(self) -> int:
        return sum(1 for f in self._features if f.model_eligible)

    @property
    def features(self) -> tuple[FeatureSpec, ...]:
        return self._features

    @property
    def feature_names(self) -> list[str]:
        return [f.name for f in self._features]

    @property
    def model_eligible_names(self) -> list[str]:
        return [f.name for f in self._features if f.model_eligible]

    def get_spec(self, name: str) -> FeatureSpec | None:
        return self._name_to_spec.get(name)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "schema_hash": self.schema_hash,
            "total_features": self.total_feature_count,
            "model_eligible_features": self.model_eligible_count,
            "features": [f.to_dict() for f in self._features],
        }


# Global registry instance
fusion_v1_registry = FeatureRegistry()
