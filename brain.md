# VARUNA-AI: Project Brain & Milestone Progress Tracker

**Problem Statement**: SIH26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
**Smart India Hackathon 2026** &bull; **Ministry of Earth Sciences (MoES) / IMD**  
**Central Research Question**: *"Can explicitly identifying the prevailing weather regime and using that information during rainfall post-processing improve raw NWP rainfall forecasts, especially for heavy and very heavy rainfall events?"*  
**Latest Update Timestamp**: `2026-09-02T22:45:00+05:30`  
**System Status**: `OPERATIONAL & PRODUCTION-READY (23/23 Automated Tests Passing)`
**Authentication**: Firebase Web Auth (`varuna-ai-960d4` — Email/Password, Google OAuth, Demo Access)
**Model Version**: Regime Classifier v2.0.0 | Correction Models v2.0.0 / v3.0.0

---

## 1. Overall System Architecture & Module Progress

```
                                    ┌────────────────────────────────────────────────────────┐
                                    │                     VARUNA-AI                          │
                                    │         End-to-End Scientific Architecture             │
                                    └──────────────────────────┬─────────────────────────────┘
                                                               │
        ┌──────────────────────────────┬───────────────────────┼───────────────────────┬──────────────────────────────┐
        ▼                              ▼                       ▼                       ▼                              ▼
 [MEMBER 1: DATA]             [MEMBER 2: REGIMES]     [MEMBER 3: ML]          [MEMBER 4: PROB/VERIF]         [MEMBER 6 & 5: GEO/API/UI]
 (weather_data/)              (regimes/)              (correction/)           (prob/, uncert/, verif/)       (geospatial/, backend/, dash/)
 Status: [COMPLETE]           Status: [COMPLETE]      Status: [COMPLETE]      Status: [COMPLETE]             Status: [COMPLETE]
 Tests: 4/4 Passed            Tests: 1/1 Passed       Tests: 3/3 Passed       Tests: 5/5 Passed              Tests: 10/10 Passed
```

---

## 2. 14-Step Milestone Progression Tracker

| Milestone | Description | Owning Module | Status | Deliverables / Artifacts | Verified Metric / Outcome |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **M1** | Observed Rainfall Ingestion & Validation | `weather_data/` | `COMPLETED` | `weather_data/ingestion/data_loader.py`, `docs/data_dictionary.md` | Non-negative clamping ($R_{obs} \ge 0$), IMD standards |
| **M2** | NWP + Observation Alignment | `weather_data/` | `COMPLETED` | `weather_data/temporal/temporal_aligner.py` | Valid time matched ($t_{valid} = t_{init} + \tau$), zero leakage |
| **M3** | Master Dataset Generation | `weather_data/` | `COMPLETED` | `weather_data/master_dataset_builder.py` | Chronological splits: Train (2018-2022), Val (2023), Test (2024) |
| **M4** | Weather Regime Classification | `regimes/` | `COMPLETED` | `regimes/training/train_classifier.py`, `regimes/inference/regime_classifier.py` | **88.52% Test Accuracy**, **0.896 Macro F1**, **0.164 Brier Score** (v2.0.0: +0.68% Acc, -0.014 Brier) |
| **M5** | Raw NWP Baseline Verification | `correction/` | `COMPLETED` | `correction/baselines/level0_raw_nwp.py` | Level 0 MAE: 8.76 mm, RMSE: 16.89 mm, Bias: -5.60 mm |
| **M6** | Statistical Bias Correction (EQM) | `correction/` | `COMPLETED` | `correction/baselines/level1_quantile_mapping.py` | Level 1 MAE: 5.71 mm, RMSE: 8.96 mm (Drizzle bias fixed: -0.04 mm) |
| **M7** | Regime-Aware ML Correction Ladder | `correction/` | `COMPLETED` | `correction/models/level2_standard_ml.py`, `level3_regime_aware_ml.py` | **L2 MAE: 5.32mm / L3 MAE: 5.22mm / L3 RMSE: 10.22mm → 39.48% RMSE reduction** vs Raw NWP; Hypothesis confirmed: L3 > L2 |
| **M8** | Heavy Rainfall Probability & Uncertainty | `probability/`, `uncertainty/` | `COMPLETED` | `probability/heavy_rainfall.py`, `uncertainty/conformal_quantiles.py` | Calibrated $P(R \ge 64.5\text{mm})$, 80% Conformal Intervals |
| **M9** | Scientific Verification Pipeline | `verification/` | `COMPLETED` | `verification/metrics.py`, `verify.py`, `docs/verification_report.md` | Full WMO/IMD metrics: POD, FAR, CSI, ETS, FSS, Contingency Tables |
| **M10** | Grid-to-District Spatial Aggregation | `geospatial/` | `COMPLETED` | `geospatial/districts/district_geometry.py`, `grid_aggregator.py` | Point-in-polygon & area-weighted GeoJSON generation for 100 named districts |
| **M11** | Backend Database & REST API | `backend/` | `COMPLETED` | `backend/models.py`, `api_views.py`, `service.py`, `urls.py` | 10 documented REST endpoints, SQLite/PostGIS ORM models, dynamic lead-time filtering |
| **M12** | Operational Forecasting Interface | `dashboard/` | `COMPLETED` | `dashboard/templates/dashboard/index.html`, `dashboard.js`, `dashboard.css` | 11 Dedicated Full-View Workspaces (Overview, GIS Map, Districts, Regimes, Performance, Verification, Alerts, History, Sources, Settings, Docs) |
| **M13** | End-to-End Live Forecast Demonstration | `experiments/` | `COMPLETED` | `experiments/run_end_to_end_demo.py` | Full 12-step forecast execution script validated |
| **M14** | Firebase User Authentication & Guard | `dashboard/` | `COMPLETED` | `dashboard/templates/dashboard/login.html`, `dashboard.js` | Firebase v10 Auth (Email/Pass, Google OAuth, Lead Meteorologist Instant Demo), Session Guards, Header User Display, Sign Out |

---

## 3. Team Member Modules & Responsibilities

### Member 1: Data Foundation Engineer (`weather_data/`)
- **Deliverables**:
  - `weather_data/metadata/data_dictionary.py`
  - `docs/data_dictionary.md`
  - `weather_data/preprocessing/validator.py`
  - `weather_data/temporal/temporal_aligner.py`
  - `weather_data/spatial/spatial_aligner.py`
  - `weather_data/features/synoptic_features.py`
  - `weather_data/ingestion/data_loader.py`
  - `weather_data/master_dataset_builder.py`
- **Output Artifacts**: `weather_data/processed/train_v1.0.0.parquet`, `val_v1.0.0.parquet`, `test_v1.0.0.parquet`, `master_v1.0.0.parquet`

### Member 2: Weather Regime Classification Engineer (`regimes/`)
- **Deliverables**:
  - `regimes/training/features.py`
  - `regimes/training/train_classifier.py`
  - `regimes/inference/regime_classifier.py`
  - `regimes/evaluation/evaluate_regimes.py`
- **Output Artifacts**: `regimes/models/regime_xgb_artifact.joblib`, `regimes/evaluation/regime_evaluation_report.json`

### Member 3: Rainfall Post-Processing ML Engineer (`correction/`)
- **Deliverables**:
  - `correction/baselines/level0_raw_nwp.py` (Identity Baseline)
  - `correction/baselines/level1_quantile_mapping.py` (Empirical Quantile Mapping)
  - `correction/models/level2_standard_ml.py` (Model A - Standard ML GBDT)
  - `correction/models/level3_regime_aware_ml.py` (Model B - VARUNA-AI Regime-Coupled ML)
  - `correction/models/correction_engine.py` (Unified Engine)
  - `correction/evaluation/evaluate_correction.py`
- **Output Artifacts**: `correction/artifacts/level1_eqm.joblib`, `level2_standard_xgb.joblib`, `level3_regime_aware_xgb.joblib`, `correction/evaluation/correction_evaluation_report.json`

### Member 4: Probability, Uncertainty & Verification Engineer (`probability/`, `uncertainty/`, `verification/`)
- **Deliverables**:
  - `probability/heavy_rainfall.py` (IMD Threshold Probability Classifiers: 15.6mm, 64.5mm, 115.6mm, 204.5mm)
  - `uncertainty/conformal_quantiles.py` (Quantile Models $q_{10}, q_{50}, q_{90}$ and 80% Conformal Prediction Bounds)
  - `verification/metrics.py` (Continuous, Categorical Contingency 2x2, Fractions Skill Score)
  - `verification/verify.py` (Verification Suite Runner)
  - `docs/verification_report.md`
- **Output Artifacts**: `verification/results.csv`, `verification/verification_matrix.json`, `docs/verification_report.md`

### Member 5: Backend & Platform Integration Engineer (`backend/`)
- **Deliverables**:
  - `backend/models.py` (`ForecastRun`, `District`, `DistrictForecast`, `ModelProvenance`)
  - `backend/service.py` (Forecast Service & Spatial Sync)
  - `backend/api_views.py` (REST Endpoints)
  - `backend/urls.py` & `backend/settings.py` & `manage.py`
- **REST Endpoints**:
  - `GET /api/v1/health/`
  - `GET /api/v1/forecasts/latest/`
  - `GET /api/v1/forecasts/list/`
  - `GET /api/v1/forecasts/{run_id}/`
  - `GET /api/v1/districts/`
  - `GET /api/v1/districts/{district_id}/forecast/`
  - `GET /api/v1/regimes/`
  - `GET /api/v1/verification/`
  - `GET /api/v1/models/`
  - `GET /login/` (Firebase Authentication portal)

### Member 6: Geospatial & Operational Interface Engineer (`geospatial/`, `dashboard/`)
- **Deliverables**:
  - `geospatial/districts/district_geometry.py` (Verified 100 Indian district centroids and geometries)
  - `geospatial/aggregation/grid_aggregator.py` (Point-in-polygon & area-weighted spatial aggregation)
  - `dashboard/views.py` & `dashboard/urls.py`
  - `dashboard/templates/dashboard/login.html` (Firebase Auth Portal)
  - `dashboard/templates/dashboard/index.html` (11-Workspace Operational Command Center)
  - `dashboard/static/css/dashboard.css` (Dark scientific slate theme with glassmorphism)
  - `dashboard/static/js/dashboard.js` (Multi-view controller, Leaflet GIS, ECharts curves, and Auth Guard)

---

## 4. Key Scientific Results Benchmark (Test Season 2024)

### Continuous Performance Ladder
| Model Level | Specification | MAE (mm) | RMSE (mm) | Mean Bias (mm) | Pearson $r$ | Error Reduction vs NWP |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Level 0** | **Raw NWP Baseline** | 8.76 | 16.89 | -5.60 | 0.977 | Baseline (0.0%) |
| **Level 1** | **Empirical Quantile Mapping** | 5.71 | 8.96 | -0.04 | 0.980 | +46.95% |
| **Level 2** | **Standard ML Regressor (Model A)** | 5.32 | 10.53 | -0.30 | 0.975 | +37.66% |
| **Level 3** | **VARUNA-AI Regime-Aware (Model B)**| **5.22** | **10.22** | **-0.27** | **0.974** | **+39.48%** |

### Heavy Rainfall Capture ($\ge 64.5$ mm)
- **Critical Success Index (CSI)**: Increased from **0.575** (Raw NWP) to **0.694** (**+20.6% relative improvement**).
- **Probability of Detection (POD)**: Increased from **0.578** (Raw NWP) to **0.802** (**+38.8% relative improvement**).
- **False Alarm Ratio (FAR)**: Reduced from **0.174** down to **0.116**.

---

## 5. Automated Verification Checklist

- [x] Data Validation non-negativity and bounds check passed (`tests/test_data.py`)
- [x] Anti-leakage chronological assertions verified (`tests/test_data.py`)
- [x] Synoptic feature engineering verified (`tests/test_features.py`)
- [x] Regime classification inference & probability sum to 1.0 verified (`tests/test_regime.py`)
- [x] Model ladder post-processing and physical zero-bounding verified (`tests/test_correction.py`)
- [x] Heavy rain probability and conformal uncertainty verified (`tests/test_probability.py`)
- [x] Continuous, categorical contingency, and spatial FSS metrics verified (`tests/test_verification.py`)
- [x] Geospatial district aggregation and GeoJSON valid (`tests/test_geospatial.py`)
- [x] Django REST API, login page, and dashboard endpoints verified (`tests/test_api.py`)
- [x] **Overall: 23 / 23 Tests Passing** (`pytest -v tests/`)
