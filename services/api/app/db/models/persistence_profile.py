# AGNIDRISHTI API — Persistence Profile ORM Model
"""
SQLAlchemy ORM model for storing/caching Phase 3 Temporal Persistence Intelligence profiles.
Derived intelligence linked 1-to-1 with thermal_observations by observation_id.
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
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PersistenceProfileModel(Base):
    """
    Derived Temporal Persistence Profile for a specific thermal observation.
    Calculated relative to observation acquisition time T without future data leakage.
    """

    __tablename__ = "persistence_profiles"

    observation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("thermal_observations.observation_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    algorithm_version: Mapped[str] = mapped_column(
        String(64), nullable=False, default="temporal_persistence_v1"
    )
    analysis_as_of: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    radius_m: Mapped[float] = mapped_column(Float, nullable=False, default=750.0)

    raw_detection_count_7d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_detection_count_30d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    active_days_7d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_days_30d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_weeks_30d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    first_seen_30d: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_30d: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    temporal_span_days_30d: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    history_coverage_days_7d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    history_coverage_days_30d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    history_coverage_ratio_30d: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    persistence_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    persistence_class: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    explanation: Mapped[str] = mapped_column(String(512), nullable=False)
    explanation_details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        Index(
            "idx_persistence_class_index",
            "persistence_class",
            "persistence_index",
        ),
    )
