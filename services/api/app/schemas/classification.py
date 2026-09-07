# AGNIDRISHTI API — Classification Schema
"""
Classification contract with confidence, evidence, reasoning, and scientific guardrails.

SCIENTIFIC GUARDRAIL:
  Never automatically state "This factory is burning" or "A gas leak caused this fire."
  Preferred: "Probable industrial thermal event", "Possible industrial fire",
             "Persistent industrial thermal source", "Requires ground verification"
  Confidence is normalized 0.0–1.0. UI may convert to percentage.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import EvidenceItem


class Classification(BaseModel):
    """Hierarchical classification result with explainability."""

    top_level_class: str = Field(
        ...,
        description="INDUSTRIAL / NON_INDUSTRIAL / UNCERTAIN",
    )
    subclass: str = Field(
        ...,
        description="Detailed L2 subclass from taxonomy",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized confidence 0.0–1.0 (NEVER mix with percentages internally)",
    )
    evidence: list[EvidenceItem] = Field(
        default_factory=list,
        description="Structured evidence items supporting classification",
    )
    reasoning_summary: str = Field(
        default="",
        description="Human-readable explanation of classification rationale",
    )
    model_version: str = Field(
        default="fixture-v0",
        description="Classifier model version identifier",
    )
    data_quality: str = Field(
        default="unknown",
        description="Data quality assessment: high / medium / low / degraded",
    )
    requires_ground_verification: bool = Field(
        default=True,
        description="Whether ground-truth verification is recommended",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of classification (UTC)",
    )
