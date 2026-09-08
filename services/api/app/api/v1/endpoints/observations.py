# AGNIDRISHTI API — PostGIS Stored Observations Endpoints
"""
Production endpoints for querying normalized satellite thermal observations from PostGIS.
These endpoints query PostGIS exclusively and DO NOT make upstream calls to NASA.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import INDIA_DEFAULT_BBOX, FIRMSErrorCode
from app.core.logging import logger
from app.db.repositories.thermal_observation import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    ThermalObservationRepository,
)
from app.db.session import get_db
from app.schemas.firms import BoundingBox
from app.schemas.observations import (
    StoredObservationItem,
    StoredObservationsResponse,
)

router = APIRouter()


def model_to_schema(obs) -> StoredObservationItem:
    """Convert an ORM model into the canonical StoredObservationItem schema."""
    return StoredObservationItem(
        id=obs.observation_id,
        latitude=obs.latitude,
        longitude=obs.longitude,
        acquisition_time_utc=obs.acquisition_time_utc,
        satellite=obs.satellite,
        instrument=obs.instrument,
        source=obs.source_product,
        provider=obs.provider,
        confidence=obs.confidence_raw,
        confidence_normalized=obs.confidence_normalized,
        frp=obs.frp,
        bright_ti4=obs.bright_ti4,
        bright_ti5=obs.bright_ti5,
        scan=obs.scan,
        track=obs.track,
        daynight=obs.daynight,
        firms_version=obs.firms_version,
        first_ingested_at=obs.first_ingested_at,
        last_seen_at=obs.last_seen_at,
        ingestion_count=obs.ingestion_count,
        stored_in_postgis=True,
        geojson={
            "type": "Point",
            "coordinates": [obs.longitude, obs.latitude],
        },
    )


@router.get(
    "",
    response_model=StoredObservationsResponse,
    summary="Query stored thermal observations from PostGIS",
    description="Queries historical, normalized thermal observations from PostgreSQL/PostGIS with indexed spatial and temporal filtering.",
)
async def get_observations(
    west: float | None = Query(None, description="West longitude (-180 to 180)"),
    south: float | None = Query(None, description="South latitude (-90 to 90)"),
    east: float | None = Query(None, description="East longitude (-180 to 180)"),
    north: float | None = Query(None, description="North latitude (-90 to 90)"),
    start_time: datetime | None = Query(None, description="Start acquisition time (UTC)"),
    end_time: datetime | None = Query(None, description="End acquisition time (UTC)"),
    sources: str | None = Query(None, description="Comma-separated sensor products"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description=f"Result page size (max {MAX_LIMIT})"),
    offset: int = Query(0, ge=0, description="Result page offset"),
    db: AsyncSession = Depends(get_db),
) -> StoredObservationsResponse:
    # 1. Validate temporal window if both provided
    if start_time and end_time and start_time > end_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_TIME_RANGE",
                "message": "start_time must be earlier than or equal to end_time.",
            },
        )

    # 2. Build and validate bounding box if any coordinate is specified
    bbox: BoundingBox | None = None
    has_any_coord = any(c is not None for c in (west, south, east, north))
    if has_any_coord:
        w = west if west is not None else INDIA_DEFAULT_BBOX[0]
        s = south if south is not None else INDIA_DEFAULT_BBOX[1]
        e = east if east is not None else INDIA_DEFAULT_BBOX[2]
        n = north if north is not None else INDIA_DEFAULT_BBOX[3]
        try:
            bbox = BoundingBox(west=w, south=s, east=e, north=n)
        except ValueError as ex:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": FIRMSErrorCode.INVALID_BOUNDING_BOX,
                    "message": str(ex),
                },
            ) from ex

    # 3. Parse source filter
    source_list = [s.strip() for s in sources.split(",") if s.strip()] if sources else None

    # 4. Query PostGIS via repository
    repo = ThermalObservationRepository(db)
    try:
        observations, total = await repo.query_spatial_temporal(
            bbox=bbox,
            start_time=start_time,
            end_time=end_time,
            sources=source_list,
            limit=limit,
            offset=offset,
        )
    except Exception as ex:
        logger.exception(f"PostGIS query failed: {ex}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "DATABASE_UNAVAILABLE",
                "message": f"Database query failure: {type(ex).__name__}",
            },
        ) from ex

    items = [model_to_schema(obs) for obs in observations]

    return StoredObservationsResponse(
        mode="stored",
        storage="PostGIS",
        count=len(items),
        total=total,
        limit=limit,
        offset=offset,
        bbox=bbox.to_dict() if bbox else None,
        observations=items,
    )


@router.get(
    "/{observation_id}",
    response_model=StoredObservationItem,
    summary="Get single stored observation by deterministic ID",
    description="Fetches a single thermal detection by its deterministic firms_* identifier. Returns 404 if not found.",
)
async def get_observation_by_id(
    observation_id: str,
    db: AsyncSession = Depends(get_db),
) -> StoredObservationItem:
    repo = ThermalObservationRepository(db)
    try:
        obs = await repo.get_by_id(observation_id)
    except Exception as ex:
        logger.exception(f"PostGIS lookup failed for {observation_id}: {ex}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "DATABASE_UNAVAILABLE",
                "message": f"Database lookup failure: {type(ex).__name__}",
            },
        ) from ex

    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "OBSERVATION_NOT_FOUND",
                "message": f"Observation with ID '{observation_id}' does not exist in PostGIS storage.",
            },
        )

    return model_to_schema(obs)
