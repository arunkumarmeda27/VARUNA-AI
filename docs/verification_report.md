# VARUNA-AI Scientific Verification Report

**Dataset Version**: `v1.0.0`
**Verification Type**: District-level independent test-set verification
**Test Samples Verified**: 15
**Generated At**: 2026-10-03T12:03:08.621877

---

## 1. Dataset Verification

- Training samples: 70
- Validation samples: 15
- Test samples: 15
- Valid samples used for verification: 15
- Invalid rows removed: 0

The current test dataset does not contain a `valid_time` column. Therefore no specific calendar test period is asserted by this report.

## 2. Research Question

> Can explicitly identifying the prevailing weather regime and using that information during rainfall post-processing improve raw NWP rainfall forecasts?

The results below provide quantitative evidence from the available independent test records. They should be interpreted in the context of the current dataset size.

## 3. Continuous Verification Metrics

| Model | MAE (mm) | RMSE (mm) | Mean Bias (mm) | Pearson Correlation |
|---|---:|---:|---:|---:|
| **Level 0: Raw NWP** | 6.977 | 8.749 | 1.917 | 0.962 |
| **Level 1: Quantile Mapping** | 7.647 | 9.623 | 1.218 | 0.951 |
| **Level 2: Standard ML** | 11.991 | 20.468 | -4.799 | 0.803 |
| **Level 3: VARUNA-AI Regime-Aware** | 11.961 | 19.367 | -3.954 | 0.846 |

Observed RMSE change from Raw NWP to VARUNA-AI Level 3: **-121.362%**.

Observed MAE change from Raw NWP to VARUNA-AI Level 3: **-71.435%**.

## 4. Categorical Rainfall Verification

| Threshold | Model | Hits | False Alarms | Misses | POD | FAR | CSI | ETS |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 2.5 | Raw_NWP | 11 | 2 | 0 | 1.0000 | 0.1538 | 0.8462 | 0.4231 |
| 2.5 | Level1_Quantile_Mapping | 11 | 2 | 0 | 1.0000 | 0.1538 | 0.8462 | 0.4231 |
| 2.5 | Level2_Standard_ML | 11 | 4 | 0 | 1.0000 | 0.2667 | 0.7333 | 0.0000 |
| 2.5 | VARUNA_AI_Level3_Regime_Aware | 11 | 4 | 0 | 1.0000 | 0.2667 | 0.7333 | 0.0000 |
| 15.6 | Raw_NWP | 8 | 2 | 1 | 0.8889 | 0.2000 | 0.7273 | 0.4000 |
| 15.6 | Level1_Quantile_Mapping | 8 | 2 | 1 | 0.8889 | 0.2000 | 0.7273 | 0.4000 |
| 15.6 | Level2_Standard_ML | 7 | 1 | 2 | 0.7778 | 0.1250 | 0.7000 | 0.4231 |
| 15.6 | VARUNA_AI_Level3_Regime_Aware | 8 | 2 | 1 | 0.8889 | 0.2000 | 0.7273 | 0.4000 |
| 64.5 | Raw_NWP | 2 | 0 | 0 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| 64.5 | Level1_Quantile_Mapping | 2 | 0 | 0 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| 64.5 | Level2_Standard_ML | 0 | 0 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 64.5 | VARUNA_AI_Level3_Regime_Aware | 0 | 0 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 115.6 | Raw_NWP | 0 | 0 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 115.6 | Level1_Quantile_Mapping | 0 | 0 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 115.6 | Level2_Standard_ML | 0 | 0 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 115.6 | VARUNA_AI_Level3_Regime_Aware | 0 | 0 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 204.5 | Raw_NWP | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 204.5 | Level1_Quantile_Mapping | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 204.5 | Level2_Standard_ML | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 204.5 | VARUNA_AI_Level3_Regime_Aware | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 5. Regime-Wise Verification

### ACTIVE_MONSOON

Sample count: **3**

| Model | MAE | RMSE | Bias | Correlation | Heavy Rain CSI | Heavy Rain POD |
|---|---:|---:|---:|---:|---:|---:|
| Raw_NWP | 4.85 | 5.355 | -3.743 | 0.988 | 0.0000 | 0.0000 |
| Level1_Quantile_Mapping | 5.367 | 6.681 | -5.367 | 1.0 | 0.0000 | 0.0000 |
| Level2_Standard_ML | 7.97 | 9.058 | -5.643 | 0.871 | 0.0000 | 0.0000 |
| VARUNA_AI_Level3_Regime_Aware | 8.683 | 9.765 | -6.11 | 0.849 | 0.0000 | 0.0000 |

### BREAK_MONSOON

Sample count: **3**

| Model | MAE | RMSE | Bias | Correlation | Heavy Rain CSI | Heavy Rain POD |
|---|---:|---:|---:|---:|---:|---:|
| Raw_NWP | 5.67 | 6.197 | 0.977 | 0.945 | 0.0000 | 0.0000 |
| Level1_Quantile_Mapping | 8.663 | 9.848 | 2.81 | 0.919 | 0.0000 | 0.0000 |
| Level2_Standard_ML | 4.673 | 5.223 | -0.853 | 0.971 | 0.0000 | 0.0000 |
| VARUNA_AI_Level3_Regime_Aware | 3.683 | 4.462 | -0.837 | 0.963 | 0.0000 | 0.0000 |

### MONSOON_LOW_DEPRESSION

Sample count: **2**

| Model | MAE | RMSE | Bias | Correlation | Heavy Rain CSI | Heavy Rain POD |
|---|---:|---:|---:|---:|---:|---:|
| Raw_NWP | 9.01 | 9.329 | -9.01 | 1.0 | 1.0000 | 1.0000 |
| Level1_Quantile_Mapping | 11.67 | 12.406 | -11.67 | 1.0 | 1.0000 | 1.0000 |
| Level2_Standard_ML | 40.835 | 51.399 | -40.835 | 1.0 | 0.0000 | 0.0000 |
| VARUNA_AI_Level3_Regime_Aware | 36.22 | 46.751 | -36.22 | 1.0 | 0.0000 | 0.0000 |

### COASTAL_RAINFALL

Sample count: **2**

| Model | MAE | RMSE | Bias | Correlation | Heavy Rain CSI | Heavy Rain POD |
|---|---:|---:|---:|---:|---:|---:|
| Raw_NWP | 16.425 | 17.282 | 16.425 | 0.0 | 0.0000 | 0.0000 |
| Level1_Quantile_Mapping | 15.36 | 16.236 | 15.36 | 0.0 | 0.0000 | 0.0000 |
| Level2_Standard_ML | 9.295 | 10.985 | 9.295 | 0.0 | 0.0000 | 0.0000 |
| VARUNA_AI_Level3_Regime_Aware | 10.75 | 12.742 | 10.75 | 0.0 | 0.0000 | 0.0000 |

### OROGRAPHIC_RAINFALL

Sample count: **3**

| Model | MAE | RMSE | Bias | Correlation | Heavy Rain CSI | Heavy Rain POD |
|---|---:|---:|---:|---:|---:|---:|
| Raw_NWP | 4.327 | 6.197 | 4.327 | 0.988 | 1.0000 | 1.0000 |
| Level1_Quantile_Mapping | 3.78 | 5.381 | 3.78 | 0.992 | 1.0000 | 1.0000 |
| Level2_Standard_ML | 10.603 | 11.276 | 0.237 | 0.969 | 0.0000 | 0.0000 |
| VARUNA_AI_Level3_Regime_Aware | 12.847 | 13.365 | 0.88 | 0.963 | 0.0000 | 0.0000 |

### WESTERN_DISTURBANCE

Sample count: **2**

| Model | MAE | RMSE | Bias | Correlation | Heavy Rain CSI | Heavy Rain POD |
|---|---:|---:|---:|---:|---:|---:|
| Raw_NWP | 4.625 | 5.494 | 4.625 | -1.0 | 0.0000 | 0.0000 |
| Level1_Quantile_Mapping | 3.61 | 4.599 | 3.61 | -1.0 | 0.0000 | 0.0000 |
| Level2_Standard_ML | 4.935 | 4.992 | 4.935 | 1.0 | 0.0000 | 0.0000 |
| VARUNA_AI_Level3_Regime_Aware | 4.915 | 4.915 | 4.915 | 1.0 | 0.0000 | 0.0000 |

## 6. Heavy Rainfall Probability

### `heavy_rain_probability`

- Samples: 15
- Mean: 0.105
- Minimum: 0.0451
- Maximum: 0.5739

## 7. Conformal Uncertainty

- Samples: 15
- Mean lower 10% bound: 14.831 mm
- Mean upper 90% bound: 44.379 mm
- Mean interval width: 29.548 mm

## 8. Spatial Fractions Skill Score

**Status**: `NOT_AVAILABLE`

The current v1.0.0 test dataset contains 15 district-level records and does not contain a validated 2D spatial grid suitable for Fractions Skill Score calculation.

No fabricated 2D grid is used in this report.

## 9. Current Scientific Limitations

- The current v1.0.0 verification dataset contains only 15 independent test records.
- The dataset is district-level rather than a validated rectangular spatial grid.
- The current test data does not contain a `valid_time` column.
- Therefore this report does not claim a specific calendar test period.
- Spatial FSS is not reported as a numerical scientific result until a genuine spatial verification dataset is available.
- Larger multi-year independent datasets are required for stronger scientific conclusions.

## 10. Reproducibility

- Dataset version: `v1.0.0`
- Verification outputs:
  - `verification/results.csv`
  - `verification/verification_matrix.json`
  - `docs/verification_report.md`

---

Generated automatically by the VARUNA-AI scientific verification pipeline.
