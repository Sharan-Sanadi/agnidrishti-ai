# AGNIDRISHTI API — Phase 9 Explanation Provider Base & Factory
"""
Abstract base class and provider factory for model explainability.
Routes to TreeExplanationProvider for tree ensembles or LinearExplanationProvider for linear models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from sklearn.pipeline import Pipeline

from app.ml.explainability.constants import (
    METHOD_UNSUPPORTED,
    STATUS_EXPLANATION_UNAVAILABLE,
)
from app.ml.explainability.schemas import (
    FeatureContributionItem,
    GroupContributionItem,
)


@dataclass
class LocalExplanationResult:
    """Internal result container for a single observation explanation."""

    status: str
    method_name: str
    method_version: str
    predicted_class: str | None
    base_value: float | None
    explained_output: float | None
    additivity_error: float | None
    raw_feature_contributions: list[FeatureContributionItem]
    top_supporting_features: list[FeatureContributionItem]
    top_opposing_features: list[FeatureContributionItem]
    group_contributions: dict[str, GroupContributionItem]
    quality_flags: list[str]


class ExplanationProvider(ABC):
    """Abstract interface for model-faithful explanation providers."""

    @abstractmethod
    def explain_batch(
        self,
        raw_feature_matrix: list[list[Any]],
        predicted_classes: list[str],
        raw_feature_dicts: list[dict[str, Any]],
    ) -> list[LocalExplanationResult]:
        """Compute model-faithful local explanations for a batch of observations."""
        pass


class UnsupportedExplanationProvider(ExplanationProvider):
    """Fallback provider when estimator family does not support faithful attribution."""

    def explain_batch(
        self,
        raw_feature_matrix: list[list[Any]],
        predicted_classes: list[str],
        raw_feature_dicts: list[dict[str, Any]],
    ) -> list[LocalExplanationResult]:
        results: list[LocalExplanationResult] = []
        for pred_class in predicted_classes:
            results.append(
                LocalExplanationResult(
                    status=STATUS_EXPLANATION_UNAVAILABLE,
                    method_name=METHOD_UNSUPPORTED,
                    method_version="unsupported_v1",
                    predicted_class=pred_class,
                    base_value=None,
                    explained_output=None,
                    additivity_error=None,
                    raw_feature_contributions=[],
                    top_supporting_features=[],
                    top_opposing_features=[],
                    group_contributions={},
                    quality_flags=["UNSUPPORTED_ESTIMATOR_FAMILY"],
                )
            )
        return results


def get_explanation_provider(
    pipeline: Pipeline,
    ordered_features: list[str],
) -> ExplanationProvider:
    """
    Factory creating the mathematically valid ExplanationProvider for the fitted pipeline.
    Avoids guessing or forcing incompatible explanation methods.
    """
    classifier = pipeline.named_steps.get("classifier")
    preprocessor = pipeline.named_steps.get("preprocessor")

    if classifier is None or preprocessor is None:
        return UnsupportedExplanationProvider()

    classifier_type = type(classifier).__name__

    if classifier_type in (
        "HistGradientBoostingClassifier",
        "RandomForestClassifier",
        "GradientBoostingClassifier",
        "ExtraTreesClassifier",
    ):
        from app.ml.explainability.tree import TreeExplanationProvider

        return TreeExplanationProvider(pipeline, ordered_features)

    elif classifier_type in ("LogisticRegression", "SGDClassifier"):
        from app.ml.explainability.linear import LinearExplanationProvider

        return LinearExplanationProvider(pipeline, ordered_features)

    return UnsupportedExplanationProvider()
