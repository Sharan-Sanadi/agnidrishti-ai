# AGNIDRISHTI API — Phase 8 Weak Labeling Unit Tests
"""
Unit tests for WeakLabelerV1 conservative labeling rules, conflict detection,
and label provenance guarantees.
"""

from __future__ import annotations

from app.ml.classification.constants import (
    CLASS_AGRICULTURAL,
    CLASS_BUILT_NON_INDUSTRIAL,
    CLASS_INDUSTRIAL,
    CLASS_MIXED,
    CLASS_NATURAL_VEGETATION,
    LABEL_VERSION,
    PROVENANCE_UNLABELED,
    PROVENANCE_WEAK_HIGH_CONFIDENCE,
)
from app.ml.classification.labeling import WeakLabelerV1


def test_label_provenance_contract() -> None:
    """Every evaluation must return complete provenance metadata."""
    res = WeakLabelerV1.evaluate("obs_test_1", {})
    assert res.observation_id == "obs_test_1"
    assert res.label_source == "labeling_functions_v1"
    assert res.label_provenance == PROVENANCE_UNLABELED
    assert res.label_version == LABEL_VERSION
    assert res.label is None


def test_industrial_inside_area_label() -> None:
    """Inside mapped industrial area must label INDUSTRIAL_THERMAL_CONTEXT."""
    feat_vec = {
        "industrial_inside_area": True,
        "industrial_context_class": "STRONG",
        "industrial_coverage_status": "COMPLETE",
    }
    res = WeakLabelerV1.evaluate("obs_ind_1", feat_vec)
    assert res.label == CLASS_INDUSTRIAL
    assert res.label_provenance == PROVENANCE_WEAK_HIGH_CONFIDENCE
    assert res.confidence_tier == "HIGH"


def test_agricultural_dominant_label() -> None:
    """Cropland dominant with industrial NONE must label AGRICULTURAL_THERMAL_CONTEXT."""
    feat_vec = {
        "industrial_context_class": "NONE",
        "industrial_inside_area": False,
        "industrial_coverage_status": "COMPLETE",
        "landcover_context_class": "CROPLAND_DOMINANT",
        "landcover_coverage_status": "COMPLETE",
    }
    res = WeakLabelerV1.evaluate("obs_ag_1", feat_vec)
    assert res.label == CLASS_AGRICULTURAL
    assert res.label_provenance == PROVENANCE_WEAK_HIGH_CONFIDENCE


def test_natural_vegetation_label() -> None:
    """Tree cover dominant with industrial NONE must label NATURAL_VEGETATION_THERMAL_CONTEXT."""
    feat_vec = {
        "industrial_context_class": "NONE",
        "industrial_inside_area": False,
        "industrial_coverage_status": "COMPLETE",
        "landcover_context_class": "TREE_COVER_DOMINANT",
        "landcover_coverage_status": "COMPLETE",
    }
    res = WeakLabelerV1.evaluate("obs_nat_1", feat_vec)
    assert res.label == CLASS_NATURAL_VEGETATION
    assert res.label_provenance == PROVENANCE_WEAK_HIGH_CONFIDENCE


def test_built_non_industrial_label() -> None:
    """Built-up dominant with industrial NONE must label BUILT_NON_INDUSTRIAL_CONTEXT."""
    feat_vec = {
        "industrial_context_class": "NONE",
        "industrial_inside_area": False,
        "industrial_coverage_status": "COMPLETE",
        "landcover_context_class": "BUILT_UP_DOMINANT",
        "landcover_coverage_status": "COMPLETE",
    }
    res = WeakLabelerV1.evaluate("obs_built_1", feat_vec)
    assert res.label == CLASS_BUILT_NON_INDUSTRIAL
    assert res.label_provenance == PROVENANCE_WEAK_HIGH_CONFIDENCE


def test_mixed_landcover_label() -> None:
    """Mixed land cover with industrial NONE must label MIXED_THERMAL_CONTEXT."""
    feat_vec = {
        "industrial_context_class": "NONE",
        "industrial_inside_area": False,
        "industrial_coverage_status": "COMPLETE",
        "landcover_context_class": "MIXED",
        "landcover_coverage_status": "COMPLETE",
    }
    res = WeakLabelerV1.evaluate("obs_mix_1", feat_vec)
    assert res.label == CLASS_MIXED
    assert res.label_provenance == PROVENANCE_WEAK_HIGH_CONFIDENCE


def test_uncovered_observation_unlabeled() -> None:
    """Observation lacking adequate coverage remains UNLABELED."""
    feat_vec = {
        "industrial_context_class": "WEAK",
        "industrial_inside_area": False,
        "industrial_coverage_status": "NO_COVERAGE",
        "landcover_context_class": "CROPLAND_DOMINANT",
        "landcover_coverage_status": "PARTIAL",
    }
    res = WeakLabelerV1.evaluate("obs_uncov_1", feat_vec)
    assert res.label is None
    assert res.label_provenance == PROVENANCE_UNLABELED
    assert res.confidence_tier == "UNCOVERED"
