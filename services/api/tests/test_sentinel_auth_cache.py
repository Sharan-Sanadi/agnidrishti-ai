# AGNIDRISHTI API — CDSE OAuth2 Token Management & Caching Unit Tests
import time
from unittest.mock import MagicMock, patch

import pytest

from app.providers.sentinel2.auth import CDSEAuthError, CDSETokenProvider


@pytest.mark.asyncio
async def test_token_caching_and_reuse():
    """Verify multiple get_access_token calls within TTL reuse the cached token."""
    provider = CDSETokenProvider(
        token_url="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        client_id="test_client_id",
        client_secret="test_secret",
        safety_skew_seconds=10.0,
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "access_token": "cached_access_token_xyz",
        "expires_in": 1800,
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp) as mock_post:
        # First call: fetches fresh token
        tok1 = await provider.get_access_token()
        assert tok1 == "cached_access_token_xyz"
        assert mock_post.call_count == 1

        # Second call: immediately after, must reuse cached token
        tok2 = await provider.get_access_token()
        assert tok2 == "cached_access_token_xyz"
        assert mock_post.call_count == 1  # Still 1, NOT 2!

        # Third call: still reuses
        tok3 = await provider.get_access_token()
        assert tok3 == "cached_access_token_xyz"
        assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_token_expiry_triggers_refresh():
    """Verify that when the cached token expires, a fresh token is requested."""
    provider = CDSETokenProvider(
        token_url="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        client_id="test_client_id",
        client_secret="test_secret",
        safety_skew_seconds=10.0,
    )

    mock_resp1 = MagicMock()
    mock_resp1.status_code = 200
    mock_resp1.json.return_value = {
        "access_token": "first_token",
        "expires_in": 100,
    }

    mock_resp2 = MagicMock()
    mock_resp2.status_code = 200
    mock_resp2.json.return_value = {
        "access_token": "refreshed_token",
        "expires_in": 100,
    }

    with patch("httpx.AsyncClient.post", side_effect=[mock_resp1, mock_resp2]) as mock_post:
        tok1 = await provider.get_access_token()
        assert tok1 == "first_token"
        assert mock_post.call_count == 1

        # Simulate expiration by forcing _expires_at to past
        provider._expires_at = time.time() - 5.0
        assert not provider.is_token_valid()

        tok2 = await provider.get_access_token()
        assert tok2 == "refreshed_token"
        assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_unauthorized_credentials_rejection():
    """Verify HTTP 401/403 raises CDSEAuthError with appropriate status code."""
    provider = CDSETokenProvider(
        token_url="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        client_id="bad_client",
        client_secret="bad_secret",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized"

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        with pytest.raises(CDSEAuthError) as exc_info:
            await provider.get_access_token()
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_missing_credentials_raises_error():
    provider = CDSETokenProvider(
        token_url="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        client_id="",
        client_secret="",
    )
    with pytest.raises(CDSEAuthError) as exc_info:
        await provider.get_access_token()
    assert "credentials not configured" in str(exc_info.value).lower()
