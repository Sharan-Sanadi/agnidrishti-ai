# AGNIDRISHTI API — Phase 6 Sentinel-2 Metric Circular Spatial Masking
"""
Computes geodesically accurate circular metric masks using local Azimuthal Equidistant (AEQD)
projection centered at the FIRMS observation coordinates.
Guarantees rectangular raster window corners outside the radius are excluded.
"""

from __future__ import annotations

import numpy as np
import pyproj
import rasterio.transform
from rasterio.transform import Affine


def create_aeqd_transformer(lat: float, lon: float) -> pyproj.Transformer:
    """Create a high-precision Azimuthal Equidistant metric transformer centered at (lat, lon)."""
    proj_str = f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m"
    return pyproj.Transformer.from_crs("EPSG:4326", proj_str, always_xy=True)


def compute_pixel_metric_distances(
    center_lat: float,
    center_lon: float,
    transform: Affine,
    height: int,
    width: int,
) -> np.ndarray:
    """
    Compute metric distance (meters) from (center_lat, center_lon) to the center of every pixel
    in a 2D raster grid defined by its Affine geotransform.

    Returns 2D float64 array of shape (height, width) with metric distances.
    """
    transformer = create_aeqd_transformer(center_lat, center_lon)

    cols, rows = np.meshgrid(np.arange(width), np.arange(height))
    xs, ys = rasterio.transform.xy(transform, rows.flatten(), cols.flatten(), offset="center")

    x_m, y_m = transformer.transform(np.array(xs), np.array(ys))
    dists_m = np.sqrt(x_m**2 + y_m**2)

    return np.asarray(dists_m).reshape((height, width))



def create_circular_mask(
    distances_m: np.ndarray,
    radius_m: float,
) -> np.ndarray:
    """
    Return a boolean 2D mask where True indicates the pixel is within radius_m meters.
    Pixels outside the metric radius (including window corners) are False.
    """
    return distances_m <= radius_m
