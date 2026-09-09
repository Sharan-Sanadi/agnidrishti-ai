# AGNIDRISHTI API — Phase 8 Classification Endpoints
"""
Production API endpoints for Phase 8 Intelligent Classification Engine.
Routes:
- GET  /api/v1/observations/{observation_id}/classification
- POST /api/v1/classification/batch
- POST /api/v1/classification/sync
- GET  /api/v1/classification/model
Zero external network calls (NASA, Overpass, WorldCover, CDSE = 0).
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.thermal_observation import ThermalObservationModel
from app.db.session import get_db
from app.ml.classification.constants import MODEL_VERSION
from app.ml.classification.registry import model_registry
from app.ml.classification.schemas import (
    BatchClassificationRequest,
    BatchClassificationResponse,
    ClassificationPredictionResponse,
    ModelMetadataResponse,
    SyncClassificationRequest,
    SyncClassificationResponse,
)
from app.ml.classification.service import classification_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/classification/model",
    response_model=ModelMetadataResponse,
    summary="Get Phase 8 model metadata, manifest, and validation metrics",
    description="Returns public manifest, cryptographic SHA-256 artifact hash, features, and weak-label agreement metrics. Does not expose server filesystem paths.",
)
async def get_classification_model_metadata() -> ModelMetadataResponse:
    manifest = model_registry.manifest
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "MODEL_UNAVAILABLE",
                "message": f"Phase 8 model '{MODEL_VERSION}' is not loaded or unavailable on server.",
            },
        )

    # Parse trained_at datetime
    try:
        trained_dt = datetime.fromisoformat(manifest.trained_at)
    except Exception:
        trained_dt = datetime.now()

    return ModelMetadataResponse(
        model_version=manifest.model_version,
        model_family=manifest.model_family,
        validation_status=manifest.validation_status,
        trained_at=trained_dt,
        fusion_schema_version=manifest.fusion_schema_version,
        fusion_schema_hash=manifest.fusion_schema_hash,
        training_dataset_fingerprint=manifest.training_dataset_fingerprint,
        classes=manifest.classes,
        features=manifest.ordered_features,
        metrics=manifest.metrics,
        artifact_hash=manifest.model_artifact_hash,
    )


@router.get(
    "/observations/{observation_id}/classification",
    response_model=ClassificationPredictionResponse,
    summary="Get classification prediction for a single observation",
    description="Retrieves the cached ML classification prediction for a canonical FIRMS observation.",
)
async def get_observation_classification(
    observation_id: str,
    db: AsyncSession = Depends(get_db),
) -> ClassificationPredictionResponse:
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

    # 2. Fetch cached classification prediction
    pred = await classification_service.get_classification_for_observation(observation_id, db)
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CLASSIFICATION_NOT_FOUND",
                "message": (
                    f"Classification prediction not found for observation '{observation_id}'. "
                    "Execute /api/v1/classification/sync first."
                ),
            },
        )

    return pred


@router.post(
    "/classification/batch",
    response_model=BatchClassificationResponse,
    summary="Batch retrieval of cached classification predictions",
    description="Bulk retrieves cached classification predictions from PostGIS (max 500 IDs).",
)
async def get_batch_classification(
    payload: BatchClassificationRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchClassificationResponse:
    try:
        preds = await classification_service.batch_classify(
            observation_ids=payload.observation_ids,
            session=db,
            model_version=payload.model_version,
        )
        return BatchClassificationResponse(
            model_version=payload.model_version,
            count=len(preds),
            predictions=preds,
        )
    except Exception as ex:
        logger.exception("Batch classification retrieval failed: %s", ex)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "BATCH_CLASSIFICATION_ERROR",
                "message": f"Failed to retrieve batch classifications: {str(ex)}",
            },
        ) from ex


@router.post(
    "/classification/sync",
    response_model=SyncClassificationResponse,
    summary="Sync and persist classification predictions in PostGIS",
    description="Evaluates evidence gating, runs batch inference on un-cached/stale observations, and upserts predictions. Zero external network calls.",
)
async def sync_classification(
    payload: SyncClassificationRequest,
    db: AsyncSession = Depends(get_db),
) -> SyncClassificationResponse:
    try:
        return await classification_service.sync_classification(
            observation_ids=payload.observation_ids,
            session=db,
            force_recompute=payload.force_recompute,
        )
    except Exception as ex:
        logger.exception("Classification sync failed: %s", ex)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "CLASSIFICATION_SYNC_ERROR",
                "message": f"Failed to execute classification sync: {str(ex)}",
            },
        ) from ex
