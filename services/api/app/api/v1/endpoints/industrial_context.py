# AGNIDRISHTI API — Industrial Context & OSM Endpoints
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.osm_context_coverage import OSMContextCoverageModel
from app.db.models.osm_industrial_feature import OSMIndustrialFeatureModel
from app.db.session import get_db
from app.schemas.industrial import (
    BatchIndustrialContextRequest,
    BatchIndustrialContextResponse,
    IndustrialContextProfileDTO,
    OSMFeatureCollection,
    OSMFeatureGeoJSON,
    OSMSyncRequest,
    OSMSyncResponse,
)
from app.services.industrial_context_service import (
    DEFAULT_INDUSTRIAL_RADIUS_M,
    IndustrialContextService,
)

router = APIRouter(tags=["Industrial Context Intelligence"])


@router.get(
    "/observations/{observation_id}/industrial-context",
    response_model=IndustrialContextProfileDTO,
    summary="Get Industrial Context Profile for Observation",
)
async def get_observation_industrial_context(
    observation_id: str,
    radius_m: float = Query(DEFAULT_INDUSTRIAL_RADIUS_M, ge=100.0, le=20000.0),
    db: AsyncSession = Depends(get_db),
) -> IndustrialContextProfileDTO:
    """
    Retrieve or compute the industrial context profile for a single canonical thermal observation.
    Executes metric PostGIS spatial calculations and 5km full envelope coverage verification.
    """
    service = IndustrialContextService(db)
    try:
        return await service.get_or_compute_profile(observation_id, radius_m)
    except Exception as ex:
        logger.error(f"Failed to fetch industrial context for observation {observation_id}: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate industrial context profile: {str(ex)}",
        ) from ex


@router.post(
    "/industrial-context/batch",
    response_model=BatchIndustrialContextResponse,
    summary="Batch Get Industrial Context Profiles",
)
async def batch_get_industrial_context(
    body: BatchIndustrialContextRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchIndustrialContextResponse:
    """
    Compute or fetch industrial context profiles for a batch of observation IDs.
    Enforces maximum batch limit of 500 observation IDs per request.
    """
    if len(body.observation_ids) > 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Batch request exceeds maximum limit of 500 observation IDs per request",
        )

    service = IndustrialContextService(db)
    profiles: dict[str, IndustrialContextProfileDTO] = {}

    for obs_id in body.observation_ids:
        try:
            profile = await service.get_or_compute_profile(obs_id)
            profiles[obs_id] = profile
        except Exception as ex:
            logger.warning(f"Error computing industrial profile for {obs_id}: {ex}")

    return BatchIndustrialContextResponse(
        total_requested=len(body.observation_ids),
        profiles=profiles,
    )


@router.post(
    "/osm/industrial/sync",
    response_model=OSMSyncResponse,
    summary="Sync Bounded OpenStreetMap Industrial Features",
)
async def sync_osm_industrial_features(
    body: OSMSyncRequest,
    db: AsyncSession = Depends(get_db),
) -> OSMSyncResponse:
    """
    Execute server-side Overpass API query for a bounded spatial bounding box.
    Normalizes features into PostGIS store and updates spatial coverage metadata.
    """
    service = IndustrialContextService(db)
    try:
        coverage_rec = await service.sync_osm_bbox(
            south=body.south,
            west=body.west,
            north=body.north,
            east=body.east,
            force_refresh=body.force_refresh,
        )
        return OSMSyncResponse(
            coverage_id=coverage_rec.coverage_id,
            status=coverage_rec.status,  # type: ignore
            feature_count=coverage_rec.feature_count,
            features_ingested=coverage_rec.feature_count,
            completed_at=coverage_rec.completed_at,
            expires_at=coverage_rec.expires_at,
        )
    except Exception as ex:
        logger.error(f"OSM sync failed for bounding box ({body.south}, {body.west}, {body.north}, {body.east}): {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OSM industrial feature sync failed: {str(ex)}",
        ) from ex


@router.get(
    "/osm/industrial/features",
    response_model=OSMFeatureCollection,
    summary="Get Stored GeoJSON Industrial Features",
)
async def get_osm_industrial_features(
    west: float = Query(-180.0, ge=-180.0, le=180.0),
    south: float = Query(-90.0, ge=-90.0, le=90.0),
    east: float = Query(180.0, ge=-180.0, le=180.0),
    north: float = Query(90.0, ge=-90.0, le=90.0),
    limit: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
) -> OSMFeatureCollection:
    """
    Retrieve stored PostGIS OSM industrial features as a GeoJSON FeatureCollection
    within a bounded spatial window.
    """
    stmt = (
        select(
            OSMIndustrialFeatureModel.osm_uid,
            OSMIndustrialFeatureModel.name,
            OSMIndustrialFeatureModel.operator,
            OSMIndustrialFeatureModel.feature_category,
            OSMIndustrialFeatureModel.geometry_quality,
            OSMIndustrialFeatureModel.thermal_relevance,
            OSMIndustrialFeatureModel.tags,
            func.ST_AsGeoJSON(OSMIndustrialFeatureModel.geom).label("geojson_str"),
        )
        .where(
            func.ST_Within(
                OSMIndustrialFeatureModel.geom,
                func.ST_MakeEnvelope(west, south, east, north, 4326),
            )
        )
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.fetchall()

    features: list[OSMFeatureGeoJSON] = []
    for r in rows:
        geom_dict = json.loads(r.geojson_str) if r.geojson_str else {"type": "Point", "coordinates": [0, 0]}
        props = {
            "osm_uid": r.osm_uid,
            "name": r.name,
            "operator": r.operator,
            "feature_category": r.feature_category,
            "geometry_quality": r.geometry_quality,
            "thermal_relevance": r.thermal_relevance,
            "tags": r.tags,
        }
        features.append(OSMFeatureGeoJSON(id=r.osm_uid, geometry=geom_dict, properties=props))

    return OSMFeatureCollection(features=features, total_count=len(features))


@router.get(
    "/osm/industrial/coverage",
    summary="Get OpenStreetMap Coverage Region Telemetry",
)
async def get_osm_coverage_telemetry(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Retrieve telemetry stats for stored OpenStreetMap coverage regions and features.
    """
    cov_stmt = select(func.count(OSMContextCoverageModel.id))
    cov_res = await db.execute(cov_stmt)
    total_coverage_regions = cov_res.scalar() or 0

    feat_stmt = select(func.count(OSMIndustrialFeatureModel.id))
    feat_res = await db.execute(feat_stmt)
    total_stored_features = feat_res.scalar() or 0

    cat_stmt = select(
        OSMIndustrialFeatureModel.feature_category,
        func.count(OSMIndustrialFeatureModel.id),
    ).group_by(OSMIndustrialFeatureModel.feature_category)
    cat_res = await db.execute(cat_stmt)
    category_counts = {r[0]: r[1] for r in cat_res.fetchall()}

    return {
        "total_coverage_regions": total_coverage_regions,
        "total_stored_features": total_stored_features,
        "category_inventory": category_counts,
        "attribution": "© OpenStreetMap contributors",
    }
