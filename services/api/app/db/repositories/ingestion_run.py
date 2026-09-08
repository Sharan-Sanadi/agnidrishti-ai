# AGNIDRISHTI API — Ingestion Run Repository
"""
Repository for recording and querying ingestion run execution audit records.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ingestion_run import IngestionRunModel


class IngestionRunRepository:
    """Repository handling ingestion run persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_run(
        self,
        run_id: str,
        provider: str,
        requested_sources: list[str],
        requested_bbox: dict[str, float],
        requested_day_range: int,
        requested_date: str | None = None,
    ) -> IngestionRunModel:
        """Initialize and persist a new ingestion run record."""
        run = IngestionRunModel(
            run_id=run_id,
            provider=provider,
            requested_sources=requested_sources,
            requested_bbox=requested_bbox,
            requested_day_range=requested_day_range,
            requested_date=requested_date,
            started_at=datetime.now(UTC),
            status="running",
            fetched_count=0,
            valid_count=0,
            rejected_count=0,
            upserted_count=0,
            successful_sources=[],
            failed_sources=[],
        )
        self.db.add(run)
        await self.db.flush()
        return run

    async def complete_run(
        self,
        run_id: str,
        status: str,
        fetched_count: int,
        valid_count: int,
        rejected_count: int,
        upserted_count: int,
        successful_sources: list[str],
        failed_sources: list[str],
        error_summary: str | None = None,
    ) -> IngestionRunModel | None:
        """Mark an ingestion run as completed/partial/failed with final metrics."""
        stmt = select(IngestionRunModel).where(IngestionRunModel.run_id == run_id)
        res = await self.db.execute(stmt)
        run = res.scalar_one_or_none()
        if run:
            run.status = status
            run.completed_at = datetime.now(UTC)
            run.fetched_count = fetched_count
            run.valid_count = valid_count
            run.rejected_count = rejected_count
            run.upserted_count = upserted_count
            run.successful_sources = successful_sources
            run.failed_sources = failed_sources
            run.error_summary = error_summary
            await self.db.flush()
        return run

    async def get_by_id(self, run_id: str) -> IngestionRunModel | None:
        """Retrieve an ingestion run record by ID."""
        stmt = select(IngestionRunModel).where(IngestionRunModel.run_id == run_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()
