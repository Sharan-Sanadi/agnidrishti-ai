# AGNIDRISHTI API — Sentinel-2 Spectral Indices Unit Tests
import numpy as np
import pytest

from app.providers.sentinel2.indices import (
    calculate_index_array,
    calculate_nbr,
    calculate_ndmi,
    calculate_ndvi,
    calculate_normalized_index,
)


def test_calculate_ndvi_scalar():
    # NIR (B08) = 0.6, Red (B04) = 0.2 -> (0.6 - 0.2) / (0.6 + 0.2) = 0.4 / 0.8 = 0.5
    ndvi = calculate_ndvi(b08=0.6, b04=0.2)
    assert ndvi is not None
    assert pytest.approx(ndvi, 1e-4) == 0.5


def test_calculate_ndmi_scalar():
    # NIR (B08) = 0.5, SWIR1 (B11) = 0.3 -> (0.5 - 0.3) / (0.5 + 0.3) = 0.2 / 0.8 = 0.25
    ndmi = calculate_ndmi(b08=0.5, b11=0.3)
    assert ndmi is not None
    assert pytest.approx(ndmi, 1e-4) == 0.25


def test_calculate_nbr_scalar():
    # NIR (B08) = 0.7, SWIR2 (B12) = 0.1 -> (0.7 - 0.1) / (0.7 + 0.1) = 0.6 / 0.8 = 0.75
    nbr = calculate_nbr(b08=0.7, b12=0.1)
    assert nbr is not None
    assert pytest.approx(nbr, 1e-4) == 0.75


def test_scalar_zero_denominator_guard():
    # Both zero: (0 - 0) / (0 + 0) -> None
    assert calculate_ndvi(b08=0.0, b04=0.0) is None
    # None input
    assert calculate_ndvi(b08=None, b04=0.2) is None
    assert calculate_ndvi(b08=0.6, b04=None) is None
    # Near zero sum
    assert calculate_normalized_index(1e-7, -1e-7) is None


def test_calculate_index_array_normal():
    b08 = np.array([[0.6, 0.5], [0.7, 0.4]], dtype=np.float32)
    b04 = np.array([[0.2, 0.5], [0.1, 0.6]], dtype=np.float32)
    arr = calculate_index_array(b08, b04)

    assert pytest.approx(float(arr[0, 0]), 1e-4) == 0.5
    assert pytest.approx(float(arr[0, 1]), 1e-4) == 0.0
    assert pytest.approx(float(arr[1, 0]), 1e-4) == 0.75
    assert pytest.approx(float(arr[1, 1]), 1e-4) == -0.2


def test_calculate_index_array_with_valid_mask_and_zeros():
    b08 = np.array([[0.6, 0.0], [0.7, 0.5]], dtype=np.float32)
    b04 = np.array([[0.2, 0.0], [0.1, 0.3]], dtype=np.float32)
    # Mask out pixel (1, 1)
    valid_mask = np.array([[True, True], [True, False]], dtype=bool)

    arr = calculate_index_array(b08, b04, valid_mask=valid_mask)

    assert pytest.approx(float(arr[0, 0]), 1e-4) == 0.5
    # (0, 1) has denom=0 -> NaN
    assert np.isnan(arr[0, 1])
    assert pytest.approx(float(arr[1, 0]), 1e-4) == 0.75
    # (1, 1) was masked out -> NaN
    assert np.isnan(arr[1, 1])
