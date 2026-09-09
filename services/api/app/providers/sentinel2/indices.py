# AGNIDRISHTI API — Phase 6 Sentinel-2 Spectral Indices
"""
Spectral index calculation functions for NDVI, NDMI, and NBR.
Enforces strict denominator guards, epsilon handling, and null propagation for invalid pixels.
Zero is never fabricated for missing/invalid data.
"""

from __future__ import annotations

import numpy as np

EPSILON = 1e-6


def calculate_normalized_index(
    band_a: float | None,
    band_b: float | None,
    epsilon: float = EPSILON,
) -> float | None:
    """
    Calculate normalized difference index (band_a - band_b) / (band_a + band_b).
    Returns None if either input is None, NaN, or if denominator is effectively zero.
    """
    if band_a is None or band_b is None:
        return None
    if np.isnan(band_a) or np.isnan(band_b):
        return None

    denom = band_a + band_b
    if abs(denom) < epsilon:
        return None

    val = (band_a - band_b) / denom
    if np.isnan(val) or np.isinf(val):
        return None

    # Clamp mathematically plausible range [-1.0, 1.0]
    return max(-1.0, min(1.0, val))



def calculate_ndvi(b08: float | None, b04: float | None) -> float | None:
    """
    Normalized Difference Vegetation Index (NDVI).
    NDVI = (NIR - Red) / (NIR + Red) = (B08 - B04) / (B08 + B04)
    Reflects photosynthetic activity and canopy density.
    """
    return calculate_normalized_index(b08, b04)


def calculate_ndmi(b08: float | None, b11: float | None) -> float | None:
    """
    Normalized Difference Moisture Index (NDMI).
    NDMI = (NIR - SWIR1) / (NIR + SWIR1) = (B08 - B11) / (B08 + B11)
    Reflects canopy water content and moisture stress.
    """
    return calculate_normalized_index(b08, b11)


def calculate_nbr(b08: float | None, b12: float | None) -> float | None:
    """
    Normalized Burn Ratio (NBR).
    NBR = (NIR - SWIR2) / (NIR + SWIR2) = (B08 - B12) / (B08 + B12)
    Highlights contrast between healthy vegetated areas (high NIR) and bare/burned surfaces (high SWIR2).
    Note: Single-scene NBR provides spectral context; it does not measure burn severity (dNBR).
    """
    return calculate_normalized_index(b08, b12)


def calculate_index_array(
    band_a_arr: np.ndarray,
    band_b_arr: np.ndarray,
    valid_mask: np.ndarray | None = None,
    epsilon: float = EPSILON,
) -> np.ndarray:
    """
    Calculate normalized difference index across 2D arrays.
    Returns array with np.nan where invalid or denominator is below epsilon.
    """
    denom = band_a_arr + band_b_arr
    numer = band_a_arr - band_b_arr

    invalid = np.abs(denom) < epsilon
    if valid_mask is not None:
        invalid = invalid | (~valid_mask)

    out = np.full_like(numer, np.nan, dtype=np.float32)
    with np.errstate(divide="ignore", invalid="ignore"):
        np.divide(numer, denom, out=out, where=~invalid)

    # Clip to valid index range
    out = np.clip(out, -1.0, 1.0)
    out[invalid] = np.nan
    return out
