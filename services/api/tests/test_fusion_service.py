# AGNIDRISHTI API — Phase 7 Feature Fusion Service & API Integration Tests
"""
Integration tests for Phase 7 Feature Fusion.
Tests:
- API endpoint validation: 500 allowed, 501 rejected (HTTP 422).
- GET /api/v1/fusion/schema.
- Real exemplar verification against live PostGIS database:
  - Complete profile (firms_30a18cb033d6d4bfd8ed): assert exact equality with Phase 1-6 sources.
  - Partial CLOUD_LIMITED profile (firms_a3600c2b088dbaca0a54).
  - Industrial NONE with valid coverage (firms_ccb8af1575de7c305d44).
- Idempotent sync: second sync reports reused, 0 duplicate rows.
- No external network calls during fusion sync.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models.feature_fusion_profile import ThermalFeatureFusionProfileModel
from app.db.models.industrial_context_profile import IndustrialContextProfileModel
from app.db.models.land_cover_profile import ThermalLandCoverProfileModel
from app.db.models.sentinel_context_profile import ThermalSentinelContextProfileModel
from app.db.models.thermal_observation import ThermalObservationModel
from app.db.session import get_db
from app.main import app
from app.schemas.fusion import BatchFusionResponse
from app.services.fusion.feature_registry import SCHEMA_VERSION_V1, fusion_v1_registry
from app.services.fusion.service import FeatureFusionService
from app.services.temporal_persistence import TemporalPersistenceService

client = TestClient(app)


def test_fusion_schema_endpoint() -> None:
    response = client.get("/api/v1/fusion/schema")
    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "fusion_v1"
    assert data["schema_hash"] == fusion_v1_registry.schema_hash
    assert data["total_features"] == 59
    assert data["model_eligible_features"] == 57
    assert len(data["features"]) == 59


def test_batch_fusion_limit_501_rejected() -> None:
    excessive_ids = [f"firms_test_excess_{i:04d}" for i in range(501)]
    response = client.post(
        "/api/v1/fusion/batch",
        json={"observation_ids": excessive_ids},
    )
    assert response.status_code == 422, f"Expected 422 for 501 items, got {response.status_code}"


def test_sync_fusion_limit_501_rejected() -> None:
    excessive_ids = [f"firms_test_excess_{i:04d}" for i in range(501)]
    response = client.post(
        "/api/v1/fusion/sync",
        json={"observation_ids": excessive_ids},
    )
    assert response.status_code == 422, f"Expected 422 for 501 items, got {response.status_code}"


def test_batch_fusion_limit_500_accepted() -> None:
    valid_ids = [f"firms_non_existent_{i:04d}" for i in range(500)]
    with patch(
        "app.api.v1.endpoints.fusion.FeatureFusionService.get_batch_profiles",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = BatchFusionResponse(
            schema_version="fusion_v1",
            count=0,
            profiles={},
        )
        response = client.post(
            "/api/v1/fusion/batch",
            json={"observation_ids": valid_ids},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schema_version"] == "fusion_v1"
        assert data["count"] == 0
        assert data["profiles"] == {}


def test_get_fusion_observation_not_found_404() -> None:
    async def mock_override_db():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        yield mock_session

    app.dependency_overrides[get_db] = mock_override_db
    try:
        response = client.get("/api/v1/observations/firms_non_existent_1234567890/fusion")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "OBSERVATION_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_live_exemplar_complete_fusion_exact_equality(db_session) -> None:
    """
    Verify complete fusion profile on real live exemplar observation 'firms_30a18cb033d6d4bfd8ed'.
    Proves exact equality with upstream Phase 1-6 values:
    - FRP matches ThermalObservationModel.frp
    - Persistence index matches TemporalPersistenceService
    - Industrial distance matches IndustrialContextProfileModel
    - Built-up fraction matches ThermalLandCoverProfileModel
    - Sentinel NDVI matches ThermalSentinelContextProfileModel
    """
    obs_id = "firms_30a18cb033d6d4bfd8ed"
    session = db_session

    # Verify upstream models exist
    obs = await session.get(ThermalObservationModel, obs_id)
    assert obs is not None, f"Observation {obs_id} must exist in DB"

    ind = (
        await session.execute(
            select(IndustrialContextProfileModel).where(
                IndustrialContextProfileModel.observation_id == obs_id
            )
        )
    ).scalar_one_or_none()
    assert ind is not None

    lc = (
        await session.execute(
            select(ThermalLandCoverProfileModel).where(
                ThermalLandCoverProfileModel.observation_id == obs_id
            )
        )
    ).scalar_one_or_none()
    assert lc is not None

    s2 = (
        await session.execute(
            select(ThermalSentinelContextProfileModel).where(
                ThermalSentinelContextProfileModel.observation_id == obs_id
            )
        )
    ).scalar_one_or_none()
    assert s2 is not None

    pers_service = TemporalPersistenceService(session)
    pers = await pers_service.analyze_observation(obs)

    # Execute fusion sync
    service = FeatureFusionService(session)
    sync_res = await service.sync_batch([obs_id])
    assert sync_res.requested == 1

    # Fetch fused profile
    profile = await service.get_profile(obs_id)
    assert profile is not None
    assert profile.observation_id == obs_id
    assert profile.schema_version == SCHEMA_VERSION_V1
    assert profile.schema_hash == fusion_v1_registry.schema_hash
    assert profile.fusion_status == "COMPLETE"
    assert profile.total_group_count == 5
    assert profile.usable_group_count == 5

    f_vec = profile.feature_vector

    # 1. Thermal Equality
    assert f_vec["thermal_frp"] == obs.frp
    assert f_vec["thermal_brightness_ti4"] == obs.bright_ti4
    assert f_vec["thermal_daynight"] == obs.daynight

    # 2. Temporal Equality (Canonical 0-100 scale preserved!)
    assert f_vec["temporal_persistence_index"] == pers.persistence_index
    assert f_vec["temporal_persistence_index"] == 100
    assert f_vec["temporal_persistence_class"] == pers.persistence_class
    assert f_vec["temporal_active_days_30d"] == pers.active_days_30d

    # 3. Industrial Equality
    assert f_vec["industrial_context_class"] == ind.context_class
    assert f_vec["industrial_nearest_distance_m"] == ind.nearest_industrial_distance_m
    assert f_vec["industrial_inside_area"] == ind.inside_industrial_area

    # 4. Land Cover Equality
    assert f_vec["landcover_point_class"] == lc.point_class_name
    assert f_vec["landcover_builtup_fraction_500m"] == lc.built_up_fraction_500m

    # 5. Sentinel-2 Equality
    assert f_vec["sentinel_quality_status"] == s2.quality_status
    assert f_vec["sentinel_ndvi_median_250m"] == s2.sentinel_ndvi_median_250m
    assert f_vec["sentinel_ndmi_median_250m"] == s2.sentinel_ndmi_median_250m
    assert f_vec["sentinel_nbr_median_250m"] == s2.sentinel_nbr_median_250m

    # High feature coverage
    assert profile.feature_coverage_percent > 80


@pytest.mark.asyncio
async def test_live_exemplar_partial_cloud_limited_null_preservation(db_session) -> None:
    """
    Verify partial fusion profile on real live exemplar observation 'firms_a3600c2b088dbaca0a54'.
    Asserts Sentinel CLOUD_LIMITED preserves honest NULL for NDVI/NDMI/NBR without imputation.
    """
    obs_id = "firms_a3600c2b088dbaca0a54"
    session = db_session

    service = FeatureFusionService(session)
    sync_res = await service.sync_batch([obs_id])
    assert sync_res.requested == 1

    profile = await service.get_profile(obs_id)
    assert profile is not None
    assert profile.fusion_status == "PARTIAL"
    assert profile.group_status["SENTINEL"] == "CLOUD_LIMITED"

    f_vec = profile.feature_vector
    # Spectral features MUST BE NULL
    assert f_vec["sentinel_ndvi_median_250m"] is None
    assert f_vec["sentinel_ndmi_median_250m"] is None
    assert f_vec["sentinel_nbr_median_250m"] is None


@pytest.mark.asyncio
async def test_live_exemplar_industrial_none_preservation(db_session) -> None:
    """
    Verify that an observation with industrial context NONE and ADEQUATE coverage
    preserves counts=0, distance=None, and evaluates group status as AVAILABLE.
    """
    obs_id = "firms_ccb8af1575de7c305d44"
    session = db_session

    service = FeatureFusionService(session)
    sync_res = await service.sync_batch([obs_id])
    assert sync_res.requested == 1

    profile = await service.get_profile(obs_id)
    assert profile is not None
    assert profile.group_status["INDUSTRIAL"] == "AVAILABLE"

    f_vec = profile.feature_vector
    assert f_vec["industrial_context_class"] == "NONE"
    assert f_vec["industrial_coverage_status"] == "ADEQUATE"
    assert f_vec["industrial_nearest_distance_m"] is None
    assert f_vec["industrial_feature_count_500m"] == 0
    assert f_vec["industrial_feature_count_5km"] == 0


@pytest.mark.asyncio
async def test_idempotent_sync_and_duplicate_prevention(db_session) -> None:
    """
    Verify that syncing the same observation batch twice:
    - Reuses existing profiles on second sync (reused == count)
    - Produces ZERO duplicate database rows (UNIQUE constraint enforced)
    """
    obs_id = "firms_30a18cb033d6d4bfd8ed"
    session = db_session

    service = FeatureFusionService(session)

    # First sync
    res1 = await service.sync_batch([obs_id])
    assert res1.requested == 1

    # Second sync (same upstream data, same schema)
    res2 = await service.sync_batch([obs_id])
    assert res2.requested == 1
    assert res2.reused == 1
    assert res2.created == 0
    assert res2.updated == 0

    # Verify DB row count is strictly 1 for this observation
    count_stmt = select(func.count()).select_from(ThermalFeatureFusionProfileModel).where(
        ThermalFeatureFusionProfileModel.observation_id == obs_id,
        ThermalFeatureFusionProfileModel.schema_version == SCHEMA_VERSION_V1,
    )
    row_count = (await session.execute(count_stmt)).scalar()
    assert row_count == 1, "There must be exactly one row per (observation_id, schema_version)"


@pytest.mark.asyncio
async def test_network_isolation_zero_external_calls(db_session, monkeypatch) -> None:
    """
    Assert that during Phase 7 feature fusion sync:
    ZERO external HTTP/network requests are made to NASA, Overpass, CDSE, or WorldCover.
    """
    import httpx

    called_urls: list[str] = []
    orig_send = httpx.AsyncClient.send

    async def tracking_send(self, request, *args, **kwargs):
        called_urls.append(str(request.url))
        return await orig_send(self, request, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "send", tracking_send)

    obs_id = "firms_30a18cb033d6d4bfd8ed"
    service = FeatureFusionService(db_session)
    res = await service.sync_batch([obs_id], force_recompute=True)

    assert res.requested == 1
    # Verify ZERO external calls made
    assert len(called_urls) == 0, f"External network calls detected during fusion sync: {called_urls}"


@pytest.mark.asyncio
async def test_bulk_database_query_efficiency_no_n_plus_one(db_session) -> None:
    """
    Verify that syncing a batch of 20 observations executes a bounded number of bulk queries,
    guaranteeing zero N+1 database operations.
    """
    # Grab 20 real observation IDs
    stmt = select(ThermalObservationModel.observation_id).limit(20)
    res = await db_session.execute(stmt)
    obs_ids = res.scalars().all()
    assert len(obs_ids) == 20

    service = FeatureFusionService(db_session)
    # First sync computes & caches persistence
    await service.sync_batch(obs_ids, force_recompute=False)

    # Second sync reads all 5 upstream tables using bulk queries (1 query per source table + upsert)
    sync_res = await service.sync_batch(obs_ids, force_recompute=True)
    assert sync_res.requested == 20
    # Exactly ~7 bulk queries total (no N+1 for 20 observations)
    assert sync_res.database_queries <= 10, f"Expected <=10 bulk queries, got {sync_res.database_queries}"
