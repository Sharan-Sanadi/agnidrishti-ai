# AGNIDRISHTI API — CDSE OAuth2 Token Management
"""
Server-side OAuth2 token provider for the Copernicus Data Space Ecosystem (CDSE).
Implements client_credentials flow, in-memory token caching with safety expiry skew,
thread-safe refresh, and bounded exception handling.
"""

from __future__ import annotations

import asyncio
import time

import httpx

from app.core.config import get_settings
from app.core.logging import logger


class CDSEAuthError(Exception):
    """Raised when authentication with CDSE fails."""
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class CDSETokenProvider:
    """
    Thread-safe, async-capable singleton for managing CDSE OAuth2 bearer tokens.
    Reuses tokens within their validity window with a configurable safety margin (default 60s).
    """

    def __init__(
        self,
        token_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        safety_skew_seconds: float = 60.0,
        timeout_seconds: float = 15.0,
    ) -> None:
        settings = get_settings()
        self.token_url = token_url if token_url is not None else settings.cdse_token_url
        self.client_id = client_id if client_id is not None else settings.cdse_client_id
        self.client_secret = client_secret if client_secret is not None else settings.cdse_client_secret
        self.safety_skew_seconds = safety_skew_seconds
        self.timeout_seconds = timeout_seconds

        self._cached_token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def is_configured(self) -> bool:
        """Check if CDSE credentials are provided."""
        return bool(self.client_id.strip() and self.client_secret.strip())

    def is_token_valid(self) -> bool:
        """Check if cached token exists and is comfortably before its expiration timestamp."""
        if not self._cached_token:
            return False
        return time.time() < (self._expires_at - self.safety_skew_seconds)

    async def get_access_token(self) -> str:
        """
        Retrieve a valid CDSE access token, refreshing only when necessary.
        Uses asyncio.Lock to ensure concurrent requests do not stampede the token endpoint.
        """
        if not self.is_configured:
            raise CDSEAuthError(
                "CDSE credentials not configured. Please set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET."
            )

        if self.is_token_valid() and self._cached_token is not None:
            return self._cached_token

        async with self._lock:
            # Re-check inside the lock in case another coroutine just refreshed it
            if self.is_token_valid() and self._cached_token is not None:
                return self._cached_token

            logger.info("Requesting fresh OAuth2 token from CDSE...")
            token, expires_in = await self._fetch_new_token()
            self._cached_token = token
            self._expires_at = time.time() + expires_in
            logger.info(f"CDSE token successfully cached. Valid for {expires_in:.0f}s (skew={self.safety_skew_seconds}s).")
            return self._cached_token

    async def _fetch_new_token(self) -> tuple[str, float]:
        """Send client_credentials POST request to CDSE Identity Provider."""
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.token_url, data=payload, headers=headers)
        except httpx.TimeoutException as ex:
            logger.error(f"CDSE token request timed out after {self.timeout_seconds}s: {ex}")
            raise CDSEAuthError("CDSE authentication request timed out", status_code=504) from ex
        except httpx.RequestError as ex:
            logger.error(f"Network error during CDSE token request: {ex}")
            raise CDSEAuthError(f"Network error connecting to CDSE token provider: {str(ex)}") from ex

        if response.status_code == 200:
            try:
                data = response.json()
            except Exception as ex:
                logger.error("CDSE token endpoint returned non-JSON response.")
                raise CDSEAuthError("Malformed response from CDSE token provider") from ex

            access_token = data.get("access_token")
            expires_in = float(data.get("expires_in", 1800))
            if not access_token:
                raise CDSEAuthError("CDSE token response missing 'access_token' field")
            return str(access_token), expires_in

        # Explicit handling of HTTP error statuses
        if response.status_code in (401, 403):
            logger.error(f"CDSE credentials rejected ({response.status_code}): Invalid client ID or secret.")
            raise CDSEAuthError("CDSE credentials rejected by identity provider", status_code=response.status_code)
        if response.status_code == 429:
            logger.warning("CDSE token endpoint rate limit exceeded (HTTP 429).")
            raise CDSEAuthError("CDSE authentication rate limited", status_code=429)

        logger.error(f"CDSE token endpoint returned HTTP {response.status_code}")
        raise CDSEAuthError(
            f"Failed to authenticate with CDSE: HTTP {response.status_code}",
            status_code=response.status_code,
        )

    def invalidate_cache(self) -> None:
        """Manually clear cached token (e.g., if an API returns 401)."""
        self._cached_token = None
        self._expires_at = 0.0


# Shared singleton instance
_token_provider: CDSETokenProvider | None = None


def get_cdse_token_provider() -> CDSETokenProvider:
    """Get or create singleton CDSETokenProvider."""
    global _token_provider
    if _token_provider is None:
        _token_provider = CDSETokenProvider()
    return _token_provider
