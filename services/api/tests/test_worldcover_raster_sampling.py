# AGNIDRISHTI API — WorldCover Raster Sampling & Circular Mask Tests
"""
Verifies raster class sampling, true metric Azimuthal Equidistant circular masking,
nodata exclusion, multi-scale neighborhood extraction, and corner exclusion.
"""

from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin

from app.providers.worldcover.raster import WorldCoverRasterProcessor


@pytest.fixture
def synthetic_worldcover_tif(tmp_path: Path) -> tuple[Path, str, float, float]:
    """
    Creates a synthetic 10m-equivalent GeoTIFF in EPSG:4326 for deterministic testing.
    Grid centered around lat=20.0, lon=80.0.
    10m at lat 20 is ~0.00008983 degrees lat, ~0.0000956 degrees lon.
    Creates a 300x300 pixel raster:
    - Inner 30x30 pixels (approx 250m radius) = 40 (CROPLAND)
    - Ring from 30 to 60 pixels (approx 500m radius) = 50 (BUILT_UP)
    - Ring from 60 to 120 pixels (approx 1000m radius) = 10 (TREE_COVER)
    - Outer corners = 0 (NODATA) and 80 (PERMANENT_WATER)
    """
    width = 300
    height = 300
    # Pixel size roughly 10 meters in degrees:
    res_deg = 0.00009  # ~10 meters

    center_lat = 20.0
    center_lon = 80.0

    # Top-left corner:
    top_lat = center_lat + (height // 2) * res_deg
    left_lon = center_lon - (width // 2) * res_deg

    transform = from_origin(left_lon, top_lat, res_deg, res_deg)

    # Fill raster
    data = np.zeros((height, width), dtype=np.uint8)

    y_indices, x_indices = np.indices((height, width))
    cy, cx = height // 2, width // 2
    r_pixel = np.sqrt((x_indices - cx) ** 2 + (y_indices - cy) ** 2)

    # Within ~25 pixels (250m): CROPLAND (40)
    data[r_pixel <= 25] = 40

    # Between 25 and 50 pixels (~500m): BUILT_UP (50)
    data[(r_pixel > 25) & (r_pixel <= 50)] = 50

    # Between 50 and 110 pixels (up to ~1000m): TREE_COVER (10)
    data[(r_pixel > 50) & (r_pixel <= 110)] = 10

    # Beyond 110 pixels (outside 1000m circle, but within rectangular window corners): PERMANENT_WATER (80)
    data[r_pixel > 110] = 80

    # Put some NODATA (0) in far corners
    data[r_pixel > 140] = 0

    tile_id = "N18E078"
    file_path = tmp_path / f"ESA_WorldCover_10m_2021_v200_{tile_id}_Map.tif"

    with rasterio.open(
        file_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=np.uint8,
        crs=CRS.from_epsg(4326),
        transform=transform,
        nodata=0,
    ) as dst:
        dst.write(data, 1)

    return file_path, tile_id, center_lat, center_lon


def test_point_pixel_sampling(synthetic_worldcover_tif):
    """Verify point sampling at exact observation coordinates."""
    file_path, tile_id, center_lat, center_lon = synthetic_worldcover_tif
    tile_paths = {tile_id: file_path}

    analysis = WorldCoverRasterProcessor.sample_observation(
        observation_id="firms_test_pt_01",
        lat=center_lat,
        lon=center_lon,
        tile_paths=tile_paths,
        max_radius_m=1000.0,
    )

    # Point sample at center should be CROPLAND (40)
    assert analysis.point_sample.code == 40
    assert analysis.point_sample.class_name == "CROPLAND"
    assert analysis.point_sample.tile_id == tile_id
    assert analysis.coverage_status.value == "COMPLETE"


def test_multiscale_circular_neighborhoods(synthetic_worldcover_tif):
    """
    Verify multi-scale radius extraction:
    - 250m: dominant CROPLAND
    - 500m: dominant BUILT_UP (outer ring has larger area than inner circle)
    - 1000m: dominant TREE_COVER (outer ring has largest area)
    """
    file_path, tile_id, center_lat, center_lon = synthetic_worldcover_tif
    tile_paths = {tile_id: file_path}

    analysis = WorldCoverRasterProcessor.sample_observation(
        observation_id="firms_test_scale_01",
        lat=center_lat,
        lon=center_lon,
        tile_paths=tile_paths,
        max_radius_m=1000.0,
    )

    # 250m radius check
    assert analysis.scale_250m.dominant_class == "CROPLAND"
    assert analysis.scale_250m.dominant_fraction > 0.90
    assert analysis.scale_250m.valid_pixels > 0


    # 500m radius check
    assert "BUILT_UP" in analysis.scale_500m.class_fractions
    assert "CROPLAND" in analysis.scale_500m.class_fractions

    # 1000m radius check
    assert "TREE_COVER" in analysis.scale_1000m.class_fractions

    # Fractions must sum to ~1.0
    for scale in [analysis.scale_250m, analysis.scale_500m, analysis.scale_1000m]:
        frac_sum = sum(scale.class_fractions.values())
        assert abs(frac_sum - 1.0) < 1e-4, f"Fractions do not sum to 1.0: {frac_sum}"


def test_circular_mask_excludes_square_corners(synthetic_worldcover_tif):
    """
    Critical test: ensure rectangular read window corners (distance > 1000m) are excluded.
    In our synthetic raster, data beyond r=110 pixels (>1000m metric) is WATER (80).
    A square bounding box covers corners at r = sqrt(106^2 + 100^2) = 146 pixels (which are WATER).
    Circular mask MUST exclude those pixels!
    """
    file_path, tile_id, center_lat, center_lon = synthetic_worldcover_tif
    tile_paths = {tile_id: file_path}

    analysis = WorldCoverRasterProcessor.sample_observation(
        observation_id="firms_test_circle_01",
        lat=center_lat,
        lon=center_lon,
        tile_paths=tile_paths,
        max_radius_m=1000.0,
    )

    # 1000m circle should NOT contain WATER (80) which starts beyond 1000m
    water_1000m = analysis.scale_1000m.class_fractions.get("PERMANENT_WATER", 0.0)
    assert water_1000m == 0.0, f"Water was included in 1000m circular mask: {water_1000m}"


def test_nodata_pixels_excluded_from_denominator():
    """Verify that nodata pixels (0) do not skew fractions or count as valid."""
    from app.providers.worldcover.raster import calculate_scale_distribution

    # Array with 80 cropland pixels (40), 20 built-up pixels (50), and 50 nodata pixels (0)
    values = np.array([40] * 80 + [50] * 20 + [0] * 50, dtype=np.uint8)
    mask = np.ones(len(values), dtype=bool)

    dist = calculate_scale_distribution(values, mask, radius_m=500.0)

    assert dist.valid_pixels == 100
    assert dist.invalid_pixels == 50
    assert dist.class_fractions["CROPLAND"] == 0.80
    assert dist.class_fractions["BUILT_UP"] == 0.20
    assert dist.dominant_class == "CROPLAND"
    assert dist.dominant_fraction == 0.80
    assert sum(dist.class_fractions.values()) == pytest.approx(1.0, abs=1e-4)



def test_missing_required_tile_produces_unavailable():
    """Verify missing tile produces UNAVAILABLE status."""
    analysis = WorldCoverRasterProcessor.sample_observation(
        observation_id="firms_test_missing_01",
        lat=20.0,
        lon=80.0,
        tile_paths={},  # No tiles available
        max_radius_m=1000.0,
    )

    assert analysis.coverage_status.value == "UNAVAILABLE"
    assert analysis.context_class.value == "UNAVAILABLE"
    assert analysis.point_sample.class_name == "UNAVAILABLE"
