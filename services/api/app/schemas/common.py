# AGNIDRISHTI API — Common Schemas
"""
Shared schema primitives: error responses, data quality, source traceability, evidence.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ==============================
# ERROR CONTRACT
# ==============================

class ErrorResponse(BaseModel):
    """Consistent API error shape. Never leaks stack traces."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] = Field(default_factory=dict)


# ==============================
# SOURCE TRACEABILITY
# ==============================

class DataSourceInfo(BaseModel):
    """Identifies where a piece of data originated."""

    source_name: str = Field(..., description="e.g. NASA_FIRMS, OPENSTREETMAP")
    source_timestamp: datetime | None = Field(None, description="When the source data was fetched")
    source_version: str | None = Field(None, description="Version or snapshot ID of the source")
    source_reference: str | None = Field(None, description="URL or identifier for the source")


# ==============================
# DATA QUALITY
# ==============================

class DataQuality(BaseModel):
    """Tracks data completeness and degradation."""

    available_sources: list[str] = Field(default_factory=list)
    missing_sources: list[str] = Field(default_factory=list)
    overall_quality: str = Field(
        default="unknown",
        description="high / medium / low / degraded / unknown",
    )
    notes: list[str] = Field(default_factory=list)


# ==============================
# EVIDENCE CONTRACT
# ==============================

class EvidenceItem(BaseModel):
    """
    Structured classification evidence.
    Not merely strings — typed, weighted, and sourced.
    """

    type: str = Field(..., description="Evidence category, e.g. industrial_proximity, land_cover")
    label: str = Field(..., description="Human-readable label")
    value: Any = Field(..., description="Evidence value")
    unit: str | None = Field(None, description="Unit of measurement if applicable")
    weight_or_importance: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Relative importance 0.0–1.0",
    )
    source: str | None = Field(None, description="Data source name")
    description: str | None = Field(None, description="Explanation of this evidence")


# ==============================
# PAGINATION (future use)
# ==============================

class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    items: list[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50
