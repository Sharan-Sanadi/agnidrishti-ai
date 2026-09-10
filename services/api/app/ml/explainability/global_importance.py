# AGNIDRISHTI API — Phase 9 Global Feature Importance Manager
"""
Loader and caching manager for global model feature importance.
Reads precomputed, deterministic permutation importance generated on held-out test data.
Zero retraining; zero runtime overhead.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from app.ml.explainability.constants import (
    EXPLANATION_VERSION,
    GLOBAL_IMPORTANCE_FILENAME,
    PHASE9_ARTIFACT_DIR,
)
from app.ml.explainability.schemas import (
    GlobalExplanationResponse,
    GlobalFeatureImportanceItem,
)

logger = logging.getLogger(__name__)


class GlobalImportanceManager:
    """Manages cached global model feature importance artifact."""

    _instance: GlobalImportanceManager | None = None
    _cached_report: GlobalExplanationResponse | None = None

    def __new__(cls) -> GlobalImportanceManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
        cls._cached_report = None

    def _load(self) -> None:
        file_path = PHASE9_ARTIFACT_DIR / GLOBAL_IMPORTANCE_FILENAME
        if not file_path.exists():
            logger.info("Global importance artifact not found at %s", file_path)
            self._cached_report = None
            return

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            top_features = [
                GlobalFeatureImportanceItem(
                    feature_name=item["feature_name"],
                    display_name=item["display_name"],
                    feature_group=item["feature_group"],
                    importance_mean=item["importance_mean"],
                    importance_std=item["importance_std"],
                    rank=item["rank"],
                )
                for item in data.get("top_features", [])
            ]

            self._cached_report = GlobalExplanationResponse(
                model_version=data.get("model_version", "agnidrishti_context_classifier_v1"),
                explanation_version=data.get("explanation_version", EXPLANATION_VERSION),
                validation_status=data.get("validation_status", "WEAK_SUPERVISION_PROTOTYPE"),
                scoring_metric=data.get("scoring_metric", "macro_f1"),
                dataset_fingerprint=data.get("dataset_fingerprint", ""),
                top_features=top_features,
                feature_groups=data.get("feature_groups", {}),
                computed_at=datetime.fromisoformat(data["computed_at"])
                if "computed_at" in data
                else datetime.now(UTC),
                random_seed=data.get("random_seed", 42),
                evaluation_split=data.get("evaluation_split", "test"),
            )
            logger.info("Loaded global feature importance report: %d features", len(top_features))
        except Exception as e:
            logger.error("Failed to parse global feature importance artifact: %s", e)
            self._cached_report = None

    @property
    def report(self) -> GlobalExplanationResponse | None:
        if self._cached_report is None:
            self._load()
        return self._cached_report


global_importance_manager = GlobalImportanceManager()
