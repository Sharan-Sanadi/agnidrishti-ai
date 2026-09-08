# AGNIDRISHTI API — Shared Pytest Fixtures
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


@pytest.fixture
async def db_session():
    """Provides a real PostGIS AsyncSession for integration tests when DB is reachable."""
    settings = get_settings()
    if not settings.is_database_configured:
        pytest.skip("DATABASE_URL not configured; skipping real PostGIS integration tests.")

    try:
        engine = create_async_engine(settings.async_database_url, pool_pre_ping=True)
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT PostGIS_Version();"))
            _ = res.scalar()
    except Exception as ex:
        pytest.skip(f"Cannot connect to PostGIS at {settings.sanitized_database_url}: {ex}")

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            # Prevent test data leakage into development/runtime database
            try:
                await session.execute(text(
                    "DELETE FROM thermal_observations WHERE observation_id LIKE 'firms_test_%' "
                    "OR observation_id LIKE 'firms_idemp_%' "
                    "OR observation_id LIKE 'firms_inside_%' "
                    "OR observation_id LIKE 'firms_outside_%' "
                    "OR observation_id LIKE 'firms_near%' "
                    "OR observation_id LIKE 'firms_far%';"
                ))
                await session.commit()
            except Exception:
                await session.rollback()

    await engine.dispose()
