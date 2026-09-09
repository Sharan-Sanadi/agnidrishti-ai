# AGNIDRISHTI API — API v1 Router

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analysis,
    classification,
    firms,
    fusion,
    hotspots,
    industrial_context,
    land_cover,
    meta,
    observations,
    persistence,
    sentinel2,
)

api_router = APIRouter()

api_router.include_router(meta.router, prefix="/meta", tags=["Meta"])
api_router.include_router(hotspots.router, prefix="/hotspots", tags=["Hotspots"])
api_router.include_router(firms.router, prefix="/firms", tags=["NASA FIRMS"])
api_router.include_router(observations.router, prefix="/observations", tags=["PostGIS Observations"])
api_router.include_router(persistence.router, tags=["Temporal Persistence"])
api_router.include_router(industrial_context.router, tags=["Industrial Context Intelligence"])
api_router.include_router(land_cover.router, tags=["Land-Cover Intelligence"])
api_router.include_router(sentinel2.router, tags=["Sentinel-2 Satellite Context"])
api_router.include_router(fusion.router, tags=["Feature Fusion Intelligence"])
api_router.include_router(classification.router, tags=["Intelligent Classification Engine"])
api_router.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
