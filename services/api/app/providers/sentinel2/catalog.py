# AGNIDRISHTI API — CDSE Sentinel-2 STAC Catalog Search
"""
Client for discovering Sentinel-2 Level-2A candidate scenes via CDSE STAC v1 API.
Enforces strict zero future leakage, configurable prior lookback windows,
bounded candidate limits, and bounded in-memory caching.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import logger
from app.providers.sentinel2.auth import CDSETokenProvider, get_cdse_token_provider
from app.providers.sentinel2.constants import SENTINEL_COLLECTION_NAME
from app.providers.sentinel2.schemas import SentinelCandidate


class CDSECatalogError(Exception):
    """Raised when STAC catalog discovery fails."""
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class CDSECatalogClient:
    """
    Search client for CDSE STAC API.
    Guarantees no future scene is ever accepted for an observation.
    """

    def __init__(
        self,
        token_provider: CDSETokenProvider | None = None,
        stac_base_url: str | None = None,
        timeout_seconds: float = 25.0,
    ) -> None:
        settings = get_settings()
        self.token_provider = token_provider or get_cdse_token_provider()
        self.stac_base_url = (stac_base_url or settings.cdse_stac_base_url).rstrip("/")
        self.search_url = f"{self.stac_base_url}/search"
        self.timeout_seconds = timeout_seconds

        # Bounded cache: (bbox_tuple, time_from_str, time_to_str) -> list[SentinelCandidate]
        self._cache: dict[tuple[Any, ...], tuple[float, list[SentinelCandidate]]] = {}
        self._cache_ttl_seconds: float = 300.0  # 5 minutes cache
        self._cache_lock = asyncio.Lock()

    async def search_candidates(
        self,
        latitude: float,
        longitude: float,
        target_firms_time_utc: datetime,
        lookback_days: int = 30,
        max_candidates: int = 8,
        search_radius_deg: float = 0.05,  # ~5.5km bounding box
    ) -> list[SentinelCandidate]:
        """
        Search for Sentinel-2 L2A candidate scenes strictly prior to target_firms_time_utc.
        """
        # Ensure target_firms_time_utc is UTC-aware
        if target_firms_time_utc.tzinfo is None:
            target_time = target_firms_time_utc.replace(tzinfo=UTC)
        else:
            target_time = target_firms_time_utc.astimezone(UTC)

        start_time = target_time - timedelta(days=lookback_days)

        # Coordinate bounding box [west, south, east, north]
        bbox = [
            round(longitude - search_radius_deg, 4),
            round(latitude - search_radius_deg, 4),
            round(longitude + search_radius_deg, 4),
            round(latitude + search_radius_deg, 4),
        ]

        # Check cache
        cache_key = (
            tuple(bbox),
            start_time.isoformat(),
            target_time.isoformat(),
            max_candidates,
        )
        async with self._cache_lock:
            cached_entry = self._cache.get(cache_key)
            if cached_entry:
                cached_at, cached_candidates = cached_entry
                import time
                if time.time() - cached_at < self._cache_ttl_seconds:
                    logger.debug(f"Returning {len(cached_candidates)} cached STAC candidates.")
                    return cached_candidates

        token = await self.token_provider.get_access_token()

        payload = {
            "collections": [SENTINEL_COLLECTION_NAME],
            "bbox": bbox,
            "datetime": f"{start_time.isoformat()}/{target_time.isoformat()}",
            "limit": max_candidates * 2,  # Fetch slightly more to ensure filtering holds
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.search_url, json=payload, headers=headers)
        except httpx.TimeoutException as ex:
            logger.error(f"CDSE STAC search timed out after {self.timeout_seconds}s: {ex}")
            raise CDSECatalogError("CDSE STAC catalog search timed out", status_code=504) from ex
        except httpx.RequestError as ex:
            logger.error(f"Network error querying CDSE STAC: {ex}")
            raise CDSECatalogError(f"Network error querying STAC catalog: {str(ex)}") from ex

        if response.status_code == 401:
            self.token_provider.invalidate_cache()
            logger.warning("CDSE STAC returned 401 Unauthorized. Invalidated token cache.")
            raise CDSECatalogError("CDSE STAC unauthorized (token expired)", status_code=401)
        if response.status_code == 429:
            logger.warning("CDSE STAC rate limit reached (HTTP 429).")
            raise CDSECatalogError("CDSE STAC rate limit exceeded", status_code=429)
        if response.status_code != 200:
            logger.error(f"CDSE STAC returned HTTP {response.status_code}: {response.text[:300]}")
            raise CDSECatalogError(
                f"CDSE STAC catalog search returned HTTP {response.status_code}",
                status_code=response.status_code,
            )

        try:
            data = response.json()
        except Exception as ex:
            logger.error("Malformed JSON received from CDSE STAC catalog.")
            raise CDSECatalogError("Malformed JSON response from STAC catalog") from ex

        raw_features = data.get("features", [])
        candidates: list[SentinelCandidate] = []

        for feat in raw_features:
            props = feat.get("properties", {})
            dt_str = props.get("datetime")
            if not dt_str:
                continue

            try:
                # Handle ISO datetime with or without Z
                acq_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            except ValueError:
                continue

            # ─── CRITICAL ZERO-FUTURE-LEAKAGE CHECK ───
            # Sentinel acquisition must be strictly <= FIRMS target time
            if acq_dt > target_time:
                logger.warning(
                    f"Rejecting future Sentinel scene {feat.get('id')} ({acq_dt}) > target ({target_time})"
                )
                continue

            cloud_cover = float(props.get("eo:cloud_cover", props.get("cloudCover", 0.0)))
            platform = props.get("platform") or props.get("satellite")

            candidate = SentinelCandidate(
                scene_id=str(feat.get("id")),
                product_id=props.get("s2:product_uri") or props.get("product_id"),
                satellite_platform=platform,
                acquisition_time_utc=acq_dt,
                cloud_cover_percentage=cloud_cover,
                bbox=feat.get("bbox"),
                properties=props,
            )
            candidates.append(candidate)

        # Sort candidates deterministically:
        # 1. Most recent prior scene first (descending acquisition time)
        # 2. Lower catalogue cloud cover
        # 3. Stable scene_id
        candidates.sort(
            key=lambda c: (
                c.acquisition_time_utc,
                -c.cloud_cover_percentage,
                c.scene_id,
            ),
            reverse=True,
        )

        bounded = candidates[:max_candidates]

        # Update cache
        async with self._cache_lock:
            import time
            # Prune old cache if oversized
            if len(self._cache) > 200:
                self._cache.clear()
            self._cache[cache_key] = (time.time(), bounded)

        return bounded
