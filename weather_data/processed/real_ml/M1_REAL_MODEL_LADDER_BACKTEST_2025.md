# M1 Real-Data Model Ladder Backtest

This report evaluates only levels supported by real data and real training.

- Dataset: `master_real_weather_2021_2025.parquet`
- Dataset SHA-256: `be2d01c1cfb379edb05d31e0a6142cac949b076090381e2a14361c2900221213`
- Train rows: 5217969
- Validation rows: 1755336
- Test rows: 1750540
- Test period: 2025-01-01T00:00:00 to 2025-12-31T00:00:00

| Level | Status | Validation MAE | Validation RMSE | Test MAE | Test RMSE |
|---|---|---:|---:|---:|---:|
| Level 0 raw ERA5 | evaluated | 3.283 | 11.418 | 3.391 | 11.058 |
| Level 1 empirical quantile mapping | evaluated | 4.705 | 14.925 | 4.783 | 14.159 |
| Level 2 standard ML | unavailable | n/a | n/a | n/a | n/a |

Level 2 standard ML unavailable: The real processed dataset lacks the required NWP and pressure-level/synoptic feature set; existing Level 2 artifact training provenance is not tied to this real dataset.
| Level 3 regime-aware ML | unavailable | n/a | n/a | n/a | n/a |

Level 3 regime-aware ML unavailable: The real processed dataset lacks the required pressure-level features and observed regime labels/probabilities; existing Level 3 artifact training provenance is not tied to this real dataset.

Level 1 was fitted on the real training period only. Validation and test metrics are calculated from held-out real IMD/ERA5 rows. No sample or synthetic rows are used.
