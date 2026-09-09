# AGNIDRISHTI API — Phase 7 Feature Fusion Schemas
"""
Pydantic schemas for Phase 7 Feature Fusion API requests and responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FusionFeatureSpecResponse(BaseModel):
    """Specification of an individual registered feature."""

    name: str = Field(..., description="Canonical snake_case feature name")
    group: str = Field(..., description="Evidence group: THERMAL, TEMPORAL, INDUSTRIAL, LAND_COVER, SENTINEL")
    source_phase: str = Field(..., description="Source intelligence phase (phase1, phase3, phase4, phase5, phase6)")
    source_field: str = Field(..., description="Upstream model attribute or column name")
    dtype: str = Field(..., description="Datatype: float, int, str, bool")
    unit: str = Field(..., description="Physical or statistical unit of measurement")
    nullable: bool = Field(..., description="Whether null/None is permitted")
    model_eligible: bool = Field(..., description="Whether feature is included in default Phase 8 ML feature matrix")
    description: str = Field(..., description="Scientific explanation and provenance")


class FusionSchemaResponse(BaseModel):
    """Schema registry response for GET /api/v1/fusion/schema."""

    schema_version: str = Field(..., description="Schema version identifier (e.g. 'fusion_v1')")
    schema_hash: str = Field(..., description="Deterministic SHA-256 hash of canonical feature registry")
    total_features: int = Field(..., description="Total count of registered features (59)")
    model_eligible_features: int = Field(..., description="Count of features eligible for ML modeling (57)")
    features: list[FusionFeatureSpecResponse] = Field(..., description="Canonical ordered list of feature specifications")


class FusionProfileResponse(BaseModel):
    """Single observation feature fusion profile response."""

    observation_id: str = Field(..., description="Canonical firms_* observation identifier")
    schema_version: str = Field(..., description="Schema version identifier (e.g. 'fusion_v1')")
    schema_hash: str = Field(..., description="Deterministic SHA-256 hash of canonical feature registry")
    source_fingerprint: str = Field(..., description="SHA-256 fingerprint of semantic upstream source data")
    fusion_status: str = Field(..., description="Status: 'COMPLETE' or 'PARTIAL'")

    total_group_count: int = Field(5, description="Total evidence groups evaluated (5)")
    evaluated_group_count: int = Field(..., description="Number of groups with non-missing evaluation")
    usable_group_count: int = Field(..., description="Number of groups with usable scientific evidence")

    expected_feature_count: int = Field(..., description="Total model-eligible features in schema (57)")
    non_null_feature_count: int = Field(..., description="Count of non-null model-eligible features present")
    feature_coverage_fraction: float = Field(..., description="Fraction of non-null model-eligible features (0.0 to 1.0)")
    feature_coverage_percent: int = Field(..., description="Integer percentage representation of feature coverage")

    feature_vector: dict[str, Any] = Field(..., description="Deterministic dictionary of all 59 registered features")
    group_status: dict[str, str] = Field(..., description="Evaluation status per evidence group")
    provenance: dict[str, Any] = Field(..., description="Detailed source product versions and scene IDs")
    quality_flags: list[str] = Field(default_factory=list, description="Quality warnings, invariant flags, or notices")

    generated_at: datetime = Field(..., description="Timestamp when fusion profile was computed")
    updated_at: datetime = Field(..., description="Timestamp when fusion profile was last updated")


class BatchFusionRequest(BaseModel):
    """Batch retrieval request payload."""

    observation_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="List of canonical observation IDs to retrieve (max 500)",
    )
    schema_version: str = Field(
        default="fusion_v1",
        description="Requested fusion schema version (default: 'fusion_v1')",
    )


class BatchFusionResponse(BaseModel):
    """Batch retrieval response envelope."""

    schema_version: str = Field(..., description="Schema version identifier")
    count: int = Field(..., description="Number of fusion profiles retrieved")
    profiles: dict[str, FusionProfileResponse] = Field(
        ...,
        description="Map of observation_id -> FusionProfileResponse",
    )


class SyncFusionRequest(BaseModel):
    """Sync request payload."""

    observation_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="List of canonical observation IDs to sync/fuse (max 500)",
    )
    force_recompute: bool = Field(
        default=False,
        description="If True, recompute and update profiles even if source fingerprint is unchanged",
    )


class SyncFusionResponse(BaseModel):
    """Sync execution metrics response."""

    requested: int = Field(..., description="Number of observation IDs requested")
    created: int = Field(..., description="Number of new fusion profiles created in PostGIS")
    updated: int = Field(..., description="Number of existing profiles updated due to source change or force_recompute")
    reused: int = Field(..., description="Number of existing profiles reused without modification (fingerprint unchanged)")
    complete: int = Field(..., description="Count of synced profiles with COMPLETE fusion status")
    partial: int = Field(..., description="Count of synced profiles with PARTIAL fusion status")
    missing_upstream_groups: dict[str, int] = Field(
        ...,
        description="Breakdown of missing groups among synced observations (e.g. {'SENTINEL': 480})",
    )
    duration_ms: float = Field(..., description="Total execution time in milliseconds")
    database_queries: int = Field(..., description="Approximate number of bulk database queries executed")
