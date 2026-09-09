# AGNIDRISHTI API — Phase 7 Source Fingerprinting
"""
Deterministic source fingerprinting for Phase 7 Feature Fusion.
Generates an invariant SHA-256 hash representing the semantic upstream data state
for an observation. If upstream data changes (e.g. Sentinel evaluated, industrial context updated),
the fingerprint changes and triggers an idempotent update. If upstream data is unchanged,
sync reuses the existing profile.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


def compute_source_fingerprint(
    feature_vector: dict[str, Any],
    group_statuses: dict[str, str],
    upstream_versions: Mapping[str, str | None],
) -> str:
    """
    Compute a deterministic SHA-256 fingerprint over semantic source features and upstream versions.
    Excludes volatile system timestamps (such as generated_at or DB updated_at) to ensure stability.
    """
    # Build a stable canonical dictionary
    payload = {
        "features": feature_vector,
        "group_statuses": group_statuses,
        "upstream_versions": {k: v for k, v in sorted(upstream_versions.items()) if v is not None},
    }

    # Strict canonical JSON serialization: sorted keys, no whitespace, allow_nan=False
    try:
        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
            default=str,
        )
    except ValueError as ex:
        # If any NaN was present, raise error - NaNs must be converted to None before fingerprinting
        raise ValueError(f"Cannot compute fingerprint: invalid numeric value in feature vector ({ex})") from ex

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
