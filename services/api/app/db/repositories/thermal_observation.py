# AGNIDRISHTI API — Thermal Observation Repository
"""
Production repository for PostGIS thermal observation persistence and spatial/temporal querying.
Guarantees idempotent bulk upsert, SRID 4326 spatial envelope filtering, and deterministic ordering.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope, ST_MakePoint, ST_SetSRID
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.thermal_observation import ThermalObservationModel
from app.schemas.firms import BoundingBox

DEFAULT_LIMIT = 500
MAX_LIMIT = 2000


class ThermalObservationRepository:
    """Repository handling all PostGIS persistence operations for thermal observations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def bulk_upsert(self, records: list[dict[str, Any]]) -> int:
        """
        Idempotent bulk upsert for thermal observations.
        If observation_id exists:
          - Preserves first_ingested_at
          - Updates last_seen_at to current timestamp
          - Increments ingestion_count
          - Updates mutable physical fields and updated_at
        Returns number of processed records.
        """
        if not records:
            return 0

        # Transform records to include PostGIS geometry expression: ST_SetSRID(ST_MakePoint(lng, lat), 4326)
        db_records = []
        for r in records:
            rec = dict(r)
            lng = rec["longitude"]
            lat = rec["latitude"]
            # CRITICAL GIS RULE: PostGIS MakePoint is (x, y) = (longitude, latitude)
            rec["geom"] = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
            db_records.append(rec)

        stmt = insert(ThermalObservationModel).values(db_records)

        # Upsert conflict mapping on primary key (observation_id)
        update_dict = {
            "last_seen_at": stmt.excluded.last_seen_at,
            "ingestion_count": ThermalObservationModel.ingestion_count + 1,
            "updated_at": func.now(),
            "confidence_raw": stmt.excluded.confidence_raw,
            "confidence_normalized": stmt.excluded.confidence_normalized,
            "frp": stmt.excluded.frp,
            "bright_ti4": stmt.excluded.bright_ti4,
            "bright_ti5": stmt.excluded.bright_ti5,
            "scan": stmt.excluded.scan,
            "track": stmt.excluded.track,
            "daynight": stmt.excluded.daynight,
            "firms_version": stmt.excluded.firms_version,
            "raw_payload": stmt.excluded.raw_payload,
        }

        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=[ThermalObservationModel.observation_id],
            set_=update_dict,
        )

        await self.db.execute(upsert_stmt)
        await self.db.flush()
        return len(records)

    async def query_spatial_temporal(
        self,
        bbox: BoundingBox | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        sources: list[str] | None = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> tuple[list[ThermalObservationModel], int]:
        """
        Query stored observations from PostGIS using indexed bounding box and UTC time filters.
        Returns (observations, total_matching_count).
        Deterministic ordering: acquisition_time_utc DESC, observation_id ASC.
        """
        # Bound limits safely
        clamped_limit = max(1, min(limit, MAX_LIMIT))
        clamped_offset = max(0, offset)

        query = select(ThermalObservationModel)
        count_query = select(func.count(ThermalObservationModel.observation_id))

        filters = []

        # 1. Spatial bounding box filter (using GiST indexed ST_Intersects & ST_MakeEnvelope)
        if bbox is not None:
            envelope = ST_MakeEnvelope(
                bbox.west,
                bbox.south,
                bbox.east,
                bbox.north,
                4326,
            )
            spatial_filter = ST_Intersects(ThermalObservationModel.geom, envelope)
            filters.append(spatial_filter)

        # 2. Temporal filters (UTC)
        if start_time is not None:
            filters.append(ThermalObservationModel.acquisition_time_utc >= start_time)
        if end_time is not None:
            filters.append(ThermalObservationModel.acquisition_time_utc <= end_time)

        # 3. Source product filter
        if sources:
            filters.append(ThermalObservationModel.source_product.in_(sources))

        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)

        # Get total matching count
        total_res = await self.db.execute(count_query)
        total_count = total_res.scalar() or 0

        # Apply deterministic ordering and pagination
        query = (
            query.order_by(
                ThermalObservationModel.acquisition_time_utc.desc(),
                ThermalObservationModel.observation_id.asc(),
            )
            .limit(clamped_limit)
            .offset(clamped_offset)
        )

        result = await self.db.execute(query)
        observations = list(result.scalars().all())

        return observations, total_count

    async def get_by_id(self, observation_id: str) -> ThermalObservationModel | None:
        """Retrieve a single observation by its deterministic observation ID."""
        stmt = select(ThermalObservationModel).where(
            ThermalObservationModel.observation_id == observation_id
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def count_total(self) -> int:
        """Count total observations stored in PostGIS."""
        stmt = select(func.count(ThermalObservationModel.observation_id))
        res = await self.db.execute(stmt)
        return res.scalar() or 0

    async def get_latest_acquisition(self) -> datetime | None:
        """Get the most recent satellite acquisition timestamp stored in PostGIS."""
        stmt = select(func.max(ThermalObservationModel.acquisition_time_utc))
        res = await self.db.execute(stmt)
        return res.scalar()
