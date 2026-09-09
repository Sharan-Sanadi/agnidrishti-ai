# AGNIDRISHTI API — Phase 7 Feature Fusion Service
"""
Production Feature Fusion Service for AGNIDRISHTI AI.
Assembles, validates, verifies invariants, fingerprints, and persists canonical
feature vectors across Phases 1-6 without arbitrary weights, classification,
or external satellite API calls.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.feature_fusion_profile import ThermalFeatureFusionProfileModel
from app.db.models.industrial_context_profile import IndustrialContextProfileModel
from app.db.models.land_cover_profile import ThermalLandCoverProfileModel
from app.db.models.persistence_profile import PersistenceProfileModel
from app.db.models.sentinel_context_profile import ThermalSentinelContextProfileModel
from app.db.models.thermal_observation import ThermalObservationModel
from app.schemas.fusion import (
    BatchFusionResponse,
    FusionProfileResponse,
    SyncFusionResponse,
)
from app.services.fusion.extractors import (
    extract_industrial_features,
    extract_land_cover_features,
    extract_sentinel_features,
    extract_temporal_features,
    extract_thermal_features,
)
from app.services.fusion.feature_registry import (
    SCHEMA_VERSION_V1,
    fusion_v1_registry,
)
from app.services.fusion.fingerprint import compute_source_fingerprint
from app.services.temporal_persistence import TemporalPersistenceService


class FeatureFusionService:
    """
    Core service orchestrating Phase 7 Feature Fusion.
    Operates strictly on local PostGIS data with zero external network requests.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.registry = fusion_v1_registry

    async def get_profile(
        self, observation_id: str, schema_version: str = SCHEMA_VERSION_V1
    ) -> FusionProfileResponse | None:
        """Fetch single cached fusion profile by observation_id and schema_version."""
        stmt = select(ThermalFeatureFusionProfileModel).where(
            ThermalFeatureFusionProfileModel.observation_id == observation_id,
            ThermalFeatureFusionProfileModel.schema_version == schema_version,
        )
        res = await self.db.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None
        return self._model_to_response(model)

    async def get_batch_profiles(
        self, observation_ids: list[str], schema_version: str = SCHEMA_VERSION_V1
    ) -> BatchFusionResponse:
        """
        Bulk fetch cached fusion profiles using a single SQL query.
        Guarantees zero N+1 database operations.
        """
        if not observation_ids:
            return BatchFusionResponse(schema_version=schema_version, count=0, profiles={})

        stmt = select(ThermalFeatureFusionProfileModel).where(
            ThermalFeatureFusionProfileModel.observation_id.in_(observation_ids),
            ThermalFeatureFusionProfileModel.schema_version == schema_version,
        )
        res = await self.db.execute(stmt)
        models = res.scalars().all()

        profiles = {m.observation_id: self._model_to_response(m) for m in models}
        return BatchFusionResponse(
            schema_version=schema_version,
            count=len(profiles),
            profiles=profiles,
        )

    async def sync_batch(
        self,
        observation_ids: list[str],
        force_recompute: bool = False,
    ) -> SyncFusionResponse:
        """
        Execute bounded bulk fusion sync for up to 500 observation IDs.
        Gathers local upstream intelligence across Phases 1-6 using bounded bulk queries.
        Identifies source changes via deterministic SHA-256 fingerprinting.
        Persists and updates profiles idempotently.
        Guarantees ZERO external network requests (NASA FIRMS, Overpass, CDSE, WorldCover = 0).
        """
        start_time = time.perf_counter()
        query_count = 0

        if not observation_ids:
            return SyncFusionResponse(
                requested=0,
                created=0,
                updated=0,
                reused=0,
                complete=0,
                partial=0,
                missing_upstream_groups={},
                duration_ms=0.0,
                database_queries=0,
            )

        unique_ids = list(dict.fromkeys(observation_ids))

        # 1. Bulk fetch thermal observations (Phase 1/2)
        q1 = select(ThermalObservationModel).where(ThermalObservationModel.observation_id.in_(unique_ids))
        res1 = await self.db.execute(q1)
        query_count += 1
        obs_models = {o.observation_id: o for o in res1.scalars().all()}

        # 2. Bulk fetch Phase 3 Temporal Persistence profiles
        q2 = select(PersistenceProfileModel).where(PersistenceProfileModel.observation_id.in_(unique_ids))
        res2 = await self.db.execute(q2)
        query_count += 1
        pers_models: dict[str, Any] = {p.observation_id: p for p in res2.scalars().all()}

        # For any observation missing cached persistence profile, compute and cache it locally
        missing_pers_ids = [oid for oid in unique_ids if oid in obs_models and oid not in pers_models]
        if missing_pers_ids:
            pers_service = TemporalPersistenceService(self.db)
            for m_id in missing_pers_ids:
                obs_item = obs_models[m_id]
                try:
                    p_prof = await pers_service.analyze_observation(obs_item)
                    pers_models[m_id] = p_prof
                    query_count += 2  # spatiotemporal neighbors + coverage queries
                    # Cache in persistence_profiles table for instantaneous subsequent reads
                    p_cached = PersistenceProfileModel(
                        observation_id=obs_item.observation_id,
                        algorithm_version=p_prof.algorithm_version,
                        analysis_as_of=p_prof.target_time,
                        radius_m=p_prof.radius_m,
                        raw_detection_count_7d=p_prof.raw_detection_count_7d,
                        raw_detection_count_30d=p_prof.raw_detection_count_30d,
                        active_days_7d=p_prof.active_days_7d,
                        active_days_30d=p_prof.active_days_30d,
                        active_weeks_30d=p_prof.active_weeks_30d,
                        first_seen_30d=p_prof.first_seen_30d,
                        last_seen_30d=p_prof.last_seen_30d,
                        temporal_span_days_30d=p_prof.temporal_span_days_30d,
                        history_coverage_days_7d=p_prof.history_coverage_days_7d,
                        history_coverage_days_30d=p_prof.history_coverage_days_30d,
                        history_coverage_ratio_30d=p_prof.history_coverage_ratio_30d,
                        persistence_index=p_prof.persistence_index,
                        persistence_class=p_prof.persistence_class,
                        explanation=p_prof.explanation,
                        explanation_details=p_prof.score_components,
                        computed_at=datetime.now(UTC),
                    )
                    self.db.add(p_cached)
                except Exception as ex:
                    logger.warning(f"Temporal analysis failed for {m_id} during fusion sync: {ex}")

        # 3. Bulk fetch Phase 4 Industrial Context profiles
        q3 = select(IndustrialContextProfileModel).where(IndustrialContextProfileModel.observation_id.in_(unique_ids))
        res3 = await self.db.execute(q3)
        query_count += 1
        ind_models = {i.observation_id: i for i in res3.scalars().all()}

        # 4. Bulk fetch Phase 5 Land Cover profiles
        q4 = select(ThermalLandCoverProfileModel).where(ThermalLandCoverProfileModel.observation_id.in_(unique_ids))
        res4 = await self.db.execute(q4)
        query_count += 1
        lc_models = {lc_item.observation_id: lc_item for lc_item in res4.scalars().all()}

        # 5. Bulk fetch Phase 6 Sentinel-2 Context profiles
        q5 = select(ThermalSentinelContextProfileModel).where(ThermalSentinelContextProfileModel.observation_id.in_(unique_ids))
        res5 = await self.db.execute(q5)
        query_count += 1
        s2_models = {s.observation_id: s for s in res5.scalars().all()}

        # 6. Bulk fetch existing fusion profiles
        q6 = select(ThermalFeatureFusionProfileModel).where(
            ThermalFeatureFusionProfileModel.observation_id.in_(unique_ids),
            ThermalFeatureFusionProfileModel.schema_version == SCHEMA_VERSION_V1,
        )
        res6 = await self.db.execute(q6)
        query_count += 1
        existing_fusion_map = {f.observation_id: f for f in res6.scalars().all()}

        # Metrics trackers
        created_count = 0
        updated_count = 0
        reused_count = 0
        complete_count = 0
        partial_count = 0
        missing_groups: dict[str, int] = {
            "THERMAL": 0,
            "TEMPORAL": 0,
            "INDUSTRIAL": 0,
            "LAND_COVER": 0,
            "SENTINEL": 0,
        }

        now_utc = datetime.now(UTC)
        rows_to_upsert: list[dict[str, Any]] = []

        for obs_id in unique_ids:
            obs = obs_models.get(obs_id)
            if not obs:
                missing_groups["THERMAL"] += 1
                continue

            pers = pers_models.get(obs_id)
            ind = ind_models.get(obs_id)
            lc = lc_models.get(obs_id)
            s2 = s2_models.get(obs_id)

            quality_flags: list[str] = []

            # 1. Thermal features
            t_feat, t_status, t_prov = extract_thermal_features(obs)

            # 2. Temporal features
            p_feat, p_status, p_prov = extract_temporal_features(pers)
            if p_status == "UNAVAILABLE":
                missing_groups["TEMPORAL"] += 1

            # 3. Industrial features
            i_feat, i_status, i_prov = extract_industrial_features(ind)
            if i_status == "UNAVAILABLE":
                missing_groups["INDUSTRIAL"] += 1

            # 4. Land Cover features
            l_feat, l_status, l_prov, l_flags = extract_land_cover_features(lc)
            quality_flags.extend(l_flags)
            if l_status == "UNAVAILABLE":
                missing_groups["LAND_COVER"] += 1

            # 5. Sentinel features
            s_feat, s_status, s_prov, s_flags = extract_sentinel_features(s2, obs.acquisition_time_utc)
            quality_flags.extend(s_flags)
            if s_status in ("UNAVAILABLE", "NOT_EVALUATED"):
                missing_groups["SENTINEL"] += 1

            # Combine all features into registered canonical dictionary
            merged_features: dict[str, Any] = {
                **t_feat,
                **p_feat,
                **i_feat,
                **l_feat,
                **s_feat,
            }

            # Canonical order matching registry
            canonical_feature_vector = {
                spec.name: merged_features.get(spec.name) for spec in self.registry.features
            }

            group_statuses = {
                "THERMAL": t_status,
                "TEMPORAL": p_status,
                "INDUSTRIAL": i_status,
                "LAND_COVER": l_status,
                "SENTINEL": s_status,
            }

            upstream_versions = {
                "thermal_source": t_prov.get("source_product"),
                "temporal_algo": p_prov.get("algorithm_version"),
                "industrial_algo": i_prov.get("algorithm_version"),
                "landcover_product": l_prov.get("product_version"),
                "sentinel_algo": s_prov.get("algorithm_version"),
            }

            provenance = {
                "schema_version": SCHEMA_VERSION_V1,
                "schema_hash": self.registry.schema_hash,
                "thermal": t_prov,
                "temporal": p_prov,
                "industrial": i_prov,
                "land_cover": l_prov,
                "sentinel": s_prov,
            }

            # Source fingerprint computation
            fingerprint = compute_source_fingerprint(
                canonical_feature_vector, group_statuses, upstream_versions
            )

            # Usable / Evaluated metrics
            evaluated_groups = sum(
                1 for st in group_statuses.values() if st not in ("UNAVAILABLE", "NOT_EVALUATED")
            )
            # Usable: groups with usable physical evidence
            # For temporal, PARTIAL (insufficient history) is still evaluated evidence
            usable_groups = 0
            if t_status == "AVAILABLE":
                usable_groups += 1
            if p_status in ("AVAILABLE", "PARTIAL"):
                usable_groups += 1
            if i_status == "AVAILABLE":
                usable_groups += 1
            if l_status == "AVAILABLE":
                usable_groups += 1
            if s_status == "AVAILABLE":
                usable_groups += 1

            # Fusion status: COMPLETE if all 5 groups are usable, else PARTIAL
            is_complete = (
                t_status == "AVAILABLE"
                and p_status in ("AVAILABLE", "PARTIAL")
                and i_status == "AVAILABLE"
                and l_status == "AVAILABLE"
                and s_status == "AVAILABLE"
            )
            fusion_status = "COMPLETE" if is_complete else "PARTIAL"
            if is_complete:
                complete_count += 1
            else:
                partial_count += 1

            # Completeness / feature coverage calculations
            expected_feats = self.registry.model_eligible_count  # 57
            non_null_feats = sum(
                1
                for spec in self.registry.features
                if spec.model_eligible and canonical_feature_vector.get(spec.name) is not None
            )
            coverage_fraction = round(non_null_feats / expected_feats, 4) if expected_feats > 0 else 0.0

            # Idempotency check against existing row
            existing = existing_fusion_map.get(obs_id)
            if (
                existing
                and existing.source_fingerprint == fingerprint
                and existing.schema_hash == self.registry.schema_hash
                and not force_recompute
            ):
                reused_count += 1
                continue

            if existing:
                updated_count += 1
            else:
                created_count += 1

            row_data = {
                "observation_id": obs_id,
                "schema_version": SCHEMA_VERSION_V1,
                "schema_hash": self.registry.schema_hash,
                "source_fingerprint": fingerprint,
                "fusion_status": fusion_status,
                "total_group_count": 5,
                "evaluated_group_count": evaluated_groups,
                "usable_group_count": usable_groups,
                "expected_feature_count": expected_feats,
                "non_null_feature_count": non_null_feats,
                "feature_coverage_fraction": coverage_fraction,
                "feature_vector": canonical_feature_vector,
                "group_status": group_statuses,
                "provenance": provenance,
                "quality_flags": quality_flags,
                "generated_at": now_utc,
                "updated_at": now_utc,
            }
            rows_to_upsert.append(row_data)

        # 7. Bulk upsert into thermal_feature_fusion_profiles
        if rows_to_upsert:
            stmt = pg_insert(ThermalFeatureFusionProfileModel).values(rows_to_upsert)
            update_dict = {
                "schema_hash": stmt.excluded.schema_hash,
                "source_fingerprint": stmt.excluded.source_fingerprint,
                "fusion_status": stmt.excluded.fusion_status,
                "evaluated_group_count": stmt.excluded.evaluated_group_count,
                "usable_group_count": stmt.excluded.usable_group_count,
                "expected_feature_count": stmt.excluded.expected_feature_count,
                "non_null_feature_count": stmt.excluded.non_null_feature_count,
                "feature_coverage_fraction": stmt.excluded.feature_coverage_fraction,
                "feature_vector": stmt.excluded.feature_vector,
                "group_status": stmt.excluded.group_status,
                "provenance": stmt.excluded.provenance,
                "quality_flags": stmt.excluded.quality_flags,
                "updated_at": stmt.excluded.updated_at,
            }
            upsert_stmt = stmt.on_conflict_do_update(
                constraint="uq_fusion_observation_schema",
                set_=update_dict,
            )
            await self.db.execute(upsert_stmt)
            query_count += 1

        await self.db.commit()
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return SyncFusionResponse(
            requested=len(observation_ids),
            created=created_count,
            updated=updated_count,
            reused=reused_count,
            complete=complete_count,
            partial=partial_count,
            missing_upstream_groups=missing_groups,
            duration_ms=duration_ms,
            database_queries=query_count,
        )

    def _model_to_response(self, m: ThermalFeatureFusionProfileModel) -> FusionProfileResponse:
        """Convert ORM model to Pydantic API response."""
        pct = round(m.feature_coverage_fraction * 100.0)
        return FusionProfileResponse(
            observation_id=m.observation_id,
            schema_version=m.schema_version,
            schema_hash=m.schema_hash,
            source_fingerprint=m.source_fingerprint,
            fusion_status=m.fusion_status,
            total_group_count=m.total_group_count,
            evaluated_group_count=m.evaluated_group_count,
            usable_group_count=m.usable_group_count,
            expected_feature_count=m.expected_feature_count,
            non_null_feature_count=m.non_null_feature_count,
            feature_coverage_fraction=round(m.feature_coverage_fraction, 4),
            feature_coverage_percent=pct,
            feature_vector=m.feature_vector,
            group_status=m.group_status,
            provenance=m.provenance,
            quality_flags=m.quality_flags,
            generated_at=m.generated_at,
            updated_at=m.updated_at,
        )
