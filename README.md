<div align="center">
  
# 🔥 Agnidrishti (अग्निदृष्टि)
**AI-Enabled Geospatial Industrial Thermal Intelligence & Monitoring System**

[![Status](https://img.shields.io/badge/Status-Phase%201%20Verified-success.svg)](#)
[![Current Phase](https://img.shields.io/badge/Current%20Phase-Phase%201%20(NASA%20FIRMS%20Ingestion)-blue.svg)](#)
[![SIH](https://img.shields.io/badge/SIH-26162-orange.svg)](#)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016-black?logo=next.js)](#)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](#)

Agnidrishti is a cutting-edge geospatial thermal-intelligence platform engineered for **Smart India Hackathon 2026 (Problem Statement SIH26162)**.

Going beyond basic thermal hotspot visualization, Agnidrishti ingests near-real-time satellite thermal anomaly feeds and will contextualize detections with temporal, industrial, land-cover, and multispectral intelligence.

</div>

---

## 📖 Core Product Principle

Agnidrishti functions as the intelligence layer over raw satellite thermal detections:

```
NASA FIRMS (VIIRS NRT)
        ↓
Reliable Backend Ingestion & Validation
        ↓
Canonical ThermalObservation DTOs
        ↓
FastAPI Endpoints
        ↓
Next.js GIS Dashboard
        ↓
Real Hotspots on Leaflet with Provenance
```

---

## 🛰️ Phase 1 — NASA FIRMS Thermal Ingestion (Completed & Verified)

Phase 1 establishes the production-grade, zero-runtime-dummy-data satellite ingestion pipeline using official **NASA FIRMS Area API**.

### Primary Sensor Feeds
- **VIIRS NOAA-20 NRT (`VIIRS_NOAA20_NRT`)**: Primary daytime and nighttime VIIRS 375m thermal anomaly product.
- **VIIRS NOAA-21 NRT (`VIIRS_NOAA21_NRT`)**: Primary VIIRS thermal detection product operating in complementary orbital track.

> [!NOTE]
> **NASA Data Advisory on Suomi-NPP**: `VIIRS_SNPP_NRT` is intentionally kept optional and not used as a default primary source due to NASA's published Suomi-NPP data quality advisory. The primary Phase 1 pipeline authoritative feeds are NOAA-20 and NOAA-21.

### What Phase 1 DOES Implement
- ✅ Official NASA FIRMS Area API client with server-side authentication.
- ✅ Bounded in-memory TTL caching with stale fallback handling for transient outages.
- ✅ Concurrent multi-sensor ingestion (NOAA-20 + NOAA-21 gathered asynchronously).
- ✅ Defensive CSV parser reading fields by name (tolerant to column reordering and extra columns).
- ✅ Timezone-aware UTC timestamp creation preserving leading-zero acquisition times (`0035` → `00:35`).
- ✅ Stable, deterministic observation IDs generated via SHA-256 hashing of physical observation parameters.
- ✅ Strict bounding-box spatial validation and day-range validation (1–5 days).
- ✅ FastAPI endpoints: `/api/v1/firms/hotspots` and `/api/v1/firms/availability`.
- ✅ Interactive Leaflet GIS frontend with genuine NASA satellite markers across India.
- ✅ Comprehensive satellite telemetry drawer (FRP in MW, Brightness TI4/TI5 in K, Confidence, Platform, Acquisition Time).
- ✅ Mode switcher: **Live (NASA FIRMS)** vs **Phase 0 Fixtures** (for offline testing).
- ✅ Honest dashboard metrics: Live Thermal Detections, NOAA-20, NOAA-21 counts, and truthful "Pending Phase 3" notices.

### What Phase 1 DOES NOT Implement
- ❌ **No Industrial Fire Classification**: Raw thermal anomalies are NOT yet classified as industrial vs non-industrial (this belongs to later intelligence phases).
- ❌ **No Persistence Intelligence**: Repeated vs transient persistence scoring belongs to Phase 3.
- ❌ **No PostGIS Storage**: Database normalization and geospatial indexing belong to Phase 2.
- ❌ **No OSM Industrial Context**: Proximity to industrial infrastructure belongs to Phase 4.
- ❌ **No ML / Sentinel-2 Analysis**: Spectral and machine learning fusion belong to Phases 6–8.

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: `>=20.0.0`
- **Package Manager**: `pnpm` (`v9` or later)
- **Python**: `>=3.11` (managed via `uv`)

### 1. Configuration & Secrets Setup

Create a `.env` file in the project root based on `.env.example`:

```bash
cp .env.example .env
```

Obtain a free NASA FIRMS MAP_KEY from [NASA FIRMS Map Key Request](https://firms.modaps.eosdis.nasa.gov/api/map_key/).

Set the key in `.env`:
```ini
# ─── NASA FIRMS ───
NASA_FIRMS_MAP_KEY=your_nasa_firms_map_key_here
NASA_FIRMS_DEFAULT_DAY_RANGE=1
NASA_FIRMS_TIMEOUT_SECONDS=20.0
NASA_FIRMS_CACHE_TTL_SECONDS=600

# ─── Frontend ───
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

> [!SECURITY]
> The MAP_KEY is loaded exclusively server-side by the FastAPI backend. It is never bundled into frontend JavaScript, exposed in network responses, or checked into version control.

### 2. Install Dependencies

```bash
# Install root and frontend workspace dependencies
pnpm install

# Install backend dependencies
cd services/api
uv sync
cd ../..
```

### 3. Run the Services

Open two terminal windows:

**Terminal 1 — Backend (FastAPI):**
```bash
pnpm dev:api
# API available at: http://localhost:8000
# Swagger OpenAPI Docs: http://localhost:8000/docs
# Health Endpoint: http://localhost:8000/health
# Live FIRMS Endpoint: http://localhost:8000/api/v1/firms/hotspots
```

**Terminal 2 — Frontend (Next.js):**
```bash
pnpm dev:web
# Dashboard available at: http://localhost:3000
```

---

## 🌐 API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/health` | `GET` | System health check |
| `/api/v1/firms/hotspots` | `GET` | Ingest live satellite thermal detections (params: `west`, `south`, `east`, `north`, `days`, `sources`, `date`, `force_refresh`) |
| `/api/v1/firms/availability` | `GET` | Check NASA FIRMS sensor data availability |
| `/api/v1/hotspots` | `GET` | Phase 0 local fixture dataset (retained for testing) |
| `/api/v1/analyze` | `POST` | Phase 0 mock analysis endpoint (retained for testing) |

---

## 🧪 Testing & Verification

Run backend unit, API, and live integration tests:
```bash
cd services/api
uv run pytest -v -s
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
| **2** | **PostGIS Storage & Normalization** | Spatial database persistence, deduplication, historical indexing. | ⏳ **Next Phase** |
| **3** | **Temporal Persistence** | Multi-day recurrence detection, thermal anomaly clustering. | ⬜ Planned |
| **4** | **Industrial Context** | OSM infrastructure enrichment, factory & refinery proximity. | ⬜ Planned |
| **5** | **Land-Cover Context** | Dynamic World / ESA WorldCover baseline filtering. | ⬜ Planned |
| **6-8** | **Sentinel-2 & ML Fusion** | Spectral indices (SWIR/NIR) and classification inference. | ⬜ Planned |
| **9-10**| **Scoring & Explainability** | Transparent attribution, AgniRisk composite scoring. | ⬜ Planned |
| **11-14**| **Advanced GIS & SIH Demo** | Temporal playback, industrial zone overlays, judge demo mode. | ⬜ Planned |

---

<div align="center">
  <p>Built with scientific integrity for Smart India Hackathon 2026 (SIH26162).</p>
</div>
