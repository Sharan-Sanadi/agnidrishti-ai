# AGNIDRISHTI API — Phase 9 Explainability Package
"""
Phase 9 Model Explainability package exports.
"""

from app.ml.explainability.constants import (
    EXPLANATION_VERSION,
    METHOD_LINEAR,
    METHOD_TREESHAP,
    STATUS_AVAILABLE,
    STATUS_ERROR,
    STATUS_EXPLANATION_INVALID,
    STATUS_EXPLANATION_UNAVAILABLE,
    STATUS_INSUFFICIENT_EVIDENCE,
    STATUS_MODEL_INVALID,
    STATUS_MODEL_UNAVAILABLE,
    STATUS_PREDICTION_STALE,
    STATUS_PREDICTION_UNAVAILABLE,
    STATUS_SCHEMA_MISMATCH,
)
from app.ml.explainability.global_importance import global_importance_manager
from app.ml.explainability.provider import (
    ExplanationProvider,
    LocalExplanationResult,
    get_explanation_provider,
)
from app.ml.explainability.schemas import (
    BatchExplanationRequest,
    BatchExplanationResponse,
    FeatureContributionItem,
    GlobalExplanationResponse,
    GlobalFeatureImportanceItem,
    GroupContributionItem,
    LocalExplanationResponse,
    SyncExplanationRequest,
    SyncExplanationResponse,
)
from app.ml.explainability.service import (
    ExplainabilityService,
    explainability_service,
)

__all__ = [
    "EXPLANATION_VERSION",
    "METHOD_TREESHAP",
    "METHOD_LINEAR",
    "STATUS_AVAILABLE",
    "STATUS_INSUFFICIENT_EVIDENCE",
    "STATUS_PREDICTION_UNAVAILABLE",
    "STATUS_PREDICTION_STALE",
    "STATUS_MODEL_UNAVAILABLE",
    "STATUS_MODEL_INVALID",
    "STATUS_SCHEMA_MISMATCH",
    "STATUS_EXPLANATION_UNAVAILABLE",
    "STATUS_EXPLANATION_INVALID",
    "STATUS_ERROR",
    "ExplanationProvider",
    "LocalExplanationResult",
    "get_explanation_provider",
    "FeatureContributionItem",
    "GroupContributionItem",
    "LocalExplanationResponse",
    "BatchExplanationRequest",
    "BatchExplanationResponse",
    "SyncExplanationRequest",
    "SyncExplanationResponse",
    "GlobalFeatureImportanceItem",
    "GlobalExplanationResponse",
    "global_importance_manager",
    "ExplainabilityService",
    "explainability_service",
]
