# AGNIDRISHTI AI — SIH26162
# Phase 9 Model Explainability — Global Feature Importance Generator
"""
Controlled offline generator for global model feature importance.
Uses scikit-learn permutation_importance on the frozen Phase-8 model and held-out test data.
ZERO RETRAINING. Deterministic random seed 42.
Outputs services/api/artifacts/models/phase9/phase9_global_importance.json.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime
from typing import Any

import numpy as np
from sklearn.inspection import permutation_importance
from sqlalchemy import select

from app.db.models.feature_fusion_profile import ThermalFeatureFusionProfileModel
from app.db.models.thermal_observation import ThermalObservationModel
from app.db.session import get_session_factory
from app.ml.classification.constants import (
    MIN_CLASS_SUPPORT,
    RANDOM_SEED,
    TRAINABLE_CLASSES,
)
from app.ml.classification.dataset import (
    DatasetRecord,
    compute_spatial_group,
    compute_training_dataset_fingerprint,
    get_model_feature_names,
)
from app.ml.classification.labeling import PROVENANCE_UNLABELED, WeakLabelerV1
from app.ml.classification.registry import model_registry
from app.ml.classification.splitting import split_grouped_dataset
from app.ml.explainability.constants import (
    EXPLANATION_VERSION,
    GLOBAL_IMPORTANCE_FILENAME,
    PHASE9_ARTIFACT_DIR,
)
from app.ml.explainability.mapping import (
    get_feature_display_name,
    get_feature_group,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("phase9_global_generator")


async def reconstruct_test_dataset() -> tuple[np.ndarray, list[str], list[str], str]:
    """Reconstruct exact Phase-8 held-out test split using frozen deterministic protocol."""
    factory = get_session_factory()
    async with factory() as session:
        stmt = (
            select(
                ThermalFeatureFusionProfileModel.observation_id,
                ThermalFeatureFusionProfileModel.feature_vector,
                ThermalObservationModel.latitude,
                ThermalObservationModel.longitude,
            )
            .join(
                ThermalObservationModel,
                ThermalObservationModel.observation_id == ThermalFeatureFusionProfileModel.observation_id,
            )
            .where(ThermalFeatureFusionProfileModel.schema_version == "fusion_v1")
        )
        res = await session.execute(stmt)
        rows = res.all()

    feature_names = get_model_feature_names(strategy_a=True)
    records: list[DatasetRecord] = []

    for obs_id, feat_vec, lat, lon in rows:
        assignment = WeakLabelerV1.evaluate(obs_id, feat_vec or {})
        if assignment.label is None or assignment.label_provenance == PROVENANCE_UNLABELED:
            continue

        clean_features = {k: (feat_vec or {}).get(k) for k in feature_names}
        spatial_grp = compute_spatial_group(lat, lon)
        records.append(
            DatasetRecord(
                observation_id=obs_id,
                features=clean_features,
                label=assignment.label,
                label_provenance=assignment.label_provenance,
                spatial_group=spatial_grp,
            )
        )

    class_counts: dict[str, int] = {}
    for r in records:
        class_counts[r.label] = class_counts.get(r.label, 0) + 1

    trainable_classes = [c for c in TRAINABLE_CLASSES if class_counts.get(c, 0) >= MIN_CLASS_SUPPORT]
    filtered_records = [r for r in records if r.label in trainable_classes]
    dataset_fp = compute_training_dataset_fingerprint(filtered_records)

    _train, _val, test_records = split_grouped_dataset(
        filtered_records, test_size=0.15, val_size=0.15, random_state=RANDOM_SEED
    )

    x_test_rows = [[r.features.get(f) for f in feature_names] for r in test_records]
    y_test = [r.label for r in test_records]

    return np.array(x_test_rows, dtype=object), y_test, feature_names, dataset_fp


def main() -> None:
    start_time = time.perf_counter()
    logger.info("=== Starting Phase 9 Global Feature Importance Generation ===")

    # 1. Verify Phase 8 model loading
    model_registry.reset()
    reg = model_registry
    if not reg.is_available or reg.model is None or reg.manifest is None:
        logger.error("FATAL: Phase 8 model is not available: %s", reg.error_message)
        return

    logger.info("Loaded frozen model artifact: %s", reg.manifest.model_version)
    logger.info("Artifact hash: %s", reg.manifest.model_artifact_hash)

    # 2. Reconstruct test dataset
    x_test, y_test, feature_names, dataset_fp = asyncio.run(reconstruct_test_dataset())
    logger.info("Reconstructed held-out test split: %d samples, %d features", len(y_test), len(feature_names))
    logger.info("Dataset fingerprint: %s", dataset_fp)

    # Verify fingerprint matches Phase 8 manifest
    if dataset_fp != reg.manifest.training_dataset_fingerprint:
        logger.warning(
            "Fingerprint mismatch with Phase 8 manifest: %s != %s",
            dataset_fp,
            reg.manifest.training_dataset_fingerprint,
        )

    # 3. Compute Permutation Importance directly through full Pipeline
    logger.info("Computing permutation importance (macro_f1, 10 repeats, seed 42)...")
    perm_result = permutation_importance(
        reg.model,
        x_test,
        y_test,
        scoring="f1_macro",
        n_repeats=10,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )

    importances_mean = (
        perm_result.importances_mean
        if hasattr(perm_result, "importances_mean")
        else perm_result["importances_mean"]
    )
    importances_std = (
        perm_result.importances_std
        if hasattr(perm_result, "importances_std")
        else perm_result["importances_std"]
    )

    # Rank features by importance_mean descending
    sorted_indices = np.argsort(-importances_mean)

    top_features: list[dict[str, Any]] = []
    group_totals: dict[str, float] = {
        "THERMAL": 0.0,
        "TEMPORAL": 0.0,
        "INDUSTRIAL": 0.0,
        "LAND_COVER": 0.0,
        "SENTINEL": 0.0,
    }

    for rank, idx in enumerate(sorted_indices, start=1):
        feat_name = feature_names[idx]
        mean_val = float(importances_mean[idx])
        std_val = float(importances_std[idx])
        grp = get_feature_group(feat_name)
        disp_name = get_feature_display_name(feat_name)

        if grp in group_totals and mean_val > 0:
            group_totals[grp] += mean_val

        top_features.append(
            {
                "feature_name": feat_name,
                "display_name": disp_name,
                "feature_group": grp,
                "importance_mean": round(mean_val, 5),
                "importance_std": round(std_val, 5),
                "rank": rank,
            }
        )

    # Normalize group relative shares
    total_pos_group = sum(group_totals.values())
    group_shares: dict[str, float] = {}
    for g, val in group_totals.items():
        group_shares[g] = round((val / total_pos_group) * 100.0, 1) if total_pos_group > 0 else 0.0

    duration = time.perf_counter() - start_time
    logger.info("Permutation importance completed in %.2fs", duration)

    # Print top 10 features
    logger.info("=== Top 10 Global Features by Permutation Importance ===")
    for item in top_features[:10]:
        logger.info(
            "  %d. %s (%s): mean=%.4f +/- %.4f",
            item["rank"],
            item["display_name"],
            item["feature_group"],
            item["importance_mean"],
            item["importance_std"],
        )

    # 4. Save artifact
    PHASE9_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = PHASE9_ARTIFACT_DIR / GLOBAL_IMPORTANCE_FILENAME

    report_payload = {
        "model_version": reg.manifest.model_version,
        "model_artifact_hash": reg.manifest.model_artifact_hash,
        "explanation_version": EXPLANATION_VERSION,
        "validation_status": reg.manifest.validation_status,
        "scoring_metric": "macro_f1",
        "dataset_fingerprint": dataset_fp,
        "evaluation_split": "test",
        "evaluation_samples": len(y_test),
        "random_seed": RANDOM_SEED,
        "n_repeats": 10,
        "duration_seconds": round(duration, 2),
        "computed_at": datetime.now(UTC).isoformat(),
        "top_features": top_features,
        "feature_groups": group_shares,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    logger.info("Saved global feature importance artifact to %s", out_file)


if __name__ == "__main__":
    main()
