# 🔥 Agnidrishti — SIH26162

> **Status:** 🚧 Under Construction — Active Development  
> **Current Milestone:** Phase 0 implemented; final local UI smoke verification still pending  
> **Next Major Phase:** Phase 1 — NASA FIRMS Thermal Hotspot Ingestion

Agnidrishti is an AI-enabled geospatial thermal-intelligence prototype being built for **Smart India Hackathon 2026 — Problem Statement SIH26162**.

The project is designed to go beyond simply plotting thermal hotspots. Its goal is to investigate a hotspot using thermal, temporal, industrial, land-cover and satellite context, then classify and explain what that thermal anomaly most likely represents.

## Core Product Principle

```text
DETECT
  ↓
UNDERSTAND
  ↓
CLASSIFY
  ↓
EXPLAIN
  ↓
MONITOR
```

Agnidrishti is **not** intended to be another NASA FIRMS clone. FIRMS provides thermal detections; Agnidrishti is being built as the intelligence layer that interprets those detections in context.

---

# 🎯 What We Are Building

The target end-to-end pipeline is:

```text
NASA FIRMS
   ↓
Thermal hotspot ingestion
   ↓
Normalization + storage
   ↓
Temporal persistence analysis
   ↓
Industrial-context analysis
   ↓
Land-cover analysis
   ↓
Satellite context
   ↓
Feature fusion
   ↓
ML classification
   ↓
Confidence + explainability
   ↓
Abnormal thermal-event scoring
   ↓
GIS dashboard + monitoring
```

The final prototype should distinguish between categories such as:

- Probable industrial fire
- Persistent industrial thermal source
- Flare-like thermal activity
- Mining / industrial thermal activity
- Forest / natural fire
- Agricultural burning
- Uncertain thermal anomaly

Scientific wording is important. The system should not claim that an exact factory is burning or that a specific physical cause has been proven solely from satellite data. Outputs should remain probabilistic and explainable.

---

# 🧭 Development Roadmap

| Phase | Name | Purpose | Status |
|---|---|---|---|
| **0** | Foundation / Architecture / Environment | Create the repository structure, working frontend/backend foundation, GIS shell, fixture data flow, contracts and development workflow | 🟡 Implemented, final smoke verification pending |
| **1** | NASA FIRMS Thermal Ingestion | Replace fixture hotspots with real FIRMS NOAA-20 / NOAA-21 detections | ⏳ Next |
| **2** | PostGIS Storage + Normalization | Persist and normalize hotspot data in geospatial storage | ⬜ Not started |
| **3** | Temporal Persistence Intelligence | Detect repeated vs transient heat and calculate persistence metrics | ⬜ Not started |
| **4** | Industrial Context / OSM | Find nearby refineries, factories, plants, mines and industrial land | ⬜ Not started |
| **5** | Land-Cover Intelligence | Understand whether hotspot surroundings are built, forest, crop, bare land, etc. | ⬜ Not started |
| **6** | Sentinel-2 Satellite Context | Add satellite evidence and relevant spectral/contextual indicators | ⬜ Not started |
| **7** | Feature Fusion | Combine thermal, temporal, industrial, land-cover and satellite features | ⬜ Not started |
| **8** | ML Classification | Train and integrate the first real baseline classification model | ⬜ Not started |
| **9** | Explainability | Show why a hotspot received a classification and confidence score | ⬜ Not started |
| **10** | Abnormal Thermal Event Scoring | Compare current activity with historical behaviour to identify unusual industrial heat | ⬜ Not started |
| **11** | Full GIS Dashboard | Complete the judge-facing geospatial intelligence dashboard | ⬜ Not started |
| **12** | Monitoring + Analytics | Add historical charts, trends and monitoring views | ⬜ Not started |
| **13** | Validation + Evaluation | Build verified test cases and evaluate classification performance | ⬜ Not started |
| **14** | SIH Demo Mode | Prepare reproducible historical/demo cases for reliable judging | ⬜ Not started |
| **15** | Future Extensions | Add only useful post-MVP extensions after the core pipeline is stable | ⬜ Future |

---

# ✅ Phase 0 — What Has Been Implemented

Phase 0 establishes the working vertical slice that all later phases will extend.

## Frontend

Current frontend foundation is under:

```text
apps/web
```

Implemented so far:

- Next.js frontend scaffold
- GIS-oriented dashboard shell
- React-Leaflet map integration
- OpenStreetMap base layer
- Satellite base-layer option through layer controls
- Fixture hotspot markers
- Marker styling based on confidence/context
- Hotspot quick-information popup
- Floating dashboard controls / filters shell
- Statistics card for active hotspot count
- Analysis drawer for hotspot investigation
- Frontend API service layer
- FastAPI integration for fixture hotspot analysis

Current frontend dependencies reported during Phase 0 include:

- `react-leaflet`
- `leaflet`
- `axios`
- `lucide-react`

> **Architecture note:** The original bootstrap plan proposed MapLibre, but the current implementation uses React-Leaflet. Since the Phase 0 GIS flow is already implemented with Leaflet, it should be preserved unless a later requirement demonstrates a concrete limitation. Do not rewrite the map stack merely for consistency with an older plan.

---

## Backend

Current backend is under:

```text
services/api
```

The FastAPI backend is intended to expose versioned endpoints under:

```text
/api/v1
```

Phase 0 currently supports fixture-driven hotspot data and analysis responses.

The backend was confirmed to be running locally on:

```text
http://localhost:8000
```

Opening the root URL currently returns:

```json
{"detail":"Not Found"}
```

This is **expected** because no `/` route is defined. It does not mean FastAPI is broken.

For API documentation, use:

```text
http://localhost:8000/docs
```

---

# 🔬 Phase 0 Fixture Mode

Phase 0 intentionally uses fixture/mock hotspot records so that the complete frontend ↔ backend interaction can be built before external APIs are introduced.

The intended Phase 0 flow is:

```text
Fixture hotspot data
      ↓
FastAPI
      ↓
Next.js frontend
      ↓
GIS marker
      ↓
User clicks hotspot
      ↓
Analysis API request
      ↓
Analysis drawer
      ↓
Fixture classification + evidence
```

Important:

> Fixture classification values are development data only. They must not be presented as outputs from a real trained AI model.

The first real ML model is scheduled for **Phase 8**.

---

# ⚠️ Current Verification State

The following development commands have already been run successfully according to the Phase 0 implementation report:

```bash
pnpm dev:api
pnpm dev:web
```

The backend was visibly reachable on port `8000`.

However, the **final browser smoke test for the frontend has not yet been confirmed by the project owner**.

Before Phase 0 is considered fully frozen, one contributor should verify:

```text
localhost:3000 opens
        ↓
GIS map renders
        ↓
Fixture hotspot markers appear
        ↓
Hotspot can be clicked
        ↓
Analysis drawer opens
        ↓
FastAPI data is displayed
        ↓
No fatal browser-console errors
```

If any of these fail, repair Phase 0 before starting Phase 1.

---

# ▶️ How To Run Phase 0 Locally

## 1. Clone the repository

```bash
git clone <REPOSITORY_URL>
cd agnidrishti
```

## 2. Install frontend/workspace dependencies

```bash
pnpm install
```

## 3. Install backend dependencies

```bash
cd services/api
uv sync
cd ../..
```

## 4. Start the FastAPI backend

```bash
pnpm dev:api
```

Expected backend:

```text
http://localhost:8000
```

Swagger/OpenAPI:

```text
http://localhost:8000/docs
```

## 5. Start the frontend in a second terminal

```bash
pnpm dev:web
```

Expected frontend:

```text
http://localhost:3000
```

---

# 🛠️ If Phase 0 Does Not Run

Do **not** immediately start Phase 1 and do not rewrite the project.

Check in this order:

1. `pnpm install` completed successfully
2. `uv sync` completed successfully
3. backend starts on port `8000`
4. frontend starts on port `3000`
5. API base URL points to `http://localhost:8000/api/v1`
6. FastAPI CORS allows `http://localhost:3000`
7. React-Leaflet is loaded as client-side code where required by Next.js
8. Leaflet CSS/assets load correctly
9. no required development environment variable is missing
10. no port conflict exists

Apply the **smallest possible fix** and preserve the working architecture.

Do not replace React-Leaflet, FastAPI, or the repository structure merely because of a local setup error.

---

# 🧱 Frozen Project Rules

All contributors must follow these rules.

### 1. Do not break completed phases

Before modifying code:

```bash
git status
```

Understand the current implementation before editing.

### 2. Keep the product aligned to SIH26162

Every feature should improve one of the following:

```text
DETECT
UNDERSTAND
CLASSIFY
EXPLAIN
MONITOR
```

Avoid unrelated features.

### 3. Working demo before unnecessary polish

UI/UX should be clean, modern and professional enough for internal SIH shortlisting, but excessive visual polish must never delay the real data pipeline.

### 4. No fake AI

Do not invent accuracy percentages, confidence values or model claims.

### 5. Preserve scientific credibility

Prefer:

- probable industrial thermal event
- possible industrial fire
- persistent industrial thermal source
- requires ground verification

Avoid unsupported causal claims.

### 6. External providers must remain modular

Future data sources include:

- NASA FIRMS
- OpenStreetMap / Overpass
- Dynamic World / ESA WorldCover
- Sentinel-2 / Google Earth Engine

Do not tightly couple the entire application to a single provider.

---

# 🔥 Next Development Task — Phase 1

Do **not** start random UI work or ML work next.

The next major implementation is:

## Phase 1 — NASA FIRMS Thermal Hotspot Ingestion

Phase 1 will:

- connect Agnidrishti to real NASA FIRMS data
- ingest NOAA-20 / NOAA-21 VIIRS thermal detections
- normalize FIRMS fields into the existing hotspot contract
- preserve fixture mode as a fallback
- expose real hotspots through the FastAPI API
- render real detections on the existing GIS map
- handle API/network failures gracefully
- keep Phase 0 behaviour intact

After Phase 1, Agnidrishti should stop being a fixture-only dashboard and become a real thermal-data system.

---

# 👥 Contributor Handoff

If you are a teammate continuing this repository, start by reading:

1. this README
2. `docs/PHASE_ROADMAP.md`
3. `docs/ARCHITECTURE.md`
4. current Git status/log
5. the code for the phase you are assigned

Do not redesign the whole project from scratch.

When using an AI coding agent, give it this rule:

> Inspect the existing Agnidrishti repository first. Preserve all working Phase 0 behaviour. Implement only the assigned phase, use the existing contracts and architecture, make the smallest safe changes, run validation after implementation, and do not start later phases automatically.

---

# 🏆 Internal SIH Goal

Agnidrishti is being built specifically to maximize our chances of getting shortlisted for the internal Smart India Hackathon round.

The final prototype should be:

- genuinely working
- strictly aligned to SIH26162
- technically defensible
- geospatial-first
- explainable
- visually stronger and easier to use than typical existing thermal/fire-monitoring dashboards
- reliable during judging
- polished enough to feel like a real product prototype without sacrificing core functionality

The priority is not to build the largest application.

The priority is to build the **strongest complete end-to-end demonstration of the PS162 solution pipeline**.

---

## Current Status Summary

```text
PHASE 0
Foundation / Architecture / Fixture GIS Flow
🟡 IMPLEMENTED — FINAL FRONTEND SMOKE VERIFICATION PENDING

PHASE 1
NASA FIRMS Thermal Ingestion
⏳ NEXT

PHASES 2–15
⬜ NOT STARTED
```

---

**Project:** Agnidrishti  
**Problem Statement:** SIH26162  
**Current Development State:** Under Construction 🚧🔥
