# AGNIDRISHTI API — OSM Industrial Feature Database Model
from __future__ import annotations

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import JSON, BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OSMIndustrialFeatureModel(Base):
    """
    Normalized OpenStreetMap (OSM) industrial infrastructure feature.
    Stores spatial geometries (Points, LineStrings, Polygons) with PostGIS SRID 4326.
    """

    __tablename__ = "osm_industrial_features"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    osm_uid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    osm_type: Mapped[str] = mapped_column(String(16), nullable=False)  # node, way, relation
    osm_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    operator: Mapped[str | None] = mapped_column(String(255), nullable=True)

    feature_category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    thermal_relevance: Mapped[str] = mapped_column(String(32), nullable=False)  # HIGH, MEDIUM, LOW

    industrial_tag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    man_made_tag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    power_tag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    plant_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    landuse: Mapped[str | None] = mapped_column(String(64), nullable=True)

    tags: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    geom: Mapped[Any] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
        nullable=False,
    )

    geometry_quality: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # EXACT_POINT, EXACT_LINE, EXACT_POLYGON, CENTER_FALLBACK

    osm_version: Mapped[int | None] = mapped_column(nullable=True)
    osm_element_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="OVERPASS_API")

    first_ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<OSMIndustrialFeatureModel(osm_uid={self.osm_uid}, category={self.feature_category}, name={self.name})>"
