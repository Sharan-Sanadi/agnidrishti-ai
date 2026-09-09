<div align="center">

# 🔥 Agnidrishti (अग्निदृष्टि)
### AI-Enabled Geospatial Industrial Thermal Intelligence & Monitoring Platform
**Smart India Hackathon 2026 • Problem Statement: SIH26162**

[![Status: Phase 6 Verified](https://img.shields.io/badge/Status-Phase%206%20Verified-00c853.svg?style=for-the-badge&logo=checkmarx)](https://github.com/Sharan-Sanadi/agnidrishti-ai)
[![SIH Problem Statement](https://img.shields.io/badge/SIH-26162-ff6d00.svg?style=for-the-badge&logo=target)](https://www.sih.gov.in/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16%20Turbopack-000000.svg?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL + PostGIS](https://img.shields.io/badge/PostGIS-3.4%20%2F%20PG16-336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgis.net)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%20Async-d71f00.svg?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org)

<br/>

**Agnidrishti** is an enterprise-grade geospatial thermal intelligence system designed to solve the critical national challenge of distinguishing legitimate industrial thermal operations (smelters, flare stacks, cement kilns, refinery units) from catastrophic industrial fires, unpermitted industrial activities, and agricultural burning.

By unifying near-real-time satellite thermal anomaly feeds (VIIRS NOAA-20 & NOAA-21 NRT) with an indexed, idempotent PostGIS spatial historical store, Agnidrishti computes PostGIS-native spatiotemporal recurrence metrics (`ST_DWithin` geography matching within 750m), strict future-leakage-safe temporal persistence, server-side OpenStreetMap (Overpass API) industrial context normalization, metric spatial proximity analysis (`ST_Distance`, `ST_Covers`), 5km coverage-gated industrial evidence classification (`STRONG`, `MODERATE`, `WEAK`, `NONE`, `UNAVAILABLE`), real ESA WorldCover 10 m 2021 v200 multi-scale circular land-cover analysis (250m, 500m, 1000m via Azimuthal Equidistant projection), and real Copernicus Sentinel-2 Level-2A BOA optical/NIR/SWIR spectral context retrieval with SCL cloud-masking, strictly prior scene discovery ($\le T_0$), and server-side True Color and SWIR Context preview generation.

</div>

---

## ⚡ Executive Summary — Phase 6 Verified

| Milestone | Capability | Verification Status |
| :--- | :--- | :---: |
| **Phase 0 — Foundation** | Next.js 16 GIS Shell, React-Leaflet, FastAPI router, Fixture Pipeline | 🟢 **Verified** |
| **Phase 1 — NASA Ingestion** | Live NOAA-20 & NOAA-21 Area API ingestion, Defensive CSV parser, Canonical DTOs | 🟢 **Verified** |
| **Phase 2 — PostGIS Storage** | Normalized PostGIS persistence, SRID 4326 Point geometry, Idempotent bulk upsert, Spatial/Temporal API | 🟢 **Verified** |
| **Phase 3 — Temporal Persistence** | PostGIS ST_DWithin(750m) spatiotemporal recurrence, 30-day historical FIRMS backfill, distinct active UTC days, coverage gating, zero-future-leakage Temporal Persistence V1 index & classification | 🟢 **Verified** |
| **Phase 4 — Industrial Context** | Server-side OpenStreetMap Overpass client, 9-category industrial taxonomy, PostGIS spatial feature store (`osm_industrial_features`), metric distance (`ST_Distance` geography), polygon containment (`ST_Covers`), 5km full-envelope coverage validation (`osm_context_coverage`), non-destructive Alembic migration, 500-batch ID API with frontend 1500-ID chunking | 🟢 **Verified** |
| **Phase 5 — Land-Cover Intelligence** | Real ESA WorldCover 10 m 2021 v200 raster integration via cloud-optimized GeoTIFFs, 11-class standard taxonomy, multi-scale circular sampling (250m, 500m, 1000m) with true AEQD projection masks (excluding rectangular window corners), 60% dominance threshold contextual classification (`CROPLAND_DOMINANT`, `TREE_COVER_DOMINANT`, `BUILT_UP_DOMINANT`, `MIXED`, etc.), PostGIS persistence (`thermal_land_cover_profiles`), and UI telemetry drawer visualization | 🟢 **Verified** |
| **Phase 6 — Sentinel-2 Satellite Context** | Real Copernicus Data Space Ecosystem (CDSE) Sentinel-2 Level-2A BOA reflectance, STAC v1 discovery, strict $\le T_0$ zero-future-leakage prior selection (30-day lookback), SCL 20m cloud masking & dataMask validation, circular AEQD metric analysis (100m, 250m, 500m), robust spectral features (NDVI, NDMI, NBR, B04/B08/B11/B12 medians/percentiles), PostGIS persistence (`thermal_sentinel_context_profiles`), True Color & SWIR Context PNG previews | 🟢 **Verified** |
| **Phase 7 — Feature Fusion** | Multi-modal fusion of temporal recurrence, industrial proximity, land-cover dominance, and spectral context into unified explainable intelligence | ⏳ **Next Phase** |

---

## 🛰️ End-to-End System Architecture

```
                                NASA FIRMS
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                    NOAA-20 NRT           NOAA-21 NRT
                    (VIIRS 375m)          (VIIRS 375m)
                         │                     │
                         └──────────┬──────────┘
                                    ▼
                    PHASE-1 ASYNC CLIENT (Reused)
                                    │
                                    ▼
                   DEFENSIVE CSV PARSER (Reused)
                     • Header-tolerant column mapping
                     • Timezone-aware UTC normalization
                     • Deterministic SHA-256 ID generation
                                    │
                                    ▼
                      CANONICAL ThermalObservation
                                    │
                                    ▼
                        PHASE-2 INGESTION SERVICE
                     • Coordinate ordering: (lng, lat)
                     • Confidence mapping (low, nominal, high)
                     • Credential sanitization from payload
                                    │
                                    ▼
                         IDEMPOTENT BULK UPSERT
                     INSERT ... ON CONFLICT (observation_id)
                     • Zero duplicates on repeated syncs
                     • Preserves first_ingested_at
                     • Increments ingestion_count
                                    │
                                    ▼
                     POSTGRESQL + POSTGIS (SRID 4326)
                      ┌─────────────┴─────────────┐
                      ▼                           ▼
                 SPATIAL INDEX               TEMPORAL INDEX
               GiST (geom Point)          (source, acq_time_utc)
                      │                           │
                      └─────────────┬─────────────┘
                                    ▼
                           GEOSPATIAL API LAYER
                      • GET /api/v1/observations (BBox / UTC)
                      • GET /api/v1/observations/{id}
                      • POST /api/v1/firms/sync
                      • GET /readiness (PostGIS Probe)
                                    │
                                    ▼
                            FASTAPI BACKEND
                                    │
                                    ▼
                          NEXT.JS 16 DASHBOARD
                                    │
                                    ▼
                             LEAFLET GIS MAP
                     • PostGIS Storage Provenance Badge
                     • Live VIIRS Thermal Hotspot Markers
                     • Comprehensive Telemetry Drawer
```

---

## 🗄️ Phase 2 — PostGIS Storage & Geospatial Normalization

Phase 2 transitions Agnidrishti from ephemeral in-memory API responses into an immutable, queryable, and auditable geospatial database.

### Core Engineering Capabilities

1. **PostgreSQL 16 + PostGIS 3.4 Containerized Infrastructure**:
   - Pinned `postgis/postgis:16-3.4` Docker service with named persistent volume `agnidrishti_postgis_data`.
   - Host-mapped port `5432:5432`, health checks, and non-root environment credential controls.

2. **Asynchronous Database Engine & Connection Pooling**:
   - Built on SQLAlchemy 2.0 async core with native `asyncpg` driver.
   - Configured with `pool_pre_ping=True`, environment-controlled pool sizes (`DB_POOL_SIZE=10`, `DB_MAX_OVERFLOW=20`), and automatic connection recycling.

3. **Production-Grade Alembic Migrations**:
   - Async migration engine (`alembic upgrade head`) strictly controlling schema evolution.
   - Enables PostGIS extension (`CREATE EXTENSION IF NOT EXISTS postgis;`).
   - Never relies on runtime `create_all()`.

4. **Authoritative PostGIS Point Geometry**:
   - Column: `geom geometry(Point, 4326)` in EPSG:4326 (WGS84).
   - **Critical GIS Coordinate Convention**: Enforces `ST_MakePoint(longitude, latitude)` — Longitude strictly mapped to X and Latitude mapped to Y.
   - Synchronized with explicit `latitude` and `longitude` numeric columns within the same transaction.

5. **Guaranteed Idempotent Bulk Upsert (Zero Duplicates)**:
   - Conflict target: `observation_id` (deterministic SHA-256 hash).
   - If an observation is ingested repeatedly:
     - Preserves original `first_ingested_at`.
     - Updates `last_seen_at = now()`.
     - Increments `ingestion_count = ingestion_count + 1`.
     - Updates mutable sensor telemetry.
     - **Database row count remains constant (zero duplicate rows).**

6. **GiST Spatial & Temporal B-Tree Indexes**:
   - `idx_thermal_observations_geom` USING GIST on `geom` for sub-millisecond bounding box intersection.
   - `idx_thermal_observations_acq_utc` on `acquisition_time_utc` for historical temporal queries.
   - Composite index `idx_thermal_obs_source_acq` on `(source_product, acquisition_time_utc)`.

7. **Ingestion Run Auditability**:
   - Persistent `ingestion_runs` table logging requested bounding box, sensors, fetched count, valid count, upserted count, and status (`completed`, `partial`, `failed`).
   - Zero credentials or authenticated URLs stored.

8. **Strict Secret Hygiene**:
   - Sanitized database URL logging (`postgresql+asyncpg://user:***@host:port/dbname`).
   - NASA FIRMS `MAP_KEY` and raw authenticated URLs are never persisted to database tables, logs, or API payloads.

---

## 🔬 Scientific Honesty & Phase Boundaries

To ensure complete scientific and technical transparency for the SIH 2026 evaluation:

| Capability | Phase | Status | Technical Description |
| :--- | :---: | :---: | :--- |
| **Satellite Hotspot Ingestion** | Phase 1 | ✅ **Live** | Ingests real VIIRS NOAA-20 & NOAA-21 Area API feeds from NASA FIRMS. |
| **PostGIS Spatial Persistence** | Phase 2 | ✅ **Live** | Normalizes detections into PostGIS Point SRID 4326 with idempotent upserts. |
| **Temporal Persistence Scoring** | Phase 3 | ✅ **Live** | Multi-day recurrence detection (ST_DWithin 750m, 30-day historical window) with Temporal Persistence V1 index & classification. |
| **Industrial Context Cross-Ref** | Phase 4 | ✅ **Live** | Proximity to OpenStreetMap industrial zones, refineries, and flare stacks (ST_Distance, ST_Covers) with 5km coverage validation. |
| **Land-Cover Context Filtering** | Phase 5 | ✅ **Live** | Real ESA WorldCover 10 m 2021 v200 multi-scale circular sampling (250m, 500m, 1000m via AEQD) with 60% dominance threshold contextual classification. |
| **Multispectral & ML Inference** | Phase 6–8 | ⏳ *Pending* | Sentinel-2 SWIR/NIR index fusion and ML fire classification belong to Phase 8. |

> [!NOTE]
> Agnidrishti strictly avoids generating synthetic classifications or premature confidence scores. Detections represent authentic satellite observations stored in PostGIS, corroborated by empirical OpenStreetMap geometries and ESA WorldCover satellite land-cover rasters.

---

## 🛠️ Database Schema Reference

### `thermal_observations`
Normalized historical satellite thermal observation catalog.

```sql
CREATE TABLE public.thermal_observations (
    observation_id          VARCHAR(64) PRIMARY KEY,      -- Deterministic firms_* SHA-256
    latitude                DOUBLE PRECISION NOT NULL,    -- WGS84 Latitude
    longitude               DOUBLE PRECISION NOT NULL,    -- WGS84 Longitude
    geom                    geometry(Point, 4326) NOT NULL, -- Authoritative PostGIS Point
    acquisition_time_utc    TIMESTAMPTZ NOT NULL,         -- Satellite acquisition timestamp
    satellite               VARCHAR(32) NOT NULL,         -- N20, N21, SNPP
    instrument              VARCHAR(32) NOT NULL,         -- VIIRS
    source_product          VARCHAR(64) NOT NULL,         -- VIIRS_NOAA20_NRT, etc.
    provider                VARCHAR(64) DEFAULT 'NASA FIRMS',
    confidence_raw          VARCHAR(32) NOT NULL,         -- Upstream confidence code ('l', 'n', 'h')
    confidence_normalized   VARCHAR(32),                  -- 'low', 'nominal', 'high'
    frp                     DOUBLE PRECISION,             -- Fire Radiative Power (MW)
    bright_ti4              DOUBLE PRECISION,             -- Brightness Temperature TI4 (K)
    bright_ti5              DOUBLE PRECISION,             -- Brightness Temperature TI5 (K)
    scan                    DOUBLE PRECISION,             -- Pixel scan resolution (km)
    track                   DOUBLE PRECISION,             -- Pixel track resolution (km)
    daynight                VARCHAR(1),                   -- 'D' (Day) or 'N' (Night)
    firms_version           VARCHAR(32),                  -- Processing version
    first_ingested_at       TIMESTAMPTZ NOT NULL,         -- Initial sync timestamp
    last_seen_at            TIMESTAMPTZ NOT NULL,         -- Most recent sync timestamp
    ingestion_count         INTEGER DEFAULT 1,            -- Physical re-observation count
    raw_payload             JSONB,                        -- Sanitized raw fields
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_obs_latitude_range CHECK (latitude >= -90.0 AND latitude <= 90.0),
    CONSTRAINT chk_obs_longitude_range CHECK (longitude >= -180.0 AND longitude <= 180.0)
);

CREATE INDEX idx_thermal_observations_geom ON public.thermal_observations USING GIST (geom);
CREATE INDEX idx_thermal_observations_acq_utc ON public.thermal_observations (acquisition_time_utc);
CREATE INDEX idx_thermal_obs_source_acq ON public.thermal_observations (source_product, acquisition_time_utc);
```

### `ingestion_runs`
Audit and reproducibility trail for satellite synchronization runs.

```sql
CREATE TABLE public.ingestion_runs (
    run_id              VARCHAR(64) PRIMARY KEY,
    provider            VARCHAR(64) DEFAULT 'NASA FIRMS',
    requested_sources   JSONB NOT NULL,
    requested_bbox      JSONB NOT NULL,
    requested_day_range INTEGER NOT NULL,
    requested_date      VARCHAR(32),
    started_at          TIMESTAMPTZ NOT NULL,
    completed_at        TIMESTAMPTZ,
    status              VARCHAR(32) NOT NULL,       -- 'running', 'completed', 'partial', 'failed'
    fetched_count       INTEGER DEFAULT 0,
    valid_count         INTEGER DEFAULT 0,
    rejected_count      INTEGER DEFAULT 0,
    upserted_count      INTEGER DEFAULT 0,
    successful_sources  JSONB DEFAULT '[]'::jsonb,
    failed_sources      JSONB DEFAULT '[]'::jsonb,
    error_summary       TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

### `thermal_land_cover_profiles`
Real ESA WorldCover 10 m 2021 v200 multi-scale metric circular land-cover analysis cache.

```sql
CREATE TABLE public.thermal_land_cover_profiles (
    observation_id              VARCHAR(64) PRIMARY KEY REFERENCES thermal_observations(observation_id) ON DELETE CASCADE,
    point_pixel_code            INTEGER,
    point_pixel_class           VARCHAR(64),
    dominance_250m_code         INTEGER,
    dominance_250m_class        VARCHAR(64),
    dominance_250m_fraction     DOUBLE PRECISION,
    dominance_500m_code         INTEGER,
    dominance_500m_class        VARCHAR(64),
    dominance_500m_fraction     DOUBLE PRECISION,
    dominance_1000m_code        INTEGER,
    dominance_1000m_class       VARCHAR(64),
    dominance_1000m_fraction    DOUBLE PRECISION,
    context_class               VARCHAR(64) NOT NULL,       -- 'CROPLAND_DOMINANT', 'TREE_COVER_DOMINANT', 'BUILT_UP_DOMINANT', 'MIXED', etc.
    coverage_status             VARCHAR(32) NOT NULL,       -- 'COMPLETE', 'PARTIAL', 'UNAVAILABLE'
    worldcover_tile             VARCHAR(16),                -- e.g. 'N12E075'
    scale_distributions         JSONB NOT NULL,             -- Pixel distributions for 250m, 500m, 1000m scales
    algorithm_version           VARCHAR(64) NOT NULL,       -- 'worldcover_v1'
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_thermal_lc_context ON public.thermal_land_cover_profiles (context_class);
CREATE INDEX idx_thermal_lc_tile ON public.thermal_land_cover_profiles (worldcover_tile);
```

---

## 🌐 API Reference

### System & Health Probes

| Endpoint | Method | Response | Description |
| :--- | :---: | :---: | :--- |
| `/health` | `GET` | `{"status": "ok"}` | Process liveness probe |
| `/readiness` | `GET` | `{"status": "ready", ...}` | Dependency readiness probe (verifies PostGIS version & connection) |

#### Sample Readiness Response:
```json
{
  "status": "ready",
  "service": "agnidrishti-api",
  "database": {
    "status": "ready",
    "ready": true,
    "database": "agnidrishti",
    "postgis_version": "3.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1",
    "target": "postgresql+asyncpg://postgres:***@localhost:5432/agnidrishti"
  }
}
```

---

### Phase 2 PostGIS Spatial & Sync Endpoints

#### 1. Synchronize NASA FIRMS into PostGIS
- **Method**: `POST`
- **Route**: `/api/v1/firms/sync`
- **Payload** (Optional):
  ```json
  {
    "west": 68.0,
    "south": 6.5,
    "east": 97.5,
    "north": 37.5,
    "days": 1,
    "sources": ["VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"],
    "force_refresh": true
  }
  ```
- **Response**:
  ```json
  {
    "status": "completed",
    "run_id": "run_a4f89d3c2b1e0755",
    "provider": "NASA FIRMS",
    "sources": ["VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"],
    "requested_bbox": {"west": 68.0, "south": 6.5, "east": 97.5, "north": 37.5},
    "day_range": 1,
    "fetched_count": 224,
    "valid_count": 224,
    "rejected_count": 0,
    "upserted_count": 224,
    "successful_sources": ["VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"],
    "failed_sources": [],
    "started_at": "2026-09-08T08:00:00Z",
    "completed_at": "2026-09-08T08:00:02Z"
  }
  ```

#### 2. Query Stored Observations from PostGIS
- **Method**: `GET`
- **Route**: `/api/v1/observations`
- **Query Parameters**:
  - `west`, `south`, `east`, `north`: Bounding box coordinates (WGS84).
  - `start_time`, `end_time`: UTC acquisition timestamp filtering.
  - `sources`: Comma-separated sensor products (`VIIRS_NOAA20_NRT,VIIRS_NOAA21_NRT`).
  - `limit`: Bounded page size (default `500`, max `2000`).
  - `offset`: Pagination offset (default `0`).
- **Response**:
  ```json
  {
    "mode": "stored",
    "storage": "PostGIS",
    "count": 224,
    "total": 224,
    "limit": 500,
    "offset": 0,
    "bbox": {"west": 68.0, "south": 6.5, "east": 97.5, "north": 37.5},
    "observations": [
      {
        "id": "firms_3eb7c881d569bc525e95",
        "latitude": 19.8923,
        "longitude": 75.3142,
        "acquisition_time_utc": "2026-09-08T07:42:00Z",
        "satellite": "N20",
        "instrument": "VIIRS",
        "source": "VIIRS_NOAA20_NRT",
        "provider": "NASA FIRMS",
        "confidence": "n",
        "confidence_normalized": "nominal",
        "frp": 14.8,
        "bright_ti4": 332.6,
        "bright_ti5": 298.1,
        "scan": 0.38,
        "track": 0.36,
        "daynight": "D",
        "firms_version": "2.0NRT",
        "first_ingested_at": "2026-09-08T08:00:01Z",
        "last_seen_at": "2026-09-08T08:00:01Z",
        "ingestion_count": 1,
        "stored_in_postgis": true,
        "geojson": {
          "type": "Point",
          "coordinates": [75.3142, 19.8923]
        }
      }
    ]
  }
  ```

#### 3. Single Observation Lookup
- **Method**: `GET`
- **Route**: `/api/v1/observations/{observation_id}`
- **Response**: Returns canonical observation or `404 OBSERVATION_NOT_FOUND`.

#### 4. Direct Phase 1 Live Endpoint (Preserved)
- **Method**: `GET`
- **Route**: `/api/v1/firms/hotspots` (direct Area API fetch without database write, preserved for debugging and baseline comparison).

---

### Phase 3 Temporal Persistence Endpoints

#### 1. Single Observation Persistence Profile
- **Method**: `GET`
- **Route**: `/api/v1/observations/{observation_id}/persistence`
- **Response**: Spatiotemporal recurrence within 750m, distinct active UTC days, and `PERSISTENT`, `RECURRING`, or `EPHEMERAL` classification.

#### 2. Batch Persistence Analysis
- **Method**: `POST`
- **Route**: `/api/v1/persistence/batch`
- **Payload**: `{"observation_ids": ["firms_..."]}` (up to 500 IDs per chunk)
- **Response**: Map of `{observation_id: PersistenceProfileResponse}`.

---

### Phase 4 Industrial Context Endpoints

#### 1. Single Observation Industrial Profile
- **Method**: `GET`
- **Route**: `/api/v1/observations/{observation_id}/industrial-context`
- **Response**: Proximity to nearest OSM industrial feature (`distance_meters`, `is_contained`, `industrial_category`, `context_class`: `STRONG`, `MODERATE`, `WEAK`, `NONE`, `UNAVAILABLE`).

#### 2. Batch Industrial Context
- **Method**: `POST`
- **Route**: `/api/v1/industrial-context/batch`
- **Payload**: `{"observation_ids": ["firms_..."]}`
- **Response**: Map of `{observation_id: IndustrialContextProfileResponse}`.

---

### Phase 5 Land-Cover Intelligence Endpoints

#### 1. Single Observation Land-Cover Profile
- **Method**: `GET`
- **Route**: `/api/v1/observations/{observation_id}/land-cover`
- **Response**: Point pixel class, circular distributions at 250m, 500m, 1000m, 60% dominance evaluation, and context classification (`CROPLAND_DOMINANT`, `TREE_COVER_DOMINANT`, `BUILT_UP_DOMINANT`, `MIXED`, etc.).

#### 2. Batch Land-Cover Profiles
- **Method**: `POST`
- **Route**: `/api/v1/land-cover/batch`
- **Payload**: `{"observation_ids": ["firms_..."]}` (up to 500 IDs per chunk)
- **Response**: Map of `{observation_id: LandCoverProfileResponse}`.

#### 3. Land-Cover Synchronize / Precompute
- **Method**: `POST`
- **Route**: `/api/v1/land-cover/sync`
- **Payload**: `{"observation_ids": [...], "force_refresh": false}`
- **Response**: `{status, total_requested, computed_count, cached_count, failed_count}`.

---

## 🚀 Quickstart & Developer Guide

### Prerequisites
- **Node.js**: `>=20.0.0`
- **Package Manager**: `pnpm` (`v9` or later)
- **Python**: `>=3.11` (managed via `uv`)
- **Docker Desktop**: For running PostgreSQL + PostGIS container

---

### Step 1: Environment Configuration

Copy the environment template:
```bash
cp .env.example .env
```

Configure `.env` with your PostGIS database connection and NASA FIRMS MAP_KEY:
```ini
# ─── PostGIS Database ───
POSTGRES_DB=agnidrishti
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agnidrishti
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT_SECONDS=30.0

# ─── NASA FIRMS API ───
# Get a free MAP_KEY: https://firms.modaps.eosdis.nasa.gov/api/map_key/
NASA_FIRMS_MAP_KEY=your_nasa_firms_map_key_here
NASA_FIRMS_DEFAULT_DAY_RANGE=1
NASA_FIRMS_TIMEOUT_SECONDS=20.0
NASA_FIRMS_CACHE_TTL_SECONDS=600

# ─── Copernicus Data Space Ecosystem (CDSE) / Sentinel-2 ───
# Obtain OAuth2 credentials at: https://dataspace.copernicus.eu/
CDSE_CLIENT_ID=your_cdse_client_id_here
CDSE_CLIENT_SECRET=your_cdse_client_secret_here
CDSE_TOKEN_URL=https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token
CDSE_SENTINEL_HUB_BASE_URL=https://sh.dataspace.copernicus.eu
CDSE_STAC_BASE_URL=https://catalogue.dataspace.copernicus.eu/stac

# ─── Frontend ───
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

### Step 2: Start PostGIS & Run Migrations

```bash
# 1. Start PostGIS container
docker compose up -d

# 2. Verify container is healthy
docker compose ps

# 3. Apply Alembic migrations
cd services/api
uv sync --extra dev
uv run alembic upgrade head
cd ../..
```

---

### Step 3: Install Frontend Dependencies

```bash
pnpm install
```

---

### Step 4: Run Development Services

Open two terminals:

**Terminal 1 — Backend (FastAPI):**
```bash
pnpm dev:api
# Swagger Docs:    http://localhost:8000/docs
# Liveness Probe:  http://localhost:8000/health
# Readiness Probe: http://localhost:8000/readiness
```

**Terminal 2 — Frontend (Next.js 16):**
```bash
pnpm dev:web
# GIS Dashboard:   http://localhost:3000
```

---

## 🛰️ Phase 6: Sentinel-2 Satellite Context (Copernicus L2A)

Agnidrishti incorporates real high-resolution optical, near-infrared (NIR), and short-wave infrared (SWIR) satellite context from the **Copernicus Data Space Ecosystem (CDSE)** Sentinel-2 Level-2A mission to contextualize NASA FIRMS thermal anomaly observations.

```
NASA FIRMS THERMAL DETECTION (Point T_0)
               │
               ▼
STAC v1 PRIOR SCENE DISCOVERY (T <= T_0, <= 30 days prior)
               │
               ▼
SCL 20m CLOUD MASKING & DATAMASK VALIDATION
               │
               ▼
SINGLE-REQUEST MULTIBAND PROCESS API (B04, B08, B11, B12, SCL, dataMask)
               │
               ▼
CIRCULAR AEQD METRIC RADII SAMPLING (100m, 250m, 500m)
               │
               ▼
SPECTRAL INDICES (NDVI, NDMI, NBR) & ROBUST MEDIANS / PERCENTILES
               │
               ▼
POSTGIS STORAGE (thermal_sentinel_context_profiles)
               │
               ▼
ANALYSIS DRAWER TELEMETRY + TRUE COLOR & SWIR CONTEXT PREVIEWS
```

### 1. Scientific Truth — Sentinel-2 Is Not A Thermal Sensor
> [!IMPORTANT]
> **Scientific Integrity Contract**: Sentinel-2 MSI is an **optical/NIR/SWIR sensor**, NOT a thermal sensor. It does **not** measure surface temperature or fire temperature. NASA FIRMS VIIRS (375m) remains the authoritative thermal anomaly sensor. Sentinel-2 contributes high-resolution 20m surface reflectance, vegetation state (NDVI), moisture context (NDMI), and burn/SWIR context (NBR). Single-scene spectral indices do not determine fire cause or fire probability.

### 2. Strict Zero-Future-Leakage Contract
- **Temporal Anchor**: Every Sentinel-2 scene search is strictly anchored to `observation.acquisition_time_utc` ($T_0$).
- **No Future Data**: Scenes acquired after $T_0$ (`scene_acquisition_time_utc > target_time_utc`) are **strictly forbidden** and rejected during candidate evaluation, even if acquired on the same calendar day.
- **Lookback Window**: Prior 30 days (`SENTINEL_LOOKBACK_DAYS = 30`). Candidate evaluation is capped at 8 nearest prior acquisitions (`SENTINEL_MAX_CANDIDATES = 8`).

### 3. SCL Cloud Masking & Quality Assessment
- **Invalid Pixels Excluded**: SCL codes `0` (NO_DATA), `1` (SATURATED/DEFECTIVE), `3` (CLOUD_SHADOW), `7` (UNCLASSIFIED/LOW_PROB), `8` (CLOUD_MEDIUM_PROB), `9` (CLOUD_HIGH_PROB), `10` (THIN_CIRRUS), and `dataMask == 0` are excluded from all spectral calculations and denominators.
- **Local Quality Tiers**:
  - `EXCELLENT`: $\ge 80\%$ valid pixels in ROI
  - `GOOD`: $\ge 60\%$ valid pixels in ROI
  - `LIMITED`: $\ge 40\%$ valid pixels in ROI
  - `CLOUD_LIMITED`: $< 40\%$ valid pixels in ROI (null indices, no fabricated zeros)

### 4. Analytical Standard & Spectral Indices
- **Resolution**: Common 20m analytical grid for B04, B08, B11, B12, and SCL.
- **Reflectance Units**: Standard Bottom-Of-Atmosphere (BOA) surface reflectance (Float32).
- **Indices with Denominator Guards**:
  - $\text{NDVI} = \frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04} + 10^{-6}}$ (Vegetation context)
  - $\text{NDMI} = \frac{\text{B08} - \text{B11}}{\text{B08} + \text{B11} + 10^{-6}}$ (Moisture context)
  - $\text{NBR} = \frac{\text{B08} - \text{B12}}{\text{B08} + \text{B12} + 10^{-6}}$ (NIR-SWIR context)

### 5. Multi-Scale Circular AEQD Metric Neighborhoods
True circular masks using local Azimuthal Equidistant projection around FIRMS coordinates at **100m**, **250m** (primary), and **500m** radii, ensuring rectangular raster corners are excluded.

### 6. Quota Safety & Production Endpoints
- `GET /api/v1/observations/{id}/sentinel-2`: Retrieve cached profile or 404.
- `POST /api/v1/sentinel-2/batch`: Read cached profiles in chunks of $\le 500$ IDs.
- `POST /api/v1/sentinel-2/sync`: Bounded remote precomputation ($\le 50$ IDs max).
- `GET /api/v1/observations/{id}/sentinel-2/preview?mode=true_color|swir_context`: Server-side rendered PNG previews with exact center crosshair overlay.

---

## 🧪 Testing & Validation Suite

Agnidrishti incorporates rigorous automated testing covering unit normalization, API contracts, and real PostGIS integration.

### Run Backend Tests & Linter
```bash
cd services/api

# Run comprehensive test suite (123 tests passing)
uv run pytest -v

# Run code linter
uv run ruff check .

cd ../..
```

### Run Frontend Verification
```bash
# Lint frontend code (0 errors)
pnpm lint:web

# Run optimized production build (TypeScript + Turbopack passing)
pnpm build:web
```

---

## 🗺️ Project Roadmap & Phase Tracking

```
[Phase 0] Foundation & GIS Shell ───────────────► 🟢 VERIFIED
[Phase 1] NASA FIRMS Real Thermal Ingestion ─────► 🟢 VERIFIED
[Phase 2] PostGIS Storage & Normalization ───────► 🟢 VERIFIED
[Phase 3] Temporal Persistence Intelligence ─────► 🟢 VERIFIED
[Phase 4] Industrial Context (OSM) ──────────────► 🟢 VERIFIED
[Phase 5] Land-Cover Intelligence (WorldCover) ─► 🟢 VERIFIED
[Phase 6] Sentinel-2 Satellite Context (CDSE) ──► 🟢 VERIFIED
[Phase 7] Geospatial Feature Fusion ─────────────► ⏳ NEXT UP
[Phase 8] ML Industrial Fire Classification ─────► ⬜ PLANNED
[Phase 9] Explainability & Attribution ──────────► ⬜ PLANNED
[Phase 10] AgniRisk Anomaly Event Scoring ───────► ⬜ PLANNED
[Phase 11] Command Center UI & Mapbox/Leaflet ───► ⬜ PLANNED
[Phase 12] Alerting & Audit Logging ─────────────► ⬜ PLANNED
[Phase 13] Historical Evaluation Benchmark ──────► ⬜ PLANNED
[Phase 14] SIH 2026 Live Demo Sandbox ───────────► ⬜ PLANNED
```

---

## 👥 Contributors

---

<div align="center">
  <b>Built with scientific integrity for Smart India Hackathon 2026 (Problem Statement: SIH26162)</b><br/>
  <i>Engineered for mission-critical industrial disaster prevention and environmental monitoring.</i>
</div>
