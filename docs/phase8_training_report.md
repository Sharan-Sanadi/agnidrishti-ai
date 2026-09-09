# AGNIDRISHTI AI — Phase 8 Model Training Report
**Model Version:** `agnidrishti_context_classifier_v1`
**Trained At:** `2026-09-09T16:26:42.380174+00:00`
**Model Family:** `hist_gradient_boosting`
**Validation Tier:** `WEAK_SUPERVISION_PROTOTYPE`
**Dataset Fingerprint:** `98783d8f325f9361c892670a1675044500439a73e7215a6f98860ac227fe6957`
**Artifact SHA-256:** `28040c6bc54a86fae48d6606bbfb3fa32657ea04cd402c93e9bd438d2add49ba`

---

## 1. Label Provenance & Data Distribution
- **Total Fusion Profiles Evaluated:** 1538
- **Weak Labels Generated:** 618
- **Unlabeled / Insufficient Evidence:** 920
- **Labeling Conflicts:** 0
- **Split Strategy:** Deterministic Spatial Grouping (~5 km grid cells, seed=42)
- **Train Samples:** 398 | **Validation:** 89 | **Test:** 131

### Per-Class Counts
- **INDUSTRIAL_THERMAL_CONTEXT:** 132
- **NATURAL_VEGETATION_THERMAL_CONTEXT:** 112
- **MIXED_THERMAL_CONTEXT:** 258
- **AGRICULTURAL_THERMAL_CONTEXT:** 43
- **BUILT_NON_INDUSTRIAL_CONTEXT:** 73

---

## 2. Candidate Model Comparison (Validation Set Macro F1)
| Model Family | Macro F1 | Weighted F1 | Balanced Accuracy |
| :--- | :--- | :--- | :--- |
| `dummy` | 0.1240 | 0.2787 | 0.2000 |
| `logistic_regression` | 0.9238 | 0.9445 | 0.9274 |
| `random_forest` | 0.9888 | 0.9889 | 0.9950 |
| `hist_gradient_boosting` | 1.0000 | 1.0000 | 1.0000 |

---

## 3. Selected Model Test Performance (WEAK-LABEL AGREEMENT)
- **Macro F1:** `0.9807`
- **Balanced Accuracy:** `0.9944`
- **Weighted F1:** `0.9849`

### Per-Class Test Breakdown
| Context Archetype | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| `INDUSTRIAL_THERMAL_CONTEXT` | 1.0000 | 1.0000 | 1.0000 | 4 |
| `AGRICULTURAL_THERMAL_CONTEXT` | 0.9091 | 1.0000 | 0.9524 | 10 |
| `NATURAL_VEGETATION_THERMAL_CONTEXT` | 1.0000 | 1.0000 | 1.0000 | 32 |
| `BUILT_NON_INDUSTRIAL_CONTEXT` | 0.9333 | 1.0000 | 0.9655 | 14 |
| `MIXED_THERMAL_CONTEXT` | 1.0000 | 0.9718 | 0.9857 | 71 |

---

## 4. Leakage Controls & Scientific Honesty
1. **Forbidden Identifier & Spatial Leakage:** All identifiers (`observation_id`, `scene_id`, `osm_uid`) and geographic coordinates (`latitude`, `longitude`) were strictly excluded from model feature matrix `X`.
2. **Anti-Circularity (Strategy A):** Direct categorical labels (`industrial_context_class`, `landcover_context_class`, etc.) were stripped from features, ensuring model learns from physical indicators (distances, counts, fractions, spectral indices, thermal brightness/FRP).
3. **Spatial Group Segregation:** No spatial ~5km grid cell overlaps between Train, Validation, and Test splits.
4. **Target Semantics:** Predicts **Thermal Context Archetype**, NOT fire cause or wildfire/crop-burning confirmation.
