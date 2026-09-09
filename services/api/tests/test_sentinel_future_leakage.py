# AGNIDRISHTI API — Zero Future Leakage & Temporal Search Window Unit Tests
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.sentinel2.auth import CDSETokenProvider
from app.providers.sentinel2.catalog import CDSECatalogClient


@pytest.mark.asyncio
async def test_strictly_no_future_leakage():
    """
    FIRMS target observation is at 2026-09-08 10:00:00 UTC.
    Candidate A: 2026-09-08 09:45:00 UTC (15 mins prior -> ALLOWED)
    Candidate B: 2026-09-08 10:00:01 UTC (1 second after -> FORBIDDEN FUTURE LEAKAGE)
    Candidate C: 2026-09-09 05:00:00 UTC (Next day -> FORBIDDEN FUTURE LEAKAGE)
    """
    target_time = datetime(2026, 9, 8, 10, 0, 0, tzinfo=UTC)

    mock_features = [
        {
            "id": "S2B_SCENE_ALLOWED_PRIOR",
            "properties": {
                "datetime": "2026-09-08T09:45:00Z",
                "eo:cloud_cover": 10.0,
                "platform": "Sentinel-2B",
            },
            "bbox": [72.6, 21.0, 72.7, 21.2],
        },
        {
            "id": "S2A_SCENE_REJECTED_FUTURE_1SEC",
            "properties": {
                "datetime": "2026-09-08T10:00:01Z",
                "eo:cloud_cover": 5.0,
                "platform": "Sentinel-2A",
            },
            "bbox": [72.6, 21.0, 72.7, 21.2],
        },
        {
            "id": "S2B_SCENE_REJECTED_FUTURE_NEXTDAY",
            "properties": {
                "datetime": "2026-09-09T05:00:00Z",
                "eo:cloud_cover": 0.0,
                "platform": "Sentinel-2B",
            },
            "bbox": [72.6, 21.0, 72.7, 21.2],
        },
    ]

    token_provider = AsyncMock(spec=CDSETokenProvider)
    token_provider.get_access_token.return_value = "mock_token"

    client = CDSECatalogClient(token_provider=token_provider)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"features": mock_features}

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        candidates = await client.search_candidates(
            latitude=21.105,
            longitude=72.653,
            target_firms_time_utc=target_time,
            lookback_days=30,
            max_candidates=10,
        )

    # Only Candidate A must survive
    assert len(candidates) == 1
    assert candidates[0].scene_id == "S2B_SCENE_ALLOWED_PRIOR"
    assert candidates[0].acquisition_time_utc <= target_time


@pytest.mark.asyncio
async def test_search_datetime_payload_window():
    """Verify the STAC API search request specifies strictly [T - lookback, T]."""
    target_time = datetime(2026, 9, 8, 12, 0, 0, tzinfo=UTC)
    lookback_days = 30
    start_time = target_time - timedelta(days=lookback_days)
    expected_dt_str = f"{start_time.isoformat()}/{target_time.isoformat()}"

    token_provider = AsyncMock(spec=CDSETokenProvider)
    token_provider.get_access_token.return_value = "mock_token"

    client = CDSECatalogClient(token_provider=token_provider)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"features": []}

    with patch("httpx.AsyncClient.post", return_value=mock_resp) as mock_post:
        _ = await client.search_candidates(
            latitude=21.105,
            longitude=72.653,
            target_firms_time_utc=target_time,
            lookback_days=lookback_days,
            max_candidates=8,
        )

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["datetime"] == expected_dt_str
        assert payload["collections"] == ["sentinel-2-l2a"]
