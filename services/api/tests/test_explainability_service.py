# AGNIDRISHTI API — Phase 9 Explainability Service & API Tests
"""
Integration and service tests for Phase 9 Model Explainability.
Verifies batch bounds (max 500, reject 501 with 422), global importance API,
unknown observation 404, and PostGIS sync idempotency.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select

from app.db.models.classification import ThermalClassificationPredictionModel
from app.db.session import get_session_factory
from app.main import app
from app.ml.explainability.schemas import (
    BatchExplanationRequest,
    SyncExplanationRequest,
)
from app.ml.explainability.service import explainability_service


def test_batch_explanation_request_validation() -> None:
    """Batch request must accept up to 500 IDs and reject 501."""
    valid_ids = [f"firms_{i}" for i in range(500)]
    req = BatchExplanationRequest(observation_ids=valid_ids)
    assert len(req.observation_ids) == 500

    overflow_ids = [f"firms_{i}" for i in range(501)]
    with pytest.raises(ValidationError):
        BatchExplanationRequest(observation_ids=overflow_ids)


def test_sync_explanation_request_validation() -> None:
    """Sync request must accept up to 500 IDs and reject 501."""
    valid_ids = [f"firms_{i}" for i in range(500)]
    req = SyncExplanationRequest(observation_ids=valid_ids)
    assert len(req.observation_ids) == 500

    overflow_ids = [f"firms_{i}" for i in range(501)]
    with pytest.raises(ValidationError):
        SyncExplanationRequest(observation_ids=overflow_ids)


def test_api_global_explanation_endpoint() -> None:
    """GET /api/v1/explanations/global returns 200 with top features and evidence groups."""
    with TestClient(app) as client:
        resp = client.get("/api/v1/explanations/global")
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_version"] == "agnidrishti_context_classifier_v1"
        assert data["explanation_version"] == "agnidrishti_explainer_v1"
        assert data["scoring_metric"] == "macro_f1"
        assert "top_features" in data
        assert len(data["top_features"]) >= 10
        assert "feature_groups" in data
        assert "THERMAL" in data["feature_groups"]
        assert "INDUSTRIAL" in data["feature_groups"]
        assert "LAND_COVER" in data["feature_groups"]


def test_api_unknown_observation_explanation_returns_404() -> None:
    """GET /api/v1/observations/{unknown_id}/explanation returns 404."""
    with TestClient(app) as client:
        resp = client.get("/api/v1/observations/firms_non_existent_id_9999/explanation")
        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "OBSERVATION_NOT_FOUND"


def test_api_batch_explanation_501_rejected_with_422() -> None:
    """POST /api/v1/explanations/batch with 501 IDs returns 422 validation error."""
    with TestClient(app) as client:
        payload = {"observation_ids": [f"obs_{i}" for i in range(501)]}
        resp = client.post("/api/v1/explanations/batch", json=payload)
        assert resp.status_code == 422


def test_api_sync_explanation_501_rejected_with_422() -> None:
    """POST /api/v1/explanations/sync with 501 IDs returns 422 validation error."""
    with TestClient(app) as client:
        payload = {"observation_ids": [f"obs_{i}" for i in range(501)]}
        resp = client.post("/api/v1/explanations/sync", json=payload)
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_sync_explanations_idempotency_and_persistence() -> None:
    """Verify that syncing explanations creates records first and reuses them on second sync."""
    factory = get_session_factory()
    async with factory() as session:
        # Fetch 5 real observation IDs that have Phase-8 predictions
        stmt = (
            select(ThermalClassificationPredictionModel.observation_id)
            .where(ThermalClassificationPredictionModel.classification_status == "AVAILABLE")
            .limit(5)
        )
        res = await session.execute(stmt)
        obs_ids = [r[0] for r in res.fetchall()]

        if not obs_ids:
            pytest.skip("No classified observations in test database to sync.")

        # 1. First sync: should create or reuse
        sync_1 = await explainability_service.sync_explanations(
            observation_ids=obs_ids,
            session=session,
            force_recompute=True,  # ensure freshly computed
        )
        assert sync_1.requested == len(obs_ids)
        assert sync_1.created + sync_1.updated == len(obs_ids)

        # 2. Second sync: should be 100% reused (idempotent)
        sync_2 = await explainability_service.sync_explanations(
            observation_ids=obs_ids,
            session=session,
            force_recompute=False,
        )
        assert sync_2.requested == len(obs_ids)
        assert sync_2.reused == len(obs_ids)
        assert sync_2.created == 0
        assert sync_2.updated == 0

        # 3. Retrieve single explanation via service
        single_exp = await explainability_service.get_explanation_for_observation(
            obs_ids[0], session
        )
        assert single_exp is not None
        assert single_exp.observation_id == obs_ids[0]
        assert single_exp.explanation_status == "AVAILABLE"
        assert len(single_exp.top_supporting_features) > 0
        assert single_exp.base_value is not None
        assert single_exp.additivity_error is not None
        assert single_exp.additivity_error < 1e-3
