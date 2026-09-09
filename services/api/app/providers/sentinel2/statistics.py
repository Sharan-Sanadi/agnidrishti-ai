# AGNIDRISHTI API — Phase 6 Sentinel-2 Spectral Statistics Computation
"""
Computes robust spectral statistics (medians, p10, p90 percentiles) across valid,
cloud-masked pixels for circular metric neighborhoods (100m, 250m, 500m), as well as
point-level pixel sampling with strict null semantics.
"""

from __future__ import annotations

import numpy as np

from app.providers.sentinel2.indices import (
    calculate_index_array,
    calculate_nbr,
    calculate_ndmi,
    calculate_ndvi,
)
from app.providers.sentinel2.quality import evaluate_pixel_validity
from app.providers.sentinel2.schemas import PointSpectralSample, RadiusSpectralStats


def compute_radius_statistics(
    b04_arr: np.ndarray,
    b08_arr: np.ndarray,
    b11_arr: np.ndarray,
    b12_arr: np.ndarray,
    scl_arr: np.ndarray,
    data_mask_arr: np.ndarray,
    distances_m: np.ndarray,
    radius_m: float,
) -> RadiusSpectralStats:
    """
    Compute multi-band reflectance and spectral index statistics for valid pixels within radius_m.
    Cloud, shadow, and invalid pixels are strictly excluded from statistical distributions.
    """
    # 1. Circular spatial mask
    spatial_mask = distances_m <= radius_m
    total_pixels = int(np.sum(spatial_mask))

    if total_pixels == 0:
        return RadiusSpectralStats(
            radius_m=radius_m,
            total_pixel_count=0,
            valid_pixel_count=0,
            valid_fraction=0.0,
        )

    # 2. Validity mask within circle
    from app.providers.sentinel2.constants import INVALID_SCL_CODES
    is_valid_scl = ~np.isin(scl_arr, list(INVALID_SCL_CODES))
    has_data = data_mask_arr == 1
    valid_mask = spatial_mask & is_valid_scl & has_data

    valid_pixel_count = int(np.sum(valid_mask))
    valid_fraction = (valid_pixel_count / total_pixels) if total_pixels > 0 else 0.0


    if valid_pixel_count == 0:
        return RadiusSpectralStats(
            radius_m=radius_m,
            total_pixel_count=total_pixels,
            valid_pixel_count=0,
            valid_fraction=round(valid_fraction, 4),
        )

    # Extract valid pixel arrays
    v_b04 = b04_arr[valid_mask].astype(float)
    v_b08 = b08_arr[valid_mask].astype(float)
    v_b11 = b11_arr[valid_mask].astype(float)
    v_b12 = b12_arr[valid_mask].astype(float)

    # Compute valid index arrays
    ndvi_arr = calculate_index_array(b08_arr, b04_arr, valid_mask=valid_mask)
    ndmi_arr = calculate_index_array(b08_arr, b11_arr, valid_mask=valid_mask)
    nbr_arr = calculate_index_array(b08_arr, b12_arr, valid_mask=valid_mask)

    v_ndvi = ndvi_arr[valid_mask]
    v_ndvi = v_ndvi[~np.isnan(v_ndvi)]

    v_ndmi = ndmi_arr[valid_mask]
    v_ndmi = v_ndmi[~np.isnan(v_ndmi)]

    v_nbr = nbr_arr[valid_mask]
    v_nbr = v_nbr[~np.isnan(v_nbr)]

    return RadiusSpectralStats(
        radius_m=radius_m,
        total_pixel_count=total_pixels,
        valid_pixel_count=valid_pixel_count,
        valid_fraction=round(valid_fraction, 4),
        b04_median=round(float(np.median(v_b04)), 4) if len(v_b04) > 0 else None,
        b08_median=round(float(np.median(v_b08)), 4) if len(v_b08) > 0 else None,
        b11_median=round(float(np.median(v_b11)), 4) if len(v_b11) > 0 else None,
        b12_median=round(float(np.median(v_b12)), 4) if len(v_b12) > 0 else None,
        ndvi_median=round(float(np.median(v_ndvi)), 4) if len(v_ndvi) > 0 else None,
        ndmi_median=round(float(np.median(v_ndmi)), 4) if len(v_ndmi) > 0 else None,
        nbr_median=round(float(np.median(v_nbr)), 4) if len(v_nbr) > 0 else None,
        ndvi_p10=round(float(np.percentile(v_ndvi, 10)), 4) if len(v_ndvi) > 0 else None,
        ndvi_p90=round(float(np.percentile(v_ndvi, 90)), 4) if len(v_ndvi) > 0 else None,
        ndmi_p10=round(float(np.percentile(v_ndmi, 10)), 4) if len(v_ndmi) > 0 else None,
        ndmi_p90=round(float(np.percentile(v_ndmi, 90)), 4) if len(v_ndmi) > 0 else None,
        nbr_p10=round(float(np.percentile(v_nbr, 10)), 4) if len(v_nbr) > 0 else None,
        nbr_p90=round(float(np.percentile(v_nbr, 90)), 4) if len(v_nbr) > 0 else None,
        b11_p90=round(float(np.percentile(v_b11, 90)), 4) if len(v_b11) > 0 else None,
        b12_p90=round(float(np.percentile(v_b12, 90)), 4) if len(v_b12) > 0 else None,
    )


def extract_point_sample(
    b04_arr: np.ndarray,
    b08_arr: np.ndarray,
    b11_arr: np.ndarray,
    b12_arr: np.ndarray,
    scl_arr: np.ndarray,
    data_mask_arr: np.ndarray,
    center_row: int,
    center_col: int,
) -> PointSpectralSample:
    """
    Extract point-level pixel reflectance and spectral indices.
    If point pixel is invalid (cloud, shadow, defect, nodata), return null values.
    """
    h, w = scl_arr.shape
    if center_row < 0 or center_row >= h or center_col < 0 or center_col >= w:
        return PointSpectralSample(is_valid=False)

    scl_val = int(scl_arr[center_row, center_col])
    dmask_val = int(data_mask_arr[center_row, center_col])

    is_valid = evaluate_pixel_validity(scl_val, dmask_val)
    if not is_valid:
        return PointSpectralSample(
            is_valid=False,
            scl_code=scl_val,
        )

    b04 = float(b04_arr[center_row, center_col])
    b08 = float(b08_arr[center_row, center_col])
    b11 = float(b11_arr[center_row, center_col])
    b12 = float(b12_arr[center_row, center_col])

    ndvi = calculate_ndvi(b08, b04)
    ndmi = calculate_ndmi(b08, b11)
    nbr = calculate_nbr(b08, b12)

    return PointSpectralSample(
        is_valid=True,
        scl_code=scl_val,
        b04=round(b04, 4),
        b08=round(b08, 4),
        b11=round(b11, 4),
        b12=round(b12, 4),
        ndvi=round(ndvi, 4) if ndvi is not None else None,
        ndmi=round(ndmi, 4) if ndmi is not None else None,
        nbr=round(nbr, 4) if nbr is not None else None,
    )
