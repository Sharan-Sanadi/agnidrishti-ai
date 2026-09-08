# AGNIDRISHTI API — Tests for FIRMS API Endpoints

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.providers.firms import FIRMSClient, get_firms_client

client = TestClient(app)

MOCK_VIIRS_CSV = (
    "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
    "20.5937,78.9629,335.5,0.4,0.4,2026-09-07,0758,N20,VIIRS,n,2.0NRT,300.0,6.5,D\n"
)


@pytest.fixture(autouse=True)
def override_firms_client():
    """Ensure mock API tests run with a valid mock key regardless of host environment."""
    mock_settings = Settings(nasa_firms_map_key="mock_test_key_123")
    mock_client = FIRMSClient(mock_settings)
    app.dependency_overrides[get_firms_client] = lambda: mock_client
    yield
    app.dependency_overrides.pop(get_firms_client, None)



@respx.mock
def test_get_firms_hotspots_success():
    """Test successful FIRMS hotspot ingestion endpoint with mock upstream."""
    # Mock upstream NASA Area API
    respx.get(url__regex=r"https://firms\.modaps\.eosdis\.nasa\.gov/api/area/csv/.*").mock(
        return_value=httpx.Response(200, text=MOCK_VIIRS_CSV)
    )

    response = client.get("/api/v1/firms/hotspots?west=70&south=15&east=85&north=25&days=1&force_refresh=true")
    assert response.status_code == 200
    data = response.json()

    assert data["mode"] == "live"
    assert data["provider"] == "NASA FIRMS"
    assert "observations" in data
    assert data["count"] >= 1
    assert data["data_status"] == "fresh"

    obs = data["observations"][0]
    assert obs["latitude"] == 20.5937
    assert obs["longitude"] == 78.9629
    assert obs["geojson"]["coordinates"] == [78.9629, 20.5937]
    assert obs["satellite"] == "N20"


def test_get_firms_hotspots_invalid_bbox():
    """Test 422 error on invalid bounding box."""
    # South > North
    response = client.get("/api/v1/firms/hotspots?west=70&south=30&east=85&north=20")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert data["detail"]["code"] == "INVALID_BOUNDING_BOX"


def test_get_firms_hotspots_invalid_days():
    """Test 422 error on days > 5."""
    response = client.get("/api/v1/firms/hotspots?days=10")
    assert response.status_code == 422


@respx.mock
def test_get_firms_hotspots_auth_error():
    """Test 401 response on invalid MAP_KEY from NASA."""
    respx.get(url__regex=r"https://firms\.modaps\.eosdis\.nasa\.gov/api/area/csv/.*").mock(
        return_value=httpx.Response(400, text="Invalid MAP_KEY.")
    )

    response = client.get("/api/v1/firms/hotspots?force_refresh=true")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["code"] == "FIRMS_AUTH_ERROR"


@respx.mock
def test_get_firms_hotspots_timeout():
    """Test 504 response on upstream timeout."""
    respx.get(url__regex=r"https://firms\.modaps\.eosdis\.nasa\.gov/api/area/csv/.*").mock(
        side_effect=httpx.ReadTimeout("Timeout connecting to NASA")
    )

    response = client.get("/api/v1/firms/hotspots?force_refresh=true")
    assert response.status_code == 504
    data = response.json()
    assert data["detail"]["code"] == "FIRMS_TIMEOUT"
