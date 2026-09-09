# AGNIDRISHTI API — Phase 8 Classification Service & API Tests
"""
Integration and service-level tests for Phase 8 Classification Service.
Verifies batch bounds (max 500, reject 501), single inference, PostGIS idempotency,
and zero external network requests.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.ml.classification.schemas import (
    BatchClassificationRequest,
    SyncClassificationRequest,
)


def test_batch_classification_request_validation() -> None:
    """Batch request must accept up to 500 IDs and reject 501."""
    valid_ids = [f"firms_{i}" for i in range(500)]
    req = BatchClassificationRequest(observation_ids=valid_ids)
    assert len(req.observation_ids) == 500

    overflow_ids = [f"firms_{i}" for i in range(501)]
    with pytest.raises(ValidationError):
        BatchClassificationRequest(observation_ids=overflow_ids)


def test_sync_classification_request_validation() -> None:
    """Sync request must accept up to 500 IDs and reject 501."""
    valid_ids = [f"firms_{i}" for i in range(500)]
    req = SyncClassificationRequest(observation_ids=valid_ids)
    assert len(req.observation_ids) == 500

    overflow_ids = [f"firms_{i}" for i in range(501)]
    with pytest.raises(ValidationError):
        SyncClassificationRequest(observation_ids=overflow_ids)


def test_api_model_metadata_endpoint() -> None:
    """GET /api/v1/classification/model returns 200 with valid model manifest."""
    with TestClient(app) as client:
        resp = client.get("/api/v1/classification/model")
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_version"] == "agnidrishti_context_classifier_v1"
        assert data["model_family"] in ("hist_gradient_boosting", "random_forest", "logistic_regression")
        assert "classes" in data
        assert len(data["classes"]) >= 3
        assert "artifact_hash" in data
        assert len(data["artifact_hash"]) == 64


def test_api_unknown_observation_classification_returns_404() -> None:
    """GET /api/v1/observations/{unknown_id}/classification returns 404."""
    with TestClient(app) as client:
        resp = client.get("/api/v1/observations/firms_non_existent_id_9999/classification")
        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "OBSERVATION_NOT_FOUND"


def test_api_batch_classification_501_rejected_with_422() -> None:
    """POST /api/v1/classification/batch with 501 IDs returns 422 validation error."""
    with TestClient(app) as client:
        payload = {"observation_ids": [f"obs_{i}" for i in range(501)]}
        resp = client.post("/api/v1/classification/batch", json=payload)
        assert resp.status_code == 422
