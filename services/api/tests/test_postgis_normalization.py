# AGNIDRISHTI API — PostGIS Normalization & Config Unit Tests
from datetime import UTC, datetime

from app.core.config import Settings
from app.schemas.firms import BoundingBox, ThermalObservation
from app.services.firms_ingestion import (
    normalize_confidence,
    observation_to_storage_record,
    sanitize_float,
)


def test_confidence_normalization():
    assert normalize_confidence("l") == "low"
    assert normalize_confidence("n") == "nominal"
    assert normalize_confidence("h") == "high"
    assert normalize_confidence("L") == "low"
    assert normalize_confidence("N") == "nominal"
    assert normalize_confidence("H") == "high"
    assert normalize_confidence("low") == "low"
    assert normalize_confidence("nominal") == "nominal"
    assert normalize_confidence("high") == "high"
    # Unknown string preserved without crashing
    assert normalize_confidence("custom_grade") == "custom_grade"
    assert normalize_confidence("") is None


def test_sanitize_float():
    assert sanitize_float(12.34) == 12.34
    assert sanitize_float(0.0) == 0.0
    assert sanitize_float(None) is None
    assert sanitize_float(float("nan")) is None
    assert sanitize_float(float("inf")) is None
    assert sanitize_float(float("-inf")) is None


def test_observation_to_storage_record_coordinates_and_metadata():
    now = datetime.now(UTC)
    obs = ThermalObservation(
        id="firms_abc1234567890",
        latitude=19.0760,
        longitude=72.8777,
        acquisition_time_utc=now,
        satellite="N20",
        instrument="VIIRS",
        source="VIIRS_NOAA20_NRT",
        confidence="n",
        frp=42.5,
        bright_ti4=335.2,
        bright_ti5=295.1,
        scan=0.38,
        track=0.36,
        daynight="D",
        firms_version="2.0NRT",
        ingestion_time_utc=now,
        geojson={"type": "Point", "coordinates": [72.8777, 19.0760]},
    )

    rec = observation_to_storage_record(obs)

    # CRITICAL GIS: Longitude and Latitude must match exactly
    assert rec["observation_id"] == "firms_abc1234567890"
    assert rec["latitude"] == 19.0760
    assert rec["longitude"] == 72.8777
    assert rec["confidence_raw"] == "n"
    assert rec["confidence_normalized"] == "nominal"
    assert rec["frp"] == 42.5
    assert rec["provider"] == "NASA FIRMS"
    assert rec["source_product"] == "VIIRS_NOAA20_NRT"
    assert rec["satellite"] == "N20"

    # Verify sanitized raw payload contains no secrets
    assert "raw_payload" in rec
    raw = rec["raw_payload"]
    assert "map_key" not in raw
    assert "password" not in raw
    assert "key" not in raw


def test_database_url_sanitization():
    settings = Settings(
        database_url="postgresql+asyncpg://myuser:supersecretpassword@db.example.com:5432/agnidrishti"
    )
    sanitized = settings.sanitized_database_url
    assert "supersecretpassword" not in sanitized
    assert "myuser:***@db.example.com:5432/agnidrishti" in sanitized

    # Empty URL handled gracefully
    settings_empty = Settings(database_url="")
    assert settings_empty.sanitized_database_url == "not_configured"


def test_async_database_url_normalization():
    # Automatically upgrades postgresql:// to postgresql+asyncpg://
    s1 = Settings(database_url="postgresql://postgres:pass@localhost:5432/mydb")
    assert s1.async_database_url == "postgresql+asyncpg://postgres:pass@localhost:5432/mydb"

    s2 = Settings(database_url="postgres://postgres:pass@localhost:5432/mydb")
    assert s2.async_database_url == "postgresql+asyncpg://postgres:pass@localhost:5432/mydb"


def test_spatial_bbox_validation():
    # Valid bounding box
    bbox = BoundingBox(west=68.0, south=6.5, east=97.5, north=37.5)
    assert bbox.west == 68.0
    assert bbox.north == 37.5

    # Inverted latitude should fail
    try:
        BoundingBox(west=68.0, south=37.5, east=97.5, north=6.5)
        assert False, "Should raise ValueError for inverted latitude"
    except ValueError:
        pass

    # Inverted longitude should fail
    try:
        BoundingBox(west=97.5, south=6.5, east=68.0, north=37.5)
        assert False, "Should raise ValueError for inverted longitude"
    except ValueError:
        pass
