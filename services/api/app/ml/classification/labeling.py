# AGNIDRISHTI API — Phase 8 Weak Supervision Labeling Functions
"""
Centralized, conservative labeling functions for Phase 8 Intelligent Classification Engine.
Derives reproducible training labels with strict provenance tracking.
Never labels 'UNKNOWN' or fabricates ground-truth fire claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


@dataclass(frozen=True)
class LabelAssignment:
    """Represents a generated training label with comprehensive provenance."""

    observation_id: str
    label: str | None
    label_source: str
    label_provenance: str
    label_version: str
    confidence_tier: str
    reference: str | None
    notes: str | None


class WeakLabelerV1:
    """
    Conservative rule-based weak label generator (labeling_functions_v1).
    Anchors labels strictly to high-confidence physical and spatial evidence:
    - INDUSTRIAL: Mapped industrial areas or STRONG/MODERATE industrial context.
    - AGRICULTURAL: Valid industrial NONE and strongly dominant cropland.
    - NATURAL: Valid industrial NONE and strongly dominant tree/grass/shrub.
    - BUILT_NON_INDUSTRIAL: Valid industrial NONE and strongly dominant built-up.
    - MIXED: Adequate evidence without a single dominant anchor.
    Any conflicting, ambiguous, or un-evaluated observation is assigned UNLABELED.
    """

    LABEL_SOURCE = "labeling_functions_v1"

    @classmethod
    def evaluate(cls, observation_id: str, feature_vector: dict[str, Any]) -> LabelAssignment:
        """Evaluate a canonical fusion feature vector and return a LabelAssignment."""
        if not feature_vector:
            return LabelAssignment(
                observation_id=observation_id,
                label=None,
                label_source=cls.LABEL_SOURCE,
                label_provenance=PROVENANCE_UNLABELED,
                label_version=LABEL_VERSION,
                confidence_tier="NONE",
                reference=None,
                notes="Empty feature vector",
            )

        ind_class = feature_vector.get("industrial_context_class")
        ind_inside = feature_vector.get("industrial_inside_area", False)
        ind_coverage = feature_vector.get("industrial_coverage_status")
        lc_class = feature_vector.get("landcover_context_class")
        lc_coverage = feature_vector.get("landcover_coverage_status")

        candidate_labels: list[str] = []
        rules_triggered: list[str] = []

        # 1. Industrial Anchor: Inside mapped industrial polygon OR STRONG/MODERATE industrial context
        if ind_inside is True or ind_class in ("STRONG", "MODERATE"):
            candidate_labels.append(CLASS_INDUSTRIAL)
            rules_triggered.append("RULE_INDUSTRIAL_INFRASTRUCTURE_PROXIMITY")

        # 2. Non-Industrial Anchors: require valid industrial NONE with adequate coverage
        if ind_class == "NONE" and ind_coverage in ("ADEQUATE", "COMPLETE"):
            if lc_coverage in ("COMPLETE", "ADEQUATE"):
                if lc_class == "CROPLAND_DOMINANT":
                    candidate_labels.append(CLASS_AGRICULTURAL)
                    rules_triggered.append("RULE_CROPLAND_DOMINANT_NO_INDUSTRY")
                elif lc_class in (
                    "TREE_COVER_DOMINANT",
                    "GRASSLAND_DOMINANT",
                    "SHRUBLAND_DOMINANT",
                    "MANGROVES_DOMINANT",
                    "WETLAND_DOMINANT",
                    "BARE_SPARSE_DOMINANT",
                ):
                    candidate_labels.append(CLASS_NATURAL_VEGETATION)
                    rules_triggered.append("RULE_NATURAL_VEGETATION_DOMINANT_NO_INDUSTRY")
                elif lc_class == "BUILT_UP_DOMINANT":
                    candidate_labels.append(CLASS_BUILT_NON_INDUSTRIAL)
                    rules_triggered.append("RULE_BUILT_NON_INDUSTRIAL_DOMINANT")
                elif lc_class == "MIXED":
                    candidate_labels.append(CLASS_MIXED)
                    rules_triggered.append("RULE_MIXED_LANDCOVER_NO_INDUSTRY")

        # Conflict resolution: if multiple disjoint anchors triggered, assign UNLABELED
        unique_labels = list(set(candidate_labels))

        if len(unique_labels) == 1:
            assigned = unique_labels[0]
            return LabelAssignment(
                observation_id=observation_id,
                label=assigned,
                label_source=cls.LABEL_SOURCE,
                label_provenance=PROVENANCE_WEAK_HIGH_CONFIDENCE,
                label_version=LABEL_VERSION,
                confidence_tier="HIGH",
                reference="; ".join(rules_triggered),
                notes=f"Assigned by {cls.LABEL_SOURCE} via {rules_triggered[0]}",
            )
        elif len(unique_labels) > 1:
            return LabelAssignment(
                observation_id=observation_id,
                label=None,
                label_source=cls.LABEL_SOURCE,
                label_provenance=PROVENANCE_UNLABELED,
                label_version=LABEL_VERSION,
                confidence_tier="CONFLICT",
                reference="; ".join(rules_triggered),
                notes=f"Conflicting weak labels: {', '.join(unique_labels)}",
            )
        else:
            return LabelAssignment(
                observation_id=observation_id,
                label=None,
                label_source=cls.LABEL_SOURCE,
                label_provenance=PROVENANCE_UNLABELED,
                label_version=LABEL_VERSION,
                confidence_tier="UNCOVERED",
                reference=None,
                notes="No conservative labeling anchor satisfied",
            )
