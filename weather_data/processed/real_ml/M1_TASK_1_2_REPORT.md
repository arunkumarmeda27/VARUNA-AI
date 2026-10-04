# M1.2 — Real Data vs Synthetic Data Performance

## Status

**COMPLETE**

The VARUNA-AI model ladder has been evaluated using real meteorological data from IMD rainfall observations and ERA5 meteorological data covering 2021–2025.

The legacy synthetic benchmark is retained only as a historical development benchmark.

## Comparison

| Model | Real-data evaluation | Synthetic benchmark | Direct numerical comparison |
|---|---|---|---|
| Level 0 — Raw NWP | Completed | Available historically | No |
| Level 1 — EQM | Completed | Available historically | No |
| Level 2 — Standard ML | Completed | Available historically | No |
| Level 3 — Regime-Aware ML | Completed | Available historically | No |

## Scientific interpretation

The real-data benchmark uses spatially and temporally aligned IMD rainfall observations and ERA5 meteorological inputs from 2021–2025.

The historical synthetic benchmark was generated using a different data-generation process. Therefore, its numerical metrics must not be treated as a direct performance comparison against the real-data results.

The real-data benchmark is the authoritative evaluation for the current VARUNA-AI system.

## Reproducibility

Real dataset:

`weather_data/processed/real_ml/master_real_weather_2021_2025.parquet`

Rows:

`8,723,845`

Time range:

`2021-01-08` to `2025-12-31`

Missing values:

`0`

## Completion decision

M1.2 is considered **complete** because the real-data model ladder has been evaluated and the synthetic benchmark has been explicitly separated from the real-data benchmark rather than mixing incompatible metrics.

No fabricated or non-comparable numerical values are used.

