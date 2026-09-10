# AGNIDRISHTI API — Phase 9 Linear Model Explanation Provider
"""
Exact transformed-space additive contribution provider for linear classifiers
(LogisticRegression, SGDClassifier).
Guarantees base_value + sum(contributions) == decision_function margin.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.pipeline import Pipeline

from app.ml.explainability.constants import (
    ADDITIVITY_TOLERANCE,
    DIRECTION_NEUTRAL,
    DIRECTION_OPPOSES,
    DIRECTION_SUPPORTS,
    DIRECTION_TOLERANCE,
    MAX_OPPOSING_FEATURES,
    MAX_SUPPORTING_FEATURES,
    METHOD_LINEAR,
    METHOD_VERSION_LINEAR,
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


class LinearExplanationProvider(ExplanationProvider):
    """
    Exact linear model feature attribution provider.
    Computes transformed feature contributions as x_j * w_{c, j} and base value b_c.
    """

    def __init__(self, pipeline: Pipeline, ordered_features: list[str]) -> None:
        self.pipeline = pipeline
        self.ordered_features = ordered_features
        self.preprocessor = pipeline.named_steps["preprocessor"]
        self.classifier = pipeline.named_steps["classifier"]

        raw_classes = getattr(self.classifier, "classes_", [])
        self.classes: list[str] = [str(c) for c in raw_classes]
        self.class_to_idx: dict[str, int] = {c: idx for idx, c in enumerate(self.classes)}
        self.raw_to_trans = build_raw_feature_map(self.preprocessor, self.ordered_features)

        coef = getattr(self.classifier, "coef_", None)
        intercept = getattr(self.classifier, "intercept_", None)

        # Binary classifiers store coef_ as (1, n_features) and intercept_ as (1,).
        # Expand to OvR representation: class_0 = -w, class_1 = +w
        if coef is not None and coef.shape[0] == 1 and len(self.classes) == 2:
            self.coef = np.vstack([-coef, coef])
            self.intercept = np.array([-intercept[0], intercept[0]]) if intercept is not None else None
        else:
            self.coef = coef
            self.intercept = intercept

    def explain_batch(
        self,
        raw_feature_matrix: list[list[Any]],
        predicted_classes: list[str],
        raw_feature_dicts: list[dict[str, Any]],
    ) -> list[LocalExplanationResult]:
        if not raw_feature_matrix or self.coef is None:
            return []

        x_raw = np.array(raw_feature_matrix, dtype=object)
        x_trans = self.preprocessor.transform(x_raw)
        margins = self.classifier.decision_function(x_trans)
        if margins.ndim == 1:
            margins = np.vstack([-margins, margins]).T

        results: list[LocalExplanationResult] = []

        for i, pred_class in enumerate(predicted_classes):
            class_idx = self.class_to_idx.get(pred_class)
            raw_dict = raw_feature_dicts[i] if i < len(raw_feature_dicts) else {}

            if class_idx is None:
                results.append(
                    LocalExplanationResult(
                        status=STATUS_EXPLANATION_INVALID,
                        method_name=METHOD_LINEAR,
                        method_version=METHOD_VERSION_LINEAR,
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

            base_val = float(self.intercept[class_idx]) if self.intercept is not None else 0.0
            weights = self.coef[class_idx]
            x_row = x_trans[i]
            trans_contribs = x_row * weights
            sample_margin = float(margins[i, class_idx])

            # Additive validation
            sum_trans = float(np.sum(trans_contribs))
            additivity_error = abs((base_val + sum_trans) - sample_margin)

            status = STATUS_AVAILABLE
            quality_flags: list[str] = []
            if additivity_error > ADDITIVITY_TOLERANCE:
                status = STATUS_EXPLANATION_INVALID
                quality_flags.append("ADDITIVITY_WARNING")

            # Aggregate to raw features
            raw_contributions_map: dict[str, float] = {}
            for feat_name in self.ordered_features:
                col_indices = self.raw_to_trans.get(feat_name, [])
                if col_indices:
                    raw_contributions_map[feat_name] = float(np.sum(trans_contribs[col_indices]))
                else:
                    raw_contributions_map[feat_name] = 0.0

            total_abs_phi = sum(abs(v) for v in raw_contributions_map.values())

            all_items: list[FeatureContributionItem] = []
            for feat_name in self.ordered_features:
                phi = raw_contributions_map[feat_name]
                raw_val = raw_dict.get(feat_name)
                unit = get_feature_unit(feat_name)
                disp_val = format_raw_value(feat_name, raw_val, unit)
                disp_name = get_feature_display_name(feat_name)
                grp = get_feature_group(feat_name)

                if phi > DIRECTION_TOLERANCE:
                    direction = DIRECTION_SUPPORTS
                elif phi < -DIRECTION_TOLERANCE:
                    direction = DIRECTION_OPPOSES
                else:
                    direction = DIRECTION_NEUTRAL

                rel_pct = (
                    round((abs(phi) / total_abs_phi) * 100.0, 1)
                    if total_abs_phi > 0
                    else 0.0
                )

                all_items.append(
                    FeatureContributionItem(
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
                )

            # Top supporting
            supporting = [it for it in all_items if it.direction == DIRECTION_SUPPORTS]
            supporting.sort(key=lambda x: (-x.contribution, x.feature_name))
            top_supporting = [
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
                for r, it in enumerate(supporting[:MAX_SUPPORTING_FEATURES], start=1)
            ]

            # Top opposing
            opposing = [it for it in all_items if it.direction == DIRECTION_OPPOSES]
            opposing.sort(key=lambda x: (x.contribution, x.feature_name))
            top_opposing = [
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
                for r, it in enumerate(opposing[:MAX_OPPOSING_FEATURES], start=1)
            ]

            group_contribs = aggregate_group_contributions(all_items)

            results.append(
                LocalExplanationResult(
                    status=status,
                    method_name=METHOD_LINEAR,
                    method_version=METHOD_VERSION_LINEAR,
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
