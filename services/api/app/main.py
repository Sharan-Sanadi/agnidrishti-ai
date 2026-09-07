# AGNIDRISHTI API — FastAPI Application
"""
Main application entry point.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-enabled geospatial industrial thermal intelligence API",
    docs_url="/docs",
    openapi_url="/openapi.json",
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
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.on_event("startup")
async def startup_event() -> None:
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")

    # Check configurations
    if not settings.is_database_configured:
        logger.warning("Database is NOT configured. Running in degraded/fixture mode.")
    if not settings.is_firms_configured:
        logger.warning("NASA FIRMS is NOT configured.")
    if not settings.is_earth_engine_configured:
        logger.warning("Google Earth Engine is NOT configured.")

