# AGNIDRISHTI API — Phase 8 ML Dataset Module
"""
Dataset assembly, feature filtering, leakage audits, and provenance fingerprinting
for Phase 8 Intelligent Classification Engine.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from app.ml.classification.constants import (
    FORBIDDEN_MODEL_FEATURES,
    SPATIAL_GRID_DEGREES,
    STRATEGY_A_EXCLUDED_CATEGORICALS,
)
from app.services.fusion.feature_registry import fusion_v1_registry


@dataclass(frozen=True)
class DatasetRecord:
    """Represents a single observation record prepared for training/evaluation."""

    observation_id: str
    features: dict[str, Any]
    label: str
    label_provenance: str
    spatial_group: str


def get_model_feature_names(strategy_a: bool = True) -> list[str]:
    """
    Return the canonical, ordered list of eligible model features from fusion_v1_registry.
    Defensively excludes any forbidden features and, if strategy_a is True, excludes
    weak-label-defining categoricals to prevent circularity.
    """
    eligible = fusion_v1_registry.model_eligible_names
    forbidden_set = set(FORBIDDEN_MODEL_FEATURES)
    strategy_a_set = set(STRATEGY_A_EXCLUDED_CATEGORICALS) if strategy_a else set()

    filtered: list[str] = []
    for f in eligible:
        if f in forbidden_set:
            continue
        if strategy_a and f in strategy_a_set:
            continue
        filtered.append(f)
    return filtered


def get_feature_types(strategy_a: bool = True) -> tuple[list[str], list[str]]:
    """
    Partition eligible features into (numeric_features, categorical_features)
    based on fusion_v1_registry specifications.
    """
    feature_names = get_model_feature_names(strategy_a=strategy_a)
    numeric: list[str] = []
    categorical: list[str] = []

    for name in feature_names:
        spec = fusion_v1_registry.get_spec(name)
        if spec is None:
            continue
        if spec.dtype in ("float", "int", "bool"):
            numeric.append(name)
        else:
            categorical.append(name)

    return numeric, categorical


def compute_spatial_group(lat: float, lon: float, grid_degrees: float = SPATIAL_GRID_DEGREES) -> str:
    """
    Compute deterministic ~5km grid cell identifier for spatial group cross-validation.
    Coordinates are used solely for grouping and NEVER included in model features.
    """
    grid_y = round(lat / grid_degrees)
    grid_x = round(lon / grid_degrees)
    return f"grid_{grid_y}_{grid_x}"


def compute_training_dataset_fingerprint(records: list[DatasetRecord]) -> str:
    """
    Compute canonical SHA-256 fingerprint over sorted (observation_id, label, spatial_group).
    Ensures absolute reproducibility and provenance linking for trained models.
    """
    sorted_items = sorted(
        (r.observation_id, r.label, r.spatial_group) for r in records
    )
    payload = json.dumps(sorted_items, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_feature_missingness(
    feature_vectors: list[dict[str, Any]], feature_names: list[str]
) -> dict[str, float]:
    """Compute the null/missing fraction for every model feature."""
    if not feature_vectors:
        return {name: 0.0 for name in feature_names}

    total = len(feature_vectors)
    missing_counts: dict[str, int] = {name: 0 for name in feature_names}

    for vec in feature_vectors:
        for name in feature_names:
            val = vec.get(name)
            if val is None:
                missing_counts[name] += 1

    return {name: round(missing_counts[name] / total, 4) for name in feature_names}


def audit_leakage(feature_matrix: list[dict[str, Any]], strategy_a: bool = True) -> list[str]:
    """
    Audit feature dictionaries for any presence of forbidden identifier or coordinate fields,
    or Strategy A circular categoricals. Returns list of detected leakage field names.
    """
    forbidden_detected: set[str] = set()
    forbidden_set = set(FORBIDDEN_MODEL_FEATURES)
    if strategy_a:
        forbidden_set.update(STRATEGY_A_EXCLUDED_CATEGORICALS)

    for row in feature_matrix:
        for key, val in row.items():
            if key in forbidden_set and val is not None:
                forbidden_detected.add(key)

    return sorted(forbidden_detected)
