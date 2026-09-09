# AGNIDRISHTI API — Full 5km Envelope Spatial Coverage Tests
import pytest

from app.services.industrial_context_service import calculate_bounding_box


def test_bounding_box_calculation_equator():
    south, west, north, east = calculate_bounding_box(0.0, 0.0, 5000.0)
    assert south < 0.0
    assert north > 0.0
    assert west < 0.0
    assert east > 0.0
    # ~5km in latitude degrees is ~0.045
    assert pytest.approx(north - south, abs=0.01) == 0.090


def test_bounding_box_calculation_mid_latitude():
    south, west, north, east = calculate_bounding_box(45.0, 10.0, 5000.0)
    assert north > 45.0
    assert south < 45.0
    # Longitude delta should widen at higher latitudes
    assert (east - west) > (north - south)
