# AGNIDRISHTI API — Phase 9 Zero External Network Calls Test
"""
Regression test asserting that Phase 9 explanation inference makes zero calls
to external APIs (NASA FIRMS, Overpass OSM, CDSE, WorldCover remote storage, LLMs).
"""

from __future__ import annotations

import httpx
import pytest
import respx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.classification import ThermalClassificationPredictionModel
from app.ml.explainability.service import explainability_service


@pytest.mark.asyncio
@respx.mock
async def test_phase9_sync_zero_external_network_calls(db_session: AsyncSession) -> None:
    """Mock all external HTTP endpoints and verify call count is exactly 0."""
    # Catch any outgoing HTTP request
    route = respx.route().mock(return_value=httpx.Response(500))

    stmt = (
        select(ThermalClassificationPredictionModel.observation_id)
        .where(ThermalClassificationPredictionModel.classification_status == "AVAILABLE")
        .limit(3)
    )
    res = await db_session.execute(stmt)
    obs_ids = [r[0] for r in res.fetchall()]

    if not obs_ids:
        pytest.skip("No classified observations in test database to test network isolation.")

    await explainability_service.sync_explanations(
        observation_ids=obs_ids,
        session=db_session,
        force_recompute=True,
    )

    # Zero HTTP requests should have been triggered
    assert route.call_count == 0, f"FATAL: Phase 9 made external HTTP calls: {route.calls}"
