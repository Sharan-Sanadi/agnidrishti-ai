# AGNIDRISHTI API — Phase 9 Model Explainability Endpoints
"""
Production API endpoints for Phase 9 Model Explainability Engine.
Routes:
- GET  /api/v1/observations/{observation_id}/explanation
- POST /api/v1/explanations/batch
- POST /api/v1/explanations/sync
- GET  /api/v1/explanations/global
Zero external network calls (NASA, Overpass, WorldCover, CDSE = 0).
Zero retraining.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.thermal_observation import ThermalObservationModel
from app.db.session import get_db
from app.ml.explainability.constants import EXPLANATION_VERSION
from app.ml.explainability.global_importance import global_importance_manager
from app.ml.explainability.schemas import (
    BatchExplanationRequest,
    BatchExplanationResponse,
    GlobalExplanationResponse,
    LocalExplanationResponse,
    SyncExplanationRequest,
    SyncExplanationResponse,
)
from app.ml.explainability.service import explainability_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/explanations/global",
    response_model=GlobalExplanationResponse,
    summary="Get global model feature importance and evidence group contributions",
    description="Returns precomputed permutation importance from the held-out test evaluation split with rank and evidence group contributions. Instant cached response.",
)
async def get_global_model_explanation() -> GlobalExplanationResponse:
    report = global_importance_manager.report
    if not report:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "GLOBAL_IMPORTANCE_UNAVAILABLE",
                "message": "Global model feature importance report is not available on server.",
            },
        )
    return report


@router.get(
    "/observations/{observation_id}/explanation",
    response_model=LocalExplanationResponse,
    summary="Get local model explanation for a single observation",
    description="Retrieves the cached model attribution explanation (TreeSHAP or LinearContribution) for a classified FIRMS observation.",
)
async def get_observation_explanation(
    observation_id: str,
    db: AsyncSession = Depends(get_db),
) -> LocalExplanationResponse:
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

    # 2. Fetch cached explanation
    explanation = await explainability_service.get_explanation_for_observation(observation_id, db)
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "EXPLANATION_NOT_FOUND",
                "message": (
                    f"Model explanation not found for observation '{observation_id}'. "
                    "Execute /api/v1/explanations/sync first."
                ),
            },
        )

    return explanation


@router.post(
    "/explanations/batch",
    response_model=BatchExplanationResponse,
    summary="Batch retrieval of cached model explanations",
    description="Bulk retrieves cached model explanations from PostGIS (max 500 IDs).",
)
async def get_batch_explanations(
    payload: BatchExplanationRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchExplanationResponse:
    try:
        exps = await explainability_service.batch_explain(
            observation_ids=payload.observation_ids,
            session=db,
        )
        return BatchExplanationResponse(
            explanation_version=EXPLANATION_VERSION,
            count=len(exps),
            explanations=exps,
        )
    except Exception as ex:
        logger.exception("Batch explanation retrieval failed: %s", ex)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "BATCH_EXPLANATION_ERROR",
                "message": f"Failed to retrieve batch explanations: {str(ex)}",
            },
        ) from ex


@router.post(
    "/explanations/sync",
    response_model=SyncExplanationResponse,
    summary="Sync and persist model explanations in PostGIS",
    description="Orchestrates TreeSHAP attribution inference on classified observations, validates mathematical additivity, and upserts explanations. Zero external network calls.",
)
async def sync_explanations(
    payload: SyncExplanationRequest,
    db: AsyncSession = Depends(get_db),
) -> SyncExplanationResponse:
    try:
        return await explainability_service.sync_explanations(
            observation_ids=payload.observation_ids,
            session=db,
            force_recompute=payload.force_recompute,
        )
    except Exception as ex:
        logger.exception("Explanation sync failed: %s", ex)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "EXPLANATION_SYNC_ERROR",
                "message": f"Failed to execute explanation sync: {str(ex)}",
            },
        ) from ex
