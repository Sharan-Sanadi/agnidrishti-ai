# AGNIDRISHTI API — NASA FIRMS Ingestion & PostGIS Synchronization Service
"""
Production orchestration service for NASA FIRMS ingestion into PostGIS.
Reuses the canonical Phase 1 FIRMSClient and Parser.
Enforces normalization, transaction safety, idempotency, and audit logging.
"""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DEFAULT_FIRMS_SENSORS
from app.core.logging import logger
from app.db.repositories.ingestion_run import IngestionRunRepository
from app.db.repositories.thermal_observation import ThermalObservationRepository
from app.providers.firms import FIRMSClient, FIRMSException
from app.schemas.firms import BoundingBox, ThermalObservation
from app.schemas.observations import FIRMSSyncResponse


def normalize_confidence(raw: str) -> str | None:
    """
    Normalize upstream confidence code into semantic form.
    VIIRS values: 'l' -> 'low', 'n' -> 'nominal', 'h' -> 'high'.
    Preserves other values safely without crashing.
    """
    cleaned = raw.strip().lower()
    mapping = {
        "l": "low",
        "n": "nominal",
        "h": "high",
        "low": "low",
        "nominal": "nominal",
        "high": "high",
    }
    return mapping.get(cleaned, cleaned or None)


def sanitize_float(val: float | None) -> float | None:
    """Ensure floating-point numbers are finite and suitable for PostgreSQL storage."""
    if val is None:
        return None
    if math.isnan(val) or math.isinf(val):
        return None
    return val


def observation_to_storage_record(obs: ThermalObservation) -> dict[str, Any]:
    """
    Transform a canonical ThermalObservation DTO into a normalized storage dictionary.
    Excludes sensitive data and strictly enforces SRID 4326 POINT(lng lat).
    """
    now = datetime.now(UTC)

    # Sanitize raw payload for auditability without storing secret tokens
    sanitized_raw = {
        "id": obs.id,
        "satellite": obs.satellite,
        "instrument": obs.instrument,
        "source": obs.source,
        "confidence": obs.confidence,
        "frp": obs.frp,
        "bright_ti4": obs.bright_ti4,
        "bright_ti5": obs.bright_ti5,
        "scan": obs.scan,
        "track": obs.track,
        "daynight": obs.daynight,
        "firms_version": obs.firms_version,
    }

    return {
        "observation_id": obs.id,
        "latitude": obs.latitude,
        "longitude": obs.longitude,
        "acquisition_time_utc": obs.acquisition_time_utc,
        "satellite": obs.satellite,
        "instrument": obs.instrument,
        "source_product": obs.source,
        "provider": "NASA FIRMS",
        "confidence_raw": obs.confidence,
        "confidence_normalized": normalize_confidence(obs.confidence),
        "frp": sanitize_float(obs.frp),
        "bright_ti4": sanitize_float(obs.bright_ti4),
        "bright_ti5": sanitize_float(obs.bright_ti5),
        "scan": sanitize_float(obs.scan),
        "track": sanitize_float(obs.track),
        "daynight": obs.daynight,
        "firms_version": obs.firms_version,
        "first_ingested_at": now,
        "last_seen_at": now,
        "ingestion_count": 1,
        "raw_payload": sanitized_raw,
        "created_at": now,
        "updated_at": now,
    }


class FIRMSIngestionService:
    """
    Orchestration service bridging NASA FIRMS and PostgreSQL/PostGIS.
    1. Validates request
    2. Creates IngestionRun audit record
    3. Calls existing Phase 1 FIRMSClient
    4. Normalizes canonical ThermalObservation records
    5. Bulk upserts idempotently into PostGIS
    6. Updates IngestionRun audit record
    7. Returns truthful sync summary
    """

    def __init__(self, db: AsyncSession, firms_client: FIRMSClient) -> None:
        self.db = db
        self.firms_client = firms_client
        self.obs_repo = ThermalObservationRepository(db)
        self.run_repo = IngestionRunRepository(db)

    async def sync(
        self,
        bbox: BoundingBox,
        day_range: int = 1,
        sources: list[str] | None = None,
        date: str | None = None,
        force_refresh: bool = False,
    ) -> FIRMSSyncResponse:
        """Execute full synchronization from NASA FIRMS into PostGIS."""
        source_list = sources or [s.value for s in DEFAULT_FIRMS_SENSORS]
        run_id = f"run_{uuid.uuid4().hex[:16]}"
        started_at = datetime.now(UTC)

        logger.info(
            f"Starting Phase 2 FIRMS sync [{run_id}] | Sources: {source_list} | Day range: {day_range} | BBox: {bbox.to_dict()}"
        )

        # 1. Create IngestionRun record
        await self.run_repo.create_run(
            run_id=run_id,
            provider="NASA FIRMS",
            requested_sources=source_list,
            requested_bbox=bbox.to_dict(),
            requested_day_range=day_range,
            requested_date=date,
        )
        await self.db.commit()

        try:
            # 2. Ingest via existing canonical Phase 1 FIRMS Client
            firms_resp = await self.firms_client.get_hotspots(
                bbox=bbox,
                day_range=day_range,
                sources=source_list,
                date=date,
                force_refresh=force_refresh,
            )

            # 3. Normalize into storage records
            storage_records = [
                observation_to_storage_record(obs) for obs in firms_resp.observations
            ]

            # 4. Bulk upsert into PostGIS
            upserted_count = await self.obs_repo.bulk_upsert(storage_records)

            # Determine final status
            if firms_resp.partial:
                status = "partial"
            elif firms_resp.failed_sources and not firms_resp.successful_sources:
                status = "failed"
            else:
                status = "completed"

            # 5. Complete IngestionRun audit record
            await self.run_repo.complete_run(
                run_id=run_id,
                status=status,
                fetched_count=firms_resp.count + firms_resp.rejected_count,
                valid_count=firms_resp.count,
                rejected_count=firms_resp.rejected_count,
                upserted_count=upserted_count,
                successful_sources=firms_resp.successful_sources,
                failed_sources=firms_resp.failed_sources,
            )
            await self.db.commit()

            logger.info(
                f"Completed FIRMS sync [{run_id}] | Status: {status} | Upserted: {upserted_count} | Valid: {firms_resp.count}"
            )

            return FIRMSSyncResponse(
                status=status,
                run_id=run_id,
                provider="NASA FIRMS",
                sources=source_list,
                requested_bbox=bbox.to_dict(),
                day_range=day_range,
                requested_date=date,
                fetched_count=firms_resp.count + firms_resp.rejected_count,
                valid_count=firms_resp.count,
                rejected_count=firms_resp.rejected_count,
                upserted_count=upserted_count,
                successful_sources=firms_resp.successful_sources,
                failed_sources=firms_resp.failed_sources,
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )

        except FIRMSException as ex:
            logger.error(f"FIRMS sync failed [{run_id}]: {ex.code} - {ex.message}")
            await self.db.rollback()
            await self.run_repo.complete_run(
                run_id=run_id,
                status="failed",
                fetched_count=0,
                valid_count=0,
                rejected_count=0,
                upserted_count=0,
                successful_sources=[],
                failed_sources=source_list,
                error_summary=f"{ex.code}: {ex.message}",
            )
            await self.db.commit()
            raise

        except Exception as ex:
            logger.exception(f"Unexpected error during FIRMS sync [{run_id}]: {ex}")
            await self.db.rollback()
            await self.run_repo.complete_run(
                run_id=run_id,
                status="failed",
                fetched_count=0,
                valid_count=0,
                rejected_count=0,
                upserted_count=0,
                successful_sources=[],
                failed_sources=source_list,
                error_summary=f"INTERNAL_ERROR: {str(ex)}",
            )
            await self.db.commit()
            raise
