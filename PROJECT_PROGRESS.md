# VARUNA-AI: Project Engineering Progress & Milestone Audit Tracker

**Smart India Hackathon 2026 | Problem Statement: SIH26080**  
**Title**: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
**Ministry / Department**: Ministry of Earth Sciences (MoES) / India Meteorological Department (IMD)  
**Repository**: [https://github.com/arunkumarmeda27/VARUNA-AI](https://github.com/arunkumarmeda27/VARUNA-AI)  
**Status**: `ALL 14 MILESTONES COMPLETE & VERIFIED` &bull; `23/23 TESTS PASSING`

---

## 1. Executive System Summary

VARUNA-AI is a domain-guided meteorological post-processing and verification platform for Indian Summer Monsoon precipitation forecasts. It directly answers the SIH26080 central research question:

> **"Can explicitly identifying the prevailing weather regime and using that information during rainfall post-processing improve raw NWP rainfall forecasts, especially for heavy and very heavy rainfall events?"**

### Primary Scientific Findings (Verified on Held-out 2024 Test Set):
- **Overall Error Reduction**: Forecast RMSE is reduced by **39.48%** (from 16.89 mm down to 10.22 mm) compared to operational Raw NWP.
- **Hypothesis Confirmation**: Regime-Aware ML (Level 3 — Model B) outperforms Standard ML without regimes (Level 2 — Model A) across both MAE (5.22 mm vs 5.32 mm) and RMSE (10.22 mm vs 10.53 mm).
- **Extreme Event Detection**: Heavy rainfall ($\ge 64.5\text{ mm}$) Critical Success Index (CSI) improves from **0.575** (Raw NWP) to **0.694** (+20.6% relative improvement), and Probability of Detection (POD) increases from **0.578** to **0.802** (+38.8%).

---

## 2. 13-Milestone Implementation & Audit Status

| # | Milestone Description | Primary Owning Module | Status | Deliverable Files | Verification Output / Metric |
| :-: | :--- | :--- | :---: | :--- | :--- |
| **M1** | Observed Rainfall Ingestion & Validation | `weather_data/` | `COMPLETE` | `weather_data/ingestion/data_loader.py`, `preprocessing/validator.py` | Non-negativity ($R \ge 0$), physical range checks, IMD 6-tier classification |
| **M2** | NWP + Observation Spatio-Temporal Alignment | `weather_data/` | `COMPLETE` | `weather_data/temporal/temporal_aligner.py`, `spatial/spatial_aligner.py` | $t_{valid} = t_{init} + \tau$, cKDTree spatial snapping, zero future leakage |
| **M3** | Master Versioned Parquet Dataset Builder | `weather_data/` | `COMPLETE` | `weather_data/master_dataset_builder.py` | Chronological splits: Train (2018-2022: 7,320 rows), Val (2023: 1,464 rows), Test (2024: 1,464 rows) |
| **M4** | Weather Regime Classification | `regimes/` | `COMPLETE` | `regimes/training/train_classifier.py`, `regimes/inference/regime_classifier.py` | **88.52% Test Accuracy**, **0.896 Macro F1**, **0.164 Brier Score** |
| **M5** | Raw NWP Baseline Verification | `correction/` | `COMPLETE` | `correction/baselines/level0_raw_nwp.py` | Level 0 MAE: 8.76 mm, RMSE: 16.89 mm, Mean Bias: -5.60 mm |
| **M6** | Empirical Quantile Mapping (EQM) | `correction/` | `COMPLETE` | `correction/baselines/level1_quantile_mapping.py` | Level 1 MAE: 5.71 mm, RMSE: 8.96 mm (Drizzle bias eliminated: -0.04 mm) |
| **M7** | Regime-Aware ML Correction Model Ladder | `correction/` | `COMPLETE` | `correction/models/level2_standard_ml.py`, `level3_regime_aware_ml.py` | **39.48% RMSE reduction** over Raw NWP; Model B > Model A across MAE & RMSE |
| **M8** | Heavy Rainfall Probability & Uncertainty | `probability/`, `uncertainty/` | `COMPLETE` | `probability/heavy_rainfall.py`, `uncertainty/conformal_quantiles.py` | Calibrated $P(R \ge 64.5\text{mm})$ (Brier: 0.064), 80% Conformal Coverage: 82.4% |
| **M9** | Scientific Verification Engine | `verification/` | `COMPLETE` | `verification/metrics.py`, `verification/verify.py` | Continuous (MAE, RMSE, Bias, $r$), Categorical (POD, FAR, CSI, ETS), Spatial (FSS) |
| **M10**| Grid-to-District Spatial Aggregation | `geospatial/` | `COMPLETE` | `geospatial/districts/district_geometry.py`, `aggregation/grid_aggregator.py` | Point-in-polygon, area-weighted mean + peak max convective preservation |
| **M11**| Backend ORM Database & REST API | `backend/` | `COMPLETE` | `backend/models.py`, `api_views.py`, `service.py`, `urls.py` | 9 REST endpoints with predictable schema, input validation, error handling |
| **M12**| Operational Scientific Decision Dashboard | `dashboard/` | `COMPLETE` | `dashboard/templates/dashboard/index.html`, `dashboard.js`, `dashboard.css` | 11 dedicated full-view workspaces (Overview, GIS Map, Districts, Regimes, Performance, Verification, Alerts, History, Sources, Settings, Docs) |
| **M13**| Live End-to-End CLI Forecast Demo & Ablation| `experiments/` | `COMPLETE` | `experiments/run_end_to_end_demo.py`, `experiments/run_ablation_study.py` | 12-step interactive forecast journey + full statistical ablation suite |
| **M14**| Firebase Authentication & Session Security| `dashboard/` | `COMPLETE` | `dashboard/templates/dashboard/login.html`, `dashboard.js`, `views.py` | Firebase v10 Auth SDK (Email/Password, Google OAuth, Lead Meteorologist Demo Mode), Session Guards |

---

## 3. Six-Member Team Responsibility Matrix

### Member 1: Data Foundation Engineer (`weather_data/`)
- **Deliverables**: `metadata/data_dictionary.py`, `preprocessing/validator.py`, `temporal/temporal_aligner.py`, `spatial/spatial_aligner.py`, `features/synoptic_features.py`, `ingestion/data_loader.py`, `master_dataset_builder.py`.
- **Inputs**: Raw NWP forecasts (24-hr lead), IMD observational rainfall, reanalysis atmospheric profiles.
- **Outputs**: Clean, validated, chronological Parquet datasets (`train_v1.0.0.parquet`, `val_v1.0.0.parquet`, `test_v1.0.0.parquet`).
- **Tests**: `tests/test_data.py`, `tests/test_features.py`.

### Member 2: Weather Regime Classification Engineer (`regimes/`)
- **Deliverables**: `training/features.py`, `training/train_classifier.py`, `inference/regime_classifier.py`, `evaluation/evaluate_regimes.py`.
- **Inputs**: Synoptic thermodynamic/kinematic feature vectors ($u_{850}$, $v_{850}$, $\|V_{850}\|$, $\theta_{850}$, $u_{200}$, $v_{200}$, $VWS$, $MSLP$, $TCWV$, $RH_{700}$, $CAPE$, $\phi_{trough}$, vorticity, moisture flux, orographic flux, offshore trough).
- **Outputs**: Calibrated class probabilities (`prob_active_monsoon`, etc.) and categorical regime prediction.
- **Tests**: `tests/test_regime.py`.

### Member 3: Rainfall Post-Processing ML Engineer (`correction/`)
- **Deliverables**: `baselines/level0_raw_nwp.py`, `baselines/level1_quantile_mapping.py`, `models/level2_standard_ml.py`, `models/level3_regime_aware_ml.py`, `models/correction_engine.py`, `evaluation/evaluate_correction.py`.
- **Inputs**: NWP precipitation, meteorological feature matrix, regime probability distribution.
- **Outputs**: Corrected grid-level rainfall predictions (mm/day) across all 4 ladder levels.
- **Tests**: `tests/test_correction.py`.

### Member 4: Probability, Uncertainty & Verification Engineer (`probability/`, `uncertainty/`, `verification/`)
- **Deliverables**: `probability/heavy_rainfall.py`, `uncertainty/conformal_quantiles.py`, `verification/metrics.py`, `verification/verify.py`.
- **Inputs**: Post-processed rainfall grids, historical observational pairs, IMD warning thresholds.
- **Outputs**: Calibrated exceedance probabilities, 80% conformal prediction intervals $[q_{10}, q_{90}]$, WMO continuous/categorical/spatial metric matrices.
- **Tests**: `tests/test_probability.py`, `tests/test_verification.py`.

### Member 5: Backend & Platform Integration Engineer (`backend/`)
- **Deliverables**: `models.py`, `api_views.py`, `service.py`, `urls.py`, `settings.py`, `manage.py`.
- **Inputs**: Corrected district forecast products, regime metrics, model provenance metadata.
- **Outputs**: Versioned REST API endpoints (`/api/v1/forecasts/`, `/api/v1/districts/`, `/api/v1/regimes/`, `/api/v1/verification/`, `/api/v1/models/`).
- **Tests**: `tests/test_api.py`.

### Member 6: Geospatial & Operational Interface Engineer (`geospatial/`, `dashboard/`)
- **Deliverables**: `geospatial/districts/district_geometry.py`, `aggregation/grid_aggregator.py`, `dashboard/templates/dashboard/index.html`, `dashboard.js`, `dashboard.css`.
- **Inputs**: Gridded forecast outputs, WGS84 GeoJSON district boundaries.
- **Outputs**: District-aggregated forecasts (mean + peak max), interactive Leaflet choropleth maps, ECharts CSI verification curves, synoptic diagnostics radar.
- **Tests**: `tests/test_geospatial.py`, `tests/test_api.py`.

---

## 4. Test Suite Audit (100% Passing)

Run tests locally:
```bash
python -m pytest -v tests/
```

```text
tests/test_api.py::TestForecastAPI::test_dashboard_home_page PASSED      [  4%]
tests/test_api.py::TestForecastAPI::test_districts_endpoint PASSED       [  8%]
tests/test_api.py::TestForecastAPI::test_health_endpoint PASSED          [ 13%]
tests/test_api.py::TestForecastAPI::test_latest_forecast_endpoint PASSED [ 17%]
tests/test_api.py::TestForecastAPI::test_login_page PASSED               [ 21%]
tests/test_api.py::TestForecastAPI::test_models_registry_endpoint PASSED [ 26%]
tests/test_api.py::TestForecastAPI::test_verification_benchmarks_endpoint PASSED [ 30%]
tests/test_correction.py::test_level0_raw_nwp PASSED                     [ 34%]
tests/test_correction.py::test_level1_quantile_mapping PASSED            [ 39%]
tests/test_correction.py::test_correction_engine_pipeline PASSED         [ 43%]
tests/test_data.py::test_data_validator_non_negativity PASSED            [ 47%]
tests/test_data.py::test_data_leakage_assertion PASSED                   [ 52%]
tests/test_data.py::test_temporal_chronological_splits PASSED            [ 56%]
tests/test_data.py::test_spatial_reference_grid_generation PASSED        [ 60%]
tests/test_features.py::test_synoptic_feature_computation PASSED         [ 65%]
tests/test_geospatial.py::test_districts_geojson_validity PASSED         [ 69%]
tests/test_geospatial.py::test_grid_to_district_aggregation PASSED       [ 73%]
tests/test_probability.py::test_heavy_rainfall_probability_estimator PASSED [ 78%]
tests/test_probability.py::test_conformal_uncertainty_estimator PASSED   [ 82%]
tests/test_regime.py::test_regime_classifier_inference PASSED            [ 86%]
tests/test_verification.py::test_continuous_metrics PASSED               [ 91%]
tests/test_verification.py::test_contingency_and_categorical_scores PASSED [ 95%]
tests/test_verification.py::test_fractions_skill_score PASSED            [100%]

============================= 23 passed in 3.61s ==============================
```
