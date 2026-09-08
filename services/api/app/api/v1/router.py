# AGNIDRISHTI API — API v1 Router

from fastapi import APIRouter

from app.api.v1.endpoints import analysis, firms, hotspots, meta, observations

api_router = APIRouter()

api_router.include_router(meta.router, prefix="/meta", tags=["Meta"])
api_router.include_router(hotspots.router, prefix="/hotspots", tags=["Hotspots"])
api_router.include_router(firms.router, prefix="/firms", tags=["NASA FIRMS"])
api_router.include_router(observations.router, prefix="/observations", tags=["PostGIS Observations"])
api_router.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
