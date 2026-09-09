# AGNIDRISHTI API — Phase 8 Classification Database Models
"""
SQLAlchemy ORM models for Phase 8 Intelligent Classification Engine.
Stores training label provenance and versioned machine learning predictions.
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
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ThermalClassificationLabelModel(Base):
    """
    Ground-truth and weak-supervision training labels with strict provenance tracking.
    Never stores 'UNKNOWN' as a training label.
    """

    __tablename__ = "thermal_classification_labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("thermal_observations.observation_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    label_source: Mapped[str] = mapped_column(String(64), nullable=False)
    label_provenance: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    label_version: Mapped[str] = mapped_column(String(32), nullable=False, default="label_v1")
    confidence_tier: Mapped[str] = mapped_column(String(32), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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
            "label_version",
            name="uq_classification_observation_label_version",
        ),
    )


class ThermalClassificationPredictionModel(Base):
    """
    Cached ML classification prediction profile for a thermal observation.
    Maintains model version, fusion schema hash, source fingerprint, classification status,
    predicted archetype class, score, and class probabilities.
    """

    __tablename__ = "thermal_classification_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("thermal_observations.observation_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    fusion_schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    fusion_schema_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    fusion_source_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)

    classification_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    predicted_class: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    class_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    class_probabilities: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    evidence_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(64), nullable=False)
    model_artifact_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    predicted_at: Mapped[datetime] = mapped_column(
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
            name="uq_classification_observation_model_version",
        ),
    )
