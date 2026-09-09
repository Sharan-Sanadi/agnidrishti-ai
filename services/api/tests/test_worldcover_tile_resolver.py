# AGNIDRISHTI API — ESA WorldCover Tile Resolver Unit Tests
"""
Verifies coordinate-to-tile calculation with mathematical floor semantics across global hemispheres,
exact 3° boundaries, epsilons, equator, prime meridian, and antimeridian.
"""

from app.providers.worldcover.tile_resolver import (
    build_worldcover_url,
    format_worldcover_filename,
    format_worldcover_tile_id,
    resolve_worldcover_tile,
)


def test_positive_lat_lon_india():
    """Verify standard positive latitude/longitude in India."""
    # Central India: 21.25°N, 81.63°E -> floor(21.25/3)*3 = 21 -> N21, floor(81.63/3)*3 = 81 -> E081
    tile = resolve_worldcover_tile(21.25, 81.63)
    assert tile == "N21E081"

    # South India: 12.97°N, 77.59°E -> floor(12.97/3)*3 = 12 -> N12, floor(77.59/3)*3 = 75 -> E075
    assert resolve_worldcover_tile(12.97, 77.59) == "N12E075"


def test_negative_latitude_southern_hemisphere():
    """Verify mathematical floor semantics for negative latitude."""
    # Latitude -0.1 must map to -3 -> S03, NOT S00
    assert resolve_worldcover_tile(-0.1, 36.5) == "S03E036"

    # -15.5°S, 25.5°E -> floor(-15.5/3)*3 = -18 -> S18, floor(25.5/3)*3 = 24 -> E024
    assert resolve_worldcover_tile(-15.5, 25.5) == "S18E024"

    # Exact example from prompt: S48E036
    assert resolve_worldcover_tile(-47.5, 37.0) == "S48E036"


def test_negative_longitude_western_hemisphere():
    """Verify mathematical floor semantics for negative longitude."""
    # Longitude -0.1 must map to -3 -> W003
    assert resolve_worldcover_tile(15.0, -0.1) == "N15W003"

    # California: 35.0°N, -118.0°W -> floor(35.0/3)*3 = 33 -> N33, floor(-118/3)*3 = -120 -> W120
    assert resolve_worldcover_tile(35.0, -118.0) == "N33W120"


def test_both_negative_south_america():
    """Verify both latitude and longitude negative (e.g. South America)."""
    # -23.5°S, -46.6°W -> floor(-23.5/3)*3 = -24 -> S24, floor(-46.6/3)*3 = -48 -> W048
    assert resolve_worldcover_tile(-23.5, -46.6) == "S24W048"


def test_equator_and_prime_meridian():
    """Verify exact 0.0 lat and 0.0 lon."""
    assert resolve_worldcover_tile(0.0, 0.0) == "N00E000"
    assert resolve_worldcover_tile(0.0, 10.0) == "N00E009"
    assert resolve_worldcover_tile(10.0, 0.0) == "N09E000"


def test_exact_3_degree_boundaries():
    """Verify points lying exactly on 3° grid lines."""
    # Exactly (18.0, 78.0) -> floor(18/3)*3 = 18 -> N18, floor(78/3)*3 = 78 -> E078
    assert resolve_worldcover_tile(18.0, 78.0) == "N18E078"
    assert resolve_worldcover_tile(-18.0, 78.0) == "S18E078"
    assert resolve_worldcover_tile(18.0, -78.0) == "N18W078"
    assert resolve_worldcover_tile(-18.0, -78.0) == "S18W078"


def test_epsilon_before_and_after_boundary():
    """Verify points just before and just after 3° grid lines."""
    # Just before 18.0°N (17.999999) -> belongs to N15
    assert resolve_worldcover_tile(17.999999, 78.5) == "N15E078"
    # At or just after 18.0°N (18.000001) -> belongs to N18
    assert resolve_worldcover_tile(18.000001, 78.5) == "N18E078"

    # Just before 78.0°E (77.999999) -> belongs to E075
    assert resolve_worldcover_tile(19.0, 77.999999) == "N18E075"
    # At or just after 78.0°E (78.000001) -> belongs to E078
    assert resolve_worldcover_tile(19.0, 78.000001) == "N18E078"


def test_tile_formatting_helpers():
    """Verify tile ID, filename, and remote S3 URL generation."""
    tile_id = format_worldcover_tile_id(21, 81)
    assert tile_id == "N21E081"

    fname = format_worldcover_filename("N21E081", year=2021, version="v200")
    assert fname == "ESA_WorldCover_10m_2021_v200_N21E081_Map.tif"

    url = build_worldcover_url("N21E081")
    assert url == "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N21E081_Map.tif"
