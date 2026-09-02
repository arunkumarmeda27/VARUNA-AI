# VARUNA-AI: Execution and Deployment Guide

**Smart India Hackathon 2026 | Problem Statement: SIH26080**  
This guide provides complete, friction-free instructions to run, evaluate, test, and containerize **VARUNA-AI** in any environment.

---

## Quick Navigation
1. [Method 1: Docker (Zero-Setup / Recommended for Evaluators)](#method-1-docker-zero-setup---recommended-for-evaluators)
2. [Method 2: Local Python Environment](#method-2-local-python-environment-windows--linux--macos)
3. [Method 3: Running the Automated Test Suite](#method-3-running-the-automated-test-suite)
4. [Method 4: Running the Live 12-Step Forecast CLI Demonstration](#method-4-running-the-live-12-step-forecast-cli-demonstration)
5. [Method 5: REST API Verification via cURL](#method-5-rest-api-verification-via-curl)

---

## Method 1: Docker (Zero-Setup - Recommended for Evaluators)

With Docker, everything (system dependencies, Python libraries, dataset building, model training, and database migrations) is handled automatically inside the container.

### Step 1: Clone the repository & navigate to directory
```bash
git clone https://github.com/arunkumarmeda27/VARUNA-AI.git
cd VARUNA-AI
```

### Step 2: Build and start the container
```bash
docker-compose up --build
```

### Step 3: Access the platform
Once started, open your web browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)** (or direct login at **[http://localhost:8000/login/](http://localhost:8000/login/)**)

#### Firebase Authentication & Operational Access:
- **Instant Demo Access**: Click `⚡ Instant Demo Access (Meteorological Evaluation Mode)` for immediate 1-click evaluation access.
- **Email & Password**: Register a new Meteorological Officer account or sign in with existing credentials.
- **Google OAuth**: One-click sign-in via Google accounts.

To stop the container:
```bash
docker-compose down
```

---

## Method 2: Local Python Environment (Windows / Linux / macOS)

### Prerequisites
- Python **3.10**, **3.11**, **3.12**, **3.13**, or **3.14** installed.
- Git installed.

### Step 1: Clone the repository
```bash
git clone https://github.com/arunkumarmeda27/VARUNA-AI.git
cd VARUNA-AI
```

### Step 2: (Optional but recommended) Create a Virtual Environment
**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Build Master Datasets and Train the Model Ladder
Run the automated vertical pipeline commands in sequence:
```bash
# 1. Ingest, validate, and build master datasets (2018-2024)
python -m weather_data.master_dataset_builder

# 2. Train & evaluate Weather Regime Classifier
python -m regimes.evaluation.evaluate_regimes

# 3. Train & evaluate Rainfall Post-Processing Model Ladder (Levels 0-3)
python -m correction.evaluation.evaluate_correction

# 4. Run full Scientific Verification Suite
python -m verification.verify
```

### Step 5: Initialize Database & Run Server
```bash
python manage.py makemigrations backend
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## Method 3: Running the Automated Test Suite

VARUNA-AI includes a comprehensive, leak-proof test suite covering physical data validation, regime classification, post-processing models, probability estimators, verification math, and REST API endpoints.

Execute all tests with:
```bash
python -m pytest -v tests/
```

**Expected Output:**
```text
============================= test session starts =============================
collected 22 items

tests/test_api.py::TestForecastAPI::test_dashboard_home_page PASSED      [  4%]
tests/test_api.py::TestForecastAPI::test_districts_endpoint PASSED       [  9%]
tests/test_api.py::TestForecastAPI::test_health_endpoint PASSED          [ 13%]
tests/test_api.py::TestForecastAPI::test_latest_forecast_endpoint PASSED [ 18%]
tests/test_api.py::TestForecastAPI::test_models_registry_endpoint PASSED [ 22%]
tests/test_api.py::TestForecastAPI::test_verification_benchmarks_endpoint PASSED [ 27%]
tests/test_correction.py::test_level0_raw_nwp PASSED                     [ 31%]
tests/test_correction.py::test_level1_quantile_mapping PASSED            [ 36%]
tests/test_correction.py::test_correction_engine_pipeline PASSED         [ 40%]
tests/test_data.py::test_data_validator_non_negativity PASSED            [ 45%]
tests/test_data.py::test_data_leakage_assertion PASSED                   [ 50%]
tests/test_data.py::test_temporal_chronological_splits PASSED            [ 54%]
tests/test_data.py::test_spatial_reference_grid_generation PASSED        [ 59%]
tests/test_features.py::test_synoptic_feature_computation PASSED         [ 63%]
tests/test_geospatial.py::test_districts_geojson_validity PASSED         [ 68%]
tests/test_geospatial.py::test_grid_to_district_aggregation PASSED       [ 72%]
tests/test_probability.py::test_heavy_rainfall_probability_estimator PASSED [ 77%]
tests/test_probability.py::test_conformal_uncertainty_estimator PASSED   [ 81%]
tests/test_regime.py::test_regime_classifier_inference PASSED            [ 86%]
tests/test_verification.py::test_continuous_metrics PASSED               [ 90%]
tests/test_verification.py::test_contingency_and_categorical_scores PASSED [ 95%]
tests/test_verification.py::test_fractions_skill_score PASSED            [100%]

============================= 22 passed in 5.01s ==============================
```

---

## Method 4: Running the Live 12-Step Forecast CLI Demonstration

To experience the complete end-to-end scientific forecast journey in the terminal without opening a browser:

```bash
python experiments/run_end_to_end_demo.py
```

This interactive script demonstrates:
1. Forecast run cycle ingestion (+24h lead time).
2. Raw NWP precipitation input.
3. Synoptic weather regime classification (Active Monsoon, Break, Low/Depression, etc.).
4. Regime probability distribution.
5. Multi-level rainfall correction execution (Level 0 $\to$ Level 1 $\to$ Level 2 $\to$ Level 3 VARUNA-AI).
6. Corrected rainfall and bias delta ($R_{corr} - R_{raw}$).
7. Calibrated heavy rain probability ($P(R \ge 64.5\text{mm})$).
8. 80% Conformal uncertainty interval ($[q_{10}, q_{90}]$).
9. Area-weighted grid-to-district spatial aggregation.
10. Ground truth observation comparison and percentage error reduction.
11. Independent test season verification summary (MAE, RMSE, CSI, POD, FAR).
12. Model provenance and reproducibility audit trail.

---

## Method 5: REST API Verification via cURL

While the server is running, you can test the REST API endpoints:

### 1. System Health Check
```bash
curl http://localhost:8000/api/v1/health/
```

### 2. Get Latest Forecast Run
```bash
curl http://localhost:8000/api/v1/forecasts/latest/
```

### 3. Get District List & GeoJSON
```bash
curl http://localhost:8000/api/v1/districts/
```

### 4. Get Specific District Forecast (e.g., Mumbai Suburban)
```bash
curl http://localhost:8000/api/v1/districts/DIST_MH_MUM/forecast/
```

### 5. Get Scientific Verification Benchmarks
```bash
curl http://localhost:8000/api/v1/verification/
```

### 6. Get Model Registry & Provenance
```bash
curl http://localhost:8000/api/v1/models/
```

---

## Operational Features on the Web Dashboard

1. **Interactive Leaflet Choropleth Map**:
   - Switch layers: **VARUNA Corrected**, **Raw NWP**, **P(Rain $\ge$ 64.5mm)**, **IMD Risk Alert**, **Bias Delta ($\Delta$)**.
   - Hover over districts (e.g. Mumbai, Ratnagiri, Wayanad, Pune, Nagpur, Cuttack, Patna, Dehradun, Jaipur) to view real-time rainfall comparisons, 80% conformal uncertainty intervals, and risk advice.
2. **Synoptic Diagnostics Radar**:
   - Live inspection of MSLP isobar depth, Low-Level Somali Jet (850 hPa), Tropical Easterly Jet (200 hPa), Deep Tropospheric Shear, Total Column Water Vapour, and Monsoon Trough latitude position.
3. **ECharts Scientific Verification Explorer**:
   - Interactive Critical Success Index (CSI) threshold curves comparing Raw NWP vs VARUNA-AI.
   - Model Ladder MAE/RMSE error comparison charts.
4. **Model Provenance & Reproducibility Audit**:
   - Full tracking of dataset version (`v1.0.0`), model checksums, feature sets, and training/test splits.
