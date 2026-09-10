# AGNIDRISHTI API — Phase 9 Class Index Matching Unit Tests
"""
Tests verifying class index alignment between Phase-8 predictions and Phase-9 explanations.
Ensures class N is never explained while displaying class M.
"""

from __future__ import annotations

from app.ml.classification.registry import model_registry
from app.ml.explainability.provider import get_explanation_provider


def test_class_index_alignment_and_specificity():
    """Verify explanations are class-specific and match the model estimator's class order."""
    pipeline = model_registry.model
    manifest = model_registry.manifest
    assert pipeline is not None
    assert manifest is not None

    ordered_features = manifest.ordered_features
    provider = get_explanation_provider(pipeline, ordered_features)

    classifier = pipeline.named_steps["classifier"]
    estimator_classes = list(getattr(classifier, "classes_", []))
    assert len(estimator_classes) == 5

    # Pick two distinct classes
    class_a = estimator_classes[0]  # AGRICULTURAL_THERMAL_CONTEXT
    class_b = estimator_classes[2]  # INDUSTRIAL_THERMAL_CONTEXT
    assert class_a != class_b

    # Construct single feature row
    row = [None] * len(ordered_features)
    row[0] = 50.0
    row[1] = 320.0
    row[18] = 300.0  # nearest industrial distance
    row[34] = 0.60  # cropland fraction
    f_dict = {ordered_features[i]: row[i] for i in range(len(ordered_features))}

    # Explain the same sample under class_a vs class_b
    res_a = provider.explain_batch([row], [class_a], [f_dict])[0]
    res_b = provider.explain_batch([row], [class_b], [f_dict])[0]

    assert res_a.status == "AVAILABLE"
    assert res_b.status == "AVAILABLE"
    assert res_a.predicted_class == class_a
    assert res_b.predicted_class == class_b

    # Base values and outputs must differ between different classes
    assert res_a.base_value != res_b.base_value
    assert res_a.explained_output != res_b.explained_output

    # Nearest industrial feature should be more positive for industrial context
    raw_contribs_a = {it.feature_name: it.contribution for it in res_a.raw_feature_contributions}
    raw_contribs_b = {it.feature_name: it.contribution for it in res_b.raw_feature_contributions}
    assert raw_contribs_a != raw_contribs_b


def test_unknown_class_handling():
    """Verify that requesting explanation for an invalid class returns EXPLANATION_INVALID."""
    pipeline = model_registry.model
    manifest = model_registry.manifest
    assert pipeline is not None
    assert manifest is not None

    ordered_features = manifest.ordered_features
    provider = get_explanation_provider(pipeline, ordered_features)

    row = [None] * len(ordered_features)
    f_dict = {ordered_features[i]: None for i in range(len(ordered_features))}

    res = provider.explain_batch([row], ["NON_EXISTENT_CLASS"], [f_dict])[0]
    assert res.status == "EXPLANATION_INVALID"
    assert "UNKNOWN_PREDICTED_CLASS" in res.quality_flags
