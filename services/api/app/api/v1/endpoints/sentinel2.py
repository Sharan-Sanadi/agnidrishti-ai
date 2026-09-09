# AGNIDRISHTI API — Phase 6 Sentinel-2 API Endpoints
"""
Production endpoints for Phase 6 Sentinel-2 Optical/SWIR Satellite Context Intelligence.
Routes:
- GET /api/v1/observations/{observation_id}/sentinel-2
- POST /api/v1/sentinel-2/batch (max 500)
- POST /api/v1/sentinel-2/sync (max 50)
- GET /api/v1/observations/{observation_id}/sentinel-2/preview
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.thermal_observation import ThermalObservationModel
from app.db.session import get_db
from app.providers.sentinel2.constants import (
    ANALYTICAL_RESOLUTION_M,
    SENTINEL_COLLECTION_NAME,
    SentinelProviderStatus,
    SentinelQualityStatus,
)
from app.schemas.sentinel2 import (
    BatchSentinelProfileRequest,
    BatchSentinelProfileResponse,
    SentinelContextProfileResponse,
    SentinelSyncRequest,
    SentinelSyncResponse,
)
from app.services.sentinel_context_service import SentinelContextService

router = APIRouter()


@router.get(
    "/observations/{observation_id}/sentinel-2",
    response_model=SentinelContextProfileResponse,
    summary="Get Sentinel-2 Satellite Context Profile for Observation",
    description="Returns high-resolution Sentinel-2 optical/SWIR reflectance, cloud-masking quality, and spectral indices (NDVI, NDMI, NBR). Returns NOT_EVALUATED if uncomputed.",
)
async def get_observation_sentinel_context(
    observation_id: str,
    db: AsyncSession = Depends(get_db),
) -> SentinelContextProfileResponse:
    """Retrieve cached Sentinel-2 profile for a canonical thermal observation."""
    # 1. Verify observation exists in canonical PostGIS store
    obs_stmt = select(ThermalObservationModel).where(
        ThermalObservationModel.observation_id == observation_id
    )
    obs_res = await db.execute(obs_stmt)
    obs = obs_res.scalar_one_or_none()
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal observation '{observation_id}' not found.",
        )

    service = SentinelContextService(db)
    profile = await service.get_profile(observation_id)

    if profile is None:
        # Return standard NOT_EVALUATED profile without triggering heavy computation
        target_time = obs.acquisition_time_utc
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=UTC)
        else:
            target_time = target_time.astimezone(UTC)

        return SentinelContextProfileResponse(
            observation_id=observation_id,
            provider="CDSE",
            collection=SENTINEL_COLLECTION_NAME,
            target_firms_time_utc=target_time,
            quality_status=SentinelQualityStatus.UNAVAILABLE,
            provider_status=SentinelProviderStatus.NOT_EVALUATED,
            analytical_resolution_m=ANALYTICAL_RESOLUTION_M,
            processed_at=datetime.now(UTC),
        )

    return profile


@router.post(
    "/sentinel-2/batch",
    response_model=BatchSentinelProfileResponse,
    summary="Batch Get Cached Sentinel-2 Context Profiles",
    description="Batch retrieve already-computed Sentinel-2 context profiles from PostGIS. Maximum limit 500 IDs per request.",
)
async def batch_get_sentinel_context(
    body: BatchSentinelProfileRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchSentinelProfileResponse:
    """Read cached Sentinel-2 context profiles in batch (max 500)."""
    if len(body.observation_ids) > 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Batch request exceeds maximum limit of 500 observation IDs per request.",
        )

    service = SentinelContextService(db)
    profiles = await service.get_batch_profiles(body.observation_ids)

    return BatchSentinelProfileResponse(
        total_requested=len(body.observation_ids),
        count=len(profiles),
        profiles=profiles,
    )


@router.post(
    "/sentinel-2/sync",
    response_model=SentinelSyncResponse,
    summary="Controlled Sentinel-2 Remote Synchronization and Precomputation",
    description="Executes controlled remote CDSE STAC and Process API retrieval for at most 50 observation IDs per request.",
)
async def sync_sentinel_context(
    body: SentinelSyncRequest,
    db: AsyncSession = Depends(get_db),
) -> SentinelSyncResponse:
    """Trigger bounded remote Sentinel-2 evaluation and PostGIS caching."""
    if len(body.observation_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Sync request exceeds maximum batch limit of 50 observation IDs per request to protect provider quota.",
        )

    service = SentinelContextService(db)
    return await service.sync_batch(
        observation_ids=body.observation_ids,
        force_refresh=body.force_refresh,
    )


@router.get(
    "/observations/{observation_id}/sentinel-2/preview",
    summary="Get Sentinel-2 Imagery Preview",
    description="Generates server-controlled True-Color RGB or SWIR Context false-color preview image for human context.",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Rendered preview image",
        }
    },
)
async def get_sentinel_preview(
    observation_id: str,
    mode: str = Query("true_color", pattern="^(true_color|swir_context)$"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Retrieve pre-rendered or on-demand preview image (PNG)."""
    service = SentinelContextService(db)
    try:
        image_bytes = await service.get_preview(observation_id, mode=mode)
        return Response(content=image_bytes, media_type="image/png")
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ex),
        ) from ex
    except Exception as ex:
        logger.error(f"Error generating {mode} preview for {observation_id}: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview generation failed: {str(ex)}",
        ) from ex
