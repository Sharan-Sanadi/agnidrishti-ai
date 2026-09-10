# AGNIDRISHTI API — Phase 9 TreeSHAP Explanation Provider
"""
Model-faithful TreeSHAP explanation provider for tree-based estimators
(HistGradientBoostingClassifier, RandomForestClassifier, GradientBoostingClassifier).
Computes exact polynomial-time Shapley values, validates mathematical additive identity,
and aggregates transformed one-hot/imputer features back to raw evidence features.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import shap
from sklearn.pipeline import Pipeline

from app.ml.explainability.constants import (
    ADDITIVITY_TOLERANCE,
    DIRECTION_NEUTRAL,
    DIRECTION_OPPOSES,
    DIRECTION_SUPPORTS,
    DIRECTION_TOLERANCE,
    MAX_OPPOSING_FEATURES,
    MAX_SUPPORTING_FEATURES,
    METHOD_TREESHAP,
    METHOD_VERSION_TREESHAP,
    STATUS_AVAILABLE,
    STATUS_EXPLANATION_INVALID,
)
from app.ml.explainability.mapping import (
    aggregate_group_contributions,
    build_raw_feature_map,
    format_raw_value,
    get_feature_display_name,
    get_feature_group,
    get_feature_unit,
)
from app.ml.explainability.provider import ExplanationProvider, LocalExplanationResult
from app.ml.explainability.schemas import FeatureContributionItem

logger = logging.getLogger(__name__)


class TreeExplanationProvider(ExplanationProvider):
    """
    TreeSHAP explanation provider using shap.TreeExplainer.
    Guarantees:
    - Additive local accuracy: base_value + sum(contributions) == decision_function margin.
    - Class-specific attributions matching the exact predicted class index.
    - Deterministic raw feature aggregation.
    """

    def __init__(self, pipeline: Pipeline, ordered_features: list[str]) -> None:
        self.pipeline = pipeline
        self.ordered_features = ordered_features
        self.preprocessor = pipeline.named_steps["preprocessor"]
        self.classifier = pipeline.named_steps["classifier"]

        # Cache class index mapping
        raw_classes = getattr(self.classifier, "classes_", [])
        self.classes: list[str] = [str(c) for c in raw_classes]
        self.class_to_idx: dict[str, int] = {c: idx for idx, c in enumerate(self.classes)}

        # Precompute transformed feature mapping
        self.raw_to_trans = build_raw_feature_map(self.preprocessor, self.ordered_features)

        # Initialize TreeExplainer once
        self.explainer = shap.TreeExplainer(self.classifier)

    def explain_batch(
        self,
        raw_feature_matrix: list[list[Any]],
        predicted_classes: list[str],
        raw_feature_dicts: list[dict[str, Any]],
    ) -> list[LocalExplanationResult]:
        if not raw_feature_matrix:
            return []

        x_raw = np.array(raw_feature_matrix, dtype=object)
        x_trans = self.preprocessor.transform(x_raw)
        margins = self.classifier.decision_function(x_trans)

        shap_exp = self.explainer(x_trans)
        shap_values = shap_exp.values  # Shape: (N, n_transformed_features, n_classes)
        expected_values = np.array(self.explainer.expected_value)  # Shape: (n_classes,)

        results: list[LocalExplanationResult] = []

        for i, pred_class in enumerate(predicted_classes):
            class_idx = self.class_to_idx.get(pred_class)
            raw_dict = raw_feature_dicts[i] if i < len(raw_feature_dicts) else {}

            if class_idx is None:
                results.append(
                    LocalExplanationResult(
                        status=STATUS_EXPLANATION_INVALID,
                        method_name=METHOD_TREESHAP,
                        method_version=METHOD_VERSION_TREESHAP,
                        predicted_class=pred_class,
                        base_value=None,
                        explained_output=None,
                        additivity_error=None,
                        raw_feature_contributions=[],
                        top_supporting_features=[],
                        top_opposing_features=[],
                        group_contributions={},
                        quality_flags=["UNKNOWN_PREDICTED_CLASS"],
                    )
                )
                continue

            base_val = float(expected_values[class_idx])
            sample_shap = shap_values[i, :, class_idx]
            sample_margin = float(margins[i, class_idx])

            # 1. Additive identity validation
            sum_trans_shap = float(np.sum(sample_shap))
            additivity_error = abs((base_val + sum_trans_shap) - sample_margin)

            quality_flags: list[str] = []
            status = STATUS_AVAILABLE

            if additivity_error > ADDITIVITY_TOLERANCE:
                status = STATUS_EXPLANATION_INVALID
                quality_flags.append("ADDITIVITY_WARNING")
                logger.warning(
                    "TreeSHAP additivity check failed! base: %s, sum_shap: %s, margin: %s, diff: %s",
                    base_val,
                    sum_trans_shap,
                    sample_margin,
                    additivity_error,
                )

            # 2. Aggregate transformed attributions to raw features
            raw_contributions_map: dict[str, float] = {}
            for feat_name in self.ordered_features:
                col_indices = self.raw_to_trans.get(feat_name, [])
                if col_indices:
                    raw_contributions_map[feat_name] = float(np.sum(sample_shap[col_indices]))
                else:
                    raw_contributions_map[feat_name] = 0.0

            total_abs_phi = sum(abs(v) for v in raw_contributions_map.values())

            # 3. Build FeatureContributionItems
            all_items: list[FeatureContributionItem] = []
            for feat_name in self.ordered_features:
                phi = raw_contributions_map[feat_name]
                raw_val = raw_dict.get(feat_name)
                unit = get_feature_unit(feat_name)
                disp_val = format_raw_value(feat_name, raw_val, unit)
                disp_name = get_feature_display_name(feat_name)
                grp = get_feature_group(feat_name)

                # Direction
                if phi > DIRECTION_TOLERANCE:
                    direction = DIRECTION_SUPPORTS
                elif phi < -DIRECTION_TOLERANCE:
                    direction = DIRECTION_OPPOSES
                else:
                    direction = DIRECTION_NEUTRAL

                # Relative contribution percentage share (display only)
                rel_pct = (
                    round((abs(phi) / total_abs_phi) * 100.0, 1)
                    if total_abs_phi > 0
                    else 0.0
                )

                item = FeatureContributionItem(
                    feature_name=feat_name,
                    display_name=disp_name,
                    feature_group=grp,
                    raw_value=raw_val,
                    display_value=disp_val,
                    unit=unit,
                    contribution=round(phi, 4),
                    relative_strength=rel_pct,
                    direction=direction,
                    rank=0,
                )
                all_items.append(item)

            # 4. Extract Top Supporting Features
            supporting_candidates = [it for it in all_items if it.direction == DIRECTION_SUPPORTS]
            supporting_candidates.sort(key=lambda x: (-x.contribution, x.feature_name))
            top_supporting: list[FeatureContributionItem] = []
            for r, it in enumerate(supporting_candidates[:MAX_SUPPORTING_FEATURES], start=1):
                top_supporting.append(
                    FeatureContributionItem(
                        feature_name=it.feature_name,
                        display_name=it.display_name,
                        feature_group=it.feature_group,
                        raw_value=it.raw_value,
                        display_value=it.display_value,
                        unit=it.unit,
                        contribution=it.contribution,
                        relative_strength=it.relative_strength,
                        direction=it.direction,
                        rank=r,
                    )
                )

            # 5. Extract Top Opposing Features
            opposing_candidates = [it for it in all_items if it.direction == DIRECTION_OPPOSES]
            opposing_candidates.sort(key=lambda x: (x.contribution, x.feature_name))
            top_opposing: list[FeatureContributionItem] = []
            for r, it in enumerate(opposing_candidates[:MAX_OPPOSING_FEATURES], start=1):
                top_opposing.append(
                    FeatureContributionItem(
                        feature_name=it.feature_name,
                        display_name=it.display_name,
                        feature_group=it.feature_group,
                        raw_value=it.raw_value,
                        display_value=it.display_value,
                        unit=it.unit,
                        contribution=it.contribution,
                        relative_strength=it.relative_strength,
                        direction=it.direction,
                        rank=r,
                    )
                )

            # 6. Aggregate Group Contributions
            group_contribs = aggregate_group_contributions(all_items)

            results.append(
                LocalExplanationResult(
                    status=status,
                    method_name=METHOD_TREESHAP,
                    method_version=METHOD_VERSION_TREESHAP,
                    predicted_class=pred_class,
                    base_value=round(base_val, 4),
                    explained_output=round(sample_margin, 4),
                    additivity_error=round(additivity_error, 6),
                    raw_feature_contributions=all_items,
                    top_supporting_features=top_supporting,
                    top_opposing_features=top_opposing,
                    group_contributions=group_contribs,
                    quality_flags=quality_flags,
                )
            )

        return results
