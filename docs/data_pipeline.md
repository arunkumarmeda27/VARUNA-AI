# VARUNA-AI: Meteorological Data Foundation & Ingestion Pipeline

**Smart India Hackathon 2026 | Problem Statement: SIH26080**  
**Module**: `weather_data/` | **Owner**: Member 1 (Data Foundation / Data Engineer)

---

## 1. Overview & Data Flow
The Data Foundation module provides the validated meteorological backbone for VARUNA-AI. It ingests numerical weather prediction (NWP) model outputs (e.g., NCMRWF NCUM, IMD GFS) and observational ground truth (IMD gridded rainfall & station data), verifies physical constraints, eliminates future leakage, and generates structured master Parquet datasets.

```
RAW DATA INGESTION (2018–2024 Monsoon Seasons: June 1 – Sept 30)
                           │
                           ▼
[1. PHYSICAL VALIDATION] (`weather_data/preprocessing/validator.py`)
   • Non-negative rainfall assertion: R_obs >= 0, R_nwp >= 0
   • Thermodynamic & kinematic physical range clamping
   • IMD 6-tier categorical classification
                           │
                           ▼
[2. TEMPORAL & SPATIAL ALIGNMENT] (`temporal/`, `spatial/`)
   • Forecast validity equation: t_valid = t_initialization + tau (tau = 24h)
   • Strict zero-leakage chronological split:
       - Train: 2018-06-01 to 2022-09-30 (7,320 grid-days, 5 seasons)
       - Validation: 2023-06-01 to 2023-09-30 (1,464 grid-days, 1 season)
       - Test (Held-out): 2024-06-01 to 2024-09-30 (1,464 grid-days, 1 season)
   • Spatial snapping to IMD standard grid coordinates via cKDTree
                           │
                           ▼
[3. SYNOPTIC FEATURE COMPUTATION] (`features/synoptic_features.py`)
   • Low-Level Jet (LLJ) speed & direction at 850 hPa
   • Tropical Easterly Jet (TEJ) speed at 200 hPa
   • Deep tropospheric vertical wind shear (200 hPa - 850 hPa)
   • Cyclonic relative vorticity proxy & moisture flux index
   • Western Ghats orographic flux index & West Coast offshore trough index
   • Convective instability metric (CAPE * RH700)
                           │
                           ▼
[4. MASTER PARQUET EXPORT] (`weather_data/processed/`)
   • train_v1.0.0.parquet, val_v1.0.0.parquet, test_v1.0.0.parquet
```

---

## 2. Leakage Prevention Protocol
1. **No Target Leakage**: Observed rainfall (`observed_rainfall`) is strictly isolated from model feature columns during feature preparation.
2. **No Normalization / EQM Leakage**: Quantile mapping ECDFs and scaler transformations are fitted exclusively on the 2018–2022 training partition and applied without updating to validation (2023) and test (2024) partitions.
3. **No Temporal Contamination**: Random k-fold splitting across time series is prohibited. All splits are strictly chronological by monsoon year.

---

## 3. Data Schema & Feature Registry

| Feature Name | Symbol | Unit | Physical Range | Meteorological Significance |
| :--- | :--- | :--- | :--- | :--- |
| `observed_rainfall` | $R_{obs}$ | mm/day | $[0.0, 1500.0]$ | IMD ground truth daily accumulation |
| `nwp_rainfall` | $R_{nwp}$ | mm/day | $[0.0, 1000.0]$ | Raw NWP 24-hr cumulative precipitation |
| `u850`, `v850` | $u_{850}, v_{850}$ | m/s | $[-60.0, 60.0]$ | Zonal / Meridional wind at 850 hPa (Somali LLJ) |
| `wind_speed_850` | $\|V_{850}\|$ | m/s | $[0.0, 80.0]$ | Low-Level Jet strength |
| `wind_dir_850` | $\theta_{850}$ | deg | $[0.0, 360.0]$ | LLJ wind direction (identifies onshore flow) |
| `u200`, `v200` | $u_{200}, v_{200}$ | m/s | $[-90.0, 90.0]$ | Tropical Easterly Jet (200 hPa) |
| `vertical_wind_shear`| $VWS$ | m/s | $[0.0, 100.0]$ | Deep tropospheric vertical wind shear |
| `mslp` | $MSLP$ | hPa | $[870.0, 1085.0]$ | Mean sea level pressure |
| `tcwv` | $TCWV$ | $\text{kg/m}^2$ | $[0.0, 100.0]$ | Total column atmospheric water vapour |
| `rh700` | $RH_{700}$ | % | $[0.0, 100.0]$ | Relative humidity at 700 hPa |
| `cape` | $CAPE$ | J/kg | $[0.0, 7000.0]$ | Convective Available Potential Energy |
| `monsoon_trough_lat` | $\phi_{trough}$ | deg N | $[15.0, 35.0]$ | Latitude position of the Monsoon Trough axis |
| `orographic_flux_idx` | $F_{oro}$ | m/s | $[0.0, 50.0]$ | Westerly moisture flux hitting Western Ghats |
| `offshore_trough_idx` | $\Delta P_{off}$ | hPa | $[-10.0, 15.0]$ | Pressure deficit along West Coast |

---

## 4. Verification & Automated Test Status
- Automated tests in `tests/test_data.py` and `tests/test_features.py` verify non-negativity, physical bounds, chronological isolation, spatial indexing, and synoptic feature calculation.
- Status: **PASSED (100% test pass rate)**.
