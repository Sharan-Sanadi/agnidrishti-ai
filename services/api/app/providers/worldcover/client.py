# AGNIDRISHTI API — ESA WorldCover Client
"""
Production client for ESA WorldCover 2021 v200 Cloud-Optimized GeoTIFF (COG) access.
Provides atomic tile caching, integrity verification, asyncio per-tile locks,
and deterministic error handling.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from pathlib import Path

import httpx
import rasterio

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


class WorldCoverClientError(Exception):
    """Base exception for WorldCover client errors."""


class WorldCoverTileNotFoundError(WorldCoverClientError):
    """Raised when tile does not exist on remote source."""


class WorldCoverRasterInvalidError(WorldCoverClientError):
    """Raised when downloaded raster fails integrity/CRS validation."""


class WorldCoverClient:
    """
    Client for acquiring and verifying ESA WorldCover 10m 2021 v200 raster tiles.
    """

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        self.cache_dir = Path(cache_dir or settings.worldcover_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._tile_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def get_tile_url(self, tile_id: str) -> str:
        """Construct official remote URL for a 3x3 degree tile."""
        filename = (
            f"ESA_WorldCover_10m_{settings.worldcover_year}_{settings.worldcover_version}_{tile_id}_Map.tif"
        )
        return f"{settings.worldcover_base_url}/{filename}"

    def get_cached_tile_path(self, tile_id: str) -> Path:
        """Path to the locally cached GeoTIFF."""
        filename = (
            f"ESA_WorldCover_10m_{settings.worldcover_year}_{settings.worldcover_version}_{tile_id}_Map.tif"
        )
        return self.cache_dir / filename

    def validate_raster_file(self, path: Path) -> bool:
        """Validate that a raster file has nonzero size, can be opened by rasterio, and has valid CRS."""
        if not path.exists() or path.stat().st_size == 0:
            return False
        try:
            with rasterio.open(path) as ds:
                if ds.count < 1 or ds.width <= 0 or ds.height <= 0:
                    return False
                if not ds.crs:
                    return False
            return True
        except Exception:
            return False

    _validate_downloaded_raster = validate_raster_file

    def is_tile_cached_and_valid(self, tile_id: str) -> bool:
        """Check if tile exists in local cache and passes rasterio opening."""
        tile_path = self.get_cached_tile_path(tile_id)
        return self.validate_raster_file(tile_path)

    def get_tile_source(self, tile_id: str) -> str | Path:
        """
        Return the raster source for a WorldCover tile.
        - If cached locally: returns Path to cached GeoTIFF.
        - Otherwise: returns the remote COG URL for range-based on-demand reading.
        """
        tile_path = self.get_cached_tile_path(tile_id)
        if self.is_tile_cached_and_valid(tile_id):
            return tile_path
        return self.get_tile_url(tile_id)

    async def ensure_tile(self, tile_id: str, force_download: bool = False) -> str | Path:
        """
        Ensure tile source is available for raster analysis.
        By default, returns local cached tile if valid, or remote COG URL for HTTP range requests.
        If force_download=True, downloads the complete GeoTIFF locally.
        """
        if not force_download:
            return self.get_tile_source(tile_id)
        return await self.download_tile(tile_id)

    async def download_tile(self, tile_id: str) -> Path:
        """
        Download the WorldCover tile completely into local cache.
        Guarantees concurrency safety using a per-tile lock.
        Downloads atomically to a .part file and verifies raster integrity before promoting.
        """
        tile_path = self.get_cached_tile_path(tile_id)
        if self.is_tile_cached_and_valid(tile_id):
            return tile_path

        lock = self._tile_locks[tile_id]
        async with lock:
            # Re-check after acquiring lock in case another task completed the download
            if self.is_tile_cached_and_valid(tile_id):
                return tile_path

            url = self.get_tile_url(tile_id)
            part_path = self.cache_dir / f"{tile_path.name}.part"

            logger.info(f"Downloading ESA WorldCover tile {tile_id} from {url}...")

            try:
                # Use streaming with generous read timeout for large GeoTIFFs
                timeout_config = httpx.Timeout(connect=20.0, read=180.0, write=30.0, pool=20.0)
                async with httpx.AsyncClient(
                    timeout=timeout_config,
                    follow_redirects=True,
                ) as http_client:
                    async with http_client.stream("GET", url) as response:
                        if response.status_code == 404:
                            raise WorldCoverTileNotFoundError(
                                f"WorldCover tile {tile_id} not found at {url} (HTTP 404)"
                            )
                        if response.status_code != 200:
                            raise WorldCoverClientError(
                                f"Failed to fetch tile {tile_id}: HTTP {response.status_code}"
                            )

                        downloaded_bytes = 0
                        with open(part_path, "wb") as f:
                            async for chunk in response.aiter_bytes(chunk_size=65536):
                                f.write(chunk)
                                downloaded_bytes += len(chunk)

                logger.info(
                    f"Downloaded {downloaded_bytes / (1024*1024):.2f} MB for tile {tile_id} to temporary file {part_path.name}"
                )

                # Validate raster integrity before promoting
                try:
                    with rasterio.open(part_path) as ds:
                        if ds.count < 1 or ds.width <= 0 or ds.height <= 0:
                            raise WorldCoverRasterInvalidError("Invalid dimensions or band count")
                        if not ds.crs:
                            raise WorldCoverRasterInvalidError("Missing CRS definition")

                except Exception as ex:
                    if part_path.exists():
                        part_path.unlink()
                    raise WorldCoverRasterInvalidError(
                        f"Downloaded tile {tile_id} failed raster validation: {ex}"
                    ) from ex

                # Atomic replace
                part_path.replace(tile_path)
                logger.info(
                    f"Successfully cached ESA WorldCover tile {tile_id} ({tile_path.stat().st_size} bytes)"
                )
                return tile_path

            except (WorldCoverTileNotFoundError, WorldCoverRasterInvalidError):
                raise
            except Exception as ex:
                if part_path.exists():
                    try:
                        part_path.unlink()
                    except Exception:
                        pass
                logger.error(f"Error downloading WorldCover tile {tile_id}: {ex}")
                raise WorldCoverClientError(f"Error downloading WorldCover tile {tile_id}: {ex}") from ex


_client_instance: WorldCoverClient | None = None


def get_worldcover_client() -> WorldCoverClient:
    """Singleton getter for WorldCover client."""
    global _client_instance
    if _client_instance is None:
        _client_instance = WorldCoverClient()
    return _client_instance
