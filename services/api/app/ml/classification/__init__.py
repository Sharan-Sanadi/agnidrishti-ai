# AGNIDRISHTI API — Phase 8 ML Classification Package
"""
Phase 8 Intelligent Classification Engine package.
Provides weak supervision labeling, leakage-safe dataset assembly,
spatial grouped splitting, candidate model training, cryptographic artifact registry,
and network-isolated inference service.
"""

from app.ml.classification.constants import (
    ALL_CLASSES,
    CLASS_AGRICULTURAL,
    CLASS_BUILT_NON_INDUSTRIAL,
    CLASS_INDUSTRIAL,
    CLASS_INSUFFICIENT_EVIDENCE,
    CLASS_MIXED,
    CLASS_NATURAL_VEGETATION,
    MIN_MODEL_FEATURE_COVERAGE,
    MODEL_VERSION,
    STATUS_AVAILABLE,
    STATUS_INSUFFICIENT_EVIDENCE,
    STATUS_MODEL_INVALID,
    STATUS_MODEL_UNAVAILABLE,
    STATUS_SCHEMA_MISMATCH,
    TRAINABLE_CLASSES,
    VALIDATION_WEAK_SUPERVISION,
)
from app.ml.classification.labeling import LabelAssignment, WeakLabelerV1
from app.ml.classification.registry import ModelRegistry, model_registry
from app.ml.classification.schemas import (
    BatchClassificationRequest,
    BatchClassificationResponse,
    ClassificationPredictionResponse,
    ClassifierManifest,
    ModelMetadataResponse,
    SyncClassificationRequest,
    SyncClassificationResponse,
)
from app.ml.classification.service import ClassificationService, classification_service

__all__ = [
    "ALL_CLASSES",
    "CLASS_AGRICULTURAL",
    "CLASS_BUILT_NON_INDUSTRIAL",
    "CLASS_INDUSTRIAL",
    "CLASS_INSUFFICIENT_EVIDENCE",
    "CLASS_MIXED",
    "CLASS_NATURAL_VEGETATION",
    "MIN_MODEL_FEATURE_COVERAGE",
    "MODEL_VERSION",
    "STATUS_AVAILABLE",
    "STATUS_INSUFFICIENT_EVIDENCE",
    "STATUS_MODEL_INVALID",
    "STATUS_MODEL_UNAVAILABLE",
    "STATUS_SCHEMA_MISMATCH",
    "TRAINABLE_CLASSES",
    "VALIDATION_WEAK_SUPERVISION",
    "LabelAssignment",
    "WeakLabelerV1",
    "ModelRegistry",
    "model_registry",
    "BatchClassificationRequest",
    "BatchClassificationResponse",
    "ClassificationPredictionResponse",
    "ClassifierManifest",
    "ModelMetadataResponse",
    "SyncClassificationRequest",
    "SyncClassificationResponse",
    "ClassificationService",
    "classification_service",
]
