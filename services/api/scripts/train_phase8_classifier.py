# AGNIDRISHTI AI — SIH26162
# Phase 8 Intelligent Classification Engine — Model Training Script
"""
Train candidate context archetype models, evaluate on spatially grouped test set,
select best model by Macro F1, serialize artifact with SHA-256 integrity verification,
and generate training reports.
Zero external calls (NASA, Overpass, WorldCover, CDSE = 0).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import platform
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import sklearn
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.models.classification import ThermalClassificationLabelModel
from app.db.models.feature_fusion_profile import ThermalFeatureFusionProfileModel
from app.db.models.thermal_observation import ThermalObservationModel
from app.db.session import get_session_factory
from app.ml.classification.constants import (
    ARTIFACT_DIR,
    MANIFEST_FILENAME,
    MIN_CLASS_SUPPORT,
    MODEL_ARTIFACT_FILENAME,
    MODEL_VERSION,
    PROVENANCE_UNLABELED,
    RANDOM_SEED,
    TRAINABLE_CLASSES,
    VALIDATION_WEAK_SUPERVISION,
)
from app.ml.classification.dataset import (
    DatasetRecord,
    audit_leakage,
    compute_feature_missingness,
    compute_spatial_group,
    compute_training_dataset_fingerprint,
    get_feature_types,
    get_model_feature_names,
)
from app.ml.classification.labeling import WeakLabelerV1
from app.ml.classification.metrics import calculate_metrics
from app.ml.classification.pipeline import build_candidate_pipeline
from app.ml.classification.schemas import ClassifierManifest
from app.ml.classification.splitting import audit_group_leakage, split_grouped_dataset
from app.services.fusion.feature_registry import fusion_v1_registry

SCRIPT_DIR = Path(__file__).resolve().parent
API_DIR = SCRIPT_DIR.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("phase8_trainer")


async def step_1_generate_and_store_labels() -> dict[str, Any]:
    """
    Load all fusion_v1 profiles, apply conservative WeakLabelerV1 rules,
    and persist labels with provenance to thermal_classification_labels.
    """
    logger.info("=== STEP 1: Label Generation & Provenance Audit ===")
    factory = get_session_factory()
    label_stats = {
        "total_profiles": 0,
        "verified_labels": 0,
        "weak_labels": 0,
        "unlabeled": 0,
        "conflicts": 0,
        "class_counts": {},
    }

    async with factory() as session:
        # Load all fusion_v1 profiles joined with thermal observations for coordinates
        stmt = (
            select(
                ThermalFeatureFusionProfileModel.observation_id,
                ThermalFeatureFusionProfileModel.feature_vector,
                ThermalFeatureFusionProfileModel.source_fingerprint,
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
        label_stats["total_profiles"] = len(rows)
        logger.info("Loaded %d fusion_v1 profiles for labeling.", len(rows))

        label_assignments = []
        for obs_id, feat_vec, _fp, lat, lon in rows:
            assignment = WeakLabelerV1.evaluate(obs_id, feat_vec or {})
            label_assignments.append((assignment, lat, lon, feat_vec))

            if assignment.label is None:
                if assignment.confidence_tier == "CONFLICT":
                    label_stats["conflicts"] += 1
                label_stats["unlabeled"] += 1
            else:
                label_stats["weak_labels"] += 1
                c = assignment.label
                label_stats["class_counts"][c] = label_stats["class_counts"].get(c, 0) + 1

        # Upsert labels into database table
        now = datetime.now(UTC)
        for assignment, _lat, _lon, _feat in label_assignments:
            if assignment.label is None:
                continue
            insert_stmt = insert(ThermalClassificationLabelModel).values(
                observation_id=assignment.observation_id,
                label=assignment.label,
                label_source=assignment.label_source,
                label_provenance=assignment.label_provenance,
                label_version=assignment.label_version,
                confidence_tier=assignment.confidence_tier,
                reference=assignment.reference,
                notes=assignment.notes,
                created_at=now,
                updated_at=now,
            ).on_conflict_do_update(
                constraint="uq_classification_observation_label_version",
                set_={
                    "label": assignment.label,
                    "label_source": assignment.label_source,
                    "label_provenance": assignment.label_provenance,
                    "confidence_tier": assignment.confidence_tier,
                    "reference": assignment.reference,
                    "notes": assignment.notes,
                    "updated_at": now,
                },
            )
            await session.execute(insert_stmt)

        await session.commit()
        logger.info("Persisted %d weak labels to thermal_classification_labels.", label_stats["weak_labels"])

    return {
        "stats": label_stats,
        "assignments": label_assignments,
    }


def step_2_assemble_dataset(raw_data: list[tuple[Any, float, float, dict[str, Any]]]) -> tuple[list[DatasetRecord], dict[str, float]]:
    """
    Assemble leakage-safe DatasetRecord objects.
    - Exclude forbidden fields and Strategy A categoricals.
    - Compute ~5km spatial grid grouping from coordinates (never stored in features).
    """
    logger.info("=== STEP 2: Dataset Assembly & Leakage Guardrails ===")
    records: list[DatasetRecord] = []
    feature_names = get_model_feature_names(strategy_a=True)
    all_feature_vectors: list[dict[str, Any]] = []

    for assignment, lat, lon, feat_vec in raw_data:
        if assignment.label is None:
            continue
        if assignment.label_provenance == PROVENANCE_UNLABELED:
            continue

        # Filter features to Strategy A model-eligible subset
        clean_features = {k: feat_vec.get(k) for k in feature_names}
        all_feature_vectors.append(clean_features)

        spatial_grp = compute_spatial_group(lat, lon)
        records.append(
            DatasetRecord(
                observation_id=assignment.observation_id,
                features=clean_features,
                label=assignment.label,
                label_provenance=assignment.label_provenance,
                spatial_group=spatial_grp,
            )
        )

    # Audit feature leakage
    leaked_features = audit_leakage(all_feature_vectors, strategy_a=True)
    if leaked_features:
        raise RuntimeError(f"FATAL: Detected feature leakage: {leaked_features}")
    logger.info("Leakage audit PASS: 0 forbidden/circular features in training matrix.")

    missingness = compute_feature_missingness(all_feature_vectors, feature_names)
    return records, missingness


def main_train() -> None:
    """Execute complete Phase 8 training workflow."""
    start_time = time.perf_counter()
    logger.info("Starting Phase 8 Intelligent Classification Training...")

    # 1. Label generation & DB persistence
    step1_result = asyncio.run(step_1_generate_and_store_labels())
    label_stats = step1_result["stats"]
    assignments = step1_result["assignments"]

    # 2. Dataset Assembly
    records, missingness = step_2_assemble_dataset(assignments)
    logger.info("Prepared %d labeled dataset records across %d spatial groups.",
                len(records), len({r.spatial_group for r in records}))

    # 3. Minimum Label Support Gate
    class_counts: dict[str, int] = {}
    for r in records:
        class_counts[r.label] = class_counts.get(r.label, 0) + 1

    trainable_classes = [c for c in TRAINABLE_CLASSES if class_counts.get(c, 0) >= MIN_CLASS_SUPPORT]
    logger.info("Class support distribution: %s", class_counts)
    logger.info("Trainable classes passing minimum support (%d+): %s", MIN_CLASS_SUPPORT, trainable_classes)

    if len(trainable_classes) < 3:
        raise RuntimeError(f"FATAL: Fewer than 3 classes meet minimum support gate ({len(trainable_classes)} < 3).")

    # Filter records to supported trainable classes
    filtered_records = [r for r in records if r.label in trainable_classes]

    # Dataset Fingerprint
    dataset_fp = compute_training_dataset_fingerprint(filtered_records)
    logger.info("Training Dataset Fingerprint (SHA-256): %s", dataset_fp)

    # 4. Spatially Grouped Splitting
    train_records, val_records, test_records = split_grouped_dataset(
        filtered_records, test_size=0.15, val_size=0.15, random_state=RANDOM_SEED
    )
    leakage_audit = audit_group_leakage(train_records, val_records, test_records)
    logger.info("Split group sizes: Train=%d, Val=%d, Test=%d", len(train_records), len(val_records), len(test_records))
    logger.info("Spatial group leakage audit: %s", leakage_audit)

    if any(count > 0 for count in leakage_audit.values()):
        raise RuntimeError(f"FATAL: Spatial group leakage detected across splits: {leakage_audit}")

    # Prepare matrix arrays
    feature_names = get_model_feature_names(strategy_a=True)
    numeric_features, categorical_features = get_feature_types(strategy_a=True)

    # Map column names to integer indices for array inputs
    numeric_indices = [feature_names.index(f) for f in numeric_features]
    categorical_indices = [feature_names.index(f) for f in categorical_features]

    def to_matrix(recs: list[DatasetRecord]) -> tuple[np.ndarray, list[str]]:
        rows = [[r.features.get(f) for f in feature_names] for r in recs]
        labels = [r.label for r in recs]
        return np.array(rows, dtype=object), labels

    x_train, y_train = to_matrix(train_records)
    x_val, y_val = to_matrix(val_records)
    x_test, y_test = to_matrix(test_records)

    # 5. Candidate Models Training & Validation Selection
    candidate_families = [
        "dummy",
        "logistic_regression",
        "random_forest",
        "hist_gradient_boosting",
    ]

    candidate_results: dict[str, Any] = {}
    best_family: str | None = None
    best_val_macro_f1 = -1.0
    best_pipeline = None

    for family in candidate_families:
        logger.info("Training candidate model: %s...", family)
        pipe = build_candidate_pipeline(
            model_family=family,
            numeric_features=numeric_indices,
            categorical_features=categorical_indices,
            random_state=RANDOM_SEED,
        )

        pipe.fit(x_train, y_train)

        # Evaluate on validation set
        val_preds = pipe.predict(x_val)
        val_preds_str = [str(p) for p in val_preds]
        val_metrics = calculate_metrics(
            y_true=y_val,
            y_pred=val_preds_str,
            class_names=trainable_classes,
            validation_status=VALIDATION_WEAK_SUPERVISION,
        )

        candidate_results[family] = {
            "macro_f1": val_metrics.macro_f1,
            "weighted_f1": val_metrics.weighted_f1,
            "balanced_accuracy": val_metrics.balanced_accuracy,
        }
        logger.info("Candidate %s — Val Macro F1: %.4f | Balanced Acc: %.4f",
                    family, val_metrics.macro_f1, val_metrics.balanced_accuracy)

        if family != "dummy" and val_metrics.macro_f1 > best_val_macro_f1:
            best_val_macro_f1 = val_metrics.macro_f1
            best_family = family
            best_pipeline = pipe

    logger.info("Selected best model family: %s (Val Macro F1: %.4f)", best_family, best_val_macro_f1)
    if best_pipeline is None or best_family is None:
        raise RuntimeError("FATAL: Failed to select best candidate model.")

    # 6. Final Evaluation on Spatially Grouped Test Set
    test_preds = best_pipeline.predict(x_test)
    test_preds_str = [str(p) for p in test_preds]
    test_metrics = calculate_metrics(
        y_true=y_test,
        y_pred=test_preds_str,
        class_names=trainable_classes,
        validation_status=VALIDATION_WEAK_SUPERVISION,
    )

    logger.info("=== FINAL TEST METRICS (Weak-Label Agreement) ===")
    logger.info("Macro F1: %.4f", test_metrics.macro_f1)
    logger.info("Balanced Accuracy: %.4f", test_metrics.balanced_accuracy)
    logger.info("Weighted F1: %.4f", test_metrics.weighted_f1)

    for c_name, c_metric in test_metrics.per_class.items():
        logger.info("Class [%s] — P: %.4f, R: %.4f, F1: %.4f, Support: %d",
                    c_name, c_metric.precision, c_metric.recall, c_metric.f1_score, c_metric.support)

    # 7. Model Artifact Serialization & Cryptographic Hash
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = ARTIFACT_DIR / MODEL_ARTIFACT_FILENAME

    joblib.dump(best_pipeline, artifact_path, compress=3)
    artifact_size_bytes = artifact_path.stat().st_size
    logger.info("Saved model artifact to %s (%d bytes).", artifact_path, artifact_size_bytes)

    # Compute SHA-256 of artifact
    hasher = hashlib.sha256()
    with open(artifact_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    artifact_sha256 = hasher.hexdigest()
    logger.info("Model artifact SHA-256: %s", artifact_sha256)

    # 8. Manifest Generation
    manifest = ClassifierManifest(
        model_version=MODEL_VERSION,
        model_family=best_family,
        model_artifact_filename=MODEL_ARTIFACT_FILENAME,
        model_artifact_hash=artifact_sha256,
        model_artifact_size_bytes=artifact_size_bytes,
        fusion_schema_version=fusion_v1_registry.schema_version,
        fusion_schema_hash=fusion_v1_registry.schema_hash,
        training_dataset_fingerprint=dataset_fp,
        classes=trainable_classes,
        ordered_features=feature_names,
        validation_status=VALIDATION_WEAK_SUPERVISION,
        metrics=test_metrics.model_dump(),
        trained_at=datetime.now(UTC).isoformat(),
        random_seed=RANDOM_SEED,
        python_version=platform.python_version(),
        sklearn_version=sklearn.__version__,
    )

    manifest_path = ARTIFACT_DIR / MANIFEST_FILENAME
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, indent=2)
    logger.info("Saved model manifest to %s.", manifest_path)

    # 9. Training Reports (JSON & Markdown)
    docs_dir = API_DIR.parent.parent / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    report_data = {
        "training_metadata": {
            "timestamp": manifest.trained_at,
            "duration_seconds": round(time.perf_counter() - start_time, 2),
            "model_version": MODEL_VERSION,
            "model_family": best_family,
            "validation_status": VALIDATION_WEAK_SUPERVISION,
            "dataset_fingerprint": dataset_fp,
            "artifact_sha256": artifact_sha256,
            "artifact_size_bytes": artifact_size_bytes,
        },
        "labels": label_stats,
        "dataset": {
            "total_labeled_samples": len(filtered_records),
            "train_samples": len(train_records),
            "val_samples": len(val_records),
            "test_samples": len(test_records),
            "spatial_groups": len({r.spatial_group for r in filtered_records}),
            "classes": trainable_classes,
        },
        "candidate_models": candidate_results,
        "test_metrics": test_metrics.model_dump(),
        "feature_missingness": missingness,
    }

    report_json_path = docs_dir / "phase8_training_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Human-readable Markdown report
    md_content = f"""# AGNIDRISHTI AI — Phase 8 Model Training Report
**Model Version:** `{MODEL_VERSION}`
**Trained At:** `{manifest.trained_at}`
**Model Family:** `{best_family}`
**Validation Tier:** `{VALIDATION_WEAK_SUPERVISION}`
**Dataset Fingerprint:** `{dataset_fp}`
**Artifact SHA-256:** `{artifact_sha256}`

---

## 1. Label Provenance & Data Distribution
- **Total Fusion Profiles Evaluated:** {label_stats['total_profiles']}
- **Weak Labels Generated:** {label_stats['weak_labels']}
- **Unlabeled / Insufficient Evidence:** {label_stats['unlabeled']}
- **Labeling Conflicts:** {label_stats['conflicts']}
- **Split Strategy:** Deterministic Spatial Grouping (~5 km grid cells, seed={RANDOM_SEED})
- **Train Samples:** {len(train_records)} | **Validation:** {len(val_records)} | **Test:** {len(test_records)}

### Per-Class Counts
"""
    for c, cnt in label_stats["class_counts"].items():
        md_content += f"- **{c}:** {cnt}\n"

    md_content += """
---

## 2. Candidate Model Comparison (Validation Set Macro F1)
| Model Family | Macro F1 | Weighted F1 | Balanced Accuracy |
| :--- | :--- | :--- | :--- |
"""
    for fam, m in candidate_results.items():
        md_content += f"| `{fam}` | {m['macro_f1']:.4f} | {m['weighted_f1']:.4f} | {m['balanced_accuracy']:.4f} |\n"

    md_content += f"""
---

## 3. Selected Model Test Performance ({test_metrics.evaluation_type})
- **Macro F1:** `{test_metrics.macro_f1:.4f}`
- **Balanced Accuracy:** `{test_metrics.balanced_accuracy:.4f}`
- **Weighted F1:** `{test_metrics.weighted_f1:.4f}`

### Per-Class Test Breakdown
| Context Archetype | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
"""
    for c_name, c_m in test_metrics.per_class.items():
        md_content += f"| `{c_name}` | {c_m.precision:.4f} | {c_m.recall:.4f} | {c_m.f1_score:.4f} | {c_m.support} |\n"

    md_content += """
---

## 4. Leakage Controls & Scientific Honesty
1. **Forbidden Identifier & Spatial Leakage:** All identifiers (`observation_id`, `scene_id`, `osm_uid`) and geographic coordinates (`latitude`, `longitude`) were strictly excluded from model feature matrix `X`.
2. **Anti-Circularity (Strategy A):** Direct categorical labels (`industrial_context_class`, `landcover_context_class`, etc.) were stripped from features, ensuring model learns from physical indicators (distances, counts, fractions, spectral indices, thermal brightness/FRP).
3. **Spatial Group Segregation:** No spatial ~5km grid cell overlaps between Train, Validation, and Test splits.
4. **Target Semantics:** Predicts **Thermal Context Archetype**, NOT fire cause or wildfire/crop-burning confirmation.
"""

    report_md_path = docs_dir / "phase8_training_report.md"
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info("Saved training reports to %s and %s.", report_json_path, report_md_path)
    logger.info("=== Phase 8 Model Training Completed Successfully in %.2fs ===", time.perf_counter() - start_time)


if __name__ == "__main__":
    main_train()
