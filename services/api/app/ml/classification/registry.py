# AGNIDRISHTI API — Phase 8 Model Registry & Secure Loader
"""
Server-controlled model loading, artifact hash verification, schema compatibility checks,
and safe singleton caching for Phase 8 Intelligent Classification Engine.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

from app.ml.classification.constants import (
    ARTIFACT_DIR,
    MANIFEST_FILENAME,
    MODEL_ARTIFACT_FILENAME,
    STATUS_AVAILABLE,
    STATUS_MODEL_INVALID,
    STATUS_MODEL_UNAVAILABLE,
    STATUS_SCHEMA_MISMATCH,
)
from app.ml.classification.schemas import ClassifierManifest
from app.services.fusion.feature_registry import fusion_v1_registry

logger = logging.getLogger(__name__)


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a local file in 64KB blocks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class ModelRegistry:
    """
    Secure singleton loader for the trained Phase 8 classification model artifact.
    Features:
    - Lazy loading: never blocks or crashes FastAPI startup if model is absent.
    - Server-controlled paths: rejects any external/arbitrary paths.
    - Cryptographic verification: verifies SHA-256 manifest hash before joblib.load.
    - Upstream compatibility check: enforces fusion_v1 schema hash match.
    """

    _instance: ModelRegistry | None = None
    _model: Pipeline | None = None
    _manifest: ClassifierManifest | None = None
    _status: str = STATUS_MODEL_UNAVAILABLE
    _error_message: str | None = None

    def __new__(cls) -> ModelRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the cached singleton instance (useful for testing or post-training reload)."""
        cls._instance = None
        cls._model = None
        cls._manifest = None
        cls._status = STATUS_MODEL_UNAVAILABLE
        cls._error_message = None

    def _load_model(self) -> None:
        """Attempt to securely verify and load the model artifact."""
        model_path = ARTIFACT_DIR / MODEL_ARTIFACT_FILENAME
        manifest_path = ARTIFACT_DIR / MANIFEST_FILENAME

        if not manifest_path.exists() or not model_path.exists():
            self._status = STATUS_MODEL_UNAVAILABLE
            self._error_message = "Model artifact or manifest file does not exist on server."
            logger.info("Phase 8 Model unavailable: %s", self._error_message)
            return

        # 1. Load and parse manifest
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest_dict = json.load(f)
            manifest = ClassifierManifest(**manifest_dict)
            self._manifest = manifest
        except Exception as e:
            self._status = STATUS_MODEL_INVALID
            self._error_message = f"Failed to parse model manifest: {e}"
            logger.error("Phase 8 Model manifest invalid: %s", e)
            return

        # 2. Verify model artifact SHA-256 integrity
        try:
            actual_hash = compute_file_sha256(model_path)
            if actual_hash != manifest.model_artifact_hash:
                self._status = STATUS_MODEL_INVALID
                self._error_message = (
                    f"Model artifact SHA-256 mismatch! Manifest: {manifest.model_artifact_hash}, "
                    f"Actual: {actual_hash}"
                )
                logger.error("Phase 8 Model SHA-256 verification failed: %s", self._error_message)
                return
        except Exception as e:
            self._status = STATUS_MODEL_INVALID
            self._error_message = f"Error computing model SHA-256: {e}"
            logger.error("Phase 8 Model hash check error: %s", e)
            return

        # 3. Verify fusion schema version and schema hash compatibility
        if (
            manifest.fusion_schema_version != fusion_v1_registry.schema_version
            or manifest.fusion_schema_hash != fusion_v1_registry.schema_hash
        ):
            self._status = STATUS_SCHEMA_MISMATCH
            self._error_message = (
                f"Fusion schema mismatch! Model trained on "
                f"{manifest.fusion_schema_version}:{manifest.fusion_schema_hash[:8]}, "
                f"current API is {fusion_v1_registry.schema_version}:{fusion_v1_registry.schema_hash[:8]}"
            )
            logger.warning("Phase 8 Schema mismatch: %s", self._error_message)
            return

        # 4. Load pipeline artifact via joblib
        try:
            pipeline = joblib.load(model_path)
            self._model = pipeline
            self._status = STATUS_AVAILABLE
            self._error_message = None
            logger.info("Phase 8 Model successfully verified and loaded: %s", manifest.model_version)
        except Exception as e:
            self._status = STATUS_MODEL_INVALID
            self._error_message = f"Failed to deserialize model pipeline: {e}"
            logger.error("Phase 8 Joblib deserialization error: %s", e)

    @property
    def status(self) -> str:
        return self._status

    @property
    def error_message(self) -> str | None:
        return self._error_message

    @property
    def model(self) -> Pipeline | None:
        return self._model

    @property
    def manifest(self) -> ClassifierManifest | None:
        return self._manifest

    @property
    def is_available(self) -> bool:
        return self._status == STATUS_AVAILABLE and self._model is not None


model_registry = ModelRegistry()
