\# VARUNA-AI â€” M1 Task 1.2

\# Backtest \& Honest Results



\## Dataset



Final real-data dataset:



master\_real\_weather\_2021\_2025.parquet



Rows evaluated: 8,723,845



Period:

2021-01-08 to 2025-12-31



Observed rainfall:

IMD rainfall



Forecast rainfall:

ERA5 rainfall



Error definition:



rainfall\_error = IMD rainfall - ERA5 rainfall





\## Official Real-Data Backtest



The existing VARUNA-AI verification metric definitions were used.



\### Continuous Metrics



MAE: 3.252 mm



RMSE: 11.109 mm



Mean Bias: -2.289 mm



Pearson Correlation: 0.363





\## Categorical Verification



\### Threshold: 1.0 mm



POD: 0.6628



CSI: 0.4642



FAR: 0.3923



Frequency Bias: 1.0907





\### Threshold: 2.5 mm



POD: 0.4622



CSI: 0.3455



FAR: 0.4223



Frequency Bias: 0.8001





\### Threshold: 10.0 mm



POD: 0.0610



CSI: 0.0570



FAR: 0.5372



Frequency Bias: 0.1318





\## Year-Wise Results



| Year | MAE | RMSE | Bias | Correlation |

|------|-----|------|------|-------------|

| 2021 | 3.334 | 11.100 | -2.402 | 0.341 |

| 2022 | 3.336 | 11.558 | -2.423 | 0.375 |

| 2023 | 2.917 | 10.370 | -1.998 | 0.374 |

| 2024 | 3.283 | 11.418 | -2.254 | 0.367 |

| 2025 | 3.391 | 11.058 | -2.370 | 0.356 |





\## Model Development Results



\### Model 1



2024 validation:



MAE: 3.921



RMSE: 10.395



R2: 0.138





\### Model 2 â€” Temporal Rainfall Features



2024 validation:



MAE: 3.592



RMSE: 9.991



R2: 0.203



2025 test:



MAE: 3.683



RMSE: 9.785



R2: 0.179





\### Model 3 â€” Temporal + Weather Features



2024 validation:



MAE: 4.278



RMSE: 9.937



R2: 0.212



2025 test:



MAE: 4.388



RMSE: 9.811



R2: 0.175





\## Important Interpretation



The ERA5 baseline verification metrics and the ML rainfall-error model metrics measure different quantities.



ERA5 baseline:



Observed rainfall versus ERA5 rainfall.



ML models:



Prediction of rainfall error.



Therefore, the two metric groups must not be presented as if they are directly comparable forecasts.





\## Weather Feature Analysis



Permutation analysis of Model 3 showed:



relative\_humidity: 0.1853



wind\_speed: 0.0873



dewpoint\_c: 0.0671



u10: 0.0669



v10: 0.0231



temperature\_c: 0.0194





\## Real Data Policy



All reported results above are based on real ERA5 and IMD-derived data.



No synthetic rainfall data was used for the reported real-data backtest.



Synthetic-data comparison is not included unless separately evaluated and documented.





\## Real-Data Held-Out Model-Ladder Evaluation

The follow-up report `M1_REAL_MODEL_LADDER_BACKTEST_2025.md` evaluates Level 0
raw ERA5 and Level 1 empirical quantile mapping on real held-out data. Level 1
was fitted only on the 2021-2023 training period; 2024 is validation and 2025
is held out for testing. The accompanying JSON records dataset SHA-256 and row
counts.

| Level | Status | Validation MAE | Validation RMSE | 2025 Test MAE | 2025 Test RMSE |
|---|---|---:|---:|---:|---:|
| Level 0 raw ERA5 | Evaluated | 3.283 | 11.418 | 3.391 | 11.058 |
| Level 1 empirical quantile mapping | Evaluated | 4.705 | 14.925 | 4.783 | 14.159 |
| Level 2 standard ML | Unavailable | n/a | n/a | n/a | n/a |
| Level 3 regime-aware ML | Unavailable | n/a | n/a | n/a | n/a |

Metrics above were calculated from the real dataset. Level 1 underperformed
the raw ERA5 baseline on the 2025 test period. Levels 2 and 3 were not
evaluated because compatible real pressure-level/synoptic features and
real-data training provenance are unavailable. Existing sample-artifact
results were not substituted.

\## Verification Status
Existing 15-row comparison artifacts are not an eligible synthetic benchmark: their
dataset lineage goes through `VARUNA_AI_100_district_sample_named.csv` and lacks
real temporal/spatial coverage. No new synthetic data or comparison results were
created. The real-vs-synthetic comparison remains pending until an independently
documented, previously existing synthetic benchmark with traceable lineage is available.

\## Verification Status



MAE: COMPLETE



RMSE: COMPLETE



Mean Bias: COMPLETE



POD: COMPLETE



CSI: COMPLETE



Year-wise verification: COMPLETE



Real-data results documentation: COMPLETE



Real 2025 held-out Level 0/1 comparison: COMPLETE

Four-tier real-data model ladder comparison: PARTIAL — Levels 0 and 1 evaluated; Levels 2 and 3 unavailable because compatible real-data feature provenance is unavailable.



Real-vs-synthetic quantitative comparison: NOT COMPARABLE — DOCUMENTED. No eligible synthetic benchmark was found. The existing verification artifacts cover 15 rows, have no valid-time column or real spatial grid, and the multi-model trainer consumes `VARUNA_AI_100_district_sample_named.csv`; these are excluded from the comparison. No synthetic rows or comparison metrics were generated.





\## M1 Task 1.2 Status



REAL-DATA BACKTEST: COMPLETE



HONEST METRICS REPORTING: COMPLETE



PUBLICATION-READY RESULTS DOCUMENTATION: COMPLETE



REMAINING PROJECT-LEVEL COMPARISONS:

- Full four-tier real-data model ladder comparison (Levels 2 and 3 require compatible real-data feature provenance)

## Real Data vs Synthetic Data Performance

The legacy synthetic benchmark was reviewed for quantitative comparison against
the new real-data backtest.

| Dataset | Status | Coverage | Quantitative comparison |
|---|---|---|---|
| Real IMD + ERA5 | Valid | 2021-2025 real temporally/spatially aligned data | Valid |
| Legacy synthetic benchmark | Excluded | 100 district rows without equivalent temporal/spatial coverage | Not valid |

### Synthetic Benchmark Eligibility

The legacy synthetic benchmark is based on
VARUNA_AI_100_district_sample_named.csv.

This dataset contains 100 district-level rows and belongs to the earlier
model-training workflow. It does not provide equivalent temporal and spatial
coverage to the real 2021-2025 IMD/ERA5 dataset.

The existing 15-row comparison artifacts also do not establish an independent,
traceable synthetic benchmark suitable for a controlled quantitative
comparison.

Therefore, the legacy synthetic benchmark is excluded from quantitative
real-vs-synthetic performance comparison.

No synthetic rows were generated, modified, or substituted to manufacture
a comparison.

### Result

The real-data evaluation is the authoritative M1.2 benchmark.

Real-vs-synthetic quantitative comparison is therefore classified as
NOT COMPARABLE — DOCUMENTED rather than reported as a numerical performance
comparison.




