# AGNIDRISHTI API — Phase 7 Feature Fusion Profile Model
"""
SQLAlchemy ORM model for storing Phase 7 Feature Fusion profiles.
Stores versioned, deterministic machine-readable feature profiles aligned with
canonical thermal observations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ThermalFeatureFusionProfileModel(Base):
    """
    Derived Phase 7 Feature Fusion Profile.
    Integrates multi-modal evidence across Phases 1-6 into one versioned, deterministic profile.
    """

    __tablename__ = "thermal_feature_fusion_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    observation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("thermal_observations.observation_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    schema_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="fusion_v1",
        index=True,
    )
    schema_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)

    # Descriptive status: COMPLETE, PARTIAL
    fusion_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    # Evidence group counters
    total_group_count: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    evaluated_group_count: Mapped[int] = mapped_column(Integer, nullable=False)
    usable_group_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Feature coverage metrics (model-eligible completeness, not model confidence)
    expected_feature_count: Mapped[int] = mapped_column(Integer, nullable=False)
    non_null_feature_count: Mapped[int] = mapped_column(Integer, nullable=False)
    feature_coverage_fraction: Mapped[float] = mapped_column(Float, nullable=False)

    # JSONB payloads
    feature_vector: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    group_status: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    quality_flags: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    # Generation timestamps
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint("observation_id", "schema_version", name="uq_fusion_observation_schema"),
        Index("idx_fusion_observation_id", "observation_id"),
        Index("idx_fusion_status", "fusion_status"),
        Index("idx_fusion_schema_version", "schema_version"),
    )
