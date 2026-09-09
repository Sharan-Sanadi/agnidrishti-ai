# AGNIDRISHTI API — Phase 6 Sentinel-2 Satellite Context Service
"""
Production service coordinating Sentinel-2 Level-2A optical/SWIR context retrieval,
cloud-masking quality analysis, metric multi-scale spectral statistics,
and PostGIS caching.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import logger
from app.db.models.sentinel_context_profile import ThermalSentinelContextProfileModel
from app.db.models.thermal_observation import ThermalObservationModel
from app.providers.sentinel2.auth import get_cdse_token_provider
from app.providers.sentinel2.catalog import CDSECatalogClient, CDSECatalogError
from app.providers.sentinel2.constants import (
    ANALYTICAL_RESOLUTION_M,
    QUALITY_THRESHOLD_LIMITED,
    SENTINEL_COLLECTION_NAME,
    TEMPORAL_THRESHOLD_FRESH_DAYS,
    TEMPORAL_THRESHOLD_RECENT_DAYS,
    SentinelProviderStatus,
    SentinelQualityStatus,
    SentinelTemporalQuality,
)
from app.providers.sentinel2.process import CDSEProcessClient, CDSEProcessError
from app.providers.sentinel2.quality import evaluate_roi_quality
from app.providers.sentinel2.schemas import SentinelCandidate
from app.providers.sentinel2.spatial import compute_pixel_metric_distances
from app.providers.sentinel2.statistics import compute_radius_statistics, extract_point_sample
from app.schemas.sentinel2 import (
    SentinelContextProfileResponse,
    SentinelSyncResponse,
)


def _compute_raster_features_sync(
    center_lat: float,
    center_lon: float,
    raster_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Synchronous CPU-bound raster masking, metric distance computation, and statistics extraction.
    Executed in a threadpool worker to prevent blocking the async event loop.
    """
    b04 = raster_data["b04"]
    b08 = raster_data["b08"]
    b11 = raster_data["b11"]
    b12 = raster_data["b12"]
    scl = raster_data["scl"]
    data_mask = raster_data["data_mask"]
    transform = raster_data["transform"]
    width = raster_data["width"]
    height = raster_data["height"]

    # 1. Metric distances from center coordinates to each pixel in window
    distances_m = compute_pixel_metric_distances(
        center_lat, center_lon, transform, height, width
    )

    # 2. Local ROI quality assessment within 500m maximum window
    roi_500m_mask = distances_m <= 500.0
    local_quality = evaluate_roi_quality(scl, data_mask, spatial_mask=roi_500m_mask)

    # 3. Point pixel sample at center
    center_row = height // 2
    center_col = width // 2
    point_sample = extract_point_sample(
        b04, b08, b11, b12, scl, data_mask, center_row, center_col
    )

    # 4. Multi-scale circular neighborhood statistics (100m, 250m, 500m)
    stats_100m = compute_radius_statistics(
        b04, b08, b11, b12, scl, data_mask, distances_m, 100.0
    )
    stats_250m = compute_radius_statistics(
        b04, b08, b11, b12, scl, data_mask, distances_m, 250.0
    )
    stats_500m = compute_radius_statistics(
        b04, b08, b11, b12, scl, data_mask, distances_m, 500.0
    )

    return {
        "local_quality": local_quality,
        "point_sample": point_sample,
        "stats_100m": stats_100m.model_dump(),
        "stats_250m": stats_250m.model_dump(),
        "stats_500m": stats_500m.model_dump(),
    }


class SentinelContextService:
    """Core service orchestrating Sentinel-2 context intelligence."""

    def __init__(
        self,
        db: AsyncSession,
        catalog_client: CDSECatalogClient | None = None,
        process_client: CDSEProcessClient | None = None,
    ) -> None:
        self.db = db
        token_prov = get_cdse_token_provider()
        self.catalog_client = catalog_client or CDSECatalogClient(token_provider=token_prov)
        self.process_client = process_client or CDSEProcessClient(token_provider=token_prov)
        self.settings = get_settings()

    async def get_profile(self, observation_id: str) -> SentinelContextProfileResponse | None:
        """Fetch cached profile from PostGIS for a single observation ID."""
        stmt = select(ThermalSentinelContextProfileModel).where(
            ThermalSentinelContextProfileModel.observation_id == observation_id
        )
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            return None
        return SentinelContextProfileResponse.model_validate(record)

    async def get_batch_profiles(
        self, observation_ids: list[str]
    ) -> dict[str, SentinelContextProfileResponse]:
        """Fetch cached profiles for a batch of observation IDs (up to 500)."""
        if not observation_ids:
            return {}

        stmt = select(ThermalSentinelContextProfileModel).where(
            ThermalSentinelContextProfileModel.observation_id.in_(observation_ids)
        )
        res = await self.db.execute(stmt)
        records = res.scalars().all()

        profiles: dict[str, SentinelContextProfileResponse] = {}
        for rec in records:
            profiles[rec.observation_id] = SentinelContextProfileResponse.model_validate(rec)
        return profiles

    async def evaluate_observation(
        self,
        observation: ThermalObservationModel,
        force_refresh: bool = False,
    ) -> SentinelContextProfileResponse:
        """
        Evaluate and persist a Sentinel-2 L2A context profile for a single observation.
        Guarantees zero future leakage: candidate scenes must be acquired <= observation target time.
        """
        obs_id = observation.observation_id

        # 1. Check existing cached profile
        if not force_refresh:
            cached = await self.get_profile(obs_id)
            if cached and cached.provider_status != SentinelProviderStatus.NOT_EVALUATED:
                return cached

        target_time = observation.acquisition_time_utc
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=UTC)
        else:
            target_time = target_time.astimezone(UTC)

        lat = observation.latitude
        lon = observation.longitude

        # 2. Check provider configuration readiness
        if not self.settings.is_cdse_configured:
            logger.warning("CDSE credentials not configured; marking profile PROVIDER_UNAVAILABLE.")
            return await self._persist_empty_profile(
                observation=observation,
                provider_status=SentinelProviderStatus.PROVIDER_UNAVAILABLE,
                quality_status=SentinelQualityStatus.UNAVAILABLE,
            )

        # 3. Discover candidates from STAC catalog strictly <= target_time
        try:
            candidates = await self.catalog_client.search_candidates(
                latitude=lat,
                longitude=lon,
                target_firms_time_utc=target_time,
                lookback_days=self.settings.sentinel_lookback_days,
                max_candidates=self.settings.sentinel_max_candidates,
            )
        except CDSECatalogError as ex:
            logger.error(f"STAC catalog discovery failed for {obs_id}: {ex}")
            status = SentinelProviderStatus.RATE_LIMITED if ex.status_code == 429 else SentinelProviderStatus.PROVIDER_UNAVAILABLE
            return await self._persist_empty_profile(
                observation=observation,
                provider_status=status,
                quality_status=SentinelQualityStatus.UNAVAILABLE,
            )

        if not candidates:
            logger.info(f"No prior Sentinel-2 scene found for {obs_id} within {self.settings.sentinel_lookback_days} days.")
            return await self._persist_empty_profile(
                observation=observation,
                provider_status=SentinelProviderStatus.NO_SCENE,
                quality_status=SentinelQualityStatus.UNAVAILABLE,
            )

        # 4. Multiband ROI around FIRMS point (~500m radius -> 0.005 deg delta)
        delta = 0.005
        bbox = [lon - delta, lat - delta, lon + delta, lat + delta]

        # 5. Evaluate candidate scenes to select the best prior scene
        # Lexicographic priority:
        # 1. Usable local valid fraction (prefer >= QUALITY_THRESHOLD_LIMITED = 0.40)
        # 2. Closest prior acquisition to FIRMS target
        # 3. Lower catalogue cloud cover
        # 4. Stable scene_id
        selected_candidate: SentinelCandidate | None = None
        selected_features: dict[str, Any] | None = None
        best_candidate: SentinelCandidate = candidates[0]
        best_features: dict[str, Any] | None = None

        for cand in candidates:
            # Enforce zero future leakage again as an invariant
            cand_time = cand.acquisition_time_utc.astimezone(UTC)
            if cand_time > target_time:
                continue

            try:
                raster_data = await self.process_client.fetch_analytical_raster(
                    bbox=bbox,
                    scene_time=cand_time,
                    width=51,
                    height=51,
                )
            except CDSEProcessError as p_err:
                logger.warning(f"Process API failed for candidate {cand.scene_id}: {p_err}")
                if p_err.status_code == 429:
                    return await self._persist_empty_profile(
                        observation=observation,
                        provider_status=SentinelProviderStatus.RATE_LIMITED,
                        quality_status=SentinelQualityStatus.UNAVAILABLE,
                    )
                continue

            # Process raster features in threadpool to keep event loop responsive
            features = await asyncio.to_thread(
                _compute_raster_features_sync,
                lat,
                lon,
                raster_data,
            )

            local_q = features["local_quality"]

            if best_features is None:
                best_candidate = cand
                best_features = features

            # Check if this candidate is usable (valid fraction >= 0.40)
            if local_q.valid_fraction >= QUALITY_THRESHOLD_LIMITED:
                selected_candidate = cand
                selected_features = features
                break  # Candidates already ordered by recency! First usable scene wins.

        # If no scene met the minimum usable threshold (0.40), use the best prior candidate
        # but mark as CLOUD_LIMITED
        is_cloud_limited = False
        if selected_candidate is None:
            if best_features is not None:
                selected_candidate = best_candidate
                selected_features = best_features
                is_cloud_limited = True
            else:
                return await self._persist_empty_profile(
                    observation=observation,
                    provider_status=SentinelProviderStatus.PROVIDER_UNAVAILABLE,
                    quality_status=SentinelQualityStatus.UNAVAILABLE,
                )

        if selected_candidate is None or selected_features is None:
            return await self._persist_empty_profile(
                observation=observation,
                provider_status=SentinelProviderStatus.PROVIDER_UNAVAILABLE,
                quality_status=SentinelQualityStatus.UNAVAILABLE,
            )

        # 6. Build profile and persist to PostGIS
        cand_acq_utc = selected_candidate.acquisition_time_utc.astimezone(UTC)

        age_seconds = (target_time - cand_acq_utc).total_seconds()
        scene_age_hours = max(0.0, round(age_seconds / 3600.0, 2))
        scene_age_days = max(0.0, round(age_seconds / 86400.0, 2))

        # Temporal quality interpretation
        if scene_age_days <= TEMPORAL_THRESHOLD_FRESH_DAYS:
            temporal_q = SentinelTemporalQuality.FRESH
        elif scene_age_days <= TEMPORAL_THRESHOLD_RECENT_DAYS:
            temporal_q = SentinelTemporalQuality.RECENT
        else:
            temporal_q = SentinelTemporalQuality.OLDER_CONTEXT

        lq = selected_features["local_quality"]
        ps = selected_features["point_sample"]
        s100 = selected_features["stats_100m"]
        s250 = selected_features["stats_250m"]
        s500 = selected_features["stats_500m"]

        prov_status = (
            SentinelProviderStatus.CLOUD_LIMITED
            if is_cloud_limited
            else SentinelProviderStatus.AVAILABLE
        )

        now_utc = datetime.now(UTC)

        profile_dict = {
            "observation_id": obs_id,
            "provider": "CDSE",
            "collection": SENTINEL_COLLECTION_NAME,
            "scene_id": selected_candidate.scene_id,
            "product_id": selected_candidate.product_id,
            "satellite_platform": selected_candidate.satellite_platform,
            "scene_acquisition_time_utc": cand_acq_utc,
            "target_firms_time_utc": target_time,
            "scene_age_hours": scene_age_hours,
            "scene_age_days": scene_age_days,
            "temporal_quality": temporal_q.value,
            "catalogue_cloud_cover": selected_candidate.cloud_cover_percentage,
            "local_valid_fraction": lq.valid_fraction,
            "local_cloud_fraction": lq.cloud_fraction,
            "local_cloud_shadow_fraction": lq.cloud_shadow_fraction,
            "local_snow_fraction": lq.snow_fraction,
            "quality_status": lq.quality_status.value,
            "provider_status": prov_status.value,
            "analytical_resolution_m": ANALYTICAL_RESOLUTION_M,
            # Point features
            "point_is_valid": ps.is_valid,
            "point_scl": ps.scl_code,
            "point_b04": ps.b04,
            "point_b08": ps.b08,
            "point_b11": ps.b11,
            "point_b12": ps.b12,
            "point_ndvi": ps.ndvi,
            "point_ndmi": ps.ndmi,
            "point_nbr": ps.nbr,
            # Multi-scale stats
            "stats_100m": s100,
            "stats_250m": s250,
            "stats_500m": s500,
            # Phase-7 explicit columns (from 250m primary context)
            "sentinel_scene_age_days": scene_age_days,
            "sentinel_valid_fraction_250m": s250.get("valid_fraction"),
            "sentinel_b04_median_250m": s250.get("b04_median"),
            "sentinel_b08_median_250m": s250.get("b08_median"),
            "sentinel_b11_median_250m": s250.get("b11_median"),
            "sentinel_b12_median_250m": s250.get("b12_median"),
            "sentinel_ndvi_median_250m": s250.get("ndvi_median"),
            "sentinel_ndmi_median_250m": s250.get("ndmi_median"),
            "sentinel_nbr_median_250m": s250.get("nbr_median"),
            "sentinel_b11_p90_250m": s250.get("b11_p90"),
            "sentinel_b12_p90_250m": s250.get("b12_p90"),
            "provenance": {
                "source": "Copernicus Data Space Ecosystem",
                "stac_url": self.settings.cdse_stac_base_url,
                "sh_url": self.settings.cdse_sentinel_hub_base_url,
                "bands": ["B04", "B08", "B11", "B12", "SCL", "dataMask"],
                "analytical_resolution_m": ANALYTICAL_RESOLUTION_M,
            },
            "algorithm_version": self.settings.sentinel_algorithm_version,
            "updated_at": now_utc,
            "processed_at": now_utc,
        }

        # 7. PostGIS idempotent upsert
        stmt = insert(ThermalSentinelContextProfileModel).values(**profile_dict)
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uq_obs_sentinel_alg_version",
            set_={k: profile_dict[k] for k in profile_dict if k not in ("id", "created_at")},
        )
        await self.db.execute(upsert_stmt)
        await self.db.commit()

        return SentinelContextProfileResponse.model_validate(profile_dict)


    async def _persist_empty_profile(
        self,
        observation: ThermalObservationModel,
        provider_status: SentinelProviderStatus,
        quality_status: SentinelQualityStatus,
    ) -> SentinelContextProfileResponse:
        """Persist an empty or failure profile to avoid repeated redundant calls."""
        obs_id = observation.observation_id
        target_time = observation.acquisition_time_utc
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=UTC)
        else:
            target_time = target_time.astimezone(UTC)

        now_utc = datetime.now(UTC)

        profile_dict = {
            "observation_id": obs_id,
            "provider": "CDSE",
            "collection": SENTINEL_COLLECTION_NAME,
            "scene_id": None,
            "product_id": None,
            "satellite_platform": None,
            "scene_acquisition_time_utc": None,
            "target_firms_time_utc": target_time,
            "scene_age_hours": None,
            "scene_age_days": None,
            "temporal_quality": None,
            "catalogue_cloud_cover": None,
            "local_valid_fraction": None,
            "local_cloud_fraction": None,
            "local_cloud_shadow_fraction": None,
            "local_snow_fraction": None,
            "quality_status": quality_status.value,
            "provider_status": provider_status.value,
            "analytical_resolution_m": ANALYTICAL_RESOLUTION_M,
            "point_is_valid": False,
            "point_scl": None,
            "point_b04": None,
            "point_b08": None,
            "point_b11": None,
            "point_b12": None,
            "point_ndvi": None,
            "point_ndmi": None,
            "point_nbr": None,
            "stats_100m": {},
            "stats_250m": {},
            "stats_500m": {},
            "sentinel_scene_age_days": None,
            "sentinel_valid_fraction_250m": None,
            "sentinel_b04_median_250m": None,
            "sentinel_b08_median_250m": None,
            "sentinel_b11_median_250m": None,
            "sentinel_b12_median_250m": None,
            "sentinel_ndvi_median_250m": None,
            "sentinel_ndmi_median_250m": None,
            "sentinel_nbr_median_250m": None,
            "sentinel_b11_p90_250m": None,
            "sentinel_b12_p90_250m": None,
            "provenance": {"status_reason": provider_status.value},
            "algorithm_version": self.settings.sentinel_algorithm_version,
            "updated_at": now_utc,
            "processed_at": now_utc,
        }

        stmt = insert(ThermalSentinelContextProfileModel).values(**profile_dict)
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uq_obs_sentinel_alg_version",
            set_={k: profile_dict[k] for k in profile_dict if k not in ("id", "created_at")},
        )
        await self.db.execute(upsert_stmt)
        await self.db.commit()

        return SentinelContextProfileResponse.model_validate(profile_dict)

    async def sync_batch(
        self,
        observation_ids: list[str],
        force_refresh: bool = False,
        concurrency_limit: int = 4,
    ) -> SentinelSyncResponse:
        """
        Controlled batch sync for at most 50 observation IDs per request.
        Coordinates bounded concurrency to protect remote CDSE quotas.
        """
        start_time = time.time()
        max_allowed = self.settings.sentinel_sync_batch_limit
        if len(observation_ids) > max_allowed:
            observation_ids = observation_ids[:max_allowed]

        # Load observations from PostGIS
        stmt = select(ThermalObservationModel).where(
            ThermalObservationModel.observation_id.in_(observation_ids)
        )
        res = await self.db.execute(stmt)
        observations = {obs.observation_id: obs for obs in res.scalars().all()}

        semaphore = asyncio.Semaphore(concurrency_limit)
        results: dict[str, SentinelContextProfileResponse] = {}

        cached_reused = 0
        computed = 0
        cloud_limited = 0
        no_scene = 0
        failed = 0

        async def _process_one(obs_id: str) -> None:
            nonlocal cached_reused, computed, cloud_limited, no_scene, failed
            obs = observations.get(obs_id)
            if not obs:
                failed += 1
                return

            # Check cache first if not forced
            if not force_refresh:
                cached = await self.get_profile(obs_id)
                if cached and cached.provider_status != SentinelProviderStatus.NOT_EVALUATED:
                    results[obs_id] = cached
                    cached_reused += 1
                    return

            async with semaphore:
                try:
                    prof = await self.evaluate_observation(obs, force_refresh=force_refresh)
                    results[obs_id] = prof
                    if prof.provider_status == SentinelProviderStatus.AVAILABLE:
                        computed += 1
                    elif prof.provider_status == SentinelProviderStatus.CLOUD_LIMITED:
                        cloud_limited += 1
                    elif prof.provider_status == SentinelProviderStatus.NO_SCENE:
                        no_scene += 1
                    else:
                        failed += 1
                except Exception as ex:
                    logger.error(f"Error evaluating Sentinel profile for {obs_id}: {ex}")
                    failed += 1

        for oid in observation_ids:
            await _process_one(oid)

        duration = round(time.time() - start_time, 2)

        return SentinelSyncResponse(
            status="completed",
            total_requested=len(observation_ids),
            cached_profiles_reused=cached_reused,
            profiles_computed=computed,
            profiles_cloud_limited=cloud_limited,
            profiles_no_scene=no_scene,
            profiles_failed=failed,
            duration_seconds=duration,
            profiles=results,
        )

    async def get_preview(
        self,
        observation_id: str,
        mode: str = "true_color",
    ) -> bytes:
        """
        Generate or fetch preview image (PNG bytes) for an observation.
        Modes: 'true_color' or 'swir_context'.
        """
        # 1. Fetch observation and profile
        stmt = select(ThermalObservationModel).where(
            ThermalObservationModel.observation_id == observation_id
        )
        res = await self.db.execute(stmt)
        obs = res.scalar_one_or_none()
        if not obs:
            raise ValueError(f"Observation '{observation_id}' not found.")

        prof = await self.get_profile(observation_id)
        if not prof or not prof.scene_acquisition_time_utc:
            # Try computing profile if not yet done
            prof = await self.evaluate_observation(obs)
            if not prof or not prof.scene_acquisition_time_utc:
                raise ValueError(f"No usable Sentinel scene for preview of observation '{observation_id}'.")

        delta = 0.005
        bbox = [
            obs.longitude - delta,
            obs.latitude - delta,
            obs.longitude + delta,
            obs.latitude + delta,
        ]

        scene_time = prof.scene_acquisition_time_utc
        return await self.process_client.fetch_preview_image(
            bbox=bbox,
            scene_time=scene_time,
            mode=mode,
            width=256,
            height=256,
        )
