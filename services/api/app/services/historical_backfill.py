# AGNIDRISHTI API — Historical NASA FIRMS Backfill Service
"""
Production service executing controlled 30-day historical NASA FIRMS backfill.
Chunks date ranges into maximum 5-day intervals per NASA API requirements.
Reuses canonical Phase 1 FIRMSClient and Phase 2 bulk_upsert to guarantee idempotency.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DEFAULT_FIRMS_SENSORS, INDIA_DEFAULT_BBOX
from app.core.logging import logger
from app.db.repositories.firms_coverage import FIRMSCoverageRepository
from app.providers.firms import FIRMSClient
from app.schemas.firms import BoundingBox
from app.services.firms_ingestion import FIRMSIngestionService


class HistoricalBackfillService:
    """
    Service for executing 30-day historical backfill from NASA FIRMS into PostGIS.
    """

    def __init__(self, db: AsyncSession, firms_client: FIRMSClient) -> None:
        self.db = db
        self.firms_client = firms_client
        self.ingestion_service = FIRMSIngestionService(db=db, firms_client=firms_client)
        self.coverage_repo = FIRMSCoverageRepository(db)

    async def execute_backfill(
        self,
        bbox: BoundingBox | None = None,
        days_history: int = 30,
        sources: list[str] | None = None,
        chunk_days: int = 5,
    ) -> dict[str, Any]:
        """
        Execute controlled backfill for the previous `days_history` days.
        Chunks date range into intervals of `chunk_days` (max 5).
        """
        eff_bbox = bbox or BoundingBox(
            west=INDIA_DEFAULT_BBOX[0],
            south=INDIA_DEFAULT_BBOX[1],
            east=INDIA_DEFAULT_BBOX[2],
            north=INDIA_DEFAULT_BBOX[3],
        )

        eff_sources = sources or [s.value for s in DEFAULT_FIRMS_SENSORS]
        eff_chunk_days = max(1, min(chunk_days, 5))
        eff_days_history = max(1, min(days_history, 90))

        today = datetime.now(UTC).date()
        start_date = today - timedelta(days=eff_days_history)

        total_fetched = 0
        total_upserted = 0
        successful_chunks = 0
        failed_chunks = 0

        current_end_date = today
        chunk_details = []

        logger.info(
            f"Starting Phase 3 Historical Backfill ({eff_days_history} days) | Sources: {eff_sources} | BBox: {eff_bbox.to_dict()}"
        )

        while current_end_date >= start_date:
            # Chunk date string for NASA FIRMS API
            date_str = current_end_date.strftime("%Y-%m-%d")

            try:
                # Synchronize chunk via Phase 2 FIRMSIngestionService
                sync_resp = await self.ingestion_service.sync(
                    bbox=eff_bbox,
                    day_range=eff_chunk_days,
                    sources=eff_sources,
                    date=date_str,
                    force_refresh=True,
                )

                total_fetched += sync_resp.fetched_count
                total_upserted += sync_resp.upserted_count
                successful_chunks += 1

                # Record coverage for each day in this chunk
                for i in range(eff_chunk_days):
                    cov_d = current_end_date - timedelta(days=i)
                    if cov_d >= start_date:
                        for s in sync_resp.successful_sources:
                            await self.coverage_repo.record_coverage(
                                source_product=s,
                                coverage_date=cov_d,
                                west=eff_bbox.west,
                                south=eff_bbox.south,
                                east=eff_bbox.east,
                                north=eff_bbox.north,
                                status="completed",
                                fetched_count=sync_resp.fetched_count,
                                valid_count=sync_resp.valid_count,
                                upserted_count=sync_resp.upserted_count,
                                run_id=sync_resp.run_id,
                            )

                chunk_details.append(
                    {
                        "date": date_str,
                        "day_range": eff_chunk_days,
                        "status": sync_resp.status,
                        "upserted": sync_resp.upserted_count,
                    }
                )

            except Exception as ex:
                logger.error(f"Backfill chunk failed for date {date_str}: {ex}")
                failed_chunks += 1
                chunk_details.append(
                    {
                        "date": date_str,
                        "day_range": eff_chunk_days,
                        "status": "failed",
                        "error": str(ex),
                    }
                )

            # Move window backward by chunk_days
            current_end_date -= timedelta(days=eff_chunk_days)

            # Brief pause between chunks to respect rate limits
            await asyncio.sleep(0.2)

        overall_status = (
            "completed"
            if failed_chunks == 0
            else ("partial" if successful_chunks > 0 else "failed")
        )

        return {
            "status": overall_status,
            "days_history": eff_days_history,
            "requested_bbox": eff_bbox.to_dict(),
            "sources": eff_sources,
            "chunks_total": successful_chunks + failed_chunks,
            "chunks_successful": successful_chunks,
            "chunks_failed": failed_chunks,
            "total_fetched": total_fetched,
            "total_upserted": total_upserted,
            "chunk_details": chunk_details,
        }
