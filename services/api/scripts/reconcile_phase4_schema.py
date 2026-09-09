import asyncio

from sqlalchemy import text

from app.db.session import get_engine


async def reconcile():
    engine = get_engine()
    async with engine.begin() as conn:
        print("--- RECONCILING PHASE 4 DATABASE SCHEMA ---")

        # 1. Drop old industrial_context_profiles table if it exists
        print("Checking industrial_context_profiles...")
        table_check = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='industrial_context_profiles';"
        ))
        if table_check.fetchone():
            print("Found old industrial_context_profiles table. Dropping table safely (0 computed records)...")
            await conn.execute(text("DROP TABLE industrial_context_profiles CASCADE;"))
            print("Dropped industrial_context_profiles successfully.")

        # 2. Reconcile osm_industrial_features table
        print("Checking osm_industrial_features...")
        table_check = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='osm_industrial_features';"
        ))
        if table_check.fetchone():
            col_check = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='osm_industrial_features' AND column_name='id';"
            ))
            if not col_check.fetchone():
                print("Reconciling osm_industrial_features: Adding id SERIAL primary key...")
                await conn.execute(text("ALTER TABLE osm_industrial_features DROP CONSTRAINT IF EXISTS pk_osm_industrial_features;"))
                await conn.execute(text("ALTER TABLE osm_industrial_features DROP CONSTRAINT IF EXISTS osm_industrial_features_pkey;"))
                await conn.execute(text("ALTER TABLE osm_industrial_features ADD COLUMN id SERIAL PRIMARY KEY;"))
                await conn.execute(text("ALTER TABLE osm_industrial_features ADD CONSTRAINT uq_osm_industrial_features_osm_uid UNIQUE (osm_uid);"))
                await conn.execute(text("UPDATE osm_industrial_features SET source_provider='OVERPASS_API' WHERE source_provider='OpenStreetMap / Overpass';"))
                print("osm_industrial_features reconciled successfully.")

        # 3. Reconcile osm_context_coverage table
        print("Checking osm_context_coverage...")
        table_check = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='osm_context_coverage';"
        ))
        if table_check.fetchone():
            col_check = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='osm_context_coverage' AND column_name='id';"
            ))
            if not col_check.fetchone():
                print("Reconciling osm_context_coverage: Adding id SERIAL primary key and bbox_geom...")
                await conn.execute(text("ALTER TABLE osm_context_coverage DROP CONSTRAINT IF EXISTS pk_osm_context_coverage;"))
                await conn.execute(text("ALTER TABLE osm_context_coverage DROP CONSTRAINT IF EXISTS osm_context_coverage_pkey;"))
                await conn.execute(text("ALTER TABLE osm_context_coverage ADD COLUMN id SERIAL PRIMARY KEY;"))
                await conn.execute(text("ALTER TABLE osm_context_coverage ADD CONSTRAINT uq_osm_context_coverage_coverage_id UNIQUE (coverage_id);"))
                await conn.execute(text("ALTER TABLE osm_context_coverage ADD COLUMN bbox_geom geometry(Polygon,4326);"))
                await conn.execute(text(
                    "UPDATE osm_context_coverage SET bbox_geom = ST_MakeEnvelope(west, south, east, north, 4326) WHERE bbox_geom IS NULL;"
                ))
                await conn.execute(text("ALTER TABLE osm_context_coverage ALTER COLUMN bbox_geom SET NOT NULL;"))
                await conn.execute(text("ALTER TABLE osm_context_coverage DROP COLUMN IF EXISTS west;"))
                await conn.execute(text("ALTER TABLE osm_context_coverage DROP COLUMN IF EXISTS south;"))
                await conn.execute(text("ALTER TABLE osm_context_coverage DROP COLUMN IF EXISTS east;"))
                await conn.execute(text("ALTER TABLE osm_context_coverage DROP COLUMN IF EXISTS north;"))
                await conn.execute(text("ALTER TABLE osm_context_coverage DROP COLUMN IF EXISTS details;"))
                print("osm_context_coverage reconciled successfully.")

        print("--- PHASE 4 SCHEMA RECONCILIATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(reconcile())
