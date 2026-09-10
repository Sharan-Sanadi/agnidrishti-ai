# AGNIDRISHTI API — Phase 9 No-Retraining Regression Test
"""
Regression test asserting that Phase 9 explanation sync and inference NEVER
call classifier .fit() or preprocessor .fit() under any circumstances.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.classification.registry import model_registry
from app.ml.explainability.service import explainability_service


@pytest.mark.asyncio
async def test_phase9_sync_never_calls_fit(db_session: AsyncSession) -> None:
    """Ensure that classifier and preprocessor .fit() are never invoked in Phase 9."""
    pipeline = model_registry.model
    assert pipeline is not None

    classifier = pipeline.named_steps["classifier"]
    preprocessor = pipeline.named_steps["preprocessor"]

    # Wrap .fit methods with mock spies
    original_clf_fit = classifier.fit
    original_pre_fit = preprocessor.fit

    mock_clf_fit = MagicMock(side_effect=original_clf_fit)
    mock_pre_fit = MagicMock(side_effect=original_pre_fit)

    classifier.fit = mock_clf_fit
    preprocessor.fit = mock_pre_fit

    try:
        # Sync explanations for up to 3 test observations
        await explainability_service.sync_explanations(
            observation_ids=["test_obs_dummy_1"],
            session=db_session,
            force_recompute=True,
        )

        # Assert zero fit calls
        assert mock_clf_fit.call_count == 0, "FATAL: classifier.fit() was called during Phase 9 sync!"
        assert mock_pre_fit.call_count == 0, "FATAL: preprocessor.fit() was called during Phase 9 sync!"

    finally:
        # Restore originals
        classifier.fit = original_clf_fit
        preprocessor.fit = original_pre_fit
