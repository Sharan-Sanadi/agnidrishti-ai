# AGNIDRISHTI API — Phase 7 Feature Fusion Endpoints
"""
Production endpoints for Phase 7 Feature Fusion Intelligence.
Routes:
- GET  /api/v1/observations/{observation_id}/fusion
- POST /api/v1/fusion/batch
- POST /api/v1/fusion/sync
- GET  /api/v1/fusion/schema
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.thermal_observation import ThermalObservationModel
from app.db.session import get_db
from app.schemas.fusion import (
    BatchFusionRequest,
    BatchFusionResponse,
    FusionFeatureSpecResponse,
    FusionProfileResponse,
    FusionSchemaResponse,
    SyncFusionRequest,
    SyncFusionResponse,
)
from app.services.fusion import (
    SCHEMA_VERSION_V1,
    FeatureFusionService,
    fusion_v1_registry,
)

router = APIRouter()


@router.get(
    "/fusion/schema",
    response_model=FusionSchemaResponse,
    summary="Get canonical fusion_v1 feature schema and registry",
    description="Returns the deterministic ordered feature registry, types, units, nullability, model-eligibility, and SHA-256 schema hash.",
)
async def get_fusion_schema() -> FusionSchemaResponse:
    return FusionSchemaResponse(
        schema_version=fusion_v1_registry.schema_version,
        schema_hash=fusion_v1_registry.schema_hash,
        total_features=fusion_v1_registry.total_feature_count,
        model_eligible_features=fusion_v1_registry.model_eligible_count,
        features=[
            FusionFeatureSpecResponse(
                name=f.name,
                group=f.group,
                source_phase=f.source_phase,
                source_field=f.source_field,
                dtype=f.dtype,
                unit=f.unit,
                nullable=f.nullable,
                model_eligible=f.model_eligible,
                description=f.description,
            )
            for f in fusion_v1_registry.features
        ],
    )


@router.get(
    "/observations/{observation_id}/fusion",
    response_model=FusionProfileResponse,
    summary="Get feature fusion profile for a single observation",
    description="Retrieves the versioned, deterministic machine-readable feature vector and profile for a canonical FIRMS observation.",
)
async def get_observation_fusion(
    observation_id: str,
    schema_version: str = Query(SCHEMA_VERSION_V1, description="Requested schema version"),
    db: AsyncSession = Depends(get_db),
) -> FusionProfileResponse:
    # 1. Verify observation exists in canonical store
    obs_stmt = select(ThermalObservationModel.observation_id).where(
        ThermalObservationModel.observation_id == observation_id
    )
    obs_res = await db.execute(obs_stmt)
    if not obs_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "OBSERVATION_NOT_FOUND",
                "message": f"Observation '{observation_id}' not found in PostGIS canonical store.",
            },
        )

    # 2. Fetch cached profile
    service = FeatureFusionService(db)
    profile = await service.get_profile(observation_id, schema_version=schema_version)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "FUSION_PROFILE_NOT_FOUND",
                "message": f"Feature fusion profile not found for observation '{observation_id}'. Execute /api/v1/fusion/sync first.",
            },
        )

    return profile


@router.post(
    "/fusion/batch",
    response_model=BatchFusionResponse,
    summary="Batch retrieval of cached feature fusion profiles",
    description="Bulk retrieves cached feature fusion profiles from PostGIS in a single query (max 500 IDs).",
)
async def get_batch_fusion(
    payload: BatchFusionRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchFusionResponse:
    service = FeatureFusionService(db)
    try:
        return await service.get_batch_profiles(
            observation_ids=payload.observation_ids,
            schema_version=payload.schema_version,
        )
    except Exception as ex:
        logger.exception(f"Batch fusion retrieval failed: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "BATCH_FUSION_ERROR",
                "message": f"Failed to retrieve batch fusion profiles: {str(ex)}",
            },
        ) from ex


@router.post(
    "/fusion/sync",
    response_model=SyncFusionResponse,
    summary="Sync and persist feature fusion profiles in PostGIS",
    description="Gathers local evidence across Phases 1-6, verifies invariants, computes fingerprints, and upserts profiles. Zero external network calls.",
)
async def sync_fusion(
    payload: SyncFusionRequest,
    db: AsyncSession = Depends(get_db),
) -> SyncFusionResponse:
    service = FeatureFusionService(db)
    try:
        return await service.sync_batch(
            observation_ids=payload.observation_ids,
            force_recompute=payload.force_recompute,
        )
    except Exception as ex:
        logger.exception(f"Fusion sync failed: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "FUSION_SYNC_ERROR",
                "message": f"Failed to execute fusion sync: {str(ex)}",
            },
        ) from ex
