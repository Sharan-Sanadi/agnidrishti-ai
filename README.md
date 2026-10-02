<div align="center">

# 🔥 AgniDrishti (अग्निदृष्टि)
### AI-Enabled Geospatial Industrial Thermal Intelligence & Decision-Support System
**Smart India Hackathon 2026 • Problem Statement: SIH26162**

[![Validation Status: Scientifically Audited](https://img.shields.io/badge/Validation-Scientifically%20Audited-00c853.svg?style=for-the-badge&logo=checkmarx)](docs/DATA_VALIDATION_REPORT.md)
[![SIH Problem Statement](https://img.shields.io/badge/SIH-26162-ff6d00.svg?style=for-the-badge&logo=target)](https://www.sih.gov.in/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16%20Turbopack-000000.svg?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL + PostGIS](https://img.shields.io/badge/PostGIS-3.4%20%2F%20PG16-336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgis.net)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.5+-F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![SHAP](https://img.shields.io/badge/SHAP-TreeExplainer-blueviolet.svg?style=for-the-badge)](https://shap.readthedocs.io)

<br/>

**AgniDrishti** is an enterprise-grade geospatial thermal intelligence and decision-support system engineered to classify satellite-detected thermal anomalies into physically grounded contextual archetypes.

By fusing near-real-time satellite infrared observations (NASA VIIRS 375m) with spatiotemporal recurrence tracking, OpenStreetMap industrial topology, ESA WorldCover 10m land-cover intelligence, and Copernicus Sentinel-2 Level-2A surface reflectance, AgniDrishti provides investigative triage to distinguish legitimate industrial thermal operations from agricultural crop burning, wildfire activity, and unmapped thermal sources.

[Explore Scientific Validation Report ➔](docs/DATA_VALIDATION_REPORT.md)

</div>

---

## 🎥 Project Demo

Watch AgniDrishti demonstrate its geospatial thermal-intelligence workflow — from thermal hotspot visualization and contextual analysis to classification, explainability, and monitoring.

[![AgniDrishti Project Demo](https://img.youtube.com/vi/Wp_z4IQJa88/maxresdefault.jpg)](https://youtu.be/Wp_z4IQJa88)

▶️ Click the preview above to watch the complete AgniDrishti project demo.

YouTube: https://youtu.be/Wp_z4IQJa88

---

## 🎯 Problem

Satellite infrared sensors detect thermal radiation across the Earth's surface daily, but **thermal anomaly detection alone does not reveal context or cause**:

1. **The Semantic Ambiguity of Infrared Radiance**:
   A high Fire Radiative Power (FRP) detection indicates elevated infrared radiance, but cannot communicate whether that radiance originates from:
   - A routine petrochemical refinery flare stack or blast furnace.
   - An uncontrolled industrial fire or chemical tank blowout.
   - Seasonal agricultural stubble / crop residue burning.
   - A spreading forest or grassland wildfire.
   - An unmapped or unpermitted industrial thermal process.
2. **Operational Alert Fatigue**:
   Emergency management agencies, environmental pollution control boards, and industrial safety inspectors receive thousands of raw thermal alerts every week. Without contextual differentiation, field dispatch resources are overwhelmed investigating routine permitted industrial operations, while dangerous anomalies remain undifferentiated in raw alert queues.
3. **The Sub-Pixel Spatial Challenge**:
   A single satellite thermal pixel (e.g., VIIRS 375m nominal footprint) integrates all radiance emitted across approximately $140,000\text{ m}^2$ on the ground. A small, high-temperature industrial burner and an expansive, lower-temperature biomass burn can produce identical integrated radiometric signatures.

---

## 💡 Solution

AgniDrishti rejects naive single-threshold alerts and arbitrary heuristic scoring formulas ($0.3 \times \text{temp} + 0.4 \times \text{distance} + \dots$). Instead, it treats thermal intelligence as a **multi-modal scientific inference problem**:

```
NASA VIIRS 375m Infrared Observation
                 │
                 ▼
    PostGIS Spatiotemporal Persistence (ST_DWithin 750m, 30d Window, t ≤ T₀)
                 │
                 ▼
    OpenStreetMap Industrial Context (ST_Distance, ST_Covers, 5km Gating)
                 │
                 ▼
    ESA WorldCover 10m Land Cover (Circular AEQD Radii: 250m, 500m, 1000m)
                 │
                 ▼
    Copernicus Sentinel-2 Level-2A Spectral Index Engine (NDVI, NDMI, NBR)
                 │
                 ▼
    59-Feature Canonical Fusion Layer (Deterministic Schema & Fingerprint)
                 │
                 ▼
    Machine Learning Context Classifier (HistGradientBoosting, 5 Archetypes)
                 │
                 ▼
    TreeSHAP Explainability Engine (Exact Mathematical Additivity: |Δ| < 10⁻³)
                 │
                 ▼
    Auditable GIS Decision Dashboard (Field-Level Verification & Telemetry)
```

> [!IMPORTANT]
> **Scientific Integrity Notice**: AgniDrishti is a **thermal-context intelligence and decision-support system**. It classifies thermal observations into probable contextual archetypes based on satellite and geospatial evidence. It does **not** claim instantaneous real-time detection, physical confirmation of fire ignition, or causal proof of how a fire physically started.

---

## 🧠 How AgniDrishti Thinks

When an infrared thermal detection arrives, AgniDrishti progressively constructs an evidence matrix across five independent physical domains:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                1. THERMAL SENSOR INGESTION                             │
│  Extracts FRP (MW), Brightness Temperatures TI4/TI5 (K), Scan & Track pixel footprints │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                             2. TEMPORAL PERSISTENCE RECURRENCE                         │
│  Queries PostGIS ST_DWithin(750m) over prior 30 days (strictly t ≤ T₀).                │
│  Computes active days, active weeks, temporal span, and recurrence classification:     │
│  PERSISTENT (≥6 active days) | RECURRING (3–5 days) | OCCASIONAL (2 days) | ISOLATED   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                              3. INDUSTRIAL TOPOLOGY & DISTANCE                         │
│  Queries OpenStreetMap industrial features via Overpass within a 5 km envelope.        │
│  Evaluates metric distance (ST_Distance geography) and polygon containment (ST_Covers).│
│  Enforces 5 km coverage validation: STRONG | MODERATE | WEAK | NONE | UNAVAILABLE      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                                4. SURFACE LAND-COVER DOMINANCE                         │
│  Extracts real ESA WorldCover 10m 2021 v200 raster data around target coordinates.     │
│  Constructs Azimuthal Equidistant (AEQD) circular metric masks (250m, 500m, 1000m).    │
│  Evaluates 60% dominance: CROPLAND, TREE_COVER, BUILT_UP, SHRUBLAND, WATER, or MIXED  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                             5. SENTINEL-2 MULTISPECTRAL CONTEXT                        │
│  Retrieves strictly prior (t ≤ T₀) cloud-filtered Sentinel-2 L2A BOA reflectance.      │
│  Applies SCL cloud masking, evaluates NDVI (vegetation), NDMI (moisture), NBR (burn).  │
│  Preserves honest nulls on cloud cover instead of fabricating zeros.                   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                                6. CANONICAL FEATURE FUSION                             │
│  Assembles 59 canonical features (57 model-eligible + 2 metadata keys).                │
│  Excludes raw coordinates (lat/lon) to prevent spatial memorization and leakage.       │
│  Computes deterministic SHA-256 schema hash and source data fingerprint.               │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                           7. CONTEXT CLASSIFICATION & EXPLAINABILITY                   │
│  HistGradientBoostingClassifier predicts one of 5 contextual archetypes.               │
│  TreeSHAP calculates exact local feature attribution (|∑ϕᵢ + ϕ₀ - f(x)| < 10⁻³).      │
│  Renders transparent waterfall attribution and domain importance in the dashboard.    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛰️ Data Sources

AgniDrishti strictly separates authoritative external source datasets from derived analytical features:

| Source Dataset | Provider / Mission | Native Resolution | Role in System | Storage / Access |
| :--- | :--- | :--- | :--- | :--- |
| **VIIRS Active Fire (VNP14IMGTDL_NRT / VJ114IMGTDL_NRT)** | NASA FIRMS (NOAA-20 / NOAA-21) | 375m nominal at nadir | Primary thermal anomaly detection feed (FRP, TI4, TI5, coordinates, UTC timestamp) | Ingested via Area API; persisted idempotently into PostGIS `thermal_observations` |
| **ESA WorldCover 2021 v200** | European Space Agency (ESA) | 10m optical/radar classification | Baseline global land-cover classification across 11 standard classes | Local Cloud-Optimized GeoTIFFs (COGs); cached in PostGIS `thermal_land_cover_profiles` |
| **Sentinel-2 MSI Level-2A** | Copernicus Data Space Ecosystem (CDSE) | 10m / 20m Bottom-Of-Atmosphere (BOA) | High-resolution multispectral surface reflectance (B04, B08, B11, B12, SCL cloud mask) | On-demand CDSE STAC / Process API; cached in PostGIS `thermal_sentinel_context_profiles` |
| **OpenStreetMap Infrastructure** | OpenStreetMap Contributors (Overpass API) | Vector geometries (points, lines, polygons) | Industrial zone polygons, factory boundaries, flare stacks, chimneys, refineries, power plants | Ingested into PostGIS `osm_industrial_features`; cached envelope status in `osm_context_coverage` |
| **PostGIS Spatial Store** | PostgreSQL 16 + PostGIS 3.4 | Ellipsoidal WGS84 (SRID 4326) | Geospatial indexing, metric distance calculations, spatial joins, recurrence clustering | Dockerized database container with persistent GiST spatial and temporal B-Tree indexing |

---

## 🧮 Feature Engineering

AgniDrishti constructs a canonical 59-feature evidence vector (`fusion_v1`) structured into five domain groups:

### 1. Feature Breakdown by Domain Group
- **Thermal Features (6)**: Fire Radiative Power (`thermal_frp` in MW), Brightness Temperatures (`thermal_brightness_ti4`, `thermal_brightness_ti5` in K), pixel dimensions (`thermal_scan`, `thermal_track` in km), normalized confidence (`thermal_confidence`: `low`, `nominal`, `high`).
- **Temporal Persistence Features (10)**: Persistence Index ($0\text{--}100$), persistence class (`PERSISTENT`, `RECURRING`, `OCCASIONAL`, `ISOLATED`, `INSUFFICIENT_HISTORY`), active UTC calendar days over 7 and 30 days, active weeks over 30 days, observation span in days, observation count over 30 days, temporal coverage ratio.
- **Industrial Proximity Features (13)**: Proximity category (`industrial_context_class`: `STRONG`, `MODERATE`, `WEAK`, `NONE`, `UNAVAILABLE`), coverage status, geodesic distance to nearest industrial geometry (`industrial_nearest_distance_m`), polygon containment flag (`industrial_inside_area`), nearest category tag, feature counts within 500m, 1km, and 5km radii, and binary proximity flags for flare stacks, chimneys, refineries, and power generation facilities.
- **Land-Cover Context Features (15)**: Point pixel code and class, contextual class (`BUILT_UP_DOMINANT`, `CROPLAND_DOMINANT`, `TREE_COVER_DOMINANT`, `SHRUBLAND_DOMINANT`, `WATER_DOMINANT`, `MIXED`, etc.), coverage status, dominant class code and fraction at 500m radius, and specific area fractions at 500m radius for tree cover, shrubland, grassland, cropland, built-up, bare/sparse, open water, and wetland.
- **Multispectral Context Features (13)**: Quality status, provider status, scene age in days relative to $T_0$, valid pixel fraction, cloud fraction, median surface reflectance for B04 (Red), B08 (NIR), B11 (SWIR-1), B12 (SWIR-2), 90th percentile reflectance for B11 and B12, and median spectral indices:
  $$\text{NDVI} = \frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04} + 10^{-6}}, \quad \text{NDMI} = \frac{\text{B08} - \text{B11}}{\text{B08} + \text{B11} + 10^{-6}}, \quad \text{NBR} = \frac{\text{B08} - \text{B12}}{\text{B08} + \text{B12} + 10^{-6}}$$

### 2. Built-in Mathematical & Methodological Safeguards
- **Spatial Leakage Prevention**: Raw geographic coordinates (`latitude` and `longitude`) are strictly excluded from the 57 model-eligible features. Models learn physical relationships (distances, area fractions, temperatures, recurrence intervals) rather than memorizing spatial coordinate boxes.
- **Strict Temporal Anti-Leakage ($t \le T_0$)**: Satellite context and historical recurrence strictly evaluate scenes and observations where $t \le T_0$ (the target observation acquisition time). Future observations relative to $T_0$ are completely excluded.
- **Zero-Division Protection**: Spectral index calculations incorporate a numerical safeguard ($\epsilon = 10^{-6}$) in denominators, preventing division-by-zero runtime exceptions or floating-point infinity values.
- **Cloud Masking with Honest Null Preservation**: When cloud cover or invalid pixels exceed $60\%$ of the analytical region of interest, spectral features evaluate to honest `None` values rather than fabricated numeric zeros, which would distort vegetation and burn signatures.
- **Multi-Scale Circular AEQD Sampling**: Land-cover and spectral features employ Azimuthal Equidistant projection circular masks at 100m, 250m, 500m, and 1000m radii, strictly excluding corner artifacts produced by standard rectangular bounding boxes.

---

## 🔬 Scientific Validation

To verify the truth and reliability of AgniDrishti's intelligence outputs, the system underwent an extensive independent scientific data validation audit ([Full Validation Report](docs/DATA_VALIDATION_REPORT.md)).

### Subsystem Verification Status

| Subsystem / Layer | Status | Mathematical & Empirical Verification |
| :--- | :---: | :--- |
| **Raw FIRMS VIIRS Parser** | ✅ **VERIFIED** | Field-by-field parity confirmed across raw CSV, Pydantic DTOs, PostGIS tables, API JSON, and frontend UI. Deterministic SHA-256 observation IDs guarantee idempotent ingestion. |
| **PostGIS Spatial Engine** | ✅ **VERIFIED** | Point geometry verified in EPSG:4326 WGS84. Exact coordinate convention verified: `ST_X(geom) == longitude` and `ST_Y(geom) == latitude`. Zero coordinate inversions. |
| **Temporal Persistence** | ✅ **VERIFIED** | 13 temporal boundary conditions audited. Strict $t \le T_0$ filtering confirmed (zero future data leakage). Active calendar day counts and persistence thresholds mathematically verified. |
| **Industrial Proximity** | ✅ **VERIFIED** | 5 test coordinate pairs validated against independent spherical Haversine formulas (relative difference $< 0.19\%$). Polygon containment (`ST_Covers`) and 5 km coverage gating verified. |
| **Land-Cover Intelligence** | ✅ **VERIFIED** | Real ESA WorldCover 10m 2021 GeoTIFF sampling verified. Circular AEQD metric radius masks confirmed to exclude rectangular window corners. 60% dominance threshold verified. |
| **Sentinel-2 Spectral Engine** | ✅ **VERIFIED** | CDSE STAC prior-scene selection ($\le T_0$) verified. SCL cloud masking and $\epsilon = 10^{-6}$ zero-division protection reproduced independently. |
| **Feature Fusion Layer** | ✅ **VERIFIED** | 59 canonical features (57 model-eligible) verified against cryptographic schema hash `b4f4d0f2...`. Coordinate leakage prevention confirmed. |
| **ML Context Classifier** | ⚠️ **PARTIALLY VERIFIED** | **Validated against weak-supervision / programmatic labels (Macro F1 = 0.9807 on 5 km spatial holdout). Independent physical ground-truth fire dispatch records are unavailable.** |
| **SHAP Explainability** | ✅ **VERIFIED** | Exact TreeSHAP local attribution additivity verified: $\left|\sum \phi_i + \phi_0 - f(x)\right| < 10^{-3}$ across evaluated observations. Linear fallback and domain groupings verified. |
| **Frontend UI Consistency** | ✅ **VERIFIED** | Complete numerical and semantic parity verified between raw backend API JSON payloads and rendered Next.js 16 dashboard components (coordinates, FRP, confidence, classes). |

---

## 📊 Validation Snapshot

The core quantitative results from the scientific audit suite:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SCIENTIFIC AUDIT SUMMARY SNAPSHOT                     │
├───────────────────────────────────┬─────────────────────────────────────────┤
│ Automated Test Suite Pass Rate    │ 178 Passed, 18 Skipped, 0 Failures      │
│ Backend Test Modules Audited      │ 38 Test Modules (100% Passing)          │
│ Real-World Hotspot Scenarios      │ 12 Scenarios Audited Across India       │
│ Temporal Persistence Boundaries   │ 13 Boundary Edge Cases Verified         │
│ Geodesic Distance Verifications   │ 5 Independent Haversine Test Pairs      │
│ Canonical Fusion Feature Vector   │ 59 Features (57 Model-Eligible)         │
│ Spatial Anti-Leakage Safeguard    │ 2 Coordinate Features Excluded (Lat/Lon)│
│ Weak-Supervision Macro F1 Score   │ 0.9807 (Held-out 5 km Spatial Groups)   │
│ Spatial Generalization Holdout    │ GroupShuffleSplit (5 km Spatial Tiles)  │
│ TreeSHAP Additivity Error Bound   │ |∑ϕᵢ + ϕ₀ - f(x)| < 0.000001 (Zero Err) │
└───────────────────────────────────┴─────────────────────────────────────────┘
```

> [!NOTE]
> The score **0.9807** represents the **Macro F1 score** of the classifier evaluated against held-out, spatially grouped programmatic labels (weak supervision). It must **never** be interpreted as verified real-world physical fire accuracy, because physical on-site ground-truth logs are not available for satellite-scale datasets.

---

## 🧪 Invariant Testing

To ensure the system remains mathematically and physically sound throughout development, AgniDrishti implements automated invariant testing in [`services/api/tests/test_data_invariants.py`](file:///d:/Desktop/PROJECTS/Agnidrishti-Ai/services/api/tests/test_data_invariants.py).

### Why Invariant Testing Matters
Standard unit tests check whether code executes without error under sample inputs. Invariant tests verify that **fundamental physical and mathematical truths hold across all data transformations**, completely independent of model performance or heuristics:

1. **Spatial Coordinate Bounds**:
   Verifies that every stored and parsed coordinate satisfies $-90.0 \le \text{latitude} \le 90.0$ and $-180.0 \le \text{longitude} \le 180.0$, and that PostGIS geometry explicitly maps `ST_X` to longitude and `ST_Y` to latitude.
2. **Non-Negative Fire Radiative Power (FRP)**:
   Verifies that thermal anomaly observations satisfy $\text{FRP} \ge 0.0\text{ MW}$.
3. **Physical Kelvin Temperature Bounds**:
   Verifies that satellite brightness temperatures (TI4 and TI5) are strictly non-negative and fall within physically plausible satellite infrared limits ($0\text{ K} < T < 600\text{ K}$).
4. **Confidence Normalization Invariant**:
   Verifies that raw upstream sensor flags (`l`, `n`, `h`) deterministically map to normalized categorical tiers (`low`, `nominal`, `high`), rejecting unmapped arbitrary strings.
5. **Temporal Persistence Metrics Bounds**:
   Verifies that the temporal persistence index is strictly bounded in $[0, 100]$, that active days $\le$ total span days, and that $7\text{-day active days} \le 30\text{-day active days}$.
6. **Spectral Index Bounds & Zero-Division Protection**:
   Verifies that normalized difference spectral indices (NDVI, NDMI, NBR) remain strictly bounded in $[-1.0, 1.0]$, and that $\epsilon = 10^{-6}$ protects against zero denominators when reflectance values approach zero.
7. **TreeSHAP Mathematical Additivity**:
   Verifies the mathematical identity of local Shapley attributions on the frozen classifier:
   $$\left| \sum_{i=1}^{M} \phi_i + \phi_0 - f(x) \right| < 10^{-3}$$
   where $\phi_i$ are individual feature attributions, $\phi_0$ is the base expected value, and $f(x)$ is the model margin decision score.

---

## 🔍 Explainability

AgniDrishti integrates TreeSHAP (`TreeExplainer`) to provide transparent feature attribution for every classification prediction:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WHAT SHAP ACTUALLY MEANS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✅ SHAP ANSWERS:                                                            │
│    "Which features and geospatial evidence vectors contributed to the       │
│     machine learning model selecting this specific classification?"         │
│                                                                             │
│ ❌ SHAP DOES NOT ANSWER:                                                    │
│    "Why did the fire physically ignite or start in the real world?"         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Interpretation Example: Industrial Flare vs. Agricultural Stubble

```
CASE-01: Jamnagar Petrochemical Complex (Industrial Context)
Base Expected Value (ϕ₀):  -0.42
  + industrial_inside_area = True       (+1.85)  [Strong push toward Industrial]
  + industrial_nearest_distance_m = 0m  (+1.42)  [Geometry inside industrial polygon]
  + landcover_builtup_fraction = 0.82   (+0.94)  [Surrounding area is built-up]
  + temporal_persistence_index = 85.0   (+0.71)  [Recurring thermal signature over 30d]
  - sentinel_ndvi_median = 0.12         (-0.08)  [Negligible vegetation influence]
--------------------------------------------------------------------------------
Model Decision Score f(x): +4.42 ➔ Predicted: INDUSTRIAL_THERMAL_CONTEXT (100.0%)
Additivity Verification:   |ϕ₀ + ∑ϕᵢ - f(x)| = 0.000000 (Exact Identity Confirmed)
```

In this case, SHAP explains that spatial containment inside a registered industrial polygon, high built-up surface fraction, and multi-week thermal persistence were the primary mathematical drivers behind the model's decision.

---

## 🗺️ Spatial Intelligence

- **Ellipsoidal PostGIS Geometry**: PostGIS 3.4 on PostgreSQL 16 stores thermal observations as `geometry(Point, 4326)`.
- **Coordinate Convention Enforced**: All geometry constructors strictly enforce `ST_MakePoint(longitude, latitude)`, binding longitude to the horizontal X-axis and latitude to the vertical Y-axis.
- **Metric Distance Calculation**: Geodesic proximity to industrial infrastructure is calculated on the WGS84 spheroid using `ST_Distance(geom::geography, target::geography)` and cross-validated against independent spherical Haversine formulas.
- **Topological Containment**: Industrial polygon boundaries are evaluated with `ST_Covers(polygon, point)` to detect thermal events occurring directly inside refinery or manufacturing facility perimeters.
- **Multi-Scale Circular AEQD Projections**: Land-cover fractions and spectral indices are sampled within circular radii of 100m, 250m, 500m, and 1000m using local Azimuthal Equidistant (AEQD) metric projections, guaranteeing uniform spatial distance in all directions and eliminating diagonal distortion from square bounding boxes.

---

## ⏱️ Temporal Intelligence

- **Multi-Window Recurrence Tracking**: For any given observation at time $T_0$, AgniDrishti queries the spatiotemporal neighborhood within 750m across a 30-day lookback window.
- **Calendar Day Normalization**: Multiple satellite overpasses on the same calendar day (e.g., daytime and nighttime passes from NOAA-20 and NOAA-21) are normalized into **distinct active UTC calendar days** to prevent multi-sensor overpass count inflation.
- **Historical Coverage Gating**: If an observation has fewer than 7 days of historical satellite record preceding $T_0$, it is classified as `INSUFFICIENT_HISTORY`, preventing false `ISOLATED` classifications on newly monitored regions.
- **Strict Anti-Leakage Boundary Guarantee**: The temporal query strictly enforces `acquisition_time_utc <= T_0`. Observations occurring even one second after $T_0$ are completely excluded from recurrence metrics.

---

## ⚠️ Known Limitations & Documented Edge Cases

To maintain complete scientific credibility for the Smart India Hackathon evaluation, AgniDrishti explicitly documents its operational boundaries and discovered edge cases:

### Fundamental Scientific Limitations
1. **Satellite Orbital Revisit Latency**:
   VIIRS instruments on NOAA-20 and NOAA-21 operate in sun-synchronous low Earth orbits, providing approximately two overpasses per satellite daily over a given location. AgniDrishti processes near-real-time observations as satellite swaths become available; it is **not** a continuous 24/7 live video surveillance feed.
2. **Integrated 375m Spatial Radiance Footprint**:
   A VIIRS 375m pixel represents an integrated radiometric measurement. Sub-pixel features cannot be resolved spatially from thermal data alone.
3. **Weak-Supervision / Programmatic Training Labels**:
   Training labels for the context classifier were generated programmatically using domain rules and multi-modal geospatial filters (`WeakLabelerV1`). Because comprehensive, independent ground-truth fire dispatch records do not exist at satellite scale, formal real-world physical accuracy cannot be claimed.
4. **OpenStreetMap Data Completeness**:
   OpenStreetMap industrial completeness varies across rural and industrial regions. AgniDrishti mitigates this by strictly distinguishing `NONE` (verified absence of mapped features within 5 km) from `UNAVAILABLE` (missing or unqueried OSM coverage).

### Documented Edge Cases & Engineering Lessons
During the scientific data validation audit, three behavioral nuances were discovered and documented:

- **Edge Case A — OpenStreetMap Taxonomy Fallback**:
  The normalizer previously defaulted arbitrary unclassified tags to `OTHER_INDUSTRIAL / LOW`. While production Overpass queries strictly filter for validated industrial tags, unit-level synthetic inputs with arbitrary tags could receive an industrial classification.
- **Edge Case B — Industrial Containment Dominance in Learned Splits**:
  When a thermal observation falls strictly inside an industrial polygon (`industrial_inside_area = True`), the classifier can predict `INDUSTRIAL_THERMAL_CONTEXT` even if temporal persistence is low (`ISOLATED`). In the learned tree structure, spatial containment inside a registered industrial facility carries high split weight.
- **Edge Case C — Offshore / Marine Thermal Anomalies**:
  Thermal anomalies occurring in open-ocean waters (e.g., offshore gas extraction rigs or maritime vessels) can be classified as `NATURAL_VEGETATION_THERMAL_CONTEXT`. This occurs because the training distribution lacked sufficient offshore marine thermal samples, and water surfaces were grouped alongside non-built natural surface classes.

---

## 🧭 Scientific Interpretation

> **AgniDrishti is a thermal-context intelligence system.**

It is engineered to estimate the **most plausible contextual archetype** (Industrial, Agricultural, Natural Vegetation, Built Non-Industrial, or Mixed) based on multi-source satellite and geospatial evidence.

It should be utilized as an **investigative decision-support and prioritization tool** for environmental regulators, disaster management authorities, and industrial inspectors. It is not an autonomous legal diagnostic tool and does not replace on-site physical inspection.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER (Next.js 16)                   │
│   Landing Page (/) • GIS Dashboard (/dashboard) • Leaflet Map • SHAP Drawer │
│   Field-Level Parity Badges • Provenance Indicators • Invariant Telemetry   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / JSON REST APIs
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                             API LAYER (FastAPI)                             │
│   /api/v1/observations  •  /api/v1/firms/sync  •  /api/v1/persistence/batch │
│   /api/v1/industrial-context/batch • /api/v1/land-cover/batch • /api/v1/fusion│
│   /api/v1/classification/evaluate • /api/v1/explanations/sync (TreeSHAP)   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ SQLAlchemy 2.0 Async (asyncpg)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                        GEOSPATIAL STORAGE (PostgreSQL 16 + PostGIS 3.4)     │
│   thermal_observations (SRID 4326 Point, GiST Index)                        │
│   osm_industrial_features (Geometries, ST_Covers, ST_Distance)              │
│   thermal_land_cover_profiles (ESA WorldCover 10m Multi-Scale AEQD Cache)   │
│   thermal_sentinel_context_profiles (CDSE L2A BOA Reflectance & Indices)   │
│   thermal_feature_fusion_profiles (59 Canonical Features, SHA-256 Hash)     │
│   thermal_classification_predictions (Archetypes, Class Probabilities)     │
│   thermal_classification_explanations (TreeSHAP Additive Attributions)      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                         UPSTREAM DATA INGESTION CLIENTS                     │
│   NASA FIRMS Area API (NOAA-20 / NOAA-21 NRT 375m)                          │
│   Overpass API (OpenStreetMap Industrial Topology)                          │
│   Local Cloud-Optimized GeoTIFFs (ESA WorldCover 10m 2021 v200)             │
│   Copernicus Data Space Ecosystem (CDSE STAC & Process API Sentinel-2 L2A)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Running Locally

### Prerequisites
- **Node.js**: `>=20.0.0`
- **Package Manager**: `pnpm` (`v9` or later)
- **Python**: `>=3.11` (managed via `uv`)
- **Docker Desktop**: For running the PostgreSQL 16 + PostGIS 3.4 container

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
# Obtain a free MAP_KEY: https://firms.modaps.eosdis.nasa.gov/api/map_key/
NASA_FIRMS_MAP_KEY=your_nasa_firms_map_key_here
NASA_FIRMS_DEFAULT_DAY_RANGE=1
NASA_FIRMS_TIMEOUT_SECONDS=20.0
NASA_FIRMS_CACHE_TTL_SECONDS=600

# ─── Copernicus Data Space Ecosystem (CDSE) / Sentinel-2 ───
# Register at: https://dataspace.copernicus.eu/
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
# Landing Page:    http://localhost:3000
# GIS Dashboard:   http://localhost:3000/dashboard
```

---

## 🧪 Testing

Agnidrishti includes comprehensive automated tests covering data normalization, PostGIS spatial queries, machine learning validation, explainability additivity, and physical data invariants:

```bash
# ─── Root Scripts ───
pnpm test:api      # Run full backend test suite across 38 modules
pnpm lint:api      # Run Ruff linter across FastAPI backend
pnpm lint:web      # Run ESLint on Next.js frontend (0 errors, 0 warnings)
pnpm build:web     # Run Next.js 16 Turbopack production build

# ─── Direct Pytest (services/api) ───
cd services/api
uv run pytest -v   # Verified: 178 passed, 18 skipped, 0 failures

# ─── Run Invariant Test Suite Specifically ───
uv run pytest tests/test_data_invariants.py -v
```

---

## 📁 Project Structure

```
Agnidrishti-Ai/
├── apps/
│   └── web/                               # Next.js 16 App Router Frontend
│       ├── src/
│       │   ├── app/                       # Page routes (/ and /dashboard)
│       │   ├── components/                # UI components (Map, Drawer, SHAP)
│       │   └── services/                  # Frontend API clients
│       ├── package.json
│       └── tailwind.config.ts
├── services/
│   └── api/                               # FastAPI Geospatial Backend
│       ├── app/
│       │   ├── api/v1/                    # REST route controllers
│       │   ├── core/                      # Settings, logging, security
│       │   ├── db/                        # SQLAlchemy async models & engine
│       │   ├── ml/                        # ML models, registry, TreeSHAP
│       │   ├── providers/                 # FIRMS, CDSE, Overpass clients
│       │   ├── schemas/                   # Pydantic v2 canonical DTOs
│       │   ├── services/                  # Spatial, temporal & fusion logic
│       │   └── utils/                     # Geodesic, raster & hash utilities
│       ├── migrations/                    # Alembic async migration scripts
│       ├── tests/                         # 38 pytest test modules (178 tests)
│       └── pyproject.toml
├── data/
│   └── fixtures/                          # Offline test fixtures & GeoTIFFs
├── docs/
│   ├── DATA_VALIDATION_REPORT.md          # Comprehensive scientific audit
│   ├── PHASE10_TEST_REPORT.md             # System test report
│   ├── phase8_model_card.md               # Context classifier documentation
│   └── phase9_explainability_model_card.md# TreeSHAP explainer model card
├── docker-compose.yml                     # PostGIS 16-3.4 container configuration
├── package.json                           # Root monorepo workspace configuration
└── pnpm-workspace.yaml                    # pnpm monorepo workspace definition
```

---

## 🛡️ Scientific Integrity & Claims Policy

To maintain the highest standards of technical credibility and scientific ethics, AgniDrishti adheres to an explicit claims policy:

### What We Can Legally & Scientifically Claim
- **Reproducible Data Transformations**: Deterministic parsing from raw NASA FIRMS CSVs into canonical PostGIS storage.
- **Validated Spatial Mathematics**: Geodesic distances calculated on the WGS84 ellipsoid and cross-verified against independent Haversine calculations.
- **Validated Temporal Boundaries**: Strict $t \le T_0$ prior-only time filtering with zero future data leakage.
- **Validated Spectral Formulas**: NDVI, NDMI, and NBR calculations independently reproduced with $\epsilon = 10^{-6}$ zero-division protection.
- **Cryptographic Feature Provenance**: SHA-256 schema hashing and source data fingerprinting on feature vectors.
- **High Weak-Supervision Classification Performance**: Macro F1 = 0.9807 when evaluated against held-out 5 km spatial groups under weak supervision.
- **Mathematically Verified Feature Attribution**: TreeSHAP additivity confirmed with absolute error $< 10^{-3}$.

### What We Do NOT Claim
- **100% Accuracy**: No real-world machine learning system operating on remote sensing data achieves flawless accuracy.
- **Ground-Truth Physical Accuracy**: Macro F1 = 0.9807 is measured against weak-supervision labels, not physical fire department dispatch logs.
- **Instantaneous Real-Time Fire Detection**: VIIRS orbits periodically (twice daily per satellite); AgniDrishti processes observations as they arrive.
- **Physical Fire Cause Confirmation**: The classifier predicts contextual archetypes, not physical causality.
- **SHAP Explanation of Physical Ignition**: SHAP explains why the *machine learning model* selected an archetype, not how or why the *physical fire* started.

---

## 🏆 Why AgniDrishti Is Different

1. **Multi-Source Evidence Fusion**: Unifies infrared thermal physics, 30-day temporal recurrence, vector industrial topology, 10m land cover, and 20m optical/SWIR reflectance into a single intelligence vector.
2. **True Geodesic & Circular Geometry**: Eliminates planar distortion and rectangular corner artifacts using WGS84 ellipsoidal distance and Azimuthal Equidistant metric circular radii.
3. **Temporal Anti-Leakage by Design**: Enforces strict historical lookback horizons ($t \le T_0$), ensuring models never access future observations during evaluation.
4. **Automated Invariant Verification**: Employs automated invariant suites that test physical and mathematical integrity independently of model accuracy.
5. **Cryptographic Provenance**: Every observation and feature schema is fingerprinted with deterministic SHA-256 digests for auditable tracking.
6. **Transparent Explainability**: TreeSHAP attributions with mathematically verified additivity provide plain-language explanations for environmental decision-makers.
7. **Scientific Transparency**: Explicitly documents known limitations, weak supervision boundaries, and discovered edge cases rather than obscuring them behind marketing claims.

---

## 📚 Scientific Validation Report

For the complete technical and empirical audit, consult the authoritative documentation:

👉 **[Read the Full Data Validation Report (docs/DATA_VALIDATION_REPORT.md)](docs/DATA_VALIDATION_REPORT.md)**

The report contains:
- Complete field-level parity tables tracing raw VIIRS CSV to the frontend interface.
- Audit traces of 12 real-world hotspot scenarios across India.
- 13 temporal boundary conditions and anti-leakage proofs.
- 5 independent geodesic distance test calculations.
- Detailed analysis of the 3 documented edge cases and engineering lessons learned.

---

## 👨‍💻 Team / Credits

**Agnidrishti** is developed for **Smart India Hackathon 2026** under Problem Statement **SIH26162: AI Industrial Fire & Thermal Source Detection**.

- **Sharan Sanadi** ([@Sharan-Sanadi](https://github.com/Sharan-Sanadi)) — `sharansanadi2006@gmail.com`
- **Omkar Biradarpatil** ([@OmkarBiradarpatil](https://github.com/OmkarBiradarpatil))
- **Sagar N M** ([@sagarnm248](https://github.com/saganm248)) — `sagarnm248@gmail.com`

---

<div align="center">
  <b>Agnidrishti — Smart India Hackathon 2026 (Problem Statement: SIH26162)</b><br/>
  <i>Engineered with scientific rigor for industrial thermal monitoring and environmental decision intelligence.</i>
</div>
