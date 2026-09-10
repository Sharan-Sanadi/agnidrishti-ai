# AGNIDRISHTI API — Phase 9 Additive Identity Unit Tests
"""
Mandatory mathematical validation tests for TreeSHAP and Linear explanation providers.
Verifies that base_value + sum(contributions) == decision_function margin within tolerance.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.ml.classification.pipeline import build_preprocessor
from app.ml.classification.registry import model_registry
from app.ml.explainability.constants import ADDITIVITY_TOLERANCE
from app.ml.explainability.linear import LinearExplanationProvider
from app.ml.explainability.provider import get_explanation_provider


def test_tree_shap_additive_identity_on_frozen_model():
    """Verify exact TreeSHAP additive identity on the frozen Phase-8 model artifact."""
    pipeline = model_registry.model
    manifest = model_registry.manifest
    assert pipeline is not None
    assert manifest is not None

    ordered_features = manifest.ordered_features
    provider = get_explanation_provider(pipeline, ordered_features)

    # Construct two distinct test vectors
    row_1 = [None] * len(ordered_features)
    # Give some realistic values
    row_1[0] = 25.0  # frp
    row_1[1] = 310.0  # ti4
    row_1[2] = 295.0  # ti5
    row_1[9] = 1.0  # persistence_index
    row_1[18] = 450.0  # nearest_distance_m
    row_1[34] = 0.85  # cropland fraction

    row_2 = [None] * len(ordered_features)
    row_2[0] = 150.0  # high frp
    row_2[1] = 345.0  # ti4
    row_2[18] = 50.0  # very close to industrial

    feature_matrix = [row_1, row_2]
    feature_dicts = [
        {ordered_features[i]: val for i, val in enumerate(row_1)},
        {ordered_features[i]: val for i, val in enumerate(row_2)},
    ]

    # Predict classes using model
    x_raw = np.array(feature_matrix, dtype=object)
    preds = list(pipeline.predict(x_raw))

    results = provider.explain_batch(feature_matrix, preds, feature_dicts)
    assert len(results) == 2

    for r in results:
        assert r.status == "AVAILABLE"
        assert r.base_value is not None
        assert r.explained_output is not None
        assert r.additivity_error is not None
        assert r.additivity_error < ADDITIVITY_TOLERANCE

        # Check raw feature sum matches explained_output - base_value
        raw_sum = sum(item.contribution for item in r.raw_feature_contributions)
        expected_diff = r.explained_output - r.base_value
        assert abs(raw_sum - expected_diff) < 0.01


def test_linear_explanation_provider_additive_identity():
    """Verify exact linear contribution math: base_value + sum(contributions) == margin."""
    ordered_features = ["feat_1", "feat_2", "cat_1"]
    preprocessor = build_preprocessor(
        numeric_features=[0, 1],
        categorical_features=[2],
        scale_numeric=True,
    )
    clf = LogisticRegression(random_state=42)
    pipe = Pipeline([("preprocessor", preprocessor), ("classifier", clf)])

    # Fit dummy linear model
    x_dummy = np.array(
        [
            [1.0, 10.0, "A"],
            [2.0, 20.0, "B"],
            [3.0, 30.0, "A"],
            [4.0, 40.0, "B"],
            [5.0, 50.0, "A"],
        ],
        dtype=object,
    )
    y_dummy = ["CLASS_X", "CLASS_Y", "CLASS_X", "CLASS_Y", "CLASS_X"]
    pipe.fit(x_dummy, y_dummy)

    provider = LinearExplanationProvider(pipe, ordered_features)
    test_rows = [[2.5, 25.0, "A"], [1.5, 15.0, "B"]]
    test_dicts = [
        {"feat_1": 2.5, "feat_2": 25.0, "cat_1": "A"},
        {"feat_1": 1.5, "feat_2": 15.0, "cat_1": "B"},
    ]
    preds = list(pipe.predict(np.array(test_rows, dtype=object)))

    results = provider.explain_batch(test_rows, preds, test_dicts)
    assert len(results) == 2

    for r in results:
        assert r.status == "AVAILABLE"
        assert r.additivity_error is not None
        assert r.additivity_error < ADDITIVITY_TOLERANCE
