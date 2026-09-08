# AGNIDRISHTI API — Stored Observations & Sync API Tests
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.db.models.thermal_observation import ThermalObservationModel
from app.db.session import get_db
from app.main import app

client = TestClient(app)


def test_health_check_preserved():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data


def test_readiness_check_unconfigured():
    with patch("app.main.check_postgis_readiness", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = {
            "status": "unhealthy",
            "ready": False,
            "error": "Connection refused",
        }
        response = client.get("/readiness")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unready"
        assert data["code"] == "DATABASE_UNAVAILABLE"


def test_readiness_check_ready():
    with patch("app.main.check_postgis_readiness", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = {
            "status": "ready",
            "ready": True,
            "database": "agnidrishti",
            "postgis_version": "3.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1",
        }
        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"]["postgis_version"].startswith("3.4")


def test_get_observations_database_unconfigured():
    with patch(
        "app.api.v1.endpoints.observations.ThermalObservationRepository.query_spatial_temporal",
        side_effect=Exception("Database unavailable"),
    ):
        response = client.get("/api/v1/observations")
        assert response.status_code == 503
        assert response.json()["detail"]["code"] == "DATABASE_UNAVAILABLE"


def test_get_observations_invalid_time_range():
    async def mock_override_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = mock_override_db
    try:
        response = client.get(
            "/api/v1/observations?start_time=2026-09-08T12:00:00Z&end_time=2026-09-08T10:00:00Z"
        )
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "INVALID_TIME_RANGE"
    finally:
        app.dependency_overrides.clear()


def test_get_observations_invalid_bbox():
    async def mock_override_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = mock_override_db
    try:
        # Inverted latitude (south > north)
        response = client.get(
            "/api/v1/observations?west=70.0&south=30.0&east=80.0&north=20.0"
        )
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "INVALID_BOUNDING_BOX"
    finally:
        app.dependency_overrides.clear()


def test_get_observations_mocked_success():
    now = datetime.now(UTC)
    mock_obs = ThermalObservationModel(
        observation_id="firms_mock12345",
        latitude=18.5204,
        longitude=73.8567,
        acquisition_time_utc=now,
        satellite="N20",
        instrument="VIIRS",
        source_product="VIIRS_NOAA20_NRT",
        provider="NASA FIRMS",
        confidence_raw="n",
        confidence_normalized="nominal",
        frp=25.0,
        bright_ti4=330.0,
        bright_ti5=295.0,
        scan=0.4,
        track=0.4,
        daynight="D",
        firms_version="2.0NRT",
        first_ingested_at=now,
        last_seen_at=now,
        ingestion_count=1,
    )

    async def mock_override_db():
        mock_session = AsyncMock()
        yield mock_session

    app.dependency_overrides[get_db] = mock_override_db

    with patch(
        "app.api.v1.endpoints.observations.ThermalObservationRepository.query_spatial_temporal",
        new_callable=AsyncMock,
    ) as mock_query:
        mock_query.return_value = ([mock_obs], 1)

        response = client.get("/api/v1/observations?west=70.0&south=15.0&east=80.0&north=25.0")
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "stored"
        assert data["storage"] == "PostGIS"
        assert data["count"] == 1
        assert data["total"] == 1
        obs = data["observations"][0]
        assert obs["id"] == "firms_mock12345"
        assert obs["stored_in_postgis"] is True
        assert obs["geojson"]["coordinates"] == [73.8567, 18.5204]

    app.dependency_overrides.clear()


def test_get_observation_by_id_not_found():
    async def mock_override_db():
        mock_session = AsyncMock()
        yield mock_session

    app.dependency_overrides[get_db] = mock_override_db

    with patch(
        "app.api.v1.endpoints.observations.ThermalObservationRepository.get_by_id",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = None

        response = client.get("/api/v1/observations/firms_nonexistent_id")
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "OBSERVATION_NOT_FOUND"

    app.dependency_overrides.clear()
