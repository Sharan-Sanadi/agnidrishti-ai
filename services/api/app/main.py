# AGNIDRISHTI API — FastAPI Application
"""
Main application entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import logger
from app.db.session import check_postgis_readiness, close_engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")

    # Check configurations
    if not settings.is_database_configured:
        logger.warning("Database is NOT configured. Running in degraded/fixture mode.")
    if not settings.is_firms_configured:
        logger.warning("NASA FIRMS is NOT configured.")
    if not settings.is_earth_engine_configured:
        logger.warning("Google Earth Engine is NOT configured.")

    yield

    logger.info("Shutting down application...")
    await close_engine()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-enabled geospatial industrial thermal intelligence API",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS setup
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Basic health check endpoint (process liveness)."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/readiness", tags=["System"])
async def readiness_check(response: Response) -> dict[str, Any]:
    """
    Readiness probe verifying PostGIS database connectivity and version.
    Returns 200 if database and PostGIS extension are ready, 503 if unavailable.
    """
    postgis_status = await check_postgis_readiness()
    if not postgis_status.get("ready"):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unready",
            "code": "DATABASE_UNAVAILABLE",
            "service": settings.app_name,
            "database": postgis_status,
        }
    return {
        "status": "ready",
        "service": settings.app_name,
        "database": postgis_status,
    }

