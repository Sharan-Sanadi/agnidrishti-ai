# AGNIDRISHTI API — Phase 8 Classification Constants
"""
Central constants, canonical class definitions, status enumerations,
and security guardrails for Phase 8 Intelligent Classification Engine.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

# -----------------------------------------------------------------------------
# Canonical Classification Targets (Thermal Context Archetypes)
# -----------------------------------------------------------------------------
CLASS_INDUSTRIAL: Final[str] = "INDUSTRIAL_THERMAL_CONTEXT"
CLASS_AGRICULTURAL: Final[str] = "AGRICULTURAL_THERMAL_CONTEXT"
CLASS_NATURAL_VEGETATION: Final[str] = "NATURAL_VEGETATION_THERMAL_CONTEXT"
CLASS_BUILT_NON_INDUSTRIAL: Final[str] = "BUILT_NON_INDUSTRIAL_CONTEXT"
CLASS_MIXED: Final[str] = "MIXED_THERMAL_CONTEXT"
CLASS_INSUFFICIENT_EVIDENCE: Final[str] = "INSUFFICIENT_EVIDENCE"

# All 5 trainable archetype classes (INSUFFICIENT_EVIDENCE is an inference gating state, not a training label)
TRAINABLE_CLASSES: Final[tuple[str, ...]] = (
    CLASS_INDUSTRIAL,
    CLASS_AGRICULTURAL,
    CLASS_NATURAL_VEGETATION,
    CLASS_BUILT_NON_INDUSTRIAL,
    CLASS_MIXED,
)

ALL_CLASSES: Final[tuple[str, ...]] = (
    *TRAINABLE_CLASSES,
    CLASS_INSUFFICIENT_EVIDENCE,
)

# -----------------------------------------------------------------------------
# Classification & Validation Statuses
# -----------------------------------------------------------------------------
STATUS_AVAILABLE: Final[str] = "AVAILABLE"
STATUS_INSUFFICIENT_EVIDENCE: Final[str] = "INSUFFICIENT_EVIDENCE"
STATUS_MODEL_UNAVAILABLE: Final[str] = "MODEL_UNAVAILABLE"
STATUS_MODEL_INVALID: Final[str] = "MODEL_INVALID"
STATUS_SCHEMA_MISMATCH: Final[str] = "SCHEMA_MISMATCH"
STATUS_ERROR: Final[str] = "ERROR"

ALL_CLASSIFICATION_STATUSES: Final[tuple[str, ...]] = (
    STATUS_AVAILABLE,
    STATUS_INSUFFICIENT_EVIDENCE,
    STATUS_MODEL_UNAVAILABLE,
    STATUS_MODEL_INVALID,
    STATUS_SCHEMA_MISMATCH,
    STATUS_ERROR,
)

# Model Validation Status Tiers
VALIDATION_WEAK_SUPERVISION: Final[str] = "WEAK_SUPERVISION_PROTOTYPE"
VALIDATION_LIMITED_VERIFIED: Final[str] = "LIMITED_VERIFIED_VALIDATION"
VALIDATION_VERIFIED: Final[str] = "VERIFIED_VALIDATION"

# Label Provenance Tiers
PROVENANCE_VERIFIED: Final[str] = "VERIFIED"
PROVENANCE_WEAK_HIGH_CONFIDENCE: Final[str] = "WEAK_HIGH_CONFIDENCE"
PROVENANCE_UNLABELED: Final[str] = "UNLABELED"

# -----------------------------------------------------------------------------
# Anti-Circularity & Leakage Guardrails (Strategy A)
# -----------------------------------------------------------------------------
# Direct categorical fields used to define weak labeling functions MUST be excluded
# from model features during weak-supervised training to prevent circular evaluation.
STRATEGY_A_EXCLUDED_CATEGORICALS: Final[tuple[str, ...]] = (
    "industrial_context_class",
    "landcover_context_class",
    "landcover_dominant_class_500m",
    "landcover_point_class",
)

# Strictly forbidden features: identifiers, raw coordinates, absolute timestamps,
# metadata IDs, URLs, and label provenance.
FORBIDDEN_MODEL_FEATURES: Final[tuple[str, ...]] = (
    "observation_id",
    "latitude",
    "longitude",
    "lat",
    "lon",
    "acquisition_time_utc",
    "timestamp",
    "scene_id",
    "osm_uid",
    "tile_id",
    "source_url",
    "id",
    "label_provenance",
    "label",
    "label_source",
    "schema_version",
)

# -----------------------------------------------------------------------------
# Operational Thresholds & Defaults
# -----------------------------------------------------------------------------
RANDOM_SEED: Final[int] = 42
MIN_MODEL_FEATURE_COVERAGE: Final[float] = 0.40  # Minimum 40% non-null model features
MIN_CLASS_SUPPORT: Final[int] = 20               # Minimum samples per trainable class
MODEL_VERSION: Final[str] = "agnidrishti_context_classifier_v1"
LABEL_VERSION: Final[str] = "label_v1"

# Spatial grouping resolution (approx. 5 km grid in degrees: 0.045 deg ~= 5 km at equator)
SPATIAL_GRID_DEGREES: Final[float] = 0.045

# Server-side model artifact storage paths
ARTIFACT_DIR: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent / "artifacts" / "models" / "phase8"
)
MODEL_ARTIFACT_FILENAME: Final[str] = f"{MODEL_VERSION}.joblib"
MANIFEST_FILENAME: Final[str] = "phase8_classifier_manifest.json"
