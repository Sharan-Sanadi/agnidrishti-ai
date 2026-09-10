# AGNIDRISHTI API — Phase 9 Explainability Schemas
"""
Pydantic schemas and serialization models for Phase 9 Model Explainability Engine.
Includes local attribution items, feature groups, batch responses, and global importance.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FeatureContributionItem(BaseModel):
    """Local attribution details for a single human-readable model feature."""

    model_config = ConfigDict(from_attributes=True)

    feature_name: str = Field(..., description="Canonical fusion_v1 raw feature name.")
    display_name: str = Field(..., description="Human-readable feature title.")
    feature_group: str = Field(..., description="Evidence group (THERMAL, TEMPORAL, INDUSTRIAL, LAND_COVER, SENTINEL).")
    raw_value: Any = Field(None, description="Actual unscaled source feature value from fusion profile.")
    display_value: str = Field(..., description="Formatted value with units or status.")
    unit: str = Field(..., description="Unit of measurement (MW, m, %, index, etc.).")
    contribution: float = Field(..., description="Signed additive contribution to predicted class decision margin.")
    relative_strength: float = Field(..., description="Display-only normalized contribution magnitude share (0-100%).")
    direction: str = Field(..., description="SUPPORTS, OPPOSES, or NEUTRAL.")
    rank: int = Field(..., description="1-indexed rank within supporting or opposing category.")


class GroupContributionItem(BaseModel):
    """Aggregated local attribution details for an evidence group."""

    model_config = ConfigDict(from_attributes=True)

    group: str = Field(..., description="Evidence group name.")
    total_contribution: float = Field(..., description="Sum of raw feature contributions in this group.")
    relative_strength: float = Field(..., description="Display-only group contribution share (0-100%).")
    direction: str = Field(..., description="SUPPORTS, OPPOSES, or NEUTRAL.")
    contribution_level: str = Field(..., description="HIGH_CONTRIBUTION, MEDIUM_CONTRIBUTION, or LOW_CONTRIBUTION.")
    feature_count: int = Field(..., description="Number of model features evaluated in this group.")


class LocalExplanationResponse(BaseModel):
    """Complete local model explanation response for a single observation."""

    model_config = ConfigDict(from_attributes=True)

    observation_id: str
    explanation_status: str
    predicted_class: str | None = None
    prediction_score: float | None = None
    model_version: str
    validation_status: str
    explanation_version: str
    method: str
    feature_coverage: float | None = None
    base_value: float | None = None
    explained_output: float | None = None
    additivity_error: float | None = None
    top_supporting_features: list[FeatureContributionItem] = Field(default_factory=list)
    top_opposing_features: list[FeatureContributionItem] = Field(default_factory=list)
    group_contributions: dict[str, GroupContributionItem] = Field(default_factory=dict)
    quality_flags: list[str] = Field(default_factory=list)
    generated_at: datetime


class BatchExplanationRequest(BaseModel):
    """Request payload for batch explanation retrieval."""

    observation_ids: list[str] = Field(..., max_length=500, description="Up to 500 observation IDs.")


class BatchExplanationResponse(BaseModel):
    """Bulk response container for multiple local explanations."""

    model_config = ConfigDict(from_attributes=True)

    explanation_version: str
    count: int = 0
    explanations: dict[str, LocalExplanationResponse] = Field(default_factory=dict)


class SyncExplanationRequest(BaseModel):
    """Request payload for explanation synchronization."""

    observation_ids: list[str] = Field(..., max_length=500, description="Up to 500 observation IDs.")
    force_recompute: bool = Field(False, description="Whether to bypass cache and recompute attributions.")


class SyncExplanationResponse(BaseModel):
    """Execution telemetry for batch explanation synchronization."""

    model_config = ConfigDict(from_attributes=True)

    requested: int
    created: int
    updated: int
    reused: int
    available: int
    insufficient_evidence: int
    duration_ms: float
    database_queries: int


class GlobalFeatureImportanceItem(BaseModel):
    """Global permutation feature importance metric for a raw model feature."""

    model_config = ConfigDict(from_attributes=True)

    feature_name: str
    display_name: str
    feature_group: str
    importance_mean: float
    importance_std: float
    rank: int


class GlobalExplanationResponse(BaseModel):
    """Global model behavior insight based on held-out evaluation data."""

    model_config = ConfigDict(from_attributes=True)

    model_version: str
    explanation_version: str
    validation_status: str
    scoring_metric: str
    dataset_fingerprint: str
    top_features: list[GlobalFeatureImportanceItem] = Field(default_factory=list)
    feature_groups: dict[str, float] = Field(default_factory=dict)
    computed_at: datetime
    random_seed: int
    evaluation_split: str
