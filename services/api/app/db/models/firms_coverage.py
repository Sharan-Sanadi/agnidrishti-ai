# AGNIDRISHTI API — FIRMS Query Coverage Model
"""
SQLAlchemy ORM model for tracking historical NASA FIRMS query dataset coverage.
Ensures Phase 3 can distinguish unqueried history from authentic zero-detection dates.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import (
    Date,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FIRMSDataCoverageModel(Base):
    """
    Dataset history coverage record.
    Tracks whether a given (source_product, date, bbox) interval has been queried from NASA FIRMS.
    """

    __tablename__ = "firms_data_coverage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    source_product: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    coverage_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Bounding box bounds (WGS84)
    west: Mapped[float] = mapped_column(nullable=False)
    south: Mapped[float] = mapped_column(nullable=False)
    east: Mapped[float] = mapped_column(nullable=False)
    north: Mapped[float] = mapped_column(nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="completed"
    )  # "completed", "partial", "failed"

    fetched_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upserted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint(
            "source_product",
            "coverage_date",
            "west",
            "south",
            "east",
            "north",
            name="uq_coverage_source_date_bbox",
        ),
        Index(
            "idx_firms_coverage_query",
            "coverage_date",
            "source_product",
        ),
    )
