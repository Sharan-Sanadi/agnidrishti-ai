# AGNIDRISHTI API — NASA FIRMS Endpoints
"""
Production endpoints for NASA FIRMS satellite thermal anomaly ingestion.

Routes:
- GET /api/v1/firms/hotspots: Fetch validated thermal detections for bounding box
- GET /api/v1/firms/availability: Check preflight data availability
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.constants import DEFAULT_FIRMS_SENSORS, INDIA_DEFAULT_BBOX, FIRMSErrorCode
from app.core.logging import logger
from app.providers.firms import (
    FIRMSClient,
    FIRMSException,
    get_firms_client,
)
from app.schemas.firms import (
    BoundingBox,
    FIRMSAvailabilityResponse,
    FIRMSHotspotsResponse,
)

router = APIRouter()


@router.get(
    "/hotspots",
    response_model=FIRMSHotspotsResponse,
    summary="Fetch live NASA FIRMS thermal anomaly observations",
    description="Fetches real satellite thermal detections (VIIRS NOAA-20 & NOAA-21 NRT) using official NASA FIRMS Area API.",
)
async def get_firms_hotspots(
    west: float | None = Query(None, description="West longitude (-180 to 180)"),
    south: float | None = Query(None, description="South latitude (-90 to 90)"),
    east: float | None = Query(None, description="East longitude (-180 to 180)"),
    north: float | None = Query(None, description="North latitude (-90 to 90)"),
    days: int = Query(1, ge=1, le=5, description="Day range (1-5)"),
    sources: str | None = Query(
        None,
        description="Comma-separated sensor feeds. Default: VIIRS_NOAA20_NRT,VIIRS_NOAA21_NRT",
    ),
    date: str | None = Query(None, description="Acquisition date in YYYY-MM-DD format (optional)"),
    force_refresh: bool = Query(False, description="Bypass in-memory cache"),
    client: FIRMSClient = Depends(get_firms_client),
) -> FIRMSHotspotsResponse:
    # Use India default bounding box if coordinates not provided
    w = west if west is not None else INDIA_DEFAULT_BBOX[0]
    s = south if south is not None else INDIA_DEFAULT_BBOX[1]
    e = east if east is not None else INDIA_DEFAULT_BBOX[2]
    n = north if north is not None else INDIA_DEFAULT_BBOX[3]

    try:
        bbox = BoundingBox(west=w, south=s, east=e, north=n)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": FIRMSErrorCode.INVALID_BOUNDING_BOX,
                "message": str(val_err),
            },
        ) from val_err

    # Parse sources
    if sources:
        source_list = [s.strip() for s in sources.split(",") if s.strip()]
    else:
        source_list = [s.value for s in DEFAULT_FIRMS_SENSORS]

    try:
        response = await client.get_hotspots(
            bbox=bbox,
            day_range=days,
            sources=source_list,
            date=date,
            force_refresh=force_refresh,
        )
        return response
    except FIRMSException as ex:
        logger.error(f"FIRMS ingestion error [{ex.code}]: {ex.message}")
        raise HTTPException(
            status_code=ex.status_code,
            detail={
                "code": ex.code,
                "message": ex.message,
            },
        ) from ex
    except Exception as ex:
        logger.exception(f"Unexpected error during FIRMS ingestion: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": FIRMSErrorCode.FIRMS_UPSTREAM_ERROR,
                "message": f"Unexpected ingestion error: {str(ex)}",
            },
        ) from ex


@router.get(
    "/availability",
    response_model=FIRMSAvailabilityResponse,
    summary="Check NASA FIRMS sensor data availability",
    description="Preflight check verifying MAP_KEY authentication and latest data range from NASA.",
)
async def get_firms_availability(
    source: str = Query("VIIRS_NOAA20_NRT", description="Sensor to query availability for"),
    client: FIRMSClient = Depends(get_firms_client),
) -> FIRMSAvailabilityResponse:
    try:
        return await client.get_data_availability(source=source)
    except FIRMSException as ex:
        raise HTTPException(
            status_code=ex.status_code,
            detail={
                "code": ex.code,
                "message": ex.message,
            },
        ) from ex
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": FIRMSErrorCode.FIRMS_UPSTREAM_ERROR,
                "message": f"Unexpected availability check error: {str(ex)}",
            },
        ) from ex
