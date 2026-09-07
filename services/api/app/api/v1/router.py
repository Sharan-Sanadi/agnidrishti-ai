# AGNIDRISHTI API — API v1 Router

from fastapi import APIRouter

from app.api.v1.endpoints import analysis, hotspots, meta

api_router = APIRouter()

api_router.include_router(meta.router, prefix="/meta", tags=["Meta"])
api_router.include_router(hotspots.router, prefix="/hotspots", tags=["Hotspots"])
api_router.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
