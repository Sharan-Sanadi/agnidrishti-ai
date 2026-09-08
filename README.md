<div align="center">
  
# 🔥 Agnidrishti (अग्निदृष्टि)
**AI-Enabled Geospatial Industrial Thermal Intelligence & Monitoring System**

[![Status](https://img.shields.io/badge/Status-Phase%202%20Verified-success.svg)](#)
[![Current Phase](https://img.shields.io/badge/Current%20Phase-Phase%202%20(PostGIS%20Storage)-blue.svg)](#)
[![SIH](https://img.shields.io/badge/SIH-26162-orange.svg)](#)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016-black?logo=next.js)](#)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](#)
[![PostGIS](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20PostGIS-336791?logo=postgresql)](#)

Agnidrishti is a cutting-edge geospatial thermal-intelligence platform engineered for **Smart India Hackathon 2026 (Problem Statement SIH26162)**.

Going beyond basic thermal hotspot visualization, Agnidrishti ingests near-real-time satellite thermal anomaly feeds, normalizes and persists them in a high-performance PostGIS historical store, and contextualizes detections with temporal, industrial, land-cover, and multispectral intelligence.

</div>

---

## 📖 Core Product Principle

Agnidrishti functions as the intelligence and persistence layer over raw satellite thermal detections:

```
                  NASA FIRMS
                      │
           ┌──────────┴──────────┐
           │                     │
      NOAA-20                NOAA-21
           │                     │
           └──────────┬──────────┘
                      ▼
             PHASE-1 FIRMS CLIENT
                      │
                      ▼
            DEFENSIVE CSV PARSER
                      │
                      ▼
         CANONICAL THERMAL OBSERVATION
                      │
                      ▼
             PHASE-2 INGESTION SERVICE
                      │
                      ▼
             IDEMPOTENT BULK UPSERT
                      │
                      ▼
            POSTGRESQL + POSTGIS (SRID 4326)
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
    SPATIAL QUERIES          TEMPORAL QUERIES
          │                       │
          └───────────┬───────────┘
                      ▼
                   FASTAPI
                      │
                      ▼
                   NEXT.JS
                      │
                      ▼
                  LEAFLET GIS
```

---

## 🛰️ Phase 1 — NASA FIRMS Thermal Ingestion (Verified)

Phase 1 establishes the production-grade, zero-runtime-dummy-data satellite ingestion pipeline using official **NASA FIRMS Area API**.

### Primary Sensor Feeds
- **VIIRS NOAA-20 NRT (`VIIRS_NOAA20_NRT`)**: Primary daytime and nighttime VIIRS 375m thermal anomaly product.
- **VIIRS NOAA-21 NRT (`VIIRS_NOAA21_NRT`)**: Primary VIIRS thermal detection product operating in complementary orbital track.

---

## 🗄️ Phase 2 — PostGIS Storage & Normalization (Completed & Verified)

Phase 2 transforms Agnidrishti from transient API responses into an immutable, reproducible, historical geospatial repository.

### What Phase 2 DOES Implement
- ✅ **PostgreSQL + PostGIS Persistence**: Dedicated container environment (`docker-compose.yml`) with pinned `postgis/postgis:16-3.4` and persistent named volume `agnidrishti_postgis_data`.
- ✅ **SQLAlchemy 2.x Async ORM**: Full async driver stack (`asyncpg`) with connection pooling (`pool_pre_ping=True`, configurable pool sizes).
- ✅ **Alembic Database Migrations**: Controlled schema lifecycle (`alembic upgrade head`) enabling PostGIS extension, tables, constraints, and indexes.
- ✅ **Canonical Geometry (`geometry(Point, 4326)`)**: Authoritative spatial column strictly following standard GIS coordinate ordering: `POINT(longitude latitude)` in EPSG:4326.
- ✅ **Idempotent Bulk Upserts**: PostgreSQL `INSERT ... ON CONFLICT (observation_id) DO UPDATE` ensures re-syncing the same NASA response produces **zero duplicate rows**, while incrementing `ingestion_count` and preserving `first_ingested_at`.
- ✅ **Spatial & Temporal Indexes**: GiST index on `geom` for fast bounding box filtering and indexes on `acquisition_time_utc` and `(source_product, acquisition_time_utc)`.
- ✅ **Ingestion Run Auditability**: `ingestion_runs` table recording requested sources, bounding boxes, fetched counts, valid counts, upserted counts, and status (`completed`, `partial`, `failed`).
- ✅ **Controlled Synchronization Endpoint**: `POST /api/v1/firms/sync` orchestrates NASA FIRMS fetch → normalization → bulk upsert.
- ✅ **PostGIS Observation Retrieval API**: `GET /api/v1/observations` queries PostGIS exclusively with spatial bounding box (`ST_MakeEnvelope`, `ST_Intersects`), UTC time window, source filters, and deterministic sorting (`acquisition_time_utc DESC, observation_id ASC`).
- ✅ **Single Observation Lookup**: `GET /api/v1/observations/{observation_id}` for deterministic `firms_*` identifiers.
- ✅ **System Readiness Probe**: `GET /readiness` verifies live database connectivity and queries `PostGIS_Version()`.
- ✅ **Frontend Provenance**: Interactive Leaflet dashboard displays storage provenance badge (`NASA FIRMS • PostGIS-backed`), last sync time, and stored record metadata in the telemetry drawer.
- ✅ **Preserved Backward Compatibility**: Direct Phase 1 live route `GET /api/v1/firms/hotspots` and Phase 0 offline fixture mode remain fully functional.

### What Phase 2 DOES NOT Implement (Scientific Honesty)
- ❌ **No Industrial Fire Classification**: Classifying thermal sources as industrial vs non-industrial belongs to subsequent intelligence phases (Phases 4, 8).
- ❌ **No Temporal Persistence Intelligence**: Calculating multi-day recurrence or thermal anomaly persistence belongs to Phase 3.
- ❌ **No OSM Industrial Enrichment**: Querying factories, refineries, and pipelines belongs to Phase 4.
- ❌ **No Land-Cover Context**: Dynamic World / WorldCover baselines belong to Phase 5.
- ❌ **No ML / Sentinel-2 Analysis**: Spectral indices (SWIR/NIR) and machine learning inference belong to Phases 6–8.

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: `>=20.0.0`
- **Package Manager**: `pnpm` (`v9` or later)
- **Python**: `>=3.11` (managed via `uv`)
- **Docker / PostGIS**: Docker Desktop (or local/cloud PostgreSQL with PostGIS extension enabled)

### 1. Configuration & Secrets Setup

Create a `.env` file in the project root based on `.env.example`:

```bash
cp .env.example .env
```

Configure your PostgreSQL/PostGIS connection and NASA FIRMS MAP_KEY in `.env`:
```ini
# ─── Backend / Database (PostgreSQL + PostGIS) ───
POSTGRES_DB=agnidrishti
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agnidrishti
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT_SECONDS=30.0

# ─── NASA FIRMS ───
# Obtain a free MAP_KEY from: https://firms.modaps.eosdis.nasa.gov/api/map_key/
NASA_FIRMS_MAP_KEY=your_nasa_firms_map_key_here
NASA_FIRMS_DEFAULT_DAY_RANGE=1
NASA_FIRMS_TIMEOUT_SECONDS=20.0
NASA_FIRMS_CACHE_TTL_SECONDS=600

# ─── Frontend ───
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

> [!SECURITY]
> Secrets (`DATABASE_URL` with password, `NASA_FIRMS_MAP_KEY`) are loaded exclusively server-side. They are never bundled into client JavaScript, exposed in network responses, logged to stdout, or checked into version control.

### 2. Start PostGIS & Run Database Migrations

**Step A — Start PostGIS via Docker:**
```bash
docker compose up -d
```

**Step B — Apply Alembic Migrations:**
```bash
cd services/api
uv sync --extra dev
uv run alembic upgrade head
cd ../..
```

### 3. Run the Development Services

Open two terminals:

**Terminal 1 — Backend (FastAPI):**
```bash
pnpm dev:api
# API available at: http://localhost:8000
# Swagger Docs:     http://localhost:8000/docs
# Liveness Probe:   http://localhost:8000/health
# Readiness Probe:  http://localhost:8000/readiness
# Stored Obs API:   http://localhost:8000/api/v1/observations
```

**Terminal 2 — Frontend (Next.js):**
```bash
pnpm dev:web
# Dashboard available at: http://localhost:3000
```

---

## 🌐 API Reference

| Endpoint | Method | Scope | Description |
| :--- | :---: | :---: | :--- |
| `/health` | `GET` | System | Process liveness probe |
| `/readiness` | `GET` | System | Readiness probe verifying PostGIS database connectivity & version |
| `/api/v1/firms/sync` | `POST` | Phase 2 | Synchronize live NASA FIRMS detections into PostGIS via idempotent bulk upsert |
| `/api/v1/observations` | `GET` | Phase 2 | Query stored observations from PostGIS (bbox, UTC time range, sensor source, pagination) |
| `/api/v1/observations/{id}` | `GET` | Phase 2 | Retrieve a single stored observation by deterministic ID |
| `/api/v1/firms/hotspots` | `GET` | Phase 1 | Direct upstream NASA FIRMS Area API query (retained for comparison & debugging) |
| `/api/v1/firms/availability` | `GET` | Phase 1 | NASA FIRMS sensor data availability preflight check |
| `/api/v1/hotspots` | `GET` | Phase 0 | Offline fixture dataset |
| `/api/v1/analyze` | `POST` | Phase 0 | Mock analysis endpoint |

---

## 🧪 Testing & Verification

Run backend unit, API, and PostGIS integration tests:
```bash
cd services/api
uv run pytest -v
uv run ruff check .
cd ../..
```

Run frontend lint and production build:
```bash
pnpm lint:web
pnpm build:web
```

---

## 🗺️ Roadmap & Phase Status

| Phase | Milestone | Scope | Status |
| :---: | :--- | :--- | :---: |
| **0** | **Foundation** | Next.js GIS shell, React-Leaflet, FastAPI router, fixture pipeline. | 🟢 **Verified** |
| **1** | **NASA FIRMS Ingestion** | Live NOAA-20/21 Area API ingestion, defensive parser, canonical DTOs, real markers. | 🟢 **Verified** |
| **2** | **PostGIS Storage & Normalization** | Spatial database persistence, deduplication, historical indexing, spatial/temporal APIs. | 🟢 **Verified** |
| **3** | **Temporal Persistence** | Multi-day recurrence detection, thermal anomaly clustering. | ⏳ **Next Phase** |
| **4** | **Industrial Context** | OSM infrastructure enrichment, factory & refinery proximity. | ⬜ Planned |
| **5** | **Land-Cover Context** | Dynamic World / ESA WorldCover baseline filtering. | ⬜ Planned |
| **6-8** | **Sentinel-2 & ML Fusion** | Spectral indices (SWIR/NIR) and classification inference. | ⬜ Planned |
| **9-10**| **Scoring & Explainability** | Transparent attribution, AgniRisk composite scoring. | ⬜ Planned |
| **11-14**| **Advanced GIS & SIH Demo** | Temporal playback, industrial zone overlays, judge demo mode. | ⬜ Planned |

---

<div align="center">
  <p>Built with scientific integrity for Smart India Hackathon 2026 (SIH26162).</p>
</div>
