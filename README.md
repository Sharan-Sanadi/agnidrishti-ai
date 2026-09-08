<div align="center">

# 👑 SAGAR NM

# 🔥 Agnidrishti (अग्निदृष्टि)
### AI-Enabled Geospatial Industrial Thermal Intelligence & Monitoring Platform
**Smart India Hackathon 2026 • Problem Statement: SIH26162**

[![Status: Phase 3 Verified](https://img.shields.io/badge/Status-Phase%203%20Verified-00c853.svg?style=for-the-badge&logo=checkmarx)](https://github.com/Sharan-Sanadi/agnidrishti-ai)
[![SIH Problem Statement](https://img.shields.io/badge/SIH-26162-ff6d00.svg?style=for-the-badge&logo=target)](https://www.sih.gov.in/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16%20Turbopack-000000.svg?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL + PostGIS](https://img.shields.io/badge/PostGIS-3.4%20%2F%20PG16-336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgis.net)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%20Async-d71f00.svg?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org)

<br/>

**Agnidrishti** is an enterprise-grade geospatial thermal intelligence system designed to solve the critical national challenge of distinguishing legitimate industrial thermal operations (smelters, flare stacks, cement kilns, refinery units) from catastrophic industrial fires, unpermitted industrial activities, and agricultural burning.

By unifying near-real-time satellite thermal anomaly feeds (VIIRS NOAA-20 & NOAA-21 NRT) with an indexed, idempotent PostGIS spatial historical store, Agnidrishti computes PostGIS-native spatiotemporal recurrence metrics (`ST_DWithin` geography matching within 750m), coverage-aware dataset history verification, and strict future-leakage-safe temporal persistence classification.

</div>

---

## ⚡ Executive Summary — Phase 3 Verified

| Milestone | Capability | Verification Status |
| :--- | :--- | :---: |
| **Phase 0 — Foundation** | Next.js 16 GIS Shell, React-Leaflet, FastAPI router, Fixture Pipeline | 🟢 **Verified** |
| **Phase 1 — NASA Ingestion** | Live NOAA-20 & NOAA-21 Area API ingestion, Defensive CSV parser, Canonical DTOs | 🟢 **Verified** |
| **Phase 2 — PostGIS Storage** | Normalized PostGIS persistence, SRID 4326 Point geometry, Idempotent bulk upsert, Spatial/Temporal API | 🟢 **Verified** |
| **Phase 3 — Temporal Persistence** | PostGIS ST_DWithin(750m) spatiotemporal recurrence, 30-day historical FIRMS backfill, distinct active UTC days, coverage gating, zero-future-leakage Temporal Persistence V1 index & classification | 🟢 **Verified** |
| **Phase 4 — Industrial Context** | OpenStreetMap (OSM) infrastructure cross-referencing & proximity tagging | ⏳ **Next Phase** |

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
| **Temporal Persistence Scoring** | Phase 3 | ⏳ *Pending* | Multi-day recurrence detection (e.g. 7/30/90-day persistence) will be computed in Phase 3. |
| **Industrial Context Cross-Ref** | Phase 4 | ⏳ *Pending* | Proximity to OpenStreetMap industrial zones, refineries, and factories belongs to Phase 4. |
| **Land-Cover Context Filtering** | Phase 5 | ⏳ *Pending* | Dynamic World / ESA WorldCover baseline classification belongs to Phase 5. |
| **Multispectral & ML Inference** | Phase 6–8 | ⏳ *Pending* | Sentinel-2 SWIR/NIR index fusion and ML fire classification belong to Phase 8. |

> [!NOTE]
> Agnidrishti strictly avoids generating synthetic classifications or premature confidence scores. Detections currently represent authentic satellite observations stored in PostGIS.

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

## 🧪 Testing & Validation Suite

Agnidrishti incorporates rigorous automated testing covering unit normalization, API contracts, and real PostGIS integration.

### Run Backend Tests & Linter
```bash
cd services/api

# Run comprehensive test suite
uv run pytest -v

# Run code linter
uv run ruff check .

cd ../..
```

### Run Frontend Verification
```bash
# Lint frontend code
pnpm lint:web

# Run optimized production build
pnpm build:web
```

---

## 🗺️ Project Roadmap & Phase Tracking

```
[Phase 0] Foundation & GIS Shell ───────────────► 🟢 VERIFIED
[Phase 1] NASA FIRMS Real Thermal Ingestion ─────► 🟢 VERIFIED
[Phase 2] PostGIS Storage & Normalization ───────► 🟢 VERIFIED
[Phase 3] Temporal Persistence Intelligence ─────► 🟢 VERIFIED
[Phase 4] Industrial Context (OSM) ──────────────► ⏳ NEXT UP
[Phase 5] Land-Cover Baseline (Dynamic World) ───► ⬜ PLANNED
[Phase 6] Sentinel-2 MSI Optical Cross-Ref ──────► ⬜ PLANNED
[Phase 7] Geospatial Feature Fusion ─────────────► ⬜ PLANNED
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

# <div align="center">👑 SAGAR NM</div>

---

<div align="center">
  <b>Built with scientific integrity for Smart India Hackathon 2026 (Problem Statement: SIH26162)</b><br/>
  <i>Engineered for mission-critical industrial disaster prevention and environmental monitoring.</i>
</div>
