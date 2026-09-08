# AGNIDRISHTI API — Phase 3 Temporal Persistence Endpoints
"""
Production endpoints for Phase 3 Temporal Persistence Intelligence and Historical Backfill.
Routes:
- GET /api/v1/observations/{observation_id}/persistence
- POST /api/v1/persistence/batch
- POST /api/v1/history/backfill
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.repositories.thermal_observation import ThermalObservationRepository
from app.db.session import get_db
from app.providers.firms import FIRMSClient, get_firms_client
from app.schemas.firms import BoundingBox
from app.schemas.persistence import (
    BackfillRequest,
    BackfillResponse,
    BatchPersistenceRequest,
    BatchPersistenceResponse,
    PersistenceProfileResponse,
)
from app.services.historical_backfill import HistoricalBackfillService
from app.services.temporal_persistence import TemporalPersistenceService

router = APIRouter()


@router.get(
    "/observations/{observation_id}/persistence",
    response_model=PersistenceProfileResponse,
    summary="Get temporal persistence profile for a single observation",
    description="Computes spatiotemporal recurrence metrics, PostGIS ST_DWithin neighborhood, and V1 persistence index relative to observation acquisition time.",
)
async def get_observation_persistence(
    observation_id: str,
    radius_m: float | None = Query(None, ge=250.0, le=2000.0, description="Spatial association radius (meters)"),
    db: AsyncSession = Depends(get_db),
) -> PersistenceProfileResponse:
    obs_repo = ThermalObservationRepository(db)
    obs = await obs_repo.get_by_id(observation_id)

    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "OBSERVATION_NOT_FOUND",
                "message": f"Observation '{observation_id}' not found in PostGIS.",
            },
        )

    service = TemporalPersistenceService(db)
    try:
        profile = await service.analyze_observation(observation=obs, radius_m=radius_m)
        return PersistenceProfileResponse(**profile.to_dict())
    except Exception as ex:
        logger.exception(f"Persistence analysis failed for {observation_id}: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "PERSISTENCE_ANALYSIS_ERROR",
                "message": f"Failed to compute persistence profile: {str(ex)}",
            },
        ) from ex


@router.post(
    "/persistence/batch",
    response_model=BatchPersistenceResponse,
    summary="Batch temporal persistence analysis for multiple observations",
    description="Computes persistence profiles for a list of observation IDs in a single batch call for GIS map rendering.",
)
async def get_batch_persistence(
    payload: BatchPersistenceRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchPersistenceResponse:
    obs_repo = ThermalObservationRepository(db)
    service = TemporalPersistenceService(db)

    profiles: dict[str, PersistenceProfileResponse] = {}

    for obs_id in payload.observation_ids:
        obs = await obs_repo.get_by_id(obs_id)
        if obs:
            try:
                prof = await service.analyze_observation(observation=obs, radius_m=payload.radius_m)
                profiles[obs_id] = PersistenceProfileResponse(**prof.to_dict())
            except Exception as ex:
                logger.warning(f"Batch persistence failed for {obs_id}: {ex}")

    alg_version = next(iter(profiles.values())).algorithm_version if profiles else "temporal_persistence_v1"

    return BatchPersistenceResponse(
        algorithm_version=alg_version,
        count=len(profiles),
        profiles=profiles,
    )


@router.post(
    "/history/backfill",
    response_model=BackfillResponse,
    summary="Execute controlled historical NASA FIRMS data backfill into PostGIS",
    description="Fetches 30-day historical NASA FIRMS observations in controlled 5-day chunks and upserts idempotently into PostGIS.",
)
async def execute_history_backfill(
    payload: BackfillRequest | None = None,
    db: AsyncSession = Depends(get_db),
    client: FIRMSClient = Depends(get_firms_client),
) -> BackfillResponse:
    req = payload or BackfillRequest()

    bbox: BoundingBox | None = None
    if any(c is not None for c in (req.west, req.south, req.east, req.north)):
        try:
            w = req.west if req.west is not None else 68.0
            s = req.south if req.south is not None else 6.0
            e = req.east if req.east is not None else 97.0
            n = req.north if req.north is not None else 37.0
            bbox = BoundingBox(west=w, south=s, east=e, north=n)
        except ValueError as ex:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INVALID_BOUNDING_BOX",
                    "message": str(ex),
                },
            ) from ex

    service = HistoricalBackfillService(db=db, firms_client=client)

    try:
        res = await service.execute_backfill(
            bbox=bbox,
            days_history=req.days_history,
            sources=req.sources,
            chunk_days=req.chunk_days,
        )
        return BackfillResponse(**res)
    except Exception as ex:
        logger.exception(f"History backfill failed: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "HISTORY_BACKFILL_FAILED",
                "message": f"Historical backfill failed: {str(ex)}",
            },
        ) from ex
