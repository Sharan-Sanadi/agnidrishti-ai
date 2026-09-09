# AGNIDRISHTI API — CDSE Sentinel Hub Process API Client
"""
Client for executing bounded Sentinel Hub Process API requests on the Copernicus Data Space.
Supports single multiband analytical raster retrieval (B04, B08, B11, B12, SCL, dataMask)
and server-defined preview visualizations (True-Color and SWIR Context).
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import httpx
from rasterio.io import MemoryFile

from app.core.config import get_settings
from app.core.logging import logger
from app.providers.sentinel2.auth import CDSETokenProvider, get_cdse_token_provider


class CDSEProcessError(Exception):
    """Raised when Process API execution fails."""
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


# Official server-controlled analytical evalscript (Float32 reflectance + SCL + dataMask)
ANALYTICAL_EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: ["B04", "B08", "B11", "B12", "SCL", "dataMask"],
    output: {
      bands: 6,
      sampleType: "FLOAT32"
    }
  };
}

function evaluatePixel(sample) {
  return [sample.B04, sample.B08, sample.B11, sample.B12, sample.SCL, sample.dataMask];
}
"""

# Server-controlled True Color RGB evalscript (B04, B03, B02 reflectance scaled for display)
TRUE_COLOR_EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: ["B04", "B03", "B02"],
    output: {
      bands: 3,
      sampleType: "AUTO"
    }
  };
}

function evaluatePixel(sample) {
  // Gain factor 2.5 for optical RGB visualization
  return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
}
"""

# Server-controlled SWIR False-Color Context evalscript (B12 SWIR-2, B08 NIR, B04 Red)
# Clearly labeled: SWIR Context, not thermal temperature.
SWIR_CONTEXT_EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: ["B12", "B08", "B04"],
    output: {
      bands: 3,
      sampleType: "AUTO"
    }
  };
}

function evaluatePixel(sample) {
  // R = SWIR2 (B12), G = NIR (B08), B = Red (B04)
  return [2.5 * sample.B12, 2.0 * sample.B08, 2.5 * sample.B04];
}
"""


class CDSEProcessClient:
    """Sentinel Hub Process API client for bounded multiband raster and preview image retrieval."""

    def __init__(
        self,
        token_provider: CDSETokenProvider | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 35.0,
    ) -> None:
        settings = get_settings()
        self.token_provider = token_provider or get_cdse_token_provider()
        self.base_url = (base_url or settings.cdse_sentinel_hub_base_url).rstrip("/")
        self.process_url = f"{self.base_url}/api/v1/process"
        self.timeout_seconds = timeout_seconds

        # In-memory raster cache: cache_key -> (cached_at, data_dict)
        self._cache: dict[tuple[Any, ...], tuple[float, dict[str, Any]]] = {}
        self._preview_cache: dict[tuple[Any, ...], tuple[float, bytes]] = {}
        self._cache_lock = asyncio.Lock()

    async def fetch_analytical_raster(
        self,
        bbox: list[float],
        scene_time: datetime,
        width: int = 51,
        height: int = 51,
    ) -> dict[str, Any]:
        """
        Retrieve 6-band Float32 analytical raster (B04, B08, B11, B12, SCL, dataMask)
        in a SINGLE bounded multiband request.
        """
        cache_key = (tuple(bbox), scene_time.isoformat(), width, height)
        async with self._cache_lock:
            cached = self._cache.get(cache_key)
            if cached:
                import time
                if time.time() - cached[0] < 600.0:  # 10 min TTL
                    return cached[1]

        token = await self.token_provider.get_access_token()

        t_from = scene_time.strftime("%Y-%m-%dT00:00:00Z")
        t_to = scene_time.strftime("%Y-%m-%dT23:59:59Z")


        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": t_from,
                                "to": t_to
                            }
                        }
                    }
                ]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/tiff"
                        }
                    }
                ]
            },
            "evalscript": ANALYTICAL_EVALSCRIPT
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "image/tiff"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(self.process_url, json=payload, headers=headers)
        except httpx.TimeoutException as ex:
            logger.error(f"CDSE Process API timed out after {self.timeout_seconds}s: {ex}")
            raise CDSEProcessError("CDSE Process API timed out", status_code=504) from ex
        except httpx.RequestError as ex:
            logger.error(f"Network error calling CDSE Process API: {ex}")
            raise CDSEProcessError(f"Network error calling Process API: {str(ex)}") from ex

        if resp.status_code == 401:
            self.token_provider.invalidate_cache()
            logger.warning("CDSE Process API returned 401. Invalidated token.")
            raise CDSEProcessError("CDSE Process API unauthorized", status_code=401)
        if resp.status_code == 429:
            logger.warning("CDSE Process API rate limit reached (HTTP 429).")
            raise CDSEProcessError("CDSE Process API rate limit exceeded", status_code=429)
        if resp.status_code != 200:
            logger.error(f"CDSE Process API error HTTP {resp.status_code}: {resp.text[:300]}")
            raise CDSEProcessError(
                f"CDSE Process API error HTTP {resp.status_code}",
                status_code=resp.status_code,
            )

        # Parse multiband GeoTIFF buffer into numpy arrays
        with MemoryFile(resp.content) as memfile:
            with memfile.open() as ds:
                bands = ds.read()  # (6, height, width)
                affine_transform = ds.transform

        result = {
            "b04": bands[0],
            "b08": bands[1],
            "b11": bands[2],
            "b12": bands[3],
            "scl": bands[4].astype(int),
            "data_mask": bands[5].astype(int),
            "transform": affine_transform,
            "width": width,
            "height": height,
        }

        async with self._cache_lock:
            import time
            if len(self._cache) > 100:
                self._cache.clear()
            self._cache[cache_key] = (time.time(), result)

        return result

    async def fetch_preview_image(
        self,
        bbox: list[float],
        scene_time: datetime,
        mode: str = "true_color",
        width: int = 256,
        height: int = 256,
    ) -> bytes:
        """
        Retrieve a compact RGB preview image (image/png or image/jpeg).
        Modes: 'true_color' (B04, B03, B02) or 'swir_context' (B12, B08, B04).
        """
        evalscript = SWIR_CONTEXT_EVALSCRIPT if mode == "swir_context" else TRUE_COLOR_EVALSCRIPT
        cache_key = (mode, tuple(bbox), scene_time.isoformat(), width, height)

        async with self._cache_lock:
            cached = self._preview_cache.get(cache_key)
            if cached:
                import time
                if time.time() - cached[0] < 600.0:
                    return cached[1]

        token = await self.token_provider.get_access_token()

        t_from = scene_time.strftime("%Y-%m-%dT00:00:00Z")
        t_to = scene_time.strftime("%Y-%m-%dT23:59:59Z")

        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": t_from,
                                "to": t_to
                            }
                        }
                    }
                ]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/png"
                        }
                    }
                ]
            },
            "evalscript": evalscript
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "image/png"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(self.process_url, json=payload, headers=headers)
        except Exception as ex:
            logger.error(f"Failed to fetch {mode} preview from Process API: {ex}")
            raise CDSEProcessError(f"Preview image generation failed: {str(ex)}") from ex

        if resp.status_code != 200:
            raise CDSEProcessError(
                f"Preview image error HTTP {resp.status_code}", status_code=resp.status_code
            )

        image_bytes = resp.content

        async with self._cache_lock:
            import time
            if len(self._preview_cache) > 100:
                self._preview_cache.clear()
            self._preview_cache[cache_key] = (time.time(), image_bytes)

        return image_bytes
