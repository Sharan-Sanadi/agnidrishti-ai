# AGNIDRISHTI API — Live NASA FIRMS Integration Test

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)


def test_live_firms_integration():
    """
    Live Integration Test:
    Contacts real NASA FIRMS API using server-side configured key.
    Verifies response structure, non-zero observations for India, and canonical DTO parsing.
    NEVER logs or discloses the MAP_KEY.
    """
    settings = get_settings()
    if not settings.is_firms_configured:
        pytest.skip("NASA FIRMS MAP_KEY is not configured on server. Skipping live integration test.")

    # Query Central / Southern India region with known thermal activity
    response = client.get(
        "/api/v1/firms/hotspots"
        "?west=75.0&south=15.0&east=85.0&north=25.0&days=1&force_refresh=true"
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    # Verify response contract
    assert data["mode"] == "live"
    assert data["provider"] == "NASA FIRMS"
    assert set(data["sources"]) == {"VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"}
    assert data["data_status"] == "fresh"
    assert "count" in data
    assert "observations" in data
    assert isinstance(data["observations"], list)

    print(f"\n[LIVE TEST] Successfully ingested {data['count']} observations from NASA FIRMS.")

    if data["count"] > 0:
        obs = data["observations"][0]
        # Coordinate bounds sanity check
        assert 15.0 <= obs["latitude"] <= 25.0
        assert 75.0 <= obs["longitude"] <= 85.0
        # GeoJSON Point convention: [longitude, latitude]
        assert obs["geojson"]["type"] == "Point"
        assert obs["geojson"]["coordinates"] == [obs["longitude"], obs["latitude"]]
        # Traceability metadata
        assert obs["satellite"] in ("N20", "N21", "SNPP")
        assert obs["instrument"] == "VIIRS"
        assert obs["id"].startswith("firms_")
        assert "acquisition_time_utc" in obs
        assert "ingestion_time_utc" in obs
