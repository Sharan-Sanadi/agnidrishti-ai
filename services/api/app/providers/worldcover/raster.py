# AGNIDRISHTI API — ESA WorldCover Raster Processor
"""
High-performance raster processing and multi-scale circular metric analysis
for ESA WorldCover 10 m 2021 v200.
Features:
- Single-read extraction with 3 metric circular masks (250m, 500m, 1000m)
- Geodesic Azimuthal Equidistant metric projection via pyproj
- Multi-tile cross-boundary pixel merging
- Nodata exclusion and valid-fraction calculation
- Deterministic Context V1 classification
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyproj
import rasterio
from rasterio.windows import from_bounds

from app.core.logging import logger
from app.providers.worldcover.constants import (
    CLASS_CODE_TO_CONTEXT_MAP,
    CONTEXT_DOMINANCE_THRESHOLD,
    MIN_VALID_PIXEL_FRACTION,
    WORLDCOVER_CLASSES,
    LandCoverContextClass,
    LandCoverCoverageStatus,
    get_class_name,
)
from app.providers.worldcover.schemas import (
    ObservationLandCoverAnalysis,
    PointLandCoverSample,
    ScaleLandCoverDistribution,
)
from app.providers.worldcover.tile_resolver import (
    resolve_neighborhood_tiles,
    resolve_point_tile,
)

METERS_PER_DEG_LAT = 111320.0


def create_aeqd_transformer(lat: float, lon: float) -> pyproj.Transformer:
    """Create a high-precision Azimuthal Equidistant metric transformer centered at (lat, lon)."""
    proj_str = f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m"
    return pyproj.Transformer.from_crs("EPSG:4326", proj_str, always_xy=True)


def calculate_scale_distribution(
    values: np.ndarray,
    mask: np.ndarray,
    radius_m: float,
) -> ScaleLandCoverDistribution:
    """
    Compute land-cover histogram and fractions for a circular metric mask.
    Excludes nodata and non-standard codes from valid denominator.
    """
    if len(values) == 0 or len(mask) == 0:
        return ScaleLandCoverDistribution(
            radius_m=radius_m,
            total_pixels=0,
            valid_pixels=0,
            invalid_pixels=0,
            valid_fraction=0.0,
            class_counts={},
            class_fractions={},
            dominant_class="UNAVAILABLE",
            dominant_fraction=0.0,
        )

    # Ensure mask is boolean
    bool_mask = mask.astype(bool) if mask.dtype != bool else mask
    selected_vals = values[bool_mask]
    total_pixels = int(len(selected_vals))

    if total_pixels == 0:
        return ScaleLandCoverDistribution(
            radius_m=radius_m,
            total_pixels=0,
            valid_pixels=0,
            invalid_pixels=0,
            valid_fraction=0.0,
            class_counts={},
            class_fractions={},
            dominant_class="UNAVAILABLE",
            dominant_fraction=0.0,
        )

    class_counts: dict[str, int] = {}
    valid_count = 0
    invalid_count = 0

    unique_codes, counts = np.unique(selected_vals, return_counts=True)
    for code_val, count in zip(unique_codes, counts, strict=False):
        c = int(code_val)
        cnt = int(count)
        if c in WORLDCOVER_CLASSES:
            name = WORLDCOVER_CLASSES[c]
            class_counts[name] = cnt
            valid_count += cnt
        else:
            invalid_count += cnt

    valid_fraction = float(valid_count / total_pixels) if total_pixels > 0 else 0.0

    class_fractions: dict[str, float] = {}
    dominant_class = "UNKNOWN"
    dominant_fraction = 0.0

    if valid_count > 0:
        # Sort classes by count descending
        sorted_classes = sorted(class_counts.items(), key=lambda item: item[1], reverse=True)
        for name, cnt in sorted_classes:
            fraction = round(float(cnt / valid_count), 4)
            class_fractions[name] = fraction

        dominant_class, max_cnt = sorted_classes[0]
        dominant_fraction = round(float(max_cnt / valid_count), 4)

    return ScaleLandCoverDistribution(
        radius_m=radius_m,
        total_pixels=total_pixels,
        valid_pixels=valid_count,
        invalid_pixels=invalid_count,
        valid_fraction=round(valid_fraction, 4),
        class_counts=class_counts,
        class_fractions=class_fractions,
        dominant_class=dominant_class,
        dominant_fraction=dominant_fraction,
    )


def classify_context_v1(
    dominant_class_500m: str | None = None,
    dominant_fraction_500m: float | None = None,
    valid_fraction_500m: float = 1.0,
    coverage_status: LandCoverCoverageStatus = LandCoverCoverageStatus.COMPLETE,
    dominant_class: str | None = None,
    dominant_fraction: float | None = None,
    valid_fraction: float | None = None,
) -> LandCoverContextClass:
    """
    Deterministic Phase 5 Context V1 Classification based on 500m neighborhood.
    Rules:
      - If coverage is UNAVAILABLE or valid pixels < 50% -> UNAVAILABLE
      - If dominant_fraction >= 0.60 -> <CLASS>_DOMINANT
      - Otherwise -> MIXED
    """
    dom_class = dominant_class if dominant_class is not None else dominant_class_500m
    dom_frac = dominant_fraction if dominant_fraction is not None else (dominant_fraction_500m or 0.0)
    v_frac = valid_fraction if valid_fraction is not None else valid_fraction_500m

    if coverage_status == LandCoverCoverageStatus.UNAVAILABLE or v_frac < MIN_VALID_PIXEL_FRACTION:
        return LandCoverContextClass.UNAVAILABLE

    if dom_frac >= CONTEXT_DOMINANCE_THRESHOLD and dom_class:
        # Find matching code
        for code, name in WORLDCOVER_CLASSES.items():
            if name == dom_class and code in CLASS_CODE_TO_CONTEXT_MAP:
                return LandCoverContextClass(CLASS_CODE_TO_CONTEXT_MAP[code])

    return LandCoverContextClass.MIXED




def is_tile_available(path: Path | str | None) -> bool:
    """Check if tile is available locally or as a remote HTTP COG URL."""
    if path is None:
        return False
    if isinstance(path, str) and (path.startswith("http://") or path.startswith("https://")):
        return True
    if isinstance(path, Path):
        return path.exists()
    return Path(str(path)).exists()


class WorldCoverRasterProcessor:
    """
    Processes ESA WorldCover GeoTIFFs to extract point samples and multi-scale circular neighborhoods.
    """

    classify_context_v1 = staticmethod(classify_context_v1)
    calculate_scale_distribution = staticmethod(calculate_scale_distribution)

    @staticmethod
    def sample_observation(
        observation_id: str,
        lat: float,
        lon: float,
        tile_paths: dict[str, Path | str],
        max_radius_m: float = 1000.0,
        open_datasets: dict[str, rasterio.DatasetReader] | None = None,
    ) -> ObservationLandCoverAnalysis:
        """
        Analyze a single thermal observation across one or more intersecting WorldCover tiles.
        1. Identifies point pixel from primary tile.
        2. Reads raster windows from all intersecting tiles covering the 1000m geodesic bounding box.
        3. Projects pixel centers using local Azimuthal Equidistant metric coordinates.
        4. Calculates circular masks for 250m, 500m, and 1000m in a single pass.
        5. Computes distributions, fractions, and Context V1 classification.
        """
        primary_tile = resolve_point_tile(lat, lon)
        required_tiles = resolve_neighborhood_tiles(lat, lon, max_radius_m)

        # Check tile availability
        missing_tiles = [
            t for t in required_tiles if t not in tile_paths or not is_tile_available(tile_paths.get(t))
        ]
        available_tiles = [
            t for t in required_tiles if t in tile_paths and is_tile_available(tile_paths.get(t))
        ]

        if primary_tile not in available_tiles:
            # Primary tile missing
            return ObservationLandCoverAnalysis(
                observation_id=observation_id,
                point_sample=PointLandCoverSample(
                    code=0,
                    class_name="UNAVAILABLE",
                    tile_id=primary_tile,
                    is_valid=False,
                ),
                scale_250m=calculate_scale_distribution(np.array([], dtype=np.uint8), np.array([], dtype=bool), 250.0),
                scale_500m=calculate_scale_distribution(np.array([], dtype=np.uint8), np.array([], dtype=bool), 500.0),
                scale_1000m=calculate_scale_distribution(np.array([], dtype=np.uint8), np.array([], dtype=bool), 1000.0),
                context_class=LandCoverContextClass.UNAVAILABLE,
                coverage_status=LandCoverCoverageStatus.UNAVAILABLE,
                tiles_used=[],
                sampled_at=datetime.now(UTC),
                error_detail=f"Primary WorldCover tile {primary_tile} is unavailable",
            )

        coverage_status = (
            LandCoverCoverageStatus.COMPLETE
            if not missing_tiles
            else LandCoverCoverageStatus.PARTIAL
        )

        # 1. Sample exact point from primary tile
        point_code = 0
        p_path = tile_paths[primary_tile]
        ds_primary = open_datasets.get(primary_tile) if open_datasets else None
        close_primary = False
        if ds_primary is None:
            ds_primary = rasterio.open(str(p_path))
            close_primary = True

        try:
            row, col = ds_primary.index(lon, lat)
            if 0 <= row < ds_primary.height and 0 <= col < ds_primary.width:
                w = rasterio.windows.Window(col, row, 1, 1)
                val = ds_primary.read(1, window=w)[0, 0]
                point_code = int(val)
        except Exception as ex:
            logger.warning(f"Error sampling point coordinate for {observation_id}: {ex}")
        finally:
            if close_primary and ds_primary:
                ds_primary.close()

        point_name = get_class_name(point_code)
        point_sample = PointLandCoverSample(
            code=point_code,
            class_name=point_name,
            tile_id=primary_tile,
            is_valid=(point_code in WORLDCOVER_CLASSES),
        )

        # 2. Extract multi-scale circular neighborhood across all available intersecting tiles
        delta_lat = max_radius_m / METERS_PER_DEG_LAT
        lat_rad = math.radians(lat)
        cos_lat = max(math.cos(lat_rad), 0.01)
        delta_lon = max_radius_m / (METERS_PER_DEG_LAT * cos_lat)

        bbox_min_lat = lat - delta_lat
        bbox_max_lat = lat + delta_lat
        bbox_min_lon = lon - delta_lon
        bbox_max_lon = lon + delta_lon

        transformer = create_aeqd_transformer(lat, lon)

        all_pixel_values: list[np.ndarray] = []
        all_pixel_distances: list[np.ndarray] = []

        for tid in available_tiles:
            tpath = tile_paths[tid]
            ds = open_datasets.get(tid) if open_datasets else None
            close_ds = False
            if ds is None:
                ds = rasterio.open(str(tpath))
                close_ds = True
            try:
                # Clip requested bbox to tile bounds to avoid out-of-bound errors
                tile_bounds = ds.bounds
                c_min_lon = max(bbox_min_lon, tile_bounds.left)
                c_max_lon = min(bbox_max_lon, tile_bounds.right)
                c_min_lat = max(bbox_min_lat, tile_bounds.bottom)
                c_max_lat = min(bbox_max_lat, tile_bounds.top)

                if c_min_lon >= c_max_lon or c_min_lat >= c_max_lat:
                    continue

                window = from_bounds(
                    c_min_lon, c_min_lat, c_max_lon, c_max_lat, transform=ds.transform
                )
                # Round window to integer pixel coordinates and clip to dataset
                window = window.round_offsets().round_lengths()
                window = window.intersection(
                    rasterio.windows.Window(0, 0, ds.width, ds.height)
                )

                if window.width <= 0 or window.height <= 0:
                    continue

                data = ds.read(1, window=window)
                win_transform = ds.window_transform(window)

                # Compute geographic center for each pixel in the window
                cols, rows = np.meshgrid(
                    np.arange(window.width), np.arange(window.height)
                )
                # Vectorized pixel center coordinates
                xs, ys = rasterio.transform.xy(
                    win_transform, rows.flatten(), cols.flatten(), offset="center"
                )

                # Project to local metric AEQD
                x_m, y_m = transformer.transform(np.array(xs), np.array(ys))
                dists_m = np.sqrt(x_m**2 + y_m**2)

                all_pixel_values.append(data.flatten())
                all_pixel_distances.append(dists_m)
            except Exception as ex:
                logger.error(f"Error reading window from tile {tid} for {observation_id}: {ex}")
                coverage_status = LandCoverCoverageStatus.PARTIAL
            finally:
                if close_ds and ds:
                    ds.close()


        if not all_pixel_values:
            # No pixels could be read
            return ObservationLandCoverAnalysis(
                observation_id=observation_id,
                point_sample=point_sample,
                scale_250m=calculate_scale_distribution(np.array([]), np.array([]), 250.0),
                scale_500m=calculate_scale_distribution(np.array([]), np.array([]), 500.0),
                scale_1000m=calculate_scale_distribution(np.array([]), np.array([]), 1000.0),
                context_class=LandCoverContextClass.UNAVAILABLE,
                coverage_status=LandCoverCoverageStatus.UNAVAILABLE,
                tiles_used=available_tiles,
                sampled_at=datetime.now(UTC),
                error_detail="Failed to read any pixels from intersecting tiles",
            )

        combined_values = np.concatenate(all_pixel_values)
        combined_distances = np.concatenate(all_pixel_distances)

        # Apply true circular metric masks (<= radius_m)
        mask_250m = combined_distances <= 250.0
        mask_500m = combined_distances <= 500.0
        mask_1000m = combined_distances <= 1000.0

        dist_250m = calculate_scale_distribution(combined_values, mask_250m, 250.0)
        dist_500m = calculate_scale_distribution(combined_values, mask_500m, 500.0)
        dist_1000m = calculate_scale_distribution(combined_values, mask_1000m, 1000.0)

        context_class = classify_context_v1(
            dominant_class_500m=dist_500m.dominant_class,
            dominant_fraction_500m=dist_500m.dominant_fraction,
            valid_fraction_500m=dist_500m.valid_fraction,
            coverage_status=coverage_status,
        )

        return ObservationLandCoverAnalysis(
            observation_id=observation_id,
            point_sample=point_sample,
            scale_250m=dist_250m,
            scale_500m=dist_500m,
            scale_1000m=dist_1000m,
            context_class=context_class,
            coverage_status=coverage_status,
            tiles_used=available_tiles,
            sampled_at=datetime.now(UTC),
        )
