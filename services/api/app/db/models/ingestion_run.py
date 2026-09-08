# AGNIDRISHTI API — Ingestion Run ORM Model
"""
Ingestion run audit table recording synchronization cycles, counts, and status.
NEVER stores authentication tokens, API keys, or raw authenticated URLs.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IngestionRunModel(Base):
    """Audit log for ingestion runs executed against NASA FIRMS."""

    __tablename__ = "ingestion_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="NASA FIRMS")

    # Sanitized request parameters
    requested_sources: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    requested_bbox: Mapped[dict[str, float]] = mapped_column(JSONB, nullable=False)
    requested_day_range: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_date: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Execution timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Status: 'running', 'completed', 'partial', 'failed'
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")

    # Metrics
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    valid_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    upserted_count: Mapped[int] = mapped_column(Integer, default=0)

    # Source breakdown
    successful_sources: Mapped[list[str]] = mapped_column(JSONB, default=list)
    failed_sources: Mapped[list[str]] = mapped_column(JSONB, default=list)

    # Diagnostic error summary (sanitized of keys)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
