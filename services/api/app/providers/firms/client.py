# AGNIDRISHTI API — NASA FIRMS HTTP Client
"""
Production-grade, asynchronous NASA FIRMS Area API client.

Features:
- Official NASA FIRMS Area API endpoint routing
- Server-side MAP_KEY protection (never logged or exposed)
- Bounded in-memory TTL caching with stale-fallback support
- Safe multi-sensor concurrency (NOAA-20 + NOAA-21)
- Structured exception mapping
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime

import httpx

from app.core.config import Settings, get_settings
from app.core.constants import (
    DEFAULT_FIRMS_SENSORS,
    FIRMS_MAX_DAY_RANGE,
    FIRMS_MIN_DAY_RANGE,
    FIRMSErrorCode,
    FIRMSSensor,
)
from app.core.logging import logger
from app.providers.firms.parser import parse_firms_csv
from app.schemas.firms import (
    BoundingBox,
    FIRMSAvailabilityItem,
    FIRMSAvailabilityResponse,
    FIRMSHotspotsResponse,
    ThermalObservation,
)

# ==============================
# DOMAIN EXCEPTIONS
# ==============================

class FIRMSError(Exception):
    """Base exception for NASA FIRMS client errors."""

    def __init__(self, code: str, message: str, status_code: int = 502):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


FIRMSException = FIRMSError


class MissingFIRMSKeyError(FIRMSException):
    def __init__(self, message: str = "NASA FIRMS MAP_KEY is not configured on the server."):
        super().__init__(FIRMSErrorCode.MISSING_FIRMS_KEY, message, status_code=500)


class FIRMSAuthError(FIRMSException):
    def __init__(self, message: str = "NASA FIRMS MAP_KEY authentication failed (Invalid MAP_KEY)."):
        super().__init__(FIRMSErrorCode.FIRMS_AUTH_ERROR, message, status_code=401)


class FIRMSValidationError(FIRMSException):
    def __init__(self, code: str, message: str):
        super().__init__(code, message, status_code=422)


class FIRMSTimeoutError(FIRMSException):
    def __init__(self, message: str = "Request to NASA FIRMS service timed out."):
        super().__init__(FIRMSErrorCode.FIRMS_TIMEOUT, message, status_code=504)


class FIRMSRateLimitError(FIRMSException):
    def __init__(self, message: str = "NASA FIRMS API rate limit exceeded."):
        super().__init__(FIRMSErrorCode.FIRMS_RATE_LIMITED, message, status_code=429)


class FIRMSUpstreamError(FIRMSException):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(FIRMSErrorCode.FIRMS_UPSTREAM_ERROR, message, status_code=status_code)


# ==============================
# IN-MEMORY TTL CACHE
# ==============================

class _CacheEntry:
    __slots__ = ("observations", "rejected_count", "fetched_at", "expiry_timestamp")

    def __init__(
        self,
        observations: list[ThermalObservation],
        rejected_count: int,
        fetched_at: datetime,
        ttl_seconds: int,
    ):
        self.observations = observations
        self.rejected_count = rejected_count
        self.fetched_at = fetched_at
        self.expiry_timestamp = time.time() + ttl_seconds


class FIRMSCache:
    """Bounded, thread-safe in-memory cache for FIRMS API responses."""

    def __init__(self, max_entries: int = 50):
        self._max_entries = max_entries
        self._cache: dict[str, _CacheEntry] = {}

    def _make_key(
        self,
        sources: list[str],
        area_str: str,
        day_range: int,
        date_str: str | None,
    ) -> str:
        sorted_sources = ",".join(sorted(sources))
        return f"{sorted_sources}|{area_str}|{day_range}|{date_str or ''}"

    def get(
        self,
        sources: list[str],
        area_str: str,
        day_range: int,
        date_str: str | None,
    ) -> tuple[list[ThermalObservation], int, datetime, str] | None:
        """
        Returns (observations, rejected_count, fetched_at, 'fresh' | 'stale') if found,
        or None if no entry exists.
        """
        key = self._make_key(sources, area_str, day_range, date_str)
        entry = self._cache.get(key)
        if not entry:
            return None

        is_expired = time.time() > entry.expiry_timestamp
        status = "stale" if is_expired else "fresh"
        return entry.observations, entry.rejected_count, entry.fetched_at, status

    def set(
        self,
        sources: list[str],
        area_str: str,
        day_range: int,
        date_str: str | None,
        observations: list[ThermalObservation],
        rejected_count: int,
        fetched_at: datetime,
        ttl_seconds: int,
    ) -> None:
        # Enforce bounding
        if len(self._cache) >= self._max_entries:
            # Evict oldest entry
            oldest_key = next(iter(self._cache))
            self._cache.pop(oldest_key, None)

        key = self._make_key(sources, area_str, day_range, date_str)
        self._cache[key] = _CacheEntry(observations, rejected_count, fetched_at, ttl_seconds)

    def clear(self) -> None:
        self._cache.clear()


# ==============================
# NASA FIRMS CLIENT
# ==============================

class FIRMSClient:
    """Production client for NASA FIRMS satellite thermal anomaly ingestion."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.cache = FIRMSCache(max_entries=50)

    @property
    def map_key(self) -> str:
        return self.settings.effective_firms_map_key

    def validate_configuration(self) -> None:
        if not self.map_key:
            raise MissingFIRMSKeyError()

    def validate_sensors(self, sources: list[str]) -> list[str]:
        """Validate and normalize requested sensor names."""
        valid_sensors = {s.value for s in FIRMSSensor}
        normalized: list[str] = []
        for src in sources:
            src_clean = src.strip()
            if src_clean not in valid_sensors:
                raise FIRMSValidationError(
                    FIRMSErrorCode.UNSUPPORTED_SOURCE,
                    f"Unsupported FIRMS sensor '{src_clean}'. Supported sensors: {sorted(valid_sensors)}",
                )
            normalized.append(src_clean)
        return normalized

    def validate_day_range(self, days: int) -> int:
        if not (FIRMS_MIN_DAY_RANGE <= days <= FIRMS_MAX_DAY_RANGE):
            raise FIRMSValidationError(
                FIRMSErrorCode.INVALID_DAY_RANGE,
                f"Invalid day_range {days}. NASA FIRMS Area API supports 1 to 5 days.",
            )
        return days

    async def _fetch_single_sensor_csv(
        self,
        client: httpx.AsyncClient,
        source: str,
        bbox: BoundingBox,
        day_range: int,
        date: str | None = None,
    ) -> str:
        """Fetch raw CSV from NASA Area API for one sensor."""
        area_str = bbox.to_firms_area()
        base_url = self.settings.nasa_firms_base_url.rstrip("/")

        # Construct path: /api/area/csv/{MAP_KEY}/{SOURCE}/{AREA_COORDINATES}/{DAY_RANGE}[/{DATE}]
        if date:
            url = f"{base_url}/api/area/csv/{self.map_key}/{source}/{area_str}/{day_range}/{date}"
        else:
            url = f"{base_url}/api/area/csv/{self.map_key}/{source}/{area_str}/{day_range}"

        # Masked URL for logging (never reveal MAP_KEY)
        masked_url = url.replace(self.map_key, "***MASKED_KEY***")
        logger.info(f"Requesting NASA FIRMS: source={source}, area={area_str}, days={day_range}, url={masked_url}")

        start_time = time.perf_counter()
        try:
            response = await client.get(url)
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"NASA FIRMS response: source={source}, status={response.status_code}, duration={duration_ms:.1f}ms")
        except httpx.TimeoutException as ex:
            logger.error(f"NASA FIRMS timeout for {source}: {ex}")
            raise FIRMSTimeoutError() from ex
        except httpx.RequestError as ex:
            logger.error(f"NASA FIRMS network request error for {source}: {ex}")
            raise FIRMSUpstreamError(f"Network error contacting NASA FIRMS: {type(ex).__name__}") from ex

        # Upstream status handling
        if response.status_code == 400:
            text = response.text.strip()
            if "invalid map_key" in text.lower():
                raise FIRMSAuthError()
            raise FIRMSUpstreamError(f"NASA FIRMS 400 error: {text}")
        elif response.status_code == 401 or response.status_code == 403:
            raise FIRMSAuthError()
        elif response.status_code == 429:
            raise FIRMSRateLimitError()
        elif response.status_code >= 500:
            raise FIRMSUpstreamError(f"NASA FIRMS server error HTTP {response.status_code}")
        elif response.status_code != 200:
            raise FIRMSUpstreamError(f"Unexpected HTTP {response.status_code} from NASA FIRMS: {response.text[:200]}")

        return response.text

    async def get_hotspots(
        self,
        bbox: BoundingBox,
        day_range: int = 1,
        sources: list[str] | None = None,
        date: str | None = None,
        force_refresh: bool = False,
    ) -> FIRMSHotspotsResponse:
        """
        Fetch, parse, and normalize FIRMS thermal observations across one or more sensors.
        Implements bounded in-memory caching and safe multi-sensor concurrency.
        """
        self.validate_configuration()
        valid_days = self.validate_day_range(day_range)
        valid_sources = self.validate_sensors(sources or [s.value for s in DEFAULT_FIRMS_SENSORS])
        area_str = bbox.to_firms_area()

        # Check cache if not forcing refresh
        if not force_refresh:
            cached = self.cache.get(valid_sources, area_str, valid_days, date)
            if cached and cached[3] == "fresh":
                obs, rej, fetched_at, status = cached
                logger.info(f"FIRMS cache HIT (fresh): {len(obs)} observations for {valid_sources}")
                return FIRMSHotspotsResponse(
                    mode="live",
                    provider="NASA FIRMS",
                    sources=valid_sources,
                    requested_bbox=bbox.to_dict(),
                    day_range=valid_days,
                    requested_date=date,
                    fetched_at=fetched_at,
                    data_status=status,
                    count=len(obs),
                    rejected_count=rej,
                    partial=False,
                    successful_sources=valid_sources,
                    failed_sources=[],
                    observations=obs,
                )

        timeout = httpx.Timeout(self.settings.nasa_firms_timeout_seconds)
        all_observations: list[ThermalObservation] = []
        total_rejected = 0
        successful_sources: list[str] = []
        failed_sources: list[str] = []
        fetch_timestamp = datetime.now(UTC)

        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = [
                self._fetch_single_sensor_csv(client, src, bbox, valid_days, date)
                for src in valid_sources
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        first_critical_exception: Exception | None = None

        for src, res in zip(valid_sources, results):
            if isinstance(res, BaseException):
                logger.warning(f"Sensor {src} failed: {res}")
                failed_sources.append(src)
                if first_critical_exception is None and isinstance(res, Exception):
                    first_critical_exception = res
            else:
                successful_sources.append(src)
                obs_list, rejected = parse_firms_csv(res, source_name=src)
                all_observations.extend(obs_list)
                total_rejected += rejected

        # If all requested sources failed
        if not successful_sources:
            # Check if we have stale cache to fall back on
            stale = self.cache.get(valid_sources, area_str, valid_days, date)
            if stale:
                obs, rej, fetched_at, _ = stale
                logger.warning("All sources failed, serving STALE cache fallback.")
                return FIRMSHotspotsResponse(
                    mode="live",
                    provider="NASA FIRMS",
                    sources=valid_sources,
                    requested_bbox=bbox.to_dict(),
                    day_range=valid_days,
                    requested_date=date,
                    fetched_at=fetched_at,
                    data_status="stale",
                    count=len(obs),
                    rejected_count=rej,
                    partial=True,
                    successful_sources=[],
                    failed_sources=failed_sources,
                    observations=obs,
                )

            # Re-raise structured exception
            if isinstance(first_critical_exception, FIRMSException):
                raise first_critical_exception
            raise FIRMSUpstreamError(f"All FIRMS sources failed: {failed_sources}")

        # Store in cache
        self.cache.set(
            sources=valid_sources,
            area_str=area_str,
            day_range=valid_days,
            date_str=date,
            observations=all_observations,
            rejected_count=total_rejected,
            fetched_at=fetch_timestamp,
            ttl_seconds=self.settings.nasa_firms_cache_ttl_seconds,
        )

        return FIRMSHotspotsResponse(
            mode="live",
            provider="NASA FIRMS",
            sources=valid_sources,
            requested_bbox=bbox.to_dict(),
            day_range=valid_days,
            requested_date=date,
            fetched_at=fetch_timestamp,
            data_status="fresh",
            count=len(all_observations),
            rejected_count=total_rejected,
            partial=len(failed_sources) > 0,
            successful_sources=successful_sources,
            failed_sources=failed_sources,
            observations=all_observations,
        )

    async def get_data_availability(self, source: str = "VIIRS_NOAA20_NRT") -> FIRMSAvailabilityResponse:
        """Preflight availability check using official NASA FIRMS data_availability API."""
        self.validate_configuration()
        base_url = self.settings.nasa_firms_base_url.rstrip("/")
        url = f"{base_url}/api/data_availability/csv/{self.map_key}/{source}"

        timeout = httpx.Timeout(self.settings.nasa_firms_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                resp = await client.get(url)
            except httpx.TimeoutException as ex:
                raise FIRMSTimeoutError() from ex
            except httpx.RequestError as ex:
                raise FIRMSUpstreamError(f"Network error checking availability: {type(ex).__name__}") from ex

        if resp.status_code == 400 and "invalid map_key" in resp.text.lower():
            raise FIRMSAuthError()
        elif resp.status_code != 200:
            raise FIRMSUpstreamError(f"Failed to check FIRMS availability: HTTP {resp.status_code}")

        # Parse CSV: data_id,min_date,max_date
        items: list[FIRMSAvailabilityItem] = []
        lines = resp.text.strip().split("\n")
        if len(lines) > 1:
            for line in lines[1:]:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    items.append(FIRMSAvailabilityItem(
                        data_id=parts[0],
                        min_date=parts[1],
                        max_date=parts[2],
                    ))

        return FIRMSAvailabilityResponse(
            provider="NASA FIRMS",
            items=items,
            checked_at=datetime.now(UTC),
        )


_client_instance: FIRMSClient | None = None

def get_firms_client() -> FIRMSClient:
    """Singleton getter for FIRMS client."""
    global _client_instance
    if _client_instance is None:
        _client_instance = FIRMSClient()
    return _client_instance
