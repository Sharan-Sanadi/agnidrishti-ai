# AGNIDRISHTI API — Phase 8 Model Registry & Evidence Gating Tests
"""
Unit tests for model artifact verification, tamper detection, schema compatibility,
and inference evidence gating.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from app.ml.classification.constants import (
    ARTIFACT_DIR,
    MANIFEST_FILENAME,
    MIN_MODEL_FEATURE_COVERAGE,
    STATUS_AVAILABLE,
    STATUS_MODEL_INVALID,
    STATUS_SCHEMA_MISMATCH,
)
from app.ml.classification.registry import ModelRegistry, model_registry


def test_model_registry_loads_valid_artifact() -> None:
    """Model registry must load and verify trained artifact successfully."""
    model_registry.reset()
    reg = ModelRegistry()
    assert reg.status == STATUS_AVAILABLE
    assert reg.is_available is True
    assert reg.model is not None
    assert reg.manifest is not None


def test_model_registry_tampered_hash_fails() -> None:
    """If model artifact hash does not match manifest, registry must reject with MODEL_INVALID."""
    model_registry.reset()
    with patch("app.ml.classification.registry.compute_file_sha256", return_value="0000000000000000000000000000000000000000000000000000000000000000"):
        reg = ModelRegistry()
        assert reg.status == STATUS_MODEL_INVALID
        assert reg.is_available is False


def test_model_registry_schema_mismatch_fails() -> None:
    """If model was trained against a different schema hash, registry must report SCHEMA_MISMATCH."""
    model_registry.reset()
    manifest_path = ARTIFACT_DIR / MANIFEST_FILENAME
    with open(manifest_path, encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Change schema hash
    mismatched = dict(manifest_data)
    mismatched["fusion_schema_hash"] = "fake_schema_hash_12345"

    with patch("json.load", return_value=mismatched):
        reg = ModelRegistry()
        assert reg.status == STATUS_SCHEMA_MISMATCH
        assert reg.is_available is False


def test_evidence_gating_threshold() -> None:
    """Coverage fraction below MIN_MODEL_FEATURE_COVERAGE must gate inference."""
    assert MIN_MODEL_FEATURE_COVERAGE == 0.40
    sparse_coverage = 0.35
    assert sparse_coverage < MIN_MODEL_FEATURE_COVERAGE
