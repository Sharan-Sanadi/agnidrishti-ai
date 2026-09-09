# AGNIDRISHTI API — Sentinel-2 Metric Spatial Sampling & Statistics Unit Tests
import numpy as np
import pytest
from rasterio.transform import Affine

from app.providers.sentinel2.constants import (
    SCL_CLOUD_HIGH_PROBABILITY,
    SCL_VEGETATION,
)
from app.providers.sentinel2.spatial import (
    compute_pixel_metric_distances,
    create_circular_mask,
)
from app.providers.sentinel2.statistics import (
    compute_radius_statistics,
    extract_point_sample,
)


def test_metric_distances_and_circular_mask_corners_excluded():
    # 51x51 grid with pixel resolution ~20m (roughly 0.00018 deg per pixel)
    center_lat = 21.105
    center_lon = 72.653
    width, height = 51, 51

    # Approx 20m in degrees
    res_deg = 20.0 / 111320.0
    west = center_lon - (width // 2) * res_deg
    north = center_lat + (height // 2) * res_deg
    transform = Affine.translation(west, north) * Affine.scale(res_deg, -res_deg)

    distances = compute_pixel_metric_distances(
        center_lat=center_lat,
        center_lon=center_lon,
        transform=transform,
        height=height,
        width=width,
    )

    # Center pixel (25, 25) must be very close to 0 meters
    assert distances[25, 25] < 15.0

    # Corners (0, 0) and (50, 50) must be approx sqrt(500^2 + 500^2) ~ 707m
    assert distances[0, 0] > 650.0
    assert distances[50, 50] > 650.0

    # 250m mask
    mask_250 = create_circular_mask(distances, 250.0)
    # Center pixel is inside
    assert bool(mask_250[25, 25])
    # Corners are strictly outside
    assert not mask_250[0, 0]
    assert not mask_250[0, 50]
    assert not mask_250[50, 0]
    assert not mask_250[50, 50]

    # 500m mask
    mask_500 = create_circular_mask(distances, 500.0)
    # Center is inside
    assert mask_500[25, 25]
    # Corners (707m) must be strictly excluded from circular 500m mask!
    assert not mask_500[0, 0]
    assert not mask_500[50, 50]


def test_radius_statistics_cloud_masking():
    # 10x10 synthetic raster
    distances = np.zeros((10, 10), dtype=float)
    # 50 pixels inside 250m
    distances[:5, :] = 100.0
    # 50 pixels outside
    distances[5:, :] = 400.0

    b04 = np.full((10, 10), 0.2, dtype=np.float32)
    b08 = np.full((10, 10), 0.6, dtype=np.float32)
    b11 = np.full((10, 10), 0.3, dtype=np.float32)
    b12 = np.full((10, 10), 0.1, dtype=np.float32)

    # In the top 5 rows (inside radius): make row 0-2 clear vegetation (30 pixels), row 3-4 cloud (20 pixels)
    scl = np.full((10, 10), SCL_VEGETATION, dtype=np.uint8)
    scl[3:5, :] = SCL_CLOUD_HIGH_PROBABILITY
    data_mask = np.ones((10, 10), dtype=np.uint8)

    stats = compute_radius_statistics(
        b04_arr=b04,
        b08_arr=b08,
        b11_arr=b11,
        b12_arr=b12,
        scl_arr=scl,
        data_mask_arr=data_mask,
        distances_m=distances,
        radius_m=250.0,
    )

    assert stats.total_pixel_count == 50
    assert stats.valid_pixel_count == 30
    assert pytest.approx(stats.valid_fraction, 1e-4) == 0.60
    # Valid NDVI = (0.6 - 0.2) / (0.6 + 0.2) = 0.5
    assert stats.ndvi_median is not None
    assert pytest.approx(stats.ndvi_median, 1e-3) == 0.5
    # Valid NDMI = (0.6 - 0.3) / (0.6 + 0.3) = 0.3333
    assert stats.ndmi_median is not None
    assert pytest.approx(stats.ndmi_median, 1e-3) == 0.3333
    # Valid NBR = (0.6 - 0.1) / (0.6 + 0.1) = 0.7143
    assert stats.nbr_median is not None
    assert pytest.approx(stats.nbr_median, 1e-3) == 0.7143


def test_extract_point_sample_valid_vs_cloudy():
    b04 = np.array([[0.2]], dtype=np.float32)
    b08 = np.array([[0.6]], dtype=np.float32)
    b11 = np.array([[0.3]], dtype=np.float32)
    b12 = np.array([[0.1]], dtype=np.float32)

    # 1. Valid pixel
    scl_valid = np.array([[SCL_VEGETATION]], dtype=np.uint8)
    dmask = np.array([[1]], dtype=np.uint8)
    sample = extract_point_sample(b04, b08, b11, b12, scl_valid, dmask, 0, 0)

    assert sample.is_valid is True
    assert sample.scl_code == SCL_VEGETATION
    assert sample.b04 == 0.2
    assert sample.b08 == 0.6
    assert sample.ndvi == 0.5

    # 2. Cloudy pixel
    scl_cloud = np.array([[SCL_CLOUD_HIGH_PROBABILITY]], dtype=np.uint8)
    sample_cloud = extract_point_sample(b04, b08, b11, b12, scl_cloud, dmask, 0, 0)

    assert sample_cloud.is_valid is False
    assert sample_cloud.scl_code == SCL_CLOUD_HIGH_PROBABILITY
    # Reflectances and indices MUST BE NONE, NEVER FABRICATED ZERO
    assert sample_cloud.b04 is None
    assert sample_cloud.b08 is None
    assert sample_cloud.b11 is None
    assert sample_cloud.b12 is None
    assert sample_cloud.ndvi is None
    assert sample_cloud.ndmi is None
    assert sample_cloud.nbr is None
