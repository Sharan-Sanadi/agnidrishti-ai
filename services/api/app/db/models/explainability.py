# AGNIDRISHTI API — Phase 9 Model Explainability Database Model
"""
SQLAlchemy ORM model for Phase 9 Model Explainability Engine.
Stores verified local feature attributions, base values, additive errors,
and evidence group contributions for Phase 8 model classifications.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ThermalClassificationExplanationModel(Base):
    """
    Cached model explanation profile for a classified thermal observation.
    Captures exact class-specific feature contributions, base value, additivity error,
    top supporting/opposing evidence, and feature group contributions.
    """

    __tablename__ = "thermal_classification_explanations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("thermal_observations.observation_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    explanation_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="agnidrishti_explainer_v1",
    )
    method_name: Mapped[str] = mapped_column(String(64), nullable=False)
    method_version: Mapped[str] = mapped_column(String(32), nullable=False)
    fusion_schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    fusion_schema_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    fusion_source_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    model_artifact_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    classification_status: Mapped[str] = mapped_column(String(32), nullable=False)
    predicted_class: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    prediction_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    explanation_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    base_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    explained_output: Mapped[float | None] = mapped_column(Float, nullable=True)
    additivity_error: Mapped[float | None] = mapped_column(Float, nullable=True)

    feature_contributions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    group_contributions: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    top_supporting: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    top_opposing: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    quality_flags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "observation_id",
            "model_version",
            "explanation_version",
            name="uq_classification_explanation_obs_model_version",
        ),
    )
