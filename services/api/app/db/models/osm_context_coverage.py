# AGNIDRISHTI API — OSM Context Coverage Database Model
from __future__ import annotations

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OSMContextCoverageModel(Base):
    """
    Tracks spatial coverage regions for OpenStreetMap queries.
    Stores bounding box geometries and expiration metadata (7-day TTL).
    """

    __tablename__ = "osm_context_coverage"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    coverage_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    query_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    bbox_geom: Mapped[Any] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=False,
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    osm_base_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False)  # RUNNING, COMPLETE, PARTIAL, FAILED
    feature_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<OSMContextCoverageModel(coverage_id={self.coverage_id}, status={self.status}, features={self.feature_count})>"
