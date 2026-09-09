# AGNIDRISHTI API — Phase 6 Sentinel-2 Cloud and Pixel Quality Evaluation
"""
Analyzes Scene Classification Layer (SCL) and dataMask arrays to determine
pixel usability, cloud contamination, and ROI-level quality categorization.
"""

from __future__ import annotations

import numpy as np

from app.providers.sentinel2.constants import (
    CLOUD_SCL_CODES,
    CLOUD_SHADOW_SCL_CODES,
    INVALID_SCL_CODES,
    QUALITY_THRESHOLD_EXCELLENT,
    QUALITY_THRESHOLD_GOOD,
    QUALITY_THRESHOLD_LIMITED,
    SCL_NO_DATA,
    SNOW_SCL_CODES,
    SentinelQualityStatus,
)
from app.providers.sentinel2.schemas import SentinelLocalQuality


def evaluate_pixel_validity(
    scl_code: int,
    data_mask: int = 1,
) -> bool:
    """
    Check if a single pixel is analytically valid.
    A pixel is valid if and only if data_mask == 1 and scl_code is not in INVALID_SCL_CODES.
    """
    if data_mask == 0:
        return False
    return scl_code not in INVALID_SCL_CODES


def evaluate_roi_quality(
    scl_array: np.ndarray,
    data_mask_array: np.ndarray | None = None,
    spatial_mask: np.ndarray | None = None,
) -> SentinelLocalQuality:
    """
    Evaluate local pixel validity within a circular or spatial ROI.

    Parameters:
        scl_array: 2D numpy array of integer SCL codes.
        data_mask_array: 2D numpy array of dataMask values (0 or 1). Default all 1s.
        spatial_mask: Optional boolean mask where True = inside the metric circular ROI.

    Returns:
        SentinelLocalQuality containing pixel counts, fractions, and quality status.
    """

    if data_mask_array is None:
        data_mask_array = np.ones_like(scl_array, dtype=np.uint8)

    if spatial_mask is not None:
        scl_pixels = scl_array[spatial_mask]
        mask_pixels = data_mask_array[spatial_mask]
    else:
        scl_pixels = scl_array.flatten()
        mask_pixels = data_mask_array.flatten()

    total_pixels = int(scl_pixels.size)
    if total_pixels == 0:
        return SentinelLocalQuality(
            total_pixels=0,
            valid_pixels=0,
            cloud_pixels=0,
            cloud_shadow_pixels=0,
            snow_pixels=0,
            no_data_pixels=0,
            valid_fraction=0.0,
            cloud_fraction=0.0,
            cloud_shadow_fraction=0.0,
            snow_fraction=0.0,
            quality_status=SentinelQualityStatus.UNAVAILABLE,
        )

    # Pixel condition vectors
    has_data = mask_pixels == 1
    is_valid_scl = ~np.isin(scl_pixels, list(INVALID_SCL_CODES))

    valid_mask = has_data & is_valid_scl
    cloud_mask = has_data & np.isin(scl_pixels, list(CLOUD_SCL_CODES))
    shadow_mask = has_data & np.isin(scl_pixels, list(CLOUD_SHADOW_SCL_CODES))
    snow_mask = has_data & np.isin(scl_pixels, list(SNOW_SCL_CODES))
    nodata_mask = (~has_data) | (scl_pixels == SCL_NO_DATA)

    valid_count = int(np.sum(valid_mask))
    cloud_count = int(np.sum(cloud_mask))
    shadow_count = int(np.sum(shadow_mask))
    snow_count = int(np.sum(snow_mask))
    nodata_count = int(np.sum(nodata_mask))

    valid_frac = valid_count / total_pixels
    cloud_frac = cloud_count / total_pixels
    shadow_frac = shadow_count / total_pixels
    snow_frac = snow_count / total_pixels


    # Determine deterministic quality classification
    if valid_count == 0:
        quality_status = SentinelQualityStatus.UNAVAILABLE
    elif valid_frac >= QUALITY_THRESHOLD_EXCELLENT:
        quality_status = SentinelQualityStatus.EXCELLENT
    elif valid_frac >= QUALITY_THRESHOLD_GOOD:
        quality_status = SentinelQualityStatus.GOOD
    elif valid_frac >= QUALITY_THRESHOLD_LIMITED:
        quality_status = SentinelQualityStatus.LIMITED
    else:
        quality_status = SentinelQualityStatus.CLOUD_LIMITED

    return SentinelLocalQuality(
        total_pixels=total_pixels,
        valid_pixels=valid_count,
        cloud_pixels=cloud_count,
        cloud_shadow_pixels=shadow_count,
        snow_pixels=snow_count,
        no_data_pixels=nodata_count,
        valid_fraction=round(valid_frac, 4),
        cloud_fraction=round(cloud_frac, 4),
        cloud_shadow_fraction=round(shadow_frac, 4),
        snow_fraction=round(snow_frac, 4),
        quality_status=quality_status,
    )
