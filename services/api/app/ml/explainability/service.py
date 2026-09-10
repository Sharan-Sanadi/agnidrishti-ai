# AGNIDRISHTI API — Phase 9 Explainability Service
"""
Business logic, validation, and PostGIS persistence orchestration for Phase 9 Model Explainability.
Provides single-observation explanation, 500-chunked retrieval, and
network-isolated sync execution with strict idempotency and staleness detection.
Zero external calls (NASA, Overpass, WorldCover, CDSE = 0).
Zero retraining.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.classification import ThermalClassificationPredictionModel
from app.db.models.explainability import ThermalClassificationExplanationModel
from app.db.models.feature_fusion_profile import ThermalFeatureFusionProfileModel
from app.ml.classification.constants import (
    MODEL_VERSION,
)
from app.ml.classification.constants import (
    STATUS_INSUFFICIENT_EVIDENCE as P8_STATUS_INSUFFICIENT_EVIDENCE,
)
from app.ml.classification.registry import model_registry
from app.ml.explainability.constants import (
    EXPLANATION_VERSION,
    METHOD_TREESHAP,
    METHOD_VERSION_TREESHAP,
    STATUS_AVAILABLE,
    STATUS_ERROR,
    STATUS_INSUFFICIENT_EVIDENCE,
    STATUS_MODEL_INVALID,
    STATUS_MODEL_UNAVAILABLE,
    STATUS_PREDICTION_STALE,
    STATUS_SCHEMA_MISMATCH,
)
from app.ml.explainability.provider import get_explanation_provider
from app.ml.explainability.schemas import (
    FeatureContributionItem,
    GroupContributionItem,
    LocalExplanationResponse,
    SyncExplanationResponse,
)

logger = logging.getLogger(__name__)


class ExplainabilityService:
    """
    High-performance model explainability service.
    Consumes local fusion_v1 profiles and Phase-8 classification predictions.
    """

    def __init__(self) -> None:
        self.registry = model_registry

    async def get_explanation_for_observation(
        self,
        observation_id: str,
        session: AsyncSession,
    ) -> LocalExplanationResponse | None:
        """Retrieve cached explanation for a single canonical observation."""
        results = await self.batch_explain([observation_id], session)
        return results.get(observation_id)

    async def batch_explain(
        self,
        observation_ids: list[str],
        session: AsyncSession,
        model_version: str = MODEL_VERSION,
        explanation_version: str = EXPLANATION_VERSION,
    ) -> dict[str, LocalExplanationResponse]:
        """
        Bulk fetch cached explanations for up to 500 observation IDs.
        No N+1 queries.
        """
        if not observation_ids:
            return {}

        query = select(ThermalClassificationExplanationModel).where(
            ThermalClassificationExplanationModel.observation_id.in_(observation_ids),
            ThermalClassificationExplanationModel.model_version == model_version,
            ThermalClassificationExplanationModel.explanation_version == explanation_version,
        )
        res = await session.execute(query)
        explanations = res.scalars().all()

        # We also bulk-fetch predictions to populate validation_status and feature_coverage if needed
        pred_query = select(ThermalClassificationPredictionModel).where(
            ThermalClassificationPredictionModel.observation_id.in_(observation_ids),
            ThermalClassificationPredictionModel.model_version == model_version,
        )
        res_preds = await session.execute(pred_query)
        preds_by_id = {p.observation_id: p for p in res_preds.scalars().all()}

        out: dict[str, LocalExplanationResponse] = {}
        for exp in explanations:
            pred = preds_by_id.get(exp.observation_id)
            val_status = pred.validation_status if pred else "WEAK_SUPERVISION_PROTOTYPE"
            evidence_cov = pred.evidence_coverage if pred else None

            # Parse top supporting
            top_sup = [
                FeatureContributionItem(**item)
                for item in (exp.top_supporting or [])
            ]
            # Parse top opposing
            top_opp = [
                FeatureContributionItem(**item)
                for item in (exp.top_opposing or [])
            ]
            # Parse groups
            groups_dict = {
                k: GroupContributionItem(**v)
                for k, v in (exp.group_contributions or {}).items()
            }

            out[exp.observation_id] = LocalExplanationResponse(
                observation_id=exp.observation_id,
                explanation_status=exp.explanation_status,
                predicted_class=exp.predicted_class,
                prediction_score=exp.prediction_score,
                model_version=exp.model_version,
                validation_status=val_status,
                explanation_version=exp.explanation_version,
                method=exp.method_name,
                feature_coverage=evidence_cov,
                base_value=exp.base_value,
                explained_output=exp.explained_output,
                additivity_error=exp.additivity_error,
                top_supporting_features=top_sup,
                top_opposing_features=top_opp,
                group_contributions=groups_dict,
                quality_flags=exp.quality_flags or [],
                generated_at=exp.generated_at,
            )
        return out

    async def sync_explanations(
        self,
        observation_ids: list[str],
        session: AsyncSession,
        force_recompute: bool = False,
    ) -> SyncExplanationResponse:
        """
        Synchronize model explanations for a batch of canonical observation IDs.
        Pipeline:
        1. Bulk fetch Phase-8 predictions.
        2. Bulk fetch fusion_v1 profiles.
        3. Bulk fetch existing explanations.
        4. Validate model artifact integrity and fusion schema.
        5. Check idempotency and evidence gating.
        6. Execute provider attribution in batch.
        7. Persist explanations to PostGIS.
        Zero external provider requests.
        """
        start_time = time.perf_counter()
        db_queries = 0

        if not observation_ids:
            return SyncExplanationResponse(
                requested=0,
                created=0,
                updated=0,
                reused=0,
                available=0,
                insufficient_evidence=0,
                duration_ms=0.0,
                database_queries=0,
            )

        # 1. Bulk fetch Phase-8 predictions
        q_preds = select(ThermalClassificationPredictionModel).where(
            ThermalClassificationPredictionModel.observation_id.in_(observation_ids),
            ThermalClassificationPredictionModel.model_version == MODEL_VERSION,
        )
        res_preds = await session.execute(q_preds)
        db_queries += 1
        preds_by_id = {p.observation_id: p for p in res_preds.scalars().all()}

        # 2. Bulk fetch fusion profiles
        q_profiles = select(ThermalFeatureFusionProfileModel).where(
            ThermalFeatureFusionProfileModel.observation_id.in_(observation_ids),
            ThermalFeatureFusionProfileModel.schema_version == "fusion_v1",
        )
        res_profiles = await session.execute(q_profiles)
        db_queries += 1
        profiles_by_id = {p.observation_id: p for p in res_profiles.scalars().all()}

        # 3. Bulk fetch existing explanations
        q_exps = select(ThermalClassificationExplanationModel).where(
            ThermalClassificationExplanationModel.observation_id.in_(observation_ids),
            ThermalClassificationExplanationModel.model_version == MODEL_VERSION,
            ThermalClassificationExplanationModel.explanation_version == EXPLANATION_VERSION,
        )
        res_exps = await session.execute(q_exps)
        db_queries += 1
        existing_exps = {e.observation_id: e for e in res_exps.scalars().all()}

        manifest = self.registry.manifest
        ordered_features = manifest.ordered_features if manifest else []
        model = self.registry.model
        model_status = self.registry.status
        artifact_hash = manifest.model_artifact_hash if manifest else ""

        created_count = 0
        updated_count = 0
        reused_count = 0
        available_count = 0
        insufficient_count = 0

        to_explain_obs_ids: list[str] = []
        to_explain_rows: list[list[Any]] = []
        to_explain_pred_classes: list[str] = []
        to_explain_raw_dicts: list[dict[str, Any]] = []

        records_to_upsert: dict[str, dict[str, Any]] = {}

        for obs_id in observation_ids:
            pred = preds_by_id.get(obs_id)
            profile = profiles_by_id.get(obs_id)
            existing = existing_exps.get(obs_id)

            if not pred or not profile:
                continue

            # Check staleness: if prediction was made on an older fusion fingerprint
            if pred.fusion_source_fingerprint != profile.source_fingerprint:
                records_to_upsert[obs_id] = {
                    "observation_id": obs_id,
                    "model_version": MODEL_VERSION,
                    "explanation_version": EXPLANATION_VERSION,
                    "method_name": METHOD_TREESHAP,
                    "method_version": METHOD_VERSION_TREESHAP,
                    "fusion_schema_version": profile.schema_version,
                    "fusion_schema_hash": profile.schema_hash,
                    "fusion_source_fingerprint": profile.source_fingerprint,
                    "model_artifact_hash": artifact_hash,
                    "classification_status": pred.classification_status,
                    "predicted_class": pred.predicted_class,
                    "prediction_score": pred.class_score,
                    "explanation_status": STATUS_PREDICTION_STALE,
                    "base_value": None,
                    "explained_output": None,
                    "additivity_error": None,
                    "feature_contributions": None,
                    "group_contributions": None,
                    "top_supporting": None,
                    "top_opposing": None,
                    "quality_flags": ["PREDICTION_FINGERPRINT_STALE"],
                }
                continue

            # Idempotency check for AVAILABLE explanations
            if (
                existing is not None
                and not force_recompute
                and existing.model_version == MODEL_VERSION
                and existing.model_artifact_hash == artifact_hash
                and existing.fusion_schema_version == profile.schema_version
                and existing.fusion_schema_hash == profile.schema_hash
                and existing.fusion_source_fingerprint == profile.source_fingerprint
                and existing.predicted_class == pred.predicted_class
                and existing.explanation_status == STATUS_AVAILABLE
            ):
                reused_count += 1
                available_count += 1
                continue

            # Insufficient Evidence handling: Section 33 & 82
            if pred.classification_status == P8_STATUS_INSUFFICIENT_EVIDENCE or not pred.predicted_class:
                insufficient_count += 1
                if existing is not None and existing.explanation_status == STATUS_INSUFFICIENT_EVIDENCE and not force_recompute:
                    reused_count += 1
                    continue

                records_to_upsert[obs_id] = {
                    "observation_id": obs_id,
                    "model_version": MODEL_VERSION,
                    "explanation_version": EXPLANATION_VERSION,
                    "method_name": METHOD_TREESHAP,
                    "method_version": METHOD_VERSION_TREESHAP,
                    "fusion_schema_version": profile.schema_version,
                    "fusion_schema_hash": profile.schema_hash,
                    "fusion_source_fingerprint": profile.source_fingerprint,
                    "model_artifact_hash": artifact_hash,
                    "classification_status": pred.classification_status,
                    "predicted_class": None,
                    "prediction_score": None,
                    "explanation_status": STATUS_INSUFFICIENT_EVIDENCE,
                    "base_value": None,
                    "explained_output": None,
                    "additivity_error": None,
                    "feature_contributions": None,
                    "group_contributions": None,
                    "top_supporting": None,
                    "top_opposing": None,
                    "quality_flags": ["EVIDENCE_GATE_NOT_MET"],
                }
                continue

            # Model validity / schema check
            if not self.registry.is_available or model is None:
                exp_status = (
                    STATUS_MODEL_INVALID
                    if model_status == "MODEL_INVALID"
                    else STATUS_SCHEMA_MISMATCH
                    if model_status == "SCHEMA_MISMATCH"
                    else STATUS_MODEL_UNAVAILABLE
                )
                records_to_upsert[obs_id] = {
                    "observation_id": obs_id,
                    "model_version": MODEL_VERSION,
                    "explanation_version": EXPLANATION_VERSION,
                    "method_name": METHOD_TREESHAP,
                    "method_version": METHOD_VERSION_TREESHAP,
                    "fusion_schema_version": profile.schema_version,
                    "fusion_schema_hash": profile.schema_hash,
                    "fusion_source_fingerprint": profile.source_fingerprint,
                    "model_artifact_hash": artifact_hash,
                    "classification_status": pred.classification_status,
                    "predicted_class": pred.predicted_class,
                    "prediction_score": pred.class_score,
                    "explanation_status": exp_status,
                    "base_value": None,
                    "explained_output": None,
                    "additivity_error": None,
                    "feature_contributions": None,
                    "group_contributions": None,
                    "top_supporting": None,
                    "top_opposing": None,
                    "quality_flags": ["MODEL_REGISTRY_ERROR"],
                }
                continue

            # Eligible for attribution calculation
            row = [profile.feature_vector.get(f) for f in ordered_features]
            to_explain_obs_ids.append(obs_id)
            to_explain_rows.append(row)
            to_explain_pred_classes.append(pred.predicted_class)
            to_explain_raw_dicts.append(profile.feature_vector)

        # 6. Run batch provider explanation if needed
        if to_explain_obs_ids and model is not None:
            try:
                provider = get_explanation_provider(model, ordered_features)
                exp_results = provider.explain_batch(
                    to_explain_rows,
                    to_explain_pred_classes,
                    to_explain_raw_dicts,
                )

                for idx, obs_id in enumerate(to_explain_obs_ids):
                    pred = preds_by_id[obs_id]
                    profile = profiles_by_id[obs_id]
                    res = exp_results[idx]

                    if res.status == STATUS_AVAILABLE:
                        available_count += 1

                    records_to_upsert[obs_id] = {
                        "observation_id": obs_id,
                        "model_version": MODEL_VERSION,
                        "explanation_version": EXPLANATION_VERSION,
                        "method_name": res.method_name,
                        "method_version": res.method_version,
                        "fusion_schema_version": profile.schema_version,
                        "fusion_schema_hash": profile.schema_hash,
                        "fusion_source_fingerprint": profile.source_fingerprint,
                        "model_artifact_hash": artifact_hash,
                        "classification_status": pred.classification_status,
                        "predicted_class": pred.predicted_class,
                        "prediction_score": pred.class_score,
                        "explanation_status": res.status,
                        "base_value": res.base_value,
                        "explained_output": res.explained_output,
                        "additivity_error": res.additivity_error,
                        "feature_contributions": [c.model_dump() for c in res.raw_feature_contributions]
                        if res.raw_feature_contributions
                        else None,
                        "group_contributions": {k: v.model_dump() for k, v in res.group_contributions.items()}
                        if res.group_contributions
                        else None,
                        "top_supporting": [c.model_dump() for c in res.top_supporting_features]
                        if res.top_supporting_features
                        else None,
                        "top_opposing": [c.model_dump() for c in res.top_opposing_features]
                        if res.top_opposing_features
                        else None,
                        "quality_flags": res.quality_flags,
                    }

            except Exception as e:
                logger.error("Batch explanation generation failed: %s", e, exc_info=True)
                for obs_id in to_explain_obs_ids:
                    pred = preds_by_id[obs_id]
                    profile = profiles_by_id[obs_id]
                    records_to_upsert[obs_id] = {
                        "observation_id": obs_id,
                        "model_version": MODEL_VERSION,
                        "explanation_version": EXPLANATION_VERSION,
                        "method_name": METHOD_TREESHAP,
                        "method_version": METHOD_VERSION_TREESHAP,
                        "fusion_schema_version": profile.schema_version,
                        "fusion_schema_hash": profile.schema_hash,
                        "fusion_source_fingerprint": profile.source_fingerprint,
                        "model_artifact_hash": artifact_hash,
                        "classification_status": pred.classification_status,
                        "predicted_class": pred.predicted_class,
                        "prediction_score": pred.class_score,
                        "explanation_status": STATUS_ERROR,
                        "base_value": None,
                        "explained_output": None,
                        "additivity_error": None,
                        "feature_contributions": None,
                        "group_contributions": None,
                        "top_supporting": None,
                        "top_opposing": None,
                        "quality_flags": ["UNHANDLED_EXCEPTION"],
                    }

        # 7. Persist records to database
        now = datetime.now(UTC)
        for obs_id, payload in records_to_upsert.items():
            existing = existing_exps.get(obs_id)
            if existing:
                for k, v in payload.items():
                    setattr(existing, k, v)
                existing.generated_at = now
                updated_count += 1
            else:
                new_exp = ThermalClassificationExplanationModel(
                    **payload,
                    generated_at=now,
                )
                session.add(new_exp)
                created_count += 1

        if created_count > 0 or updated_count > 0:
            await session.commit()
            db_queries += 1

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return SyncExplanationResponse(
            requested=len(observation_ids),
            created=created_count,
            updated=updated_count,
            reused=reused_count,
            available=available_count,
            insufficient_evidence=insufficient_count,
            duration_ms=round(duration_ms, 2),
            database_queries=db_queries,
        )


explainability_service = ExplainabilityService()
