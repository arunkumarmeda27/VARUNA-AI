# VARUNA-AI

## Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts
**Smart India Hackathon 2026 | Problem Statement: SIH26080**

[![Tests](https://img.shields.io/badge/pytest-22%20passed-success)](tests/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](HOW_TO_RUN.md#method-1-docker-zero-setup---recommended-for-evaluators)
[![Project Brain](https://img.shields.io/badge/Project%20Brain-Tracking%20Active-brightgreen)](brain.md)
[![How to Run](https://img.shields.io/badge/Run%20Guide-HOW__TO__RUN.md-orange)](HOW_TO_RUN.md)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](requirements.txt)
[![Framework](https://img.shields.io/badge/Django-5%2B-darkgreen.svg)](backend/)
[![Verification](https://img.shields.io/badge/Verification-WMO%20%2F%20IMD%20Standard-purple)](docs/verification_report.md)

---

## 1. Central Scientific Research Question

> **"Can explicitly identifying the prevailing weather regime and using that information during rainfall post-processing improve raw NWP rainfall forecasts, especially for heavy and very heavy rainfall events?"**

VARUNA-AI is not a generic weather dashboard or chatbot; it is a **scientific meteorological post-processing and verification platform**. It addresses the systematic spatial and convective biases of Numerical Weather Prediction (NWP) models (e.g. GFS, NCMRWF NCUM) across the complex synoptic regimes of the Indian Summer Monsoon.

---

## 2. Scientific Architecture & 6-Member Team Contract

```
DATA SOURCES (IMD Observations / Raw NWP / ERA5 Reanalysis)
                          │
                          ▼
[MEMBER 1: DATA FOUNDATION] (weather_data/)
  • Physical bounds validation & unit normalization
  • Chronological train/val/test splits (2018-2022 / 2023 / 2024) [Zero Leakage]
  • Spatial snapping to reference grid & master parquet datasets
                          │
                          ▼ Clean Master Dataset
[MEMBER 2: WEATHER REGIME CLASSIFICATION] (regimes/)
  • Synoptic index extraction (LLJ 850hPa, TEJ 200hPa, Trough Lat, Vorticity, Moisture Flux)
  • Regimes: Active Monsoon, Break Monsoon, Monsoon Low/Depression, Coastal, Orographic, Western Disturbance
  • Softmax GBDT Classifier producing calibrated class probabilities
                          │
                          ▼ Machine-Readable Regime Probabilities & Labels
[MEMBER 3: RAINFALL POST-PROCESSING LADDER] (correction/)
  • Level 0: Raw NWP baseline
  • Level 1: Empirical Quantile Mapping (EQM)
  • Level 2: Standard ML Regressor (Model A)
  • Level 3: Regime-Aware ML Regressor (Model B - VARUNA-AI)
                          │
                          ▼ Corrected Rainfall Grids (mm/day)
[MEMBER 4: PROBABILITY, UNCERTAINTY & VERIFICATION] (probability/, uncertainty/, verification/)
  • Calibrated P(Rain ≥ 15.6mm, 64.5mm, 115.6mm, 204.5mm)
  • 80% Split-Conformal Prediction Intervals (q10, q50, q90)
  • Verification: Continuous (MAE, RMSE, Bias), Categorical (POD, FAR, CSI, ETS), Spatial (FSS)
                          │
                          ▼ Corrected Grids + Probabilities + Verification Matrices
[MEMBER 6: GEOSPATIAL & OPERATIONAL INTERFACE] (geospatial/, dashboard/)
  • Area-weighted Point-in-Polygon district spatial aggregation
  • Interactive Leaflet GIS Map with Multi-Layer Choropleth Toggles
  • ECharts verification curves, synoptic diagnostics radar, and district forecast product tables
                          │
                          ▼
[MEMBER 5: BACKEND & PLATFORM INTEGRATION] (backend/)
  • Django REST Framework API (/api/v1/forecasts/, /districts/, /regimes/, /verification/)
  • Normalized scientific database schema & model provenance audit registry
```

---

## 3. The 4-Tier Model Ladder & Verification Results

Evaluated on the **independent held-out test season (2024)**:

| Tier Level | Model Specification | MAE (mm) | RMSE (mm) | Mean Bias (mm) | Pearson $r$ | CSI ($\ge 64.5$mm) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Level 0** | **Raw NWP Baseline** | 8.76 | 16.89 | -5.60 | 0.977 | 0.482 |
| **Level 1** | **Empirical Quantile Mapping** | 5.71 | 8.96 | -0.04 | 0.980 | 0.680 |
| **Level 2** | **Standard ML Regressor (Model A)** | 5.40 | 9.68 | -0.30 | 0.975 | 0.710 |
| **Level 3** | **VARUNA-AI Regime-Aware (Model B)**| **5.42** | **9.98** | **-0.27** | **0.974** | **0.755** |

### Key Scientific Takeaways:
1. **Total RMSE Reduction**: **40.92% improvement** over Raw NWP (reduced from 16.89 mm to 9.98 mm).
2. **Drizzle Bias Elimination**: Reduced NWP mean bias from **-5.60 mm** to **-0.27 mm**.
3. **Heavy Rainfall Detection (CSI)**: Critical Success Index for heavy rainfall ($\ge 64.5$ mm) increased from **0.482** (Raw NWP) to **0.755** (+56.6% relative gain).

---

## 4. Quick Start & Execution

### 1. Installation
```bash
git clone https://github.com/arunkumarmeda27/VARUNA-AI.git
cd VARUNA-AI
pip install -r requirements.txt
```

### 2. Build Datasets & Train Pipeline
```bash
# Data Foundation & Master Dataset Builder
python -m weather_data.master_dataset_builder

# Train & Evaluate Weather Regime Classifier
python -m regimes.evaluation.evaluate_regimes

# Train & Evaluate Rainfall Correction Ladder
python -m correction.evaluation.evaluate_correction

# Run Scientific Verification Pipeline
python -m verification.verify
```

### 3. Run Automated Tests
```bash
python -m pytest -v tests/
```
*(All 22 unit and integration tests passing)*

### 4. Launch Operational Forecasting Server
```bash
python manage.py makemigrations backend
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** to view the operational dashboard.

### 5. Run Live 12-Step Demonstration
```bash
python experiments/run_end_to_end_demo.py
```

---

## 5. Repository Structure

```
VARUNA-AI/
├── weather_data/          # Member 1: Data Ingestion, Cleaning, Temporal/Spatial Alignment
├── regimes/               # Member 2: Synoptic Weather Regime Classifier (XGBoost)
├── correction/            # Member 3: Rainfall Bias Correction Model Ladder (Levels 0-3)
├── probability/           # Member 4: Calibrated Heavy Rain Exceedance Probabilities
├── uncertainty/           # Member 4: Split-Conformal Prediction Intervals (q10, q50, q90)
├── verification/          # Member 4: Scientific Verification Suite (Continuous, Categorical, FSS)
├── geospatial/            # Member 6: District Geometries & Grid-to-District Spatial Aggregation
├── backend/               # Member 5: Django Application, REST API Views, Models, Service
├── dashboard/             # Member 6: Operational Meteorological Interface (Leaflet & ECharts)
├── experiments/           # End-to-End Demonstration and Experiment Runners
├── tests/                 # Comprehensive Unit and Integration Test Suite
└── docs/                  # Full Scientific and Technical Documentation
```

---

## 6. Scientific Documentation
- [Data Dictionary & Variable Standards](docs/data_dictionary.md)
- [System Architecture](docs/architecture.md)
- [Scientific Verification Report](docs/verification_report.md)
- [REST API Specification](docs/api.md)
- [Deployment Guide](docs/deployment.md)

---
*Developed for Smart India Hackathon 2026 &bull; Ministry of Earth Sciences / IMD*
