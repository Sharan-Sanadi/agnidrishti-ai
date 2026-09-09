# AGNIDRISHTI API — Phase 8 Classification Schemas
"""
Pydantic schemas for Phase 8 Intelligent Classification API requests, responses, and manifests.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ClassificationPredictionResponse(BaseModel):
    """Classification prediction payload for a single thermal observation."""

    observation_id: str = Field(..., description="Canonical firms_* observation identifier")
    classification_status: str = Field(
        ...,
        description="Status: AVAILABLE, INSUFFICIENT_EVIDENCE, MODEL_UNAVAILABLE, MODEL_INVALID, SCHEMA_MISMATCH, ERROR",
    )
    predicted_class: str | None = Field(
        None,
        description="Predicted archetype class (e.g. INDUSTRIAL_THERMAL_CONTEXT, AGRICULTURAL_THERMAL_CONTEXT)",
    )
    class_score: float | None = Field(
        None,
        description="Support score/probability for predicted class (0.0 to 1.0)",
    )
    class_probabilities: dict[str, float] | None = Field(
        None,
        description="Calibrated model probabilities across all trainable context classes",
    )
    evidence_coverage: float | None = Field(
        None,
        description="Fraction of available model features (0.0 to 1.0)",
    )
    validation_status: str = Field(
        ...,
        description="Validation rigor tier: WEAK_SUPERVISION_PROTOTYPE, LIMITED_VERIFIED_VALIDATION, VERIFIED_VALIDATION",
    )
    model_version: str = Field(..., description="Model version identifier")
    fusion_schema_version: str = Field(..., description="Upstream fusion schema version (fusion_v1)")
    fusion_schema_hash: str = Field(..., description="SHA-256 hash of canonical fusion_v1 registry")
    fusion_source_fingerprint: str = Field(..., description="SHA-256 source fingerprint of observation data")
    predicted_at: datetime = Field(..., description="Timestamp when prediction was generated")


class BatchClassificationRequest(BaseModel):
    """Batch classification retrieval request payload."""

    observation_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="List of canonical observation IDs to retrieve (max 500)",
    )
    model_version: str = Field(
        default="agnidrishti_context_classifier_v1",
        description="Requested model version",
    )


class BatchClassificationResponse(BaseModel):
    """Batch classification response envelope."""

    model_version: str = Field(..., description="Model version identifier")
    count: int = Field(..., description="Number of predictions retrieved")
    predictions: dict[str, ClassificationPredictionResponse] = Field(
        ...,
        description="Map of observation_id -> ClassificationPredictionResponse",
    )


class SyncClassificationRequest(BaseModel):
    """Sync classification request payload."""

    observation_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="List of canonical observation IDs to classify and persist (max 500)",
    )
    force_recompute: bool = Field(
        default=False,
        description="If True, recompute prediction even if source fingerprint is unchanged",
    )


class SyncClassificationResponse(BaseModel):
    """Sync execution metrics response."""

    requested: int = Field(..., description="Number of observation IDs requested")
    created: int = Field(..., description="Number of new predictions persisted in PostGIS")
    updated: int = Field(..., description="Number of existing predictions updated")
    reused: int = Field(..., description="Number of predictions reused without modification")
    available: int = Field(..., description="Count of observations with status AVAILABLE")
    insufficient_evidence: int = Field(..., description="Count of observations with status INSUFFICIENT_EVIDENCE")
    class_distribution: dict[str, int] = Field(
        ...,
        description="Count of predictions per archetype class in this sync batch",
    )
    duration_ms: float = Field(..., description="Total execution duration in milliseconds")
    database_queries: int = Field(..., description="Approximate number of database queries executed")


class ModelMetadataResponse(BaseModel):
    """Detailed model manifest and evaluation metadata."""

    model_version: str = Field(..., description="Model version identifier")
    model_family: str = Field(..., description="Algorithm family (e.g. RandomForestClassifier, HistGradientBoostingClassifier)")
    validation_status: str = Field(..., description="Validation tier (e.g. WEAK_SUPERVISION_PROTOTYPE)")
    trained_at: datetime = Field(..., description="Timestamp when model training completed")
    fusion_schema_version: str = Field(..., description="Associated fusion schema version")
    fusion_schema_hash: str = Field(..., description="Associated fusion schema hash")
    training_dataset_fingerprint: str = Field(..., description="SHA-256 fingerprint of training dataset snapshot")
    classes: list[str] = Field(..., description="List of trained target archetype classes")
    features: list[str] = Field(..., description="Ordered list of model input features")
    metrics: dict[str, Any] = Field(..., description="Evaluation metrics (Macro F1, per-class F1, confusion matrix)")
    artifact_hash: str = Field(..., description="Cryptographic SHA-256 hash of joblib artifact")


class ClassMetric(BaseModel):
    """Per-class performance evaluation metrics."""

    precision: float = Field(..., description="Precision score for this class")
    recall: float = Field(..., description="Recall score for this class")
    f1_score: float = Field(..., description="F1-score for this class")
    support: int = Field(..., description="Number of evaluation samples for this class")


class MetricsSummary(BaseModel):
    """Overall model evaluation metrics summary."""

    macro_f1: float = Field(..., description="Unweighted Macro-averaged F1 score")
    weighted_f1: float = Field(..., description="Support-weighted F1 score")
    balanced_accuracy: float = Field(..., description="Balanced accuracy score across classes")
    per_class: dict[str, ClassMetric] = Field(..., description="Metrics broken down per class")
    confusion_matrix: dict[str, dict[str, int]] = Field(..., description="Confusion matrix representation")
    class_names: list[str] = Field(..., description="Ordered list of evaluated class names")
    total_eval_samples: int = Field(..., description="Total number of evaluated samples")
    evaluation_type: str = Field(..., description="Evaluation semantics: WEAK-LABEL AGREEMENT or VERIFIED TEST PERFORMANCE")


class ClassifierManifest(BaseModel):
    """Model storage manifest for server-side persistence and cryptographic verification."""

    model_version: str
    model_family: str
    model_artifact_filename: str
    model_artifact_hash: str
    model_artifact_size_bytes: int
    fusion_schema_version: str
    fusion_schema_hash: str
    training_dataset_fingerprint: str
    classes: list[str]
    ordered_features: list[str]
    validation_status: str
    metrics: dict[str, Any]
    trained_at: str
    random_seed: int
    python_version: str
    sklearn_version: str
