# AGNIDRISHTI API — Overpass API Async Client
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import logger

OVERPASS_DEFAULT_URL = "https://overpass-api.de/api/interpreter"


class OverpassClientError(Exception):
    """Base exception for Overpass API provider errors."""


class OverpassClient:
    """
    Async client for querying industrial infrastructure features from OpenStreetMap via Overpass API.
    Constructs server-side bounded Overpass QL queries for industrial taxonomy.
    """

    def __init__(self, endpoint_url: str | None = None, timeout_seconds: float = 30.0) -> None:
        settings = get_settings()
        self.endpoint_url = endpoint_url or getattr(settings, "overpass_api_url", OVERPASS_DEFAULT_URL)
        self.timeout_seconds = timeout_seconds

    def build_industrial_query(self, south: float, west: float, north: float, east: float) -> str:
        """
        Construct bounded Overpass QL query targeting industrial taxonomy:
        - man_made: flare, chimney, works, storage_tank
        - industrial: refinery, works
        - power: plant
        - landuse: industrial
        """
        bbox_str = f"{south},{west},{north},{east}"
        query = f"""
[out:json][timeout:25];
(
  node["man_made"="flare"]({bbox_str});
  way["man_made"="flare"]({bbox_str});
  node["industrial"="refinery"]({bbox_str});
  way["industrial"="refinery"]({bbox_str});
  relation["industrial"="refinery"]({bbox_str});
  node["man_made"="chimney"]({bbox_str});
  way["man_made"="chimney"]({bbox_str});
  node["power"="plant"]({bbox_str});
  way["power"="plant"]({bbox_str});
  relation["power"="plant"]({bbox_str});
  node["man_made"="works"]({bbox_str});
  way["man_made"="works"]({bbox_str});
  relation["man_made"="works"]({bbox_str});
  way["landuse"="industrial"]({bbox_str});
  relation["landuse"="industrial"]({bbox_str});
  node["man_made"="storage_tank"]({bbox_str});
  way["man_made"="storage_tank"]({bbox_str});
);
out body center qt;
"""
        return query.strip()

    async def fetch_industrial_features(
        self, south: float, west: float, north: float, east: float, retries: int = 2
    ) -> list[dict[str, Any]]:
        """
        Execute bounded Overpass query with retries and rate limit handling.
        Returns list of raw Overpass JSON elements.
        """
        query_ql = self.build_industrial_query(south, west, north, east)
        logger.info(f"Querying Overpass API for bbox ({south}, {west}, {north}, {east})")

        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        self.endpoint_url,
                        data={"data": query_ql},
                        headers={"User-Agent": "Agnidrishti-AI/1.0 (SIH26162 Thermal Intelligence)"},
                    )

                    if response.status_code == 429:
                        logger.warning(f"Overpass API rate limited (429), attempt {attempt + 1}/{retries + 1}")
                        if attempt < retries:
                            await asyncio.sleep(2.0 * (attempt + 1))
                            continue
                        raise OverpassClientError("Overpass API rate limit exceeded (HTTP 429)")

                    if response.status_code >= 500:
                        logger.warning(f"Overpass API server error ({response.status_code}), attempt {attempt + 1}/{retries + 1}")
                        if attempt < retries:
                            await asyncio.sleep(2.0 * (attempt + 1))
                            continue
                        raise OverpassClientError(f"Overpass API server error (HTTP {response.status_code})")

                    response.raise_for_status()

                    payload = response.json()
                    elements = payload.get("elements", [])
                    logger.info(f"Received {len(elements)} raw elements from Overpass API")
                    return elements

            except httpx.TimeoutException as ex:
                logger.warning(f"Overpass request timed out (attempt {attempt + 1}/{retries + 1}): {ex}")
                if attempt < retries:
                    await asyncio.sleep(2.0)
                    continue
                raise OverpassClientError("Overpass API request timed out") from ex
            except httpx.HTTPStatusError as ex:
                raise OverpassClientError(f"Overpass API HTTP error: {ex.response.status_code}") from ex
            except Exception as ex:
                logger.error(f"Overpass client unexpected failure: {ex}")
                raise OverpassClientError(f"Overpass query failed: {str(ex)}") from ex

        return []
