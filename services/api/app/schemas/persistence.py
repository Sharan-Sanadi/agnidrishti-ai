# AGNIDRISHTI API — Temporal Persistence Schemas
"""
Pydantic schemas for Phase 3 Temporal Persistence API requests and responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ScoreComponentsSchema(BaseModel):
    active_days_score: float = Field(..., description="Active days contribution (max 45)")
    temporal_span_score: float = Field(..., description="Temporal span contribution (max 25)")
    multi_week_score: float = Field(..., description="Multi-week contribution (max 20)")
    recency_score: float = Field(..., description="Recency contribution (max 10)")


class PersistenceProfileResponse(BaseModel):
    """Canonical Phase 3 Temporal Persistence Response."""

    observation_id: str = Field(..., description="Deterministic observation ID")
    analysis_as_of: datetime = Field(..., description="Analysis UTC timestamp (target acquisition time)")
    radius_m: float = Field(..., description="Spatial association radius in meters")
    algorithm_version: str = Field(..., description="Algorithm version identifier")

    raw_detection_count_7d: int = Field(..., description="Raw detections within radius in 7d window")
    raw_detection_count_30d: int = Field(..., description="Raw detections within radius in 30d window")

    active_days_7d: int = Field(..., description="Distinct UTC active days within radius in 7d window")
    active_days_30d: int = Field(..., description="Distinct UTC active days within radius in 30d window")
    active_weeks_30d: int = Field(..., description="Distinct calendar weeks with activity in 30d window")

    first_seen_30d: datetime | None = Field(None, description="First acquisition time in 30d window")
    last_seen_30d: datetime | None = Field(None, description="Most recent acquisition time in 30d window")
    temporal_span_days_30d: float = Field(..., description="Temporal span between first and last seen (days)")

    history_coverage_days_7d: int = Field(..., description="Queried dataset coverage days in 7d window")
    history_coverage_days_30d: int = Field(..., description="Queried dataset coverage days in 30d window")
    history_coverage_ratio_30d: float = Field(..., description="Ratio of queried days to 30d window")

    persistence_index: int = Field(..., ge=0, le=100, description="Heuristic Persistence Index (0-100)")
    persistence_class: str = Field(..., description="Classification category: ISOLATED, OCCASIONAL, RECURRING, PERSISTENT, or INSUFFICIENT_HISTORY")
    explanation: str = Field(..., description="Deterministic scientific explanation text")
    score_components: ScoreComponentsSchema = Field(..., description="Component breakdown of Persistence Index")


class BatchPersistenceRequest(BaseModel):
    """Request payload for batch persistence analysis."""

    observation_ids: list[str] = Field(..., min_length=1, max_length=500, description="List of observation IDs to analyze")
    radius_m: float | None = Field(None, ge=250.0, le=2000.0, description="Spatial association radius (meters)")


class BatchPersistenceResponse(BaseModel):
    """Response envelope for batch persistence analysis."""

    algorithm_version: str
    count: int
    profiles: dict[str, PersistenceProfileResponse]


class BackfillRequest(BaseModel):
    """Request payload for historical FIRMS backfill."""

    days_history: int = Field(30, ge=1, le=90, description="Number of historical days to backfill (max 90)")
    west: float | None = Field(None, description="West longitude")
    south: float | None = Field(None, description="South latitude")
    east: float | None = Field(None, description="East longitude")
    north: float | None = Field(None, description="North latitude")
    sources: list[str] | None = Field(None, description="Satellite sensor sources")
    chunk_days: int = Field(5, ge=1, le=5, description="Chunk size in days (max 5)")


class BackfillResponse(BaseModel):
    """Response for historical FIRMS backfill execution."""

    status: str
    days_history: int
    requested_bbox: dict[str, float]
    sources: list[str]
    chunks_total: int
    chunks_successful: int
    chunks_failed: int
    total_fetched: int
    total_upserted: int
    chunk_details: list[dict[str, Any]]
