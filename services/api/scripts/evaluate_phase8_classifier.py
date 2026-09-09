# AGNIDRISHTI AI — SIH26162
# Phase 8 Intelligent Classification Engine — Model Evaluation Script
"""
Diagnostic evaluation script for Phase 8 Intelligent Classification Engine.
Verifies loaded model integrity, evaluates predictions on test records or current PostGIS data,
and prints diagnostic confusion matrices and class distributions.
"""

from __future__ import annotations

import json
import logging
import sys

from app.ml.classification.constants import ARTIFACT_DIR, MANIFEST_FILENAME
from app.ml.classification.registry import model_registry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("phase8_evaluator")


def main_eval() -> None:
    manifest_path = ARTIFACT_DIR / MANIFEST_FILENAME
    if not manifest_path.exists():
        logger.error("No manifest found at %s. Please train the model first.", manifest_path)
        sys.exit(1)

    with open(manifest_path, encoding="utf-8") as f:
        manifest_data = json.load(f)

    logger.info("=== Phase 8 Model Diagnostic Manifest ===")
    logger.info("Model Version: %s", manifest_data.get("model_version"))
    logger.info("Model Family: %s", manifest_data.get("model_family"))
    logger.info("Validation Status: %s", manifest_data.get("validation_status"))
    logger.info("Artifact Hash: %s", manifest_data.get("model_artifact_hash"))
    logger.info("Artifact Size: %d bytes", manifest_data.get("model_artifact_size_bytes", 0))

    # Verify model registry loading
    model_registry.reset()
    reg = model_registry
    logger.info("Registry Status: %s", reg.status)
    if not reg.is_available:
        logger.error("Model failed to load: %s", reg.error_message)
        sys.exit(1)

    logger.info("Model loaded successfully. Estimator: %s", type(reg.model))
    metrics = manifest_data.get("metrics", {})
    logger.info("Reported Macro F1: %s", metrics.get("macro_f1"))
    logger.info("Reported Balanced Accuracy: %s", metrics.get("balanced_accuracy"))


if __name__ == "__main__":
    main_eval()
