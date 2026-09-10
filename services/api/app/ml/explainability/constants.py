# AGNIDRISHTI API — Phase 9 Explainability Constants
"""
Central constants, status enumerations, mathematical tolerances,
and display registries for Phase 9 Model Explainability Engine.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

# -----------------------------------------------------------------------------
# Versioning & Method Identifiers
# -----------------------------------------------------------------------------
EXPLANATION_VERSION: Final[str] = "agnidrishti_explainer_v1"
METHOD_TREESHAP: Final[str] = "TreeSHAP"
METHOD_LINEAR: Final[str] = "LinearContribution"
METHOD_UNSUPPORTED: Final[str] = "UnsupportedEstimator"

METHOD_VERSION_TREESHAP: Final[str] = "treeshap_v1"
METHOD_VERSION_LINEAR: Final[str] = "linear_v1"

# -----------------------------------------------------------------------------
# Explanation Statuses
# -----------------------------------------------------------------------------
STATUS_AVAILABLE: Final[str] = "AVAILABLE"
STATUS_INSUFFICIENT_EVIDENCE: Final[str] = "INSUFFICIENT_EVIDENCE"
STATUS_PREDICTION_UNAVAILABLE: Final[str] = "PREDICTION_UNAVAILABLE"
STATUS_PREDICTION_STALE: Final[str] = "PREDICTION_STALE"
STATUS_MODEL_UNAVAILABLE: Final[str] = "MODEL_UNAVAILABLE"
STATUS_MODEL_INVALID: Final[str] = "MODEL_INVALID"
STATUS_SCHEMA_MISMATCH: Final[str] = "SCHEMA_MISMATCH"
STATUS_EXPLANATION_UNAVAILABLE: Final[str] = "EXPLANATION_UNAVAILABLE"
STATUS_EXPLANATION_INVALID: Final[str] = "EXPLANATION_INVALID"
STATUS_ERROR: Final[str] = "ERROR"

ALL_EXPLANATION_STATUSES: Final[tuple[str, ...]] = (
    STATUS_AVAILABLE,
    STATUS_INSUFFICIENT_EVIDENCE,
    STATUS_PREDICTION_UNAVAILABLE,
    STATUS_PREDICTION_STALE,
    STATUS_MODEL_UNAVAILABLE,
    STATUS_MODEL_INVALID,
    STATUS_SCHEMA_MISMATCH,
    STATUS_EXPLANATION_UNAVAILABLE,
    STATUS_EXPLANATION_INVALID,
    STATUS_ERROR,
)

# -----------------------------------------------------------------------------
# Direction & Contribution Semantics
# -----------------------------------------------------------------------------
DIRECTION_SUPPORTS: Final[str] = "SUPPORTS"
DIRECTION_OPPOSES: Final[str] = "OPPOSES"
DIRECTION_NEUTRAL: Final[str] = "NEUTRAL"

# Group Contribution Strength Tiers (describing attribution magnitude only)
CONTRIBUTION_HIGH: Final[str] = "HIGH_CONTRIBUTION"
CONTRIBUTION_MEDIUM: Final[str] = "MEDIUM_CONTRIBUTION"
CONTRIBUTION_LOW: Final[str] = "LOW_CONTRIBUTION"

# -----------------------------------------------------------------------------
# Numerical Tolerances & Limits
# -----------------------------------------------------------------------------
# Additive check tolerance: abs((base + sum(contributions)) - decision_function)
ADDITIVITY_TOLERANCE: Final[float] = 1e-3
# Direction classification threshold: contribution > TOLERANCE -> SUPPORTS
DIRECTION_TOLERANCE: Final[float] = 1e-4

MAX_SUPPORTING_FEATURES: Final[int] = 5
MAX_OPPOSING_FEATURES: Final[int] = 3
MAX_BATCH_SIZE: Final[int] = 500

# -----------------------------------------------------------------------------
# Artifact Paths
# -----------------------------------------------------------------------------
PHASE9_ARTIFACT_DIR: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent / "artifacts" / "models" / "phase9"
)
GLOBAL_IMPORTANCE_FILENAME: Final[str] = "phase9_global_importance.json"
