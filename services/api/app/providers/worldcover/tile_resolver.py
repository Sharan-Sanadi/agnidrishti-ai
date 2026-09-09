# AGNIDRISHTI API — ESA WorldCover Tile Resolver
"""
Authoritative 3° x 3° tile identifier resolver for ESA WorldCover 2021 v200.
Enforces mathematical floor semantics, coordinate boundary precision,
and geodesic multi-tile envelope discovery for metric neighborhoods.
"""

from __future__ import annotations

import math
from typing import NamedTuple

TILE_SIZE_DEG = 3


class TileBounds(NamedTuple):
    tile_id: str
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


def format_tile_id(tile_lat: int, tile_lon: int) -> str:
    """
    Format lower-left corner (tile_lat, tile_lon) into official WorldCover tile ID.
    Example: (12, 75) -> 'N12E075'
             (-48, 36) -> 'S48E036'
             (-3, -123) -> 'S03W123'
    """
    lat_prefix = "N" if tile_lat >= 0 else "S"
    lon_prefix = "E" if tile_lon >= 0 else "W"
    return f"{lat_prefix}{abs(tile_lat):02d}{lon_prefix}{abs(tile_lon):03d}"


format_worldcover_tile_id = format_tile_id


def format_worldcover_filename(tile_id: str, year: int = 2021, version: str = "v200") -> str:
    """Generate official WorldCover map GeoTIFF filename."""
    return f"ESA_WorldCover_10m_{year}_{version}_{tile_id}_Map.tif"


def build_worldcover_url(
    tile_id: str,
    base_url: str = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map",
    year: int = 2021,
    version: str = "v200",
) -> str:
    """Generate official ESA WorldCover S3 URL for tile."""
    fname = format_worldcover_filename(tile_id, year=year, version=version)
    return f"{base_url.rstrip('/')}/{fname}"



def parse_tile_id(tile_id: str) -> tuple[int, int]:
    """
    Parse official tile ID into (tile_lat, tile_lon) lower-left corner integers.
    Example: 'N12E075' -> (12, 75)
             'S48E036' -> (-48, 36)
    """
    if len(tile_id) != 7:
        raise ValueError(f"Invalid WorldCover tile ID format: {tile_id}")

    lat_prefix = tile_id[0].upper()
    lat_val = int(tile_id[1:3])
    lon_prefix = tile_id[3].upper()
    lon_val = int(tile_id[4:7])

    tile_lat = lat_val if lat_prefix == "N" else -lat_val
    tile_lon = lon_val if lon_prefix == "E" else -lon_val

    return tile_lat, tile_lon


def get_tile_bounds(tile_id: str) -> TileBounds:
    """Return geographic bounding box for the 3° x 3° tile."""
    tile_lat, tile_lon = parse_tile_id(tile_id)
    return TileBounds(
        tile_id=tile_id,
        min_lat=float(tile_lat),
        max_lat=float(tile_lat + TILE_SIZE_DEG),
        min_lon=float(tile_lon),
        max_lon=float(tile_lon + TILE_SIZE_DEG),
    )


def resolve_point_tile(lat: float, lon: float) -> str:
    """
    Resolve the official WorldCover tile containing the exact point (lat, lon).
    Uses strict mathematical floor semantics:
      tile_lat = floor(lat / 3) * 3
      tile_lon = floor(lon / 3) * 3
    Clamped to valid world bounds [-90, 90] and [-180, 180].
    """
    # Clamp coordinates to geographic limits
    clamped_lat = max(-90.0, min(90.0, lat))
    # Normalize longitude to [-180, 180)
    norm_lon = ((lon + 180.0) % 360.0) - 180.0

    # Special boundary edge cases for exactly +90.0 and +180.0
    if clamped_lat == 90.0:
        tile_lat = 87
    else:
        tile_lat = int(math.floor(clamped_lat / TILE_SIZE_DEG) * TILE_SIZE_DEG)

    if norm_lon == 180.0:
        tile_lon = 177
    else:
        tile_lon = int(math.floor(norm_lon / TILE_SIZE_DEG) * TILE_SIZE_DEG)

    return format_tile_id(tile_lat, tile_lon)


resolve_worldcover_tile = resolve_point_tile


def resolve_neighborhood_tiles(
    lat: float,
    lon: float,
    radius_m: float = 1000.0,
) -> list[str]:
    """
    Determine all WorldCover tiles intersecting the metric circular radius around (lat, lon).
    Calculates a geodesic bounding envelope.
    Near tile boundaries or corners, this returns 2 or 4 tiles respectively.
    """
    meters_per_deg_lat = 111320.0
    delta_lat = radius_m / meters_per_deg_lat

    lat_rad = math.radians(lat)
    cos_lat = max(math.cos(lat_rad), 0.01)
    delta_lon = radius_m / (meters_per_deg_lat * cos_lat)

    min_lat = max(-90.0, lat - delta_lat)
    max_lat = min(90.0, lat + delta_lat)
    min_lon = lon - delta_lon
    max_lon = lon + delta_lon

    start_lat_tile = int(math.floor(min_lat / TILE_SIZE_DEG) * TILE_SIZE_DEG)
    end_lat_tile = int(math.floor(max_lat / TILE_SIZE_DEG) * TILE_SIZE_DEG)

    tiles = set()
    # Handle normal latitude steps
    curr_lat = start_lat_tile
    while curr_lat <= end_lat_tile:
        # Avoid stepping beyond +87
        lat_step = min(curr_lat, 87)

        # Check longitude range (handling antimeridian wrap if needed)
        curr_lon = math.floor(min_lon / TILE_SIZE_DEG) * TILE_SIZE_DEG
        end_lon = math.floor(max_lon / TILE_SIZE_DEG) * TILE_SIZE_DEG
        while curr_lon <= end_lon:
            norm_lon = ((curr_lon + 180.0) % 360.0) - 180.0
            if norm_lon == 180.0:
                lon_step = 177
            else:
                lon_step = int(math.floor(norm_lon / TILE_SIZE_DEG) * TILE_SIZE_DEG)
            tiles.add(format_tile_id(lat_step, lon_step))
            curr_lon += TILE_SIZE_DEG

        curr_lat += TILE_SIZE_DEG

    # Ensure the primary point tile is always included
    primary_tile = resolve_point_tile(lat, lon)
    tiles.add(primary_tile)

    # Sort deterministically with primary tile first
    result = [primary_tile]
    for t in sorted(tiles):
        if t != primary_tile:
            result.append(t)

    return result
