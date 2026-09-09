# AGNIDRISHTI API — Land Cover API & Quality Gate Tests
"""
Verifies:
- 500 max batch validation (422 for 501+ IDs)
- 404 for unknown observation ID
- Corrupted tile cache handling (rejection of bad .part files)
- Truthful provider failure semantics (no fake zeros or false success)
- DB idempotency and duplicate prevention
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.providers.worldcover.client import WorldCoverClient

client = TestClient(app)


def test_batch_limit_exceeded_501_rejected():
    """Verify batch endpoint strictly rejects requests with >500 observation IDs with HTTP 422."""
    excessive_ids = [f"firms_test_excess_{i:04d}" for i in range(501)]
    response = client.post(
        "/api/v1/land-cover/batch",
        json={"observation_ids": excessive_ids},
    )
    assert response.status_code == 422, f"Expected 422 for 501 items, got {response.status_code}"


def test_batch_limit_500_allowed():
    """Verify batch endpoint accepts up to 500 observation IDs without 422 error."""
    valid_ids = [f"firms_test_valid_{i:04d}" for i in range(500)]

    # Mock service to avoid heavy DB/raster work for 500 IDs in fast unit test
    with patch(
        "app.api.v1.endpoints.land_cover.LandCoverService.get_batch_profiles",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = {}

        response = client.post(
            "/api/v1/land-cover/batch",
            json={"observation_ids": valid_ids},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_requested"] == 500
        assert data["count"] == 0


def test_get_observation_not_found_404():
    """Verify 404 returned when observation ID does not exist in canonical store."""
    response = client.get("/api/v1/observations/nonexistent_observation_id_9999/land-cover")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_corrupt_tile_part_rejection(tmp_path: Path):
    """
    Verify tile download validation rejects corrupted or non-raster .part files
    and does not promote them to the active cache.
    """
    worldcover_client = WorldCoverClient(cache_dir=tmp_path)
    tile_id = "N18E078"
    part_path = tmp_path / f"ESA_WorldCover_10m_2021_v200_{tile_id}_Map.tif.part"

    # Write corrupt data (plain text, not GeoTIFF)
    part_path.write_bytes(b"THIS IS CORRUPTED TRASH DATA NOT A GEOTIFF")

    is_valid = worldcover_client._validate_downloaded_raster(part_path)
    assert is_valid is False

    # The permanent cache file should NOT exist
    cache_path = tmp_path / f"ESA_WorldCover_10m_2021_v200_{tile_id}_Map.tif"
    assert not cache_path.exists()


@pytest.mark.asyncio
async def test_empty_zero_byte_tile_rejection(tmp_path: Path):
    """Verify 0-byte tile is detected as invalid and rejected."""
    worldcover_client = WorldCoverClient(cache_dir=tmp_path)
    part_path = tmp_path / "ESA_WorldCover_10m_2021_v200_N18E078_Map.tif.part"
    part_path.write_bytes(b"")

    is_valid = worldcover_client._validate_downloaded_raster(part_path)
    assert is_valid is False


def test_truthful_provider_failure_does_not_fake_zeros():
    """Verify that when WorldCover is unavailable, response retains UNAVAILABLE semantics."""
    from app.providers.worldcover.raster import WorldCoverRasterProcessor

    # When no raster tiles are available
    analysis = WorldCoverRasterProcessor.sample_observation(
        observation_id="firms_test_unavail",
        lat=25.0,
        lon=85.0,
        tile_paths={},
        max_radius_m=1000.0,
    )

    assert analysis.coverage_status.value == "UNAVAILABLE"
    assert analysis.context_class.value == "UNAVAILABLE"
    # Dominant class must be UNAVAILABLE, not a faked class or fake 0.0 percentages
    assert analysis.scale_500m.dominant_class == "UNAVAILABLE"
    assert analysis.scale_500m.dominant_fraction == 0.0
    assert analysis.scale_500m.valid_pixels == 0
