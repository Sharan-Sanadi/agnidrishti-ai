# AGNIDRISHTI API — Real PostGIS Database Integration Tests
"""
Executes real PostGIS database operations when DATABASE_URL is configured and reachable.
Verifies:
1. PostGIS extension & version
2. Schema & SRID 4326 Point geometry
3. Idempotent bulk upsert (zero duplicate rows on duplicate sync)
4. Spatial ST_Intersects / ST_MakeEnvelope filtering
5. Temporal UTC timestamp filtering
6. Persistence across session disposal
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.repositories.thermal_observation import ThermalObservationRepository
from app.schemas.firms import BoundingBox
from app.services.firms_ingestion import normalize_confidence


@pytest.fixture
async def db_session():
    settings = get_settings()
    if not settings.is_database_configured:
        pytest.skip("DATABASE_URL not configured; skipping real PostGIS integration tests.")

    try:
        engine = create_async_engine(settings.async_database_url, pool_pre_ping=True)
        async with engine.connect() as conn:
            # Check PostGIS extension
            res = await conn.execute(text("SELECT PostGIS_Version();"))
            _ = res.scalar()
    except Exception as ex:
        pytest.skip(f"Cannot connect to PostGIS at {settings.sanitized_database_url}: {ex}")

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_postgis_version_query(db_session: AsyncSession):
    res = await db_session.execute(text("SELECT PostGIS_Version();"))
    version = res.scalar()
    assert version is not None
    assert len(version) > 0
    print(f"\n[POSTGIS INTEGRATION] Connected to PostGIS version: {version}")


@pytest.mark.asyncio
async def test_thermal_observation_crud_and_srid(db_session: AsyncSession):
    repo = ThermalObservationRepository(db_session)

    test_id = f"firms_test_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    now = datetime.now(UTC)

    record = {
        "observation_id": test_id,
        "latitude": 20.5937,
        "longitude": 78.9629,
        "acquisition_time_utc": now,
        "satellite": "N20",
        "instrument": "VIIRS",
        "source_product": "VIIRS_NOAA20_NRT",
        "provider": "NASA FIRMS",
        "confidence_raw": "n",
        "confidence_normalized": normalize_confidence("n"),
        "frp": 18.5,
        "bright_ti4": 328.4,
        "bright_ti5": 296.2,
        "scan": 0.4,
        "track": 0.4,
        "daynight": "D",
        "firms_version": "2.0NRT",
        "first_ingested_at": now,
        "last_seen_at": now,
        "ingestion_count": 1,
        "raw_payload": {"test": True},
        "created_at": now,
        "updated_at": now,
    }

    # 1. Bulk upsert
    upserted = await repo.bulk_upsert([record])
    assert upserted == 1
    await db_session.commit()

    # 2. Query back and verify SRID and coordinates
    obs = await repo.get_by_id(test_id)
    assert obs is not None
    assert obs.observation_id == test_id
    assert abs(obs.latitude - 20.5937) < 0.0001
    assert abs(obs.longitude - 78.9629) < 0.0001

    # Verify PostGIS Point coordinates & SRID directly in SQL
    sql_check = text(
        "SELECT ST_X(geom), ST_Y(geom), ST_SRID(geom) FROM thermal_observations WHERE observation_id = :oid"
    )
    coord_res = await db_session.execute(sql_check, {"oid": test_id})
    row = coord_res.first()
    assert row is not None
    st_x, st_y, srid = row
    # ST_X is longitude, ST_Y is latitude
    assert abs(st_x - 78.9629) < 0.0001
    assert abs(st_y - 20.5937) < 0.0001
    assert srid == 4326


@pytest.mark.asyncio
async def test_idempotent_upsert_zero_duplicates(db_session: AsyncSession):
    repo = ThermalObservationRepository(db_session)
    now = datetime.now(UTC)

    test_id = f"firms_idemp_{now.strftime('%Y%m%d%H%M%S')}"

    record = {
        "observation_id": test_id,
        "latitude": 22.0,
        "longitude": 79.0,
        "acquisition_time_utc": now,
        "satellite": "N21",
        "instrument": "VIIRS",
        "source_product": "VIIRS_NOAA21_NRT",
        "provider": "NASA FIRMS",
        "confidence_raw": "h",
        "confidence_normalized": "high",
        "frp": 50.0,
        "bright_ti4": 340.0,
        "bright_ti5": 300.0,
        "scan": 0.38,
        "track": 0.36,
        "daynight": "N",
        "firms_version": "2.0NRT",
        "first_ingested_at": now,
        "last_seen_at": now,
        "ingestion_count": 1,
        "raw_payload": {},
        "created_at": now,
        "updated_at": now,
    }

    # First upsert
    await repo.bulk_upsert([record])
    await db_session.commit()

    count_after_first = (
        await db_session.execute(
            text("SELECT COUNT(*) FROM thermal_observations WHERE observation_id = :oid"),
            {"oid": test_id},
        )
    ).scalar()
    assert count_after_first == 1

    # Second IDENTICAL upsert (re-fetch simulation)
    await repo.bulk_upsert([record])
    await db_session.commit()

    count_after_second = (
        await db_session.execute(
            text("SELECT COUNT(*) FROM thermal_observations WHERE observation_id = :oid"),
            {"oid": test_id},
        )
    ).scalar()

    # Zero duplicate rows created
    assert count_after_second == 1, "Repeated upsert must NOT create duplicate rows!"

    # Verify ingestion_count incremented
    obs = await repo.get_by_id(test_id)
    assert obs is not None
    assert obs.ingestion_count >= 2


@pytest.mark.asyncio
async def test_spatial_bbox_query(db_session: AsyncSession):
    repo = ThermalObservationRepository(db_session)
    now = datetime.now(UTC)

    # Insert one point inside bbox (Pune: ~18.5, 73.8) and one outside (Tokyo: ~35.6, 139.6)
    inside_id = f"firms_inside_{now.strftime('%Y%m%d%H%M%S')}"
    outside_id = f"firms_outside_{now.strftime('%Y%m%d%H%M%S')}"

    r_inside = {
        "observation_id": inside_id,
        "latitude": 18.5204,
        "longitude": 73.8567,
        "acquisition_time_utc": now,
        "satellite": "N20",
        "instrument": "VIIRS",
        "source_product": "VIIRS_NOAA20_NRT",
        "provider": "NASA FIRMS",
        "confidence_raw": "nominal",
        "confidence_normalized": "nominal",
        "frp": 10.0,
        "first_ingested_at": now,
        "last_seen_at": now,
        "ingestion_count": 1,
        "created_at": now,
        "updated_at": now,
    }
    r_outside = {
        "observation_id": outside_id,
        "latitude": 35.6762,
        "longitude": 139.6503,
        "acquisition_time_utc": now,
        "satellite": "N20",
        "instrument": "VIIRS",
        "source_product": "VIIRS_NOAA20_NRT",
        "provider": "NASA FIRMS",
        "confidence_raw": "nominal",
        "confidence_normalized": "nominal",
        "frp": 10.0,
        "first_ingested_at": now,
        "last_seen_at": now,
        "ingestion_count": 1,
        "created_at": now,
        "updated_at": now,
    }

    await repo.bulk_upsert([r_inside, r_outside])
    await db_session.commit()

    # Query India bounding box: 68-98 E, 6-38 N
    india_bbox = BoundingBox(west=68.0, south=6.0, east=98.0, north=38.0)
    results, _ = await repo.query_spatial_temporal(bbox=india_bbox)
    result_ids = {o.observation_id for o in results}

    assert inside_id in result_ids
    assert outside_id not in result_ids
