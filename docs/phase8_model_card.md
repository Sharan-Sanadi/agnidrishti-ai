# AGNIDRISHTI — Phase 8 Model Card

## Model Name
`agnidrishti_context_classifier_v1`

## Model Family
`HistGradientBoostingClassifier` (scikit-learn)

## Version
`fusion_v1` schema • `label_v1` weak supervision

## Purpose
Classify satellite-observed **thermal context archetypes** from multi-modal fusion profiles.
Each thermal observation receives one of 6 outcome labels:

| Class | Meaning |
|---|---|
| `INDUSTRIAL_THERMAL_CONTEXT` | Thermal anomaly near verified industrial infrastructure |
| `AGRICULTURAL_THERMAL_CONTEXT` | Thermal anomaly in cropland-dominated landscape |
| `NATURAL_VEGETATION_THERMAL_CONTEXT` | Thermal anomaly in tree/shrub/grass dominated landscape |
| `BUILT_NON_INDUSTRIAL_CONTEXT` | Thermal anomaly in built-up area without industrial proximity |
| `MIXED_THERMAL_CONTEXT` | Ambiguous or mixed-evidence context |
| `INSUFFICIENT_EVIDENCE` | Feature coverage < 40%, model prediction withheld |

## Out of Scope — Critical Disclaimer
This model classifies **thermal context**, NOT fire cause.

- **Does NOT confirm** industrial fire, wildfire, crop burning, or arson.
- **Does NOT score** abnormality, risk, or danger.
- Fire cause / abnormality scoring is reserved for **Phase 10** (future).
- Context classification is a prerequisite signal for downstream decision-support.

## Training Data

| Metric | Value |
|---|---|
| Fusion profiles evaluated | 1,538 |
| Weak labels generated | 618 |
| Labeling engine | `WeakLabelerV1` (conservative rule-based) |
| Spatial groups (5 km grid) | 195 |
| Label provenance | `WEAK_SUPERVISION` |
| Label version | `label_v1` |

### Class Distribution (Training Labels)

| Class | Count |
|---|---|
| MIXED_THERMAL_CONTEXT | 258 |
| INDUSTRIAL_THERMAL_CONTEXT | 132 |
| NATURAL_VEGETATION_THERMAL_CONTEXT | 112 |
| BUILT_NON_INDUSTRIAL_CONTEXT | 73 |
| AGRICULTURAL_THERMAL_CONTEXT | 43 |

All classes have ≥ 20 support samples.

## Features
57 features from `fusion_v1` multi-modal profiles across 5 source layers:

- **Thermal** (9): FRP, brightness TI4/TI5, scan, track, day/night, satellite, instrument, confidence
- **Temporal** (7): Persistence index/class, active days 7d/30d, active weeks, span, coverage ratio, detection count
- **Industrial** (10): OSM coverage, distance, inside area, category, feature counts at 500m/1km/5km, flare/chimney/refinery/power plant flags
- **Land Cover** (9): Point code, coverage status, dominant fraction, tree/shrub/grass/cropland/built-up/bare/water/wetland fractions at 500m
- **Sentinel-2** (12): Quality/provider status, scene age, valid/cloud fractions, B04/B08/B11/B12 medians, NDVI/NDMI/NBR medians, B11/B12 p90 at 250m

### Excluded Features (Anti-Leakage)
- `latitude`, `longitude` — geographic coordinate memorization forbidden
- `observation_id`, `acq_date`, `acq_time` — identifier/temporal leakage forbidden

## Splitting Strategy
- **GroupShuffleSplit** with ~5 km spatial grid groups
- 70% train / 15% validation / 15% test
- **Zero spatial group overlap** between splits (verified by `audit_group_leakage`)

| Split | Samples | Groups |
|---|---|---|
| Train | 398 | — |
| Validation | 89 | — |
| Test | 131 | — |

## Candidate Model Selection

| Model | Macro F1 (Val) |
|---|---|
| DummyClassifier | 0.1240 |
| LogisticRegression | 0.9238 |
| RandomForestClassifier | 0.9888 |
| **HistGradientBoostingClassifier** | **1.0000** |

Selected: `HistGradientBoostingClassifier` (highest validation Macro F1).

## Test Metrics (Weak-Label Agreement)

| Metric | Score |
|---|---|
| **Macro F1** | **0.9807** |
| Weighted F1 | 0.9849 |
| Balanced Accuracy | 0.9944 |

### Per-Class Metrics

| Class | P | R | F1 | Support |
|---|---|---|---|---|
| INDUSTRIAL_THERMAL_CONTEXT | 1.000 | 1.000 | 1.000 | 4 |
| AGRICULTURAL_THERMAL_CONTEXT | 0.909 | 1.000 | 0.952 | 10 |
| NATURAL_VEGETATION_THERMAL_CONTEXT | 1.000 | 1.000 | 1.000 | 32 |
| BUILT_NON_INDUSTRIAL_CONTEXT | 0.933 | 1.000 | 0.966 | 14 |
| MIXED_THERMAL_CONTEXT | 1.000 | 0.972 | 0.986 | 71 |

## Model Artifact

| Property | Value |
|---|---|
| File | `services/api/artifacts/models/phase8/agnidrishti_context_classifier_v1.joblib` |
| Size | 162,333 bytes |
| SHA-256 | `28040c6bc54a86fae48d6606bbfb3fa32657ea04cd402c93e9bd438d2add49ba` |
| Dataset fingerprint | `98783d8f325f9361c892670a1675044500439a73e7215a6f98860ac227fe6957` |

## Inference Pipeline

1. Load `fusion_v1` profile from PostGIS
2. Compute `evidence_coverage` = fraction of non-null features
3. If coverage < 0.40 → `INSUFFICIENT_EVIDENCE` (model not invoked)
4. Apply `ColumnTransformer` (median imputation + indicators → one-hot → standard scaling)
5. `predict_proba` → argmax class + max probability as `class_score`
6. Store prediction in `thermal_classification_predictions` table (idempotent upsert)

## Limitations

1. **Weak supervision only** — labels are rule-derived, not human-annotated ground truth
2. **Validation tier**: `WEAK_SUPERVISION_PROTOTYPE` — metrics measure agreement with weak labeler, not real-world accuracy
3. **Small test support** for some classes (Industrial: 4 samples in test split)
4. **Geographic bias** — trained on observations from the current database (primarily Indian subcontinent)
5. **No temporal drift detection** — model does not detect concept drift over time
6. **INSUFFICIENT_EVIDENCE gating** — 24 observations (1.6%) had < 40% feature coverage and received no prediction

## Ethical Considerations

- This model **must never** be used as sole evidence for regulatory action, criminal investigation, or insurance decisions.
- Context classification is one signal among many in a multi-phase decision-support pipeline.
- Human expert review is required before any operational conclusion.
