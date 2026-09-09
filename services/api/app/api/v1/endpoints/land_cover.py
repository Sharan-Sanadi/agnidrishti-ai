# AGNIDRISHTI API — Phase 5 Land-Cover Intelligence Endpoints
"""
Production endpoints for ESA WorldCover 2021 v200 land-cover intelligence.
- GET /observations/{observation_id}/land-cover: Retrieve profile for single observation (404 if not found)
- POST /land-cover/batch: Batch retrieval with <= 500 IDs max constraint
- POST /land-cover/sync: Controlled sync/precomputation of WorldCover profiles
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.thermal_observation import ThermalObservationModel
from app.db.session import get_db
from app.schemas.land_cover import (
    BatchLandCoverRequest,
    BatchLandCoverResponse,
    LandCoverProfileResponse,
    LandCoverSyncRequest,
    LandCoverSyncResponse,
)
from app.services.land_cover_service import LandCoverService

router = APIRouter(tags=["Land-Cover Intelligence"])


@router.get(
    "/observations/{observation_id}/land-cover",
    response_model=LandCoverProfileResponse,
    summary="Get Land-Cover Intelligence Profile for Observation",
)
async def get_observation_land_cover(
    observation_id: str,
    db: AsyncSession = Depends(get_db),
) -> LandCoverProfileResponse:
    """
    Retrieve or compute ESA WorldCover 2021 v200 land-cover profile for a single canonical thermal observation.
    Returns point class, multi-scale neighborhood composition (250m, 500m, 1000m), and Context V1 classification.
    """
    # Verify observation exists in canonical store
    obs_res = await db.execute(
        select(ThermalObservationModel.observation_id).where(
            ThermalObservationModel.observation_id == observation_id
        )
    )
    if not obs_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal observation '{observation_id}' not found.",
        )

    service = LandCoverService(db)
    try:
        profile = await service.get_or_compute_profile(observation_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate land-cover profile for observation '{observation_id}'.",
            )
        return profile
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"Failed to evaluate land cover for {observation_id}: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing land-cover profile: {str(ex)}",
        ) from ex


@router.post(
    "/land-cover/batch",
    response_model=BatchLandCoverResponse,
    summary="Batch Get Land-Cover Intelligence Profiles",
)
async def batch_get_land_cover(
    body: BatchLandCoverRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchLandCoverResponse:
    """
    Batch retrieve or compute land-cover profiles for observation IDs.
    Enforces maximum batch limit of 500 observation IDs per request (returns 422 if exceeded).
    """
    if len(body.observation_ids) > 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Batch request exceeds maximum limit of 500 observation IDs per request",
        )

    service = LandCoverService(db)
    profiles = await service.get_batch_profiles(body.observation_ids)

    return BatchLandCoverResponse(
        total_requested=len(body.observation_ids),
        count=len(profiles),
        profiles=profiles,
    )


@router.post(
    "/land-cover/sync",
    response_model=LandCoverSyncResponse,
    summary="Sync and Precompute Land-Cover Profiles",
)
async def sync_land_cover(
    body: LandCoverSyncRequest,
    db: AsyncSession = Depends(get_db),
) -> LandCoverSyncResponse:
    """
    Controlled precomputation endpoint for land-cover intelligence.
    Extracts required ESA WorldCover 2021 v200 tiles, processes circular masks,
    and updates database profiles idempotently.
    """
    service = LandCoverService(db)
    try:
        return await service.sync_land_cover(
            observation_ids=body.observation_ids,
            limit=body.limit,
            force_recompute=body.force_recompute,
        )
    except Exception as ex:
        logger.error(f"Land cover sync failed: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Land-cover sync failed: {str(ex)}",
        ) from ex
