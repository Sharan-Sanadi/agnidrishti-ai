# AGNIDRISHTI API — ESA WorldCover Multi-Tile Boundary Unit Tests
"""
Verifies neighborhood tile resolution when circular metric radius (1000m)
crosses single-tile boundaries (2 tiles) and corners (up to 4 tiles).
"""

from app.providers.worldcover.tile_resolver import resolve_neighborhood_tiles


def test_single_tile_interior_observation():
    """Observation located safely in the interior of a 3x3 tile only requires 1 tile."""
    # Point at (22.5°N, 82.5°E) is right in the center of N21E081 (boundaries: 21-24N, 81-84E)
    tiles = resolve_neighborhood_tiles(22.5, 82.5, radius_m=1000.0)
    assert tiles == ["N21E081"]


def test_eastern_tile_boundary_crossing():
    """Observation 200m west of the eastern tile boundary requires 2 tiles (base + east neighbor)."""
    # Eastern boundary of N21E081 is at 84.0°E.
    # At 22.0°N, 1 degree lon is ~103,165 m.
    # 200m is approximately 0.00194 degrees.
    # So 83.998°E is ~200m from 84.0°E.
    # A 1000m radius extends past 84.0°E into N21E084!
    lat = 22.0
    lon = 83.998
    tiles = resolve_neighborhood_tiles(lat, lon, radius_m=1000.0)

    assert "N21E081" in tiles
    assert "N21E084" in tiles
    assert len(tiles) == 2


def test_northern_tile_boundary_crossing():
    """Observation 200m south of northern boundary requires 2 tiles (base + north neighbor)."""
    # Northern boundary of N21E081 is at 24.0°N.
    # 1 degree lat is ~111,000m. 200m is ~0.0018 degrees.
    # Lat 23.998°N is ~200m from 24.0°N.
    lat = 23.998
    lon = 82.5
    tiles = resolve_neighborhood_tiles(lat, lon, radius_m=1000.0)

    assert "N21E081" in tiles
    assert "N24E081" in tiles
    assert len(tiles) == 2


def test_four_tile_corner_crossing():
    """Observation near the northeast corner requires 4 tiles (SW, SE, NW, NE)."""
    # Northeast corner of N21E081 is at (24.0°N, 84.0°E).
    # Point at (23.998°N, 83.998°E) is within 250m of the 4-tile vertex.
    # A 1000m circular neighborhood covers:
    # 1. N21E081 (SW)
    # 2. N21E084 (SE)
    # 3. N24E081 (NW)
    # 4. N24E084 (NE)
    lat = 23.998
    lon = 83.998
    tiles = resolve_neighborhood_tiles(lat, lon, radius_m=1000.0)

    assert len(tiles) == 4
    assert set(tiles) == {"N21E081", "N21E084", "N24E081", "N24E084"}


def test_equator_corner_crossing_negative_hemisphere():
    """Verify corner crossing spanning equator (e.g. crossing between N00 and S03)."""
    # Boundary at lat 0.0° and lon 36.0°
    # Lat -0.001° (in S03), Lon 35.999° (in E033)
    tiles = resolve_neighborhood_tiles(-0.001, 35.999, radius_m=1000.0)
    assert len(tiles) == 4
    assert set(tiles) == {"S03E033", "S03E036", "N00E033", "N00E036"}
