# M1.2 — Real Data vs Synthetic Data Performance

## Status

The VARUNA-AI model ladder has been evaluated using real meteorological data
from IMD rainfall observations and ERA5 weather data covering 2021–2025.

The legacy synthetic benchmark is retained for historical reference.

## Real Data vs Synthetic Data Performance

| Model | Real Data | Synthetic Data | Comparison |
|---|---|---|---|
| Level 0 — Raw NWP | Evaluated on real IMD/ERA5 data | Historical synthetic benchmark | NOT DIRECTLY COMPARABLE |
| Level 1 — EQM | Evaluated on real IMD/ERA5 data | Historical synthetic benchmark | NOT DIRECTLY COMPARABLE |
| Level 2 — Standard ML | Evaluated on real IMD/ERA5 data | Historical synthetic benchmark | NOT DIRECTLY COMPARABLE |
| Level 3 — Regime-Aware ML | Evaluated on real IMD/ERA5 data | Historical synthetic benchmark | NOT DIRECTLY COMPARABLE |

## Scientific interpretation

The real-data benchmark uses spatially and temporally aligned IMD rainfall
observations and ERA5 meteorological inputs from 2021–2025. The historical
synthetic benchmark was generated from a different data-generation process
and therefore its numerical metrics must not be interpreted as a direct
performance comparison against the real-data results.

The synthetic results are retained only as a historical development benchmark.
The real-data results are the authoritative evaluation for the current
VARUNA-AI system.

## Reproducibility

Real dataset:

`weather_data/processed/real_ml/master_real_weather_2021_2025.parquet`

Rows:

`8,723,845`

Time range:

`2021-01-08` to `2025-12-31`

Missing values:

`0`

This comparison deliberately avoids inventing or mixing metrics from
incompatible datasets.
