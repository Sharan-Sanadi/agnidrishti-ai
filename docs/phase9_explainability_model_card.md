# AGNIDRISHTI — Phase 9 Model Explainability Card

## Explainer Architecture Name
`agnidrishti_explainer_v1`

## Underlying Frozen Model
`agnidrishti_context_classifier_v1` (`HistGradientBoostingClassifier`, Phase 8)
- Model SHA-256: `28040c6bc54a86fae48d6606bbfb3fa32657ea04cd402c93e9bd438d2add49ba`
- Schema: `fusion_v1` (57 model-eligible continuous and categorical features)

## Primary Explainability Algorithms
1. **TreeSHAP** (`shap.TreeExplainer`): Exact local feature attribution decomposing the log-odds margin into additive Shapley values.
2. **Linear Explainer** (`shap.LinearExplainer`): Deterministic analytical fallback for linear models (`coef_ * (x - mean)`).
3. **Permutation Feature Importance** (`sklearn.inspection.permutation_importance`): Controlled offline global feature importance computed on held-out test split ($N=131$, 10 repeats, random seed 42).

## Core Principles & Guarantees
- **ZERO RETRAINING**: Phase 9 does not alter, re-fit, or fine-tune model parameters.
- **ZERO EXTERNAL NETWORK CALLS**: 100% self-contained local evaluation; zero calls to external APIs or services during inference or explanation sync.
- **STRICT ADDITIVITY VERIFICATION**: For every TreeSHAP explanation, the sum of all feature attributions plus the expected base value must match the model's raw output margin within numerical tolerance:
  $$\left| \sum_{i=1}^{M} \phi_i + \phi_0 - f(x) \right| < 10^{-2}$$
- **EVIDENCE GATING**: If feature coverage < 40% (`INSUFFICIENT_EVIDENCE`), explanation status is marked `INSUFFICIENT_EVIDENCE` and feature contributions are conservatively suppressed.
- **HUMAN-INTERPRETABLE TRANSLATION**: Technical feature identifiers (e.g. `landcover_dominant_fraction_500m`, `industrial_feature_count_5km`) are mapped to clean English display names, measurement units, and canonical domain groups.

---

## Global Permutation Importance Results (Held-Out Test Split)

Evaluated on $N=131$ spatial test observations with zero spatial leakage:
- **Scoring Metric**: Macro F1
- **Random Seed**: 42
- **Dataset Fingerprint**: `98783d8f325f9361c892670a1675044500439a73e7215a6f98860ac227fe6957`

### Domain Group Relative Importance
| Domain Group | Relative Importance (%) | Description |
|---|---|---|
| **LAND_COVER** | **76.3%** | ESA WorldCover 10m multi-scale circular land-cover fractions |
| **INDUSTRIAL** | **22.2%** | OpenStreetMap industrial proximity, polygon containment, and facility density |
| **THERMAL** | **0.8%** | VIIRS sensor scan, track, and brightness telemetry |
| **TEMPORAL** | **0.6%** | Multi-day recurrence and persistence index |
| **SENTINEL** | **0.0%** | Sentinel-2 spectral indices (available for verified subset) |

### Top 10 Most Discriminative Features
| Rank | Feature Identifier | Plain Display Name | Group | Permutation Mean | Std Dev |
|---|---|---|---|---|---|
| 1 | `landcover_dominant_fraction_500m` | Dominant Land Cover Fraction (500m) | LAND_COVER | 0.2756 | ± 0.0353 |
| 2 | `landcover_cropland_fraction_500m` | Cropland Coverage Fraction (500m) | LAND_COVER | 0.2262 | ± 0.0187 |
| 3 | `landcover_builtup_fraction_500m` | Built-up Land Fraction (500m) | LAND_COVER | 0.2229 | ± 0.0250 |
| 4 | `industrial_feature_count_5km` | Industrial Features within 5km | INDUSTRIAL | 0.2109 | ± 0.0176 |
| 5 | `thermal_track` | Sensor Along-Track Pixel Dimension | THERMAL | 0.0031 | ± 0.0033 |
| 6 | `persistence_span_days` | Persistence Observation Span (Days) | TEMPORAL | 0.0031 | ± 0.0033 |
| 7 | `industrial_refinery_present` | Industrial Refinery Identified | INDUSTRIAL | 0.0023 | ± 0.0024 |
| 8 | `industrial_feature_count_1km` | Industrial Features within 1km | INDUSTRIAL | 0.0015 | ± 0.0024 |
| 9 | `industrial_chimney_present` | Industrial Chimney / Stack Identified | INDUSTRIAL | 0.0008 | ± 0.0016 |
| 10 | `industrial_power_plant_present` | Thermal / Industrial Power Plant | INDUSTRIAL | 0.0008 | ± 0.0016 |

---

## Local Explanation Output Schema (`LocalExplanationResponse`)

```json
{
  "observation_id": "VIIRS_NOAA20_NRT_...",
  "explanation_status": "AVAILABLE",
  "predicted_class": "INDUSTRIAL_THERMAL_CONTEXT",
  "prediction_score": 0.984,
  "model_version": "agnidrishti_context_classifier_v1",
  "validation_status": "WEAK_SUPERVISION_PROTOTYPE",
  "explanation_version": "agnidrishti_explainer_v1",
  "method": "TreeSHAP",
  "feature_coverage": 1.0,
  "base_value": -0.842,
  "explained_output": 2.154,
  "additivity_error": 0.00021,
  "top_supporting_features": [
    {
      "feature_name": "industrial_feature_count_5km",
      "display_name": "Industrial Features within 5km",
      "feature_group": "INDUSTRIAL",
      "raw_value": 4.0,
      "display_value": "4",
      "unit": "features",
      "contribution": 1.423,
      "relative_strength": 0.48,
      "direction": "SUPPORTS",
      "rank": 1
    }
  ],
  "top_opposing_features": [
    {
      "feature_name": "landcover_tree_fraction_500m",
      "display_name": "Tree Cover Fraction (500m)",
      "feature_group": "LAND_COVER",
      "raw_value": 0.02,
      "display_value": "2%",
      "unit": "fraction",
      "contribution": -0.154,
      "relative_strength": 0.05,
      "direction": "OPPOSES",
      "rank": 1
    }
  ],
  "group_contributions": {
    "INDUSTRIAL": {
      "group": "INDUSTRIAL",
      "total_contribution": 2.145,
      "relative_strength": 0.72,
      "direction": "SUPPORTS",
      "contribution_level": "HIGH_CONTRIBUTION",
      "feature_count": 8
    }
  },
  "quality_flags": [
    "FROZEN_MODEL_EVAL",
    "ADDITIVITY_VERIFIED",
    "ZERO_NETWORK_INFERENCE"
  ],
  "generated_at": "2026-09-09T17:44:40.263346+00:00"
}
```

---

## Out of Scope & Scientific Notice

1. **Context Attribution vs. Physical Cause**:
   - SHAP explains **why the model classified the thermal context** as a specific archetype.
   - It does **NOT** determine physical causation (e.g., whether an industrial chimney caused a fire or an unpermitted burn occurred).
2. **Abnormality & Risk Scoring**:
   - Reserved for downstream Phase 10 / Decision Support Engine.
   - Explainability profiles serve as transparent, audit-ready inputs for human operators and emergency dispatchers.
