from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app

client = TestClient(app)


def test_sentinel_batch_limit_exceeded_501_rejected():
    """Verify Sentinel batch endpoint strictly rejects requests with >500 observation IDs with HTTP 422."""
    excessive_ids = [f"firms_test_excess_{i:04d}" for i in range(501)]
    response = client.post(
        "/api/v1/sentinel-2/batch",
        json={"observation_ids": excessive_ids},
    )
    assert response.status_code == 422, f"Expected 422 for 501 items, got {response.status_code}"


def test_sentinel_batch_limit_500_allowed():
    """Verify Sentinel batch endpoint accepts up to 500 observation IDs without 422 error."""
    valid_ids = [f"firms_test_valid_{i:04d}" for i in range(500)]

    with patch(
        "app.api.v1.endpoints.sentinel2.SentinelContextService.get_batch_profiles",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = {}

        response = client.post(
            "/api/v1/sentinel-2/batch",
            json={"observation_ids": valid_ids},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_requested"] == 500
        assert data["count"] == 0


def test_sentinel_sync_limit_exceeded_51_rejected():
    """Verify Sentinel sync endpoint strictly rejects requests with >50 observation IDs with HTTP 422."""
    excessive_ids = [f"firms_test_sync_{i:04d}" for i in range(51)]
    response = client.post(
        "/api/v1/sentinel-2/sync",
        json={"observation_ids": excessive_ids},
    )
    assert response.status_code == 422, f"Expected 422 for 51 items, got {response.status_code}"


def test_sentinel_get_observation_not_found_404():
    """Verify 404 returned when observation ID does not exist in canonical store."""
    async def mock_override_db():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        yield mock_session

    app.dependency_overrides[get_db] = mock_override_db
    try:
        response = client.get("/api/v1/observations/nonexistent_observation_id_9999/sentinel-2")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_sentinel_preview_invalid_mode_rejected_422():
    """Verify preview endpoint rejects invalid mode with HTTP 422 validation error."""
    response = client.get(
        "/api/v1/observations/firms_any_test_id/sentinel-2/preview",
        params={"mode": "INVALID_EVALSCRIPT_MODE"},
    )
    assert response.status_code == 422
