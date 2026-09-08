# AGNIDRISHTI API — Async Database Session Management
"""
Async database engine and session management.
Ensures connection pooling, health checks, and secure credential handling.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.logging import logger

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the singleton async SQLAlchemy engine.
    Uses pool_pre_ping and environment-driven pool settings.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.async_database_url
        if not url:
            raise RuntimeError(
                "DATABASE_URL is not configured. PostGIS operations require a configured database connection."
            )

        logger.info(f"Initializing async database engine with target: {settings.sanitized_database_url}")

        _engine = create_async_engine(
            url,
            pool_pre_ping=True,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout_seconds,
            echo=False,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the singleton session factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an async database session per request.
    Rolls back on unhandled exception and automatically closes on completion.
    Raises HTTP 503 DATABASE_UNAVAILABLE if database is unconfigured.
    """
    settings = get_settings()
    if not settings.is_database_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "DATABASE_UNAVAILABLE",
                "message": "Database is not configured. DATABASE_URL must be provided for PostGIS operations.",
            },
        )

    try:
        session_maker = get_session_factory()
    except Exception as ex:
        logger.error(f"Failed to initialize database engine: {ex}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "DATABASE_UNAVAILABLE",
                "message": f"Database initialization failed: {str(ex)}",
            },
        ) from ex

    async with session_maker() as session:
        try:
            yield session
        except HTTPException:
            raise
        except Exception:
            await session.rollback()
            raise


async def check_postgis_readiness() -> dict[str, Any]:
    """
    Verify PostgreSQL connectivity and PostGIS extension installation.
    Executes 'SELECT PostGIS_Version();' and checks current database.
    Never exposes credentials.
    """
    settings = get_settings()
    if not settings.is_database_configured:
        return {
            "status": "unconfigured",
            "ready": False,
            "error": "DATABASE_URL is not set",
        }

    try:
        engine = get_engine()
        async with engine.connect() as conn:
            # Query PostGIS version and current database
            result = await conn.execute(text("SELECT PostGIS_Version(), current_database();"))
            row = result.first()
            if row:
                postgis_version = row[0]
                current_db = row[1]
                return {
                    "status": "ready",
                    "ready": True,
                    "database": current_db,
                    "postgis_version": postgis_version,
                    "target": settings.sanitized_database_url,
                }
            return {
                "status": "unknown",
                "ready": False,
                "error": "Query returned no results",
            }
    except Exception as ex:
        logger.error(f"PostGIS readiness check failed: {type(ex).__name__} - {ex}")
        return {
            "status": "unhealthy",
            "ready": False,
            "error": f"{type(ex).__name__}: {str(ex)}",
            "target": settings.sanitized_database_url,
        }


async def close_engine() -> None:
    """Close async database engine pool on application shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        logger.info("Disposing database connection pool...")
        await _engine.dispose()
        _engine = None
        _session_factory = None
