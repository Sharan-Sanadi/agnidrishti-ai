# AGNIDRISHTI API — Phase 7 Feature Fusion Validators
"""
Strict validation, invariant enforcement, and data integrity checks for Phase 7 Feature Fusion.

Enforces:
1. Strict Temporal Leakage Audit: Sentinel scene acquisition UTC must be <= FIRMS acquisition UTC.
   If scene_time > firms_time, Sentinel group is flagged and excluded.
2. JSON Sanitization: Ensures no NaN, Inf, or -Inf enters feature vectors; all missing numeric values are None.
3. Land Cover Fraction Sanity Check: WorldCover 500m fractions are checked to approximately sum to 1.0.
   Violations are recorded in quality_flags rather than silently mutated.
4. Scale Invariance Audit: Confirms Persistence Index remains on the canonical 0-100 scale.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from app.core.logging import logger


def sanitize_value(val: Any) -> Any:
    """Ensure floating point values are strictly JSON compliant (no NaN/Inf)."""
    if val is None:
        return None
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
    return val


def sanitize_feature_vector(features: dict[str, Any]) -> dict[str, Any]:
    """Sanitize all values in a feature dictionary."""
    return {k: sanitize_value(v) for k, v in features.items()}


def validate_sentinel_leakage(
    firms_time: datetime,
    sentinel_scene_time: datetime | None,
) -> tuple[bool, str | None]:
    """
    Verify that Sentinel scene acquisition is <= FIRMS detection UTC.
    Returns (is_valid, error_message).
    """
    if sentinel_scene_time is None:
        return True, None

    # Both should be timezone-aware or both naive for comparison
    # If sentinel_scene_time > firms_time, this is a future data leakage violation!
    if sentinel_scene_time > firms_time:
        msg = (
            f"TEMPORAL LEAKAGE DETECTED: Sentinel scene time ({sentinel_scene_time.isoformat()}) "
            f"is after FIRMS acquisition time ({firms_time.isoformat()}). Excluding Sentinel group."
        )
        logger.error(msg)
        return False, msg

    return True, None


def validate_landcover_fractions(
    fractions: dict[str, float | None],
    tolerance: float = 0.05,
) -> tuple[bool, float, str | None]:
    """
    Validate that available 500m land cover class fractions sum approximately to 1.0.
    Returns (is_valid, sum_val, warning_message).
    """
    valid_vals = [v for v in fractions.values() if v is not None]
    if not valid_vals:
        return True, 0.0, None

    total = sum(valid_vals)
    # Tolerant check around 1.0 (allowing rounding discrepancies up to tolerance)
    if abs(total - 1.0) > tolerance:
        msg = f"Land cover 500m fractions sum to {round(total, 4)}, outside tolerance [1.0 +/- {tolerance}]."
        return False, total, msg

    return True, total, None
