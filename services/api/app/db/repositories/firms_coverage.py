# AGNIDRISHTI API — FIRMS Data Coverage Repository
"""
Repository for recording and querying historical NASA FIRMS query coverage.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.firms_coverage import FIRMSDataCoverageModel


class FIRMSCoverageRepository:
    """Repository handling FIRMS dataset coverage records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_coverage(
        self,
        source_product: str,
        coverage_date: date,
        west: float,
        south: float,
        east: float,
        north: float,
        status: str = "completed",
        fetched_count: int = 0,
        valid_count: int = 0,
        upserted_count: int = 0,
        run_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Upsert a coverage record for a specific source, date, and bounding box."""
        now = datetime.now(UTC)
        stmt = insert(FIRMSDataCoverageModel).values(
            source_product=source_product,
            coverage_date=coverage_date,
            west=west,
            south=south,
            east=east,
            north=north,
            status=status,
            fetched_count=fetched_count,
            valid_count=valid_count,
            upserted_count=upserted_count,
            run_id=run_id,
            details=details,
            completed_at=now,
        )

        update_dict = {
            "status": stmt.excluded.status,
            "fetched_count": stmt.excluded.fetched_count,
            "valid_count": stmt.excluded.valid_count,
            "upserted_count": stmt.excluded.upserted_count,
            "run_id": stmt.excluded.run_id,
            "details": stmt.excluded.details,
            "completed_at": now,
        }

        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uq_coverage_source_date_bbox",
            set_=update_dict,
        )

        await self.db.execute(upsert_stmt)
        await self.db.flush()

    async def get_covered_days(
        self,
        start_date: date,
        end_date: date,
        west: float | None = None,
        south: float | None = None,
        east: float | None = None,
        north: float | None = None,
        sources: list[str] | None = None,
    ) -> int:
        """
        Count the number of distinct dates between start_date and end_date
        that have completed FIRMS query coverage in PostGIS.
        """
        stmt = select(func.count(func.distinct(FIRMSDataCoverageModel.coverage_date))).where(
            FIRMSDataCoverageModel.coverage_date >= start_date,
            FIRMSDataCoverageModel.coverage_date <= end_date,
            FIRMSDataCoverageModel.status == "completed",
        )

        if sources:
            stmt = stmt.where(FIRMSDataCoverageModel.source_product.in_(sources))

        res = await self.db.execute(stmt)
        return res.scalar() or 0
