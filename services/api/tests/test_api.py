from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_hotspots():
    response = client.get("/api/v1/hotspots")
    assert response.status_code == 200
    data = response.json()
    assert "hotspots" in data
    assert "total" in data
    assert data["analysis_mode"] == "fixture"

def test_get_hotspot_found():
    # Fetch all hotspots to get a valid ID
    response = client.get("/api/v1/hotspots")
    data = response.json()
    if data["hotspots"]:
        valid_id = data["hotspots"][0]["id"]
        res = client.get(f"/api/v1/hotspots/{valid_id}")
        assert res.status_code == 200
        assert res.json()["id"] == valid_id

def test_get_hotspot_not_found():
    response = client.get("/api/v1/hotspots/invalid-id")
    assert response.status_code == 404

def test_analyze_hotspot():
    payload = {"latitude": 20.0, "longitude": 78.0}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "hotspot" in data
    assert "classification" in data
    assert data["analysis_mode"] == "fixture"

def test_analyze_invalid_coordinates():
    # Invalid latitude
    payload = {"latitude": 100.0, "longitude": 78.0}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422

    # Invalid longitude
    payload2 = {"latitude": 20.0, "longitude": 200.0}
    response2 = client.post("/api/v1/analyze", json=payload2)
    assert response2.status_code == 422
