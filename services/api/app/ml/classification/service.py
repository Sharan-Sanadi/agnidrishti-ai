# AGNIDRISHTI API — Phase 8 Classification Service
"""
Business logic and persistence orchestration for Phase 8 Intelligent Classification Engine.
Provides single-observation classification, bulk 500-chunked retrieval, and
network-isolated sync execution with strict idempotency.
Zero external calls (NASA, Overpass, WorldCover, CDSE = 0).
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.classification import ThermalClassificationPredictionModel
from app.db.models.feature_fusion_profile import ThermalFeatureFusionProfileModel
from app.ml.classification.constants import (
    MIN_MODEL_FEATURE_COVERAGE,
    MODEL_VERSION,
    STATUS_AVAILABLE,
    STATUS_ERROR,
    STATUS_INSUFFICIENT_EVIDENCE,
    VALIDATION_WEAK_SUPERVISION,
)
from app.ml.classification.registry import model_registry
from app.ml.classification.schemas import (
    ClassificationPredictionResponse,
    SyncClassificationResponse,
)

logger = logging.getLogger(__name__)


class ClassificationService:
    """
    High-performance classification inference service.
    Consumes local fusion_v1 profiles without external network requests.
    """

    def __init__(self) -> None:
        self.registry = model_registry

    async def get_classification_for_observation(
        self,
        observation_id: str,
        session: AsyncSession,
    ) -> ClassificationPredictionResponse | None:
        """
        Retrieve or compute classification for a single canonical observation.
        Returns None if observation has no fusion_v1 profile.
        """
        results = await self.batch_classify([observation_id], session)
        return results.get(observation_id)

    async def batch_classify(
        self,
        observation_ids: list[str],
        session: AsyncSession,
        model_version: str = MODEL_VERSION,
    ) -> dict[str, ClassificationPredictionResponse]:
        """
        Bulk fetch cached classification predictions for up to 500 observation IDs.
        No N+1 queries.
        """
        if not observation_ids:
            return {}

        query = select(ThermalClassificationPredictionModel).where(
            ThermalClassificationPredictionModel.observation_id.in_(observation_ids),
            ThermalClassificationPredictionModel.model_version == model_version,
        )
        res = await session.execute(query)
        predictions = res.scalars().all()

        out: dict[str, ClassificationPredictionResponse] = {}
        for p in predictions:
            out[p.observation_id] = ClassificationPredictionResponse(
                observation_id=p.observation_id,
                classification_status=p.classification_status,
                predicted_class=p.predicted_class,
                class_score=p.class_score,
                class_probabilities=p.class_probabilities,
                evidence_coverage=p.evidence_coverage,
                validation_status=p.validation_status,
                model_version=p.model_version,
                fusion_schema_version=p.fusion_schema_version,
                fusion_schema_hash=p.fusion_schema_hash,
                fusion_source_fingerprint=p.fusion_source_fingerprint,
                predicted_at=p.predicted_at,
            )
        return out

    async def sync_classification(
        self,
        observation_ids: list[str],
        session: AsyncSession,
        force_recompute: bool = False,
    ) -> SyncClassificationResponse:
        """
        Synchronize classification predictions for a batch of canonical observation IDs.
        Pipeline:
        1. Bulk fetch fusion_v1 profiles from database.
        2. Bulk fetch existing predictions for idempotency check.
        3. Check evidence gate and model availability.
        4. Run single batch array inference for observations requiring prediction.
        5. Persist/update predictions in PostGIS.
        Zero external provider requests.
        """
        start_time = time.perf_counter()
        db_queries = 0

        if not observation_ids:
            return SyncClassificationResponse(
                requested=0,
                created=0,
                updated=0,
                reused=0,
                available=0,
                insufficient_evidence=0,
                class_distribution={},
                duration_ms=0.0,
                database_queries=0,
            )

        # 1. Bulk query fusion profiles
        q_profiles = select(ThermalFeatureFusionProfileModel).where(
            ThermalFeatureFusionProfileModel.observation_id.in_(observation_ids),
            ThermalFeatureFusionProfileModel.schema_version == "fusion_v1",
        )
        res_profiles = await session.execute(q_profiles)
        db_queries += 1
        profiles_by_id = {p.observation_id: p for p in res_profiles.scalars().all()}

        # 2. Bulk query existing predictions
        q_preds = select(ThermalClassificationPredictionModel).where(
            ThermalClassificationPredictionModel.observation_id.in_(observation_ids),
            ThermalClassificationPredictionModel.model_version == MODEL_VERSION,
        )
        res_preds = await session.execute(q_preds)
        db_queries += 1
        existing_preds = {p.observation_id: p for p in res_preds.scalars().all()}

        created_count = 0
        updated_count = 0
        reused_count = 0
        available_count = 0
        insufficient_count = 0
        class_dist: dict[str, int] = {}

        # 3. Identify which observations need fresh inference
        to_infer_obs_ids: list[str] = []
        to_infer_rows: list[list[Any]] = []

        manifest = self.registry.manifest
        ordered_features = manifest.ordered_features if manifest else []
        model = self.registry.model
        model_status = self.registry.status
        val_status = manifest.validation_status if manifest else VALIDATION_WEAK_SUPERVISION
        artifact_hash = manifest.model_artifact_hash if manifest else None

        records_to_upsert: dict[str, dict[str, Any]] = {}

        for obs_id in observation_ids:
            profile = profiles_by_id.get(obs_id)
            if not profile:
                continue

            existing = existing_preds.get(obs_id)

            # Check if existing prediction is fresh and idempotent
            if (
                existing is not None
                and not force_recompute
                and existing.fusion_source_fingerprint == profile.source_fingerprint
                and existing.classification_status == STATUS_AVAILABLE
            ):
                reused_count += 1
                available_count += 1
                if existing.predicted_class:
                    class_dist[existing.predicted_class] = class_dist.get(existing.predicted_class, 0) + 1
                continue

            # Minimum evidence gating check
            coverage = profile.feature_coverage_fraction
            if coverage < MIN_MODEL_FEATURE_COVERAGE:
                insufficient_count += 1
                records_to_upsert[obs_id] = {
                    "observation_id": obs_id,
                    "model_version": MODEL_VERSION,
                    "fusion_schema_version": profile.schema_version,
                    "fusion_schema_hash": profile.schema_hash,
                    "fusion_source_fingerprint": profile.source_fingerprint,
                    "classification_status": STATUS_INSUFFICIENT_EVIDENCE,
                    "predicted_class": None,
                    "class_score": None,
                    "class_probabilities": None,
                    "evidence_coverage": coverage,
                    "validation_status": val_status,
                    "model_artifact_hash": artifact_hash,
                }
                continue

            # If model is unavailable / invalid / schema mismatched
            if not self.registry.is_available or model is None:
                records_to_upsert[obs_id] = {
                    "observation_id": obs_id,
                    "model_version": MODEL_VERSION,
                    "fusion_schema_version": profile.schema_version,
                    "fusion_schema_hash": profile.schema_hash,
                    "fusion_source_fingerprint": profile.source_fingerprint,
                    "classification_status": model_status,
                    "predicted_class": None,
                    "class_score": None,
                    "class_probabilities": None,
                    "evidence_coverage": coverage,
                    "validation_status": val_status,
                    "model_artifact_hash": artifact_hash,
                }
                continue

            # Eligible for ML model inference
            row = [profile.feature_vector.get(f) for f in ordered_features]
            to_infer_obs_ids.append(obs_id)
            to_infer_rows.append(row)

        # 4. Execute batch array inference if observations need prediction
        if to_infer_obs_ids and model is not None:
            try:
                x_mat = np.array(to_infer_rows, dtype=object)
                preds = model.predict(x_mat)
                has_proba = hasattr(model, "predict_proba")
                probas = model.predict_proba(x_mat) if has_proba else None
                class_labels: list[str] = list(getattr(model, "classes_", []))

                for i, obs_id in enumerate(to_infer_obs_ids):
                    profile = profiles_by_id[obs_id]
                    pred_class = str(preds[i])

                    class_prob_dict: dict[str, float] | None = None
                    score: float = 1.0

                    if probas is not None and class_labels:
                        prob_row = probas[i]
                        class_prob_dict = {
                            lbl: round(float(prob_row[idx]), 4)
                            for idx, lbl in enumerate(class_labels)
                        }
                        if pred_class in class_prob_dict:
                            score = class_prob_dict[pred_class]

                    available_count += 1
                    class_dist[pred_class] = class_dist.get(pred_class, 0) + 1

                    records_to_upsert[obs_id] = {
                        "observation_id": obs_id,
                        "model_version": MODEL_VERSION,
                        "fusion_schema_version": profile.schema_version,
                        "fusion_schema_hash": profile.schema_hash,
                        "fusion_source_fingerprint": profile.source_fingerprint,
                        "classification_status": STATUS_AVAILABLE,
                        "predicted_class": pred_class,
                        "class_score": round(score, 4),
                        "class_probabilities": class_prob_dict,
                        "evidence_coverage": round(profile.feature_coverage_fraction, 4),
                        "validation_status": val_status,
                        "model_artifact_hash": artifact_hash,
                    }
            except Exception as e:
                logger.error("Batch classification inference failed: %s", e, exc_info=True)
                for obs_id in to_infer_obs_ids:
                    profile = profiles_by_id[obs_id]
                    records_to_upsert[obs_id] = {
                        "observation_id": obs_id,
                        "model_version": MODEL_VERSION,
                        "fusion_schema_version": profile.schema_version,
                        "fusion_schema_hash": profile.schema_hash,
                        "fusion_source_fingerprint": profile.source_fingerprint,
                        "classification_status": STATUS_ERROR,
                        "predicted_class": None,
                        "class_score": None,
                        "class_probabilities": None,
                        "evidence_coverage": profile.feature_coverage_fraction,
                        "validation_status": val_status,
                        "model_artifact_hash": artifact_hash,
                    }

        # 5. Persist records to database
        now = datetime.now(UTC)
        for obs_id, payload in records_to_upsert.items():
            existing = existing_preds.get(obs_id)
            if existing:
                for k, v in payload.items():
                    setattr(existing, k, v)
                existing.predicted_at = now
                updated_count += 1
            else:
                new_pred = ThermalClassificationPredictionModel(
                    **payload,
                    predicted_at=now,
                )
                session.add(new_pred)
                created_count += 1

        if created_count > 0 or updated_count > 0:
            await session.commit()
            db_queries += 1

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return SyncClassificationResponse(
            requested=len(observation_ids),
            created=created_count,
            updated=updated_count,
            reused=reused_count,
            available=available_count,
            insufficient_evidence=insufficient_count,
            class_distribution=class_dist,
            duration_ms=round(duration_ms, 2),
            database_queries=db_queries,
        )


classification_service = ClassificationService()
