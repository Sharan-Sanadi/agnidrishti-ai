# AGNIDRISHTI API — Sentinel-2 SCL Masking & Quality Evaluation Unit Tests
import numpy as np

from app.providers.sentinel2.constants import (
    SCL_CLOUD_HIGH_PROBABILITY,
    SCL_CLOUD_MEDIUM_PROBABILITY,
    SCL_CLOUD_SHADOWS,
    SCL_DARK_AREA_PIXELS,
    SCL_NO_DATA,
    SCL_NOT_VEGETATED,
    SCL_SATURATED_OR_DEFECTIVE,
    SCL_SNOW_OR_ICE,
    SCL_THIN_CIRRUS,
    SCL_UNCLASSIFIED,
    SCL_VEGETATION,
    SCL_WATER,
    SentinelQualityStatus,
)
from app.providers.sentinel2.quality import (
    evaluate_pixel_validity,
    evaluate_roi_quality,
)


def test_individual_scl_validity_codes():
    # 0 = NO_DATA -> invalid
    assert not evaluate_pixel_validity(SCL_NO_DATA, data_mask=1)

    # 1 = SATURATED_OR_DEFECTIVE -> invalid
    assert not evaluate_pixel_validity(SCL_SATURATED_OR_DEFECTIVE, data_mask=1)

    # 2 = DARK_AREA_PIXELS -> valid
    assert evaluate_pixel_validity(SCL_DARK_AREA_PIXELS, data_mask=1)

    # 3 = CLOUD_SHADOWS -> invalid
    assert not evaluate_pixel_validity(SCL_CLOUD_SHADOWS, data_mask=1)

    # 4 = VEGETATION -> valid
    assert evaluate_pixel_validity(SCL_VEGETATION, data_mask=1)

    # 5 = NOT_VEGETATED -> valid
    assert evaluate_pixel_validity(SCL_NOT_VEGETATED, data_mask=1)

    # 6 = WATER -> valid
    assert evaluate_pixel_validity(SCL_WATER, data_mask=1)

    # 7 = UNCLASSIFIED -> invalid
    assert not evaluate_pixel_validity(SCL_UNCLASSIFIED, data_mask=1)

    # 8 = CLOUD_MEDIUM_PROBABILITY -> invalid
    assert not evaluate_pixel_validity(SCL_CLOUD_MEDIUM_PROBABILITY, data_mask=1)

    # 9 = CLOUD_HIGH_PROBABILITY -> invalid
    assert not evaluate_pixel_validity(SCL_CLOUD_HIGH_PROBABILITY, data_mask=1)

    # 10 = THIN_CIRRUS -> invalid
    assert not evaluate_pixel_validity(SCL_THIN_CIRRUS, data_mask=1)

    # 11 = SNOW_OR_ICE -> valid surface (tracked as snow)
    assert evaluate_pixel_validity(SCL_SNOW_OR_ICE, data_mask=1)


def test_data_mask_zero_always_invalid():
    # Even vegetation code (4) is invalid if dataMask is 0
    assert not evaluate_pixel_validity(SCL_VEGETATION, data_mask=0)
    assert not evaluate_pixel_validity(SCL_NOT_VEGETATED, data_mask=0)


def test_evaluate_roi_quality_excellent():
    # 100% vegetation
    scl = np.full((10, 10), SCL_VEGETATION, dtype=np.uint8)
    quality = evaluate_roi_quality(scl)
    assert quality.total_pixels == 100
    assert quality.valid_pixels == 100
    assert quality.valid_fraction == 1.0
    assert quality.quality_status == SentinelQualityStatus.EXCELLENT


def test_evaluate_roi_quality_good():
    # 70% valid, 30% cloud
    scl = np.array([SCL_VEGETATION] * 70 + [SCL_CLOUD_HIGH_PROBABILITY] * 30, dtype=np.uint8).reshape((10, 10))
    quality = evaluate_roi_quality(scl)
    assert quality.valid_pixels == 70
    assert quality.valid_fraction == 0.70
    assert quality.cloud_fraction == 0.30
    assert quality.quality_status == SentinelQualityStatus.GOOD


def test_evaluate_roi_quality_limited():
    # 50% valid, 50% cloud
    scl = np.array([SCL_NOT_VEGETATED] * 50 + [SCL_CLOUD_MEDIUM_PROBABILITY] * 50, dtype=np.uint8).reshape((10, 10))
    quality = evaluate_roi_quality(scl)
    assert quality.valid_fraction == 0.50
    assert quality.quality_status == SentinelQualityStatus.LIMITED


def test_evaluate_roi_quality_cloud_limited():
    # 20% valid, 80% cloud
    scl = np.array([SCL_VEGETATION] * 20 + [SCL_CLOUD_HIGH_PROBABILITY] * 80, dtype=np.uint8).reshape((10, 10))
    quality = evaluate_roi_quality(scl)
    assert quality.valid_fraction == 0.20
    assert quality.quality_status == SentinelQualityStatus.CLOUD_LIMITED


def test_evaluate_roi_quality_zero_valid():
    # 100% cloud
    scl = np.full((10, 10), SCL_CLOUD_HIGH_PROBABILITY, dtype=np.uint8)
    quality = evaluate_roi_quality(scl)
    assert quality.valid_pixels == 0
    assert quality.quality_status == SentinelQualityStatus.UNAVAILABLE


def test_evaluate_roi_with_spatial_mask():
    # 10x10 array where only a 4-pixel center is inside spatial mask
    scl = np.full((10, 10), SCL_CLOUD_HIGH_PROBABILITY, dtype=np.uint8)
    scl[4:6, 4:6] = SCL_VEGETATION  # 4 pixels clear in center

    spatial_mask = np.zeros((10, 10), dtype=bool)
    spatial_mask[4:6, 4:6] = True

    quality = evaluate_roi_quality(scl, spatial_mask=spatial_mask)
    assert quality.total_pixels == 4
    assert quality.valid_pixels == 4
    assert quality.valid_fraction == 1.0
    assert quality.quality_status == SentinelQualityStatus.EXCELLENT
