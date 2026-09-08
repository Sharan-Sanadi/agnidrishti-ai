# AGNIDRISHTI API — Tests for FIRMS Client & Parser

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.providers.firms.client import (
    FIRMSCache,
    FIRMSClient,
    FIRMSValidationError,
    MissingFIRMSKeyError,
)
from app.providers.firms.parser import (
    generate_observation_id,
    normalize_acq_time,
    parse_firms_csv,
)
from app.schemas.firms import BoundingBox


def test_normalize_acq_time():
    """Verify leading-zero time normalization."""
    assert normalize_acq_time("758") == (7, 58, "07:58")
    assert normalize_acq_time("0035") == (0, 35, "00:35")
    assert normalize_acq_time("35") == (0, 35, "00:35")
    assert normalize_acq_time("5") == (0, 5, "00:05")
    assert normalize_acq_time("1425") == (14, 25, "14:25")
    assert normalize_acq_time("0") == (0, 0, "00:00")


def test_generate_observation_id_stability():
    """Verify deterministic observation identifier generation."""
    id1 = generate_observation_id(
        source="VIIRS_NOAA20_NRT",
        satellite="N20",
        acq_iso="2026-09-07T07:58:00+00:00",
        latitude=15.0153,
        longitude=79.70184,
    )
    id2 = generate_observation_id(
        source="VIIRS_NOAA20_NRT",
        satellite="N20",
        acq_iso="2026-09-07T07:58:00+00:00",
        latitude=15.0153,
        longitude=79.70184,
    )
    assert id1 == id2
    assert id1.startswith("firms_")
    # Must be 26 chars (firms_ + 20 hex chars)
    assert len(id1) == 26

    # Verify ID never matches fixture UUID format
    assert "-" not in id1
    assert not id1.startswith("11111111")
    assert not id1.startswith("22222222")
    assert not id1.startswith("33333333")

    # Different coordinates yield different ID
    id3 = generate_observation_id(
        source="VIIRS_NOAA20_NRT",
        satellite="N20",
        acq_iso="2026-09-07T07:58:00+00:00",
        latitude=15.0154,
        longitude=79.70184,
    )
    assert id1 != id3


def test_parse_firms_csv_valid():
    """Verify standard VIIRS CSV parsing with real NASA column names."""
    csv_sample = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
        "15.01530,79.70184,335.52,0.39,0.36,2026-09-07,758,N20,VIIRS,l,2.0NRT,301.28,5.42,D\n"
        "20.86604,84.98908,342.10,0.51,0.49,2026-09-07,1402,N21,VIIRS,h,2.0NRT,298.40,12.50,N\n"
    )

    observations, rejected = parse_firms_csv(csv_sample, "VIIRS_NOAA20_NRT")
    assert rejected == 0
    assert len(observations) == 2

    first = observations[0]
    assert first.latitude == 15.0153
    assert first.longitude == 79.70184
    assert first.satellite == "N20"
    assert first.instrument == "VIIRS"
    assert first.confidence == "l"
    assert first.bright_ti4 == 335.52
    assert first.bright_ti5 == 301.28
    assert first.frp == 5.42
    assert first.daynight == "D"
    assert first.acquisition_time_utc == datetime(2026, 9, 7, 7, 58, tzinfo=UTC)
    # GeoJSON convention: [longitude, latitude]
    assert first.geojson["coordinates"] == [79.70184, 15.0153]


def test_parse_firms_csv_tolerant_to_extra_columns():
    """Parser must tolerate extra future columns without failing."""
    csv_with_extra = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight,extra_col_1,extra_col_2\n"
        "18.5204,73.8567,330.0,0.4,0.4,2026-09-07,0830,N20,VIIRS,n,2.0NRT,300.0,3.5,D,foo,bar\n"
    )
    observations, rejected = parse_firms_csv(csv_with_extra, "VIIRS_NOAA20_NRT")
    assert len(observations) == 1
    assert rejected == 0
    assert observations[0].latitude == 18.5204


def test_parse_firms_csv_empty():
    """Empty CSV or header-only returns zero observations."""
    header_only = "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
    obs, rej = parse_firms_csv(header_only, "VIIRS_NOAA20_NRT")
    assert obs == []
    assert rej == 0

    obs2, rej2 = parse_firms_csv("", "VIIRS_NOAA20_NRT")
    assert obs2 == []
    assert rej2 == 0


def test_parse_firms_csv_skips_malformed_rows():
    """Malformed individual rows are tracked in rejected_count without crashing dataset."""
    csv_malformed = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
        "NOT_A_LAT,79.70184,335.52,0.39,0.36,2026-09-07,758,N20,VIIRS,l,2.0NRT,301.28,5.42,D\n"
        "15.01530,79.70184,335.52,0.39,0.36,2026-09-07,758,N20,VIIRS,l,2.0NRT,301.28,5.42,D\n"
        "15.01530,999.000,335.52,0.39,0.36,2026-09-07,758,N20,VIIRS,l,2.0NRT,301.28,5.42,D\n"
    )
    obs, rej = parse_firms_csv(csv_malformed, "VIIRS_NOAA20_NRT")
    assert len(obs) == 1
    assert rej == 2


def test_bounding_box_validation():
    """Verify strict spatial bounds checking."""
    # Valid
    bbox = BoundingBox(west=68.0, south=6.5, east=97.5, north=37.5)
    assert bbox.to_firms_area() == "68.0000,6.5000,97.5000,37.5000"

    # South >= North
    with pytest.raises(ValidationError):
        BoundingBox(west=68.0, south=37.5, east=97.5, north=6.5)

    # West >= East (antimeridian rejection)
    with pytest.raises(ValidationError):
        BoundingBox(west=97.5, south=6.5, east=68.0, north=37.5)

    # Out of range
    with pytest.raises(ValidationError):
        BoundingBox(west=-190.0, south=6.5, east=97.5, north=37.5)


def test_client_validation():
    """Verify client parameter validations."""
    settings = Settings(nasa_firms_map_key="fake_key")
    client = FIRMSClient(settings)

    # Day range
    assert client.validate_day_range(1) == 1
    assert client.validate_day_range(5) == 5
    with pytest.raises(FIRMSValidationError):
        client.validate_day_range(0)
    with pytest.raises(FIRMSValidationError):
        client.validate_day_range(6)

    # Sensors
    valid_sensors = client.validate_sensors(["VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"])
    assert len(valid_sensors) == 2
    with pytest.raises(FIRMSValidationError):
        client.validate_sensors(["MODIS_INVALID"])

    # Missing key
    no_key_client = FIRMSClient(Settings(nasa_firms_map_key="", firms_map_key=""))
    with pytest.raises(MissingFIRMSKeyError):
        no_key_client.validate_configuration()


def test_firms_cache():
    """Verify in-memory TTL caching behaviour."""
    cache = FIRMSCache(max_entries=5)
    sources = ["VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]

    # Miss
    assert cache.get(sources, "68,6.5,97.5,37.5", 1, None) is None

    # Set
    dummy_obs = []
    now = datetime.now(UTC)
    cache.set(
        sources=sources,
        area_str="68,6.5,97.5,37.5",
        day_range=1,
        date_str=None,
        observations=dummy_obs,
        rejected_count=0,
        fetched_at=now,
        ttl_seconds=60,
    )

    # Hit
    hit = cache.get(["VIIRS_NOAA21_NRT", "VIIRS_NOAA20_NRT"], "68,6.5,97.5,37.5", 1, None)
    assert hit is not None
    obs, rej, fetched_at, status = hit
    assert status == "fresh"
    assert fetched_at == now
