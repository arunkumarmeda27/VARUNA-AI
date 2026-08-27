# VARUNA-AI

## Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

> An adaptive scientific forecasting system that identifies the prevailing weather regime, improves NWP rainfall forecasts, estimates heavy-rainfall probability, and delivers verified district-level rainfall intelligence.

---

## About

VARUNA-AI is an AI/ML-based post-processing system for Numerical Weather Prediction (NWP) rainfall forecasts.

Rainfall forecast errors vary across weather situations such as:

- Active monsoon
- Break monsoon
- Monsoon lows and depressions
- Coastal rainfall
- Orographic rainfall
- Western disturbances

Instead of applying one correction method to every situation, VARUNA-AI first identifies the prevailing regime and then applies an appropriate rainfall post-processing strategy.

### Core principle

> **Understand the weather regime first. Correct the forecast intelligently second.**

---

## Problem Statement

**SIH26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts**

The system aims to:

1. Identify the prevailing weather regime.
2. Correct errors in raw NWP rainfall forecasts.
3. Improve grid-level and district-level rainfall forecasts.
4. Estimate the probability of heavy and very heavy rainfall.
5. Quantify prediction uncertainty where supported.
6. Verify forecast improvement using scientific metrics.

VARUNA-AI is a post-processing layer. It does not replace the underlying NWP system.

---

## System Flow

```text
NWP + Meteorological Data
          |
          v
Scientific Data Processing
          |
          v
Weather Regime Classification
          |
          v
Regime-Aware Rainfall Correction
          |
          v
Corrected Rainfall Forecast
          |
      +---+---+
      |       |
      v       v
Heavy Rain  Verification
Probability
      |       |
      +---+---+
          |
          v
District-Level Forecast
          |
          v
Operational Interface
```

---

## Main System Outputs

For each grid or district, the system can provide:

- Detected weather regime
- Regime confidence
- Raw NWP rainfall
- AI-corrected rainfall
- Heavy rainfall probability
- Prediction range / uncertainty
- Risk category
- Verification information
- District-level map data

Example:

```text
District: Example District

Regime: Active Monsoon
Regime Confidence: 81%

Raw NWP: 42 mm
Corrected Forecast: 61 mm

Heavy Rain Probability: 76%
Expected Range: 54–68 mm
Risk: High
```

The values above are illustrative only.

---

## Scientific Pipeline

### 1. Data Ingestion

Possible inputs:

- NWP rainfall forecasts
- Observed rainfall
- Temperature
- Humidity
- Wind
- Pressure
- Geographic data
- Additional meteorological variables when available

Supported formats may include:

```text
GRIB
NetCDF
CSV
GeoJSON / Shapefile
```

### 2. Data Processing

The pipeline handles:

- Missing values
- Invalid values
- Unit consistency
- Timestamp normalization
- Temporal alignment
- Spatial alignment
- Feature engineering

### 3. Weather Regime Classification

The first model determines the prevailing weather regime.

Possible classes depend on the available data and labels.

Example:

```text
Active Monsoon: 72%
Depression: 16%
Coastal: 7%
Break: 5%
```

### 4. Rainfall Bias Correction

The second model uses:

```text
Raw NWP Rainfall
+
Meteorological Features
+
Detected Regime
+
Historical Error Features
```

to produce:

```text
Corrected Rainfall Forecast
```

### 5. Heavy Rainfall Probability

The system estimates:

```text
P(Rainfall > Threshold)
```

for the selected operational threshold.

### 6. Uncertainty and Risk

Where implemented and validated, the system can provide:

```text
Forecast
+
Prediction Range
+
Confidence
+
Risk
```

### 7. Verification

The system compares:

```text
Raw NWP
    vs
VARUNA-AI
    vs
Observed Rainfall
```

---

## Verification Metrics

### Continuous

- RMSE
- MAE
- Bias

### Event-based

- ETS
- CSI
- POD
- FAR

### Spatial

- FSS where applicable

The project should also evaluate performance separately by weather regime.

The goal is not to claim that the AI is better, but to **demonstrate measurable improvement**.

---

## Regime-Wise Evaluation

A major research question is:

> **Does regime awareness actually improve forecast post-processing?**

The system should compare performance across regimes:

```text
                    Raw NWP    VARUNA-AI

Active Monsoon         X            X
Break Monsoon          X            X
Low / Depression       X            X
Coastal                X            X
Orographic             X            X
```

This analysis should identify:

- Which regimes improve most.
- Which regimes remain difficult.
- Whether one correction approach works consistently.
- Where additional modeling is required.

---

## Geospatial Processing

NWP outputs may be grid-based, while operational users may need district-level information.

```text
Forecast Grid
      +
District Geometry
      |
      v
Spatial Intersection
      |
      v
Aggregation
      |
      v
District Forecast
```

The aggregation method should be explicitly documented and validated.

Possible methods include:

- Area-weighted aggregation
- Mean
- Maximum
- Threshold-based classification

---

## Technology Stack

### Scientific Computing

```text
Python
Xarray
NumPy
Pandas
Dask when required
```

### Weather Formats

```text
cfgrib
netCDF4
```

### Machine Learning

```text
Scikit-learn
XGBoost
```

### Geospatial

```text
GeoPandas
Shapely
Rasterio
PostgreSQL
PostGIS
```

### Application

```text
Django
Celery
Redis
```

### Authentication

```text
Firebase Authentication
```

### Visualization

```text
Django Templates
HTML
CSS
Vanilla JavaScript
Leaflet
Apache ECharts
```

### Engineering

```text
Pytest
Docker
Nginx
Git
```

---

## Architecture Responsibilities

```text
Firebase
    -> User identity and authentication

Django
    -> Application workflow and access control

Python + Xarray
    -> Scientific weather data processing

Scikit-learn / XGBoost
    -> Regime classification and rainfall correction

PostgreSQL + PostGIS
    -> Scientific, operational and geospatial data

Celery + Redis
    -> Long-running processing

Leaflet
    -> Geospatial visualization

ECharts
    -> Scientific visualization
```

Firebase is intentionally not used as the primary scientific database.

---

## Repository Structure

```text
varuna-ai/
|
├── weather_data/
|   ├── ingestion/
|   ├── preprocessing/
|   ├── temporal/
|   ├── spatial/
|   └── features/
|
├── regimes/
|   ├── training/
|   ├── inference/
|   └── evaluation/
|
├── correction/
|   ├── baselines/
|   ├── models/
|   └── evaluation/
|
├── probability/
├── uncertainty/
├── verification/
|
├── geospatial/
|   ├── districts/
|   ├── grids/
|   └── aggregation/
|
├── backend/
├── authentication/
├── tasks/
├── dashboard/
├── tests/
├── docs/
|
├── README.md
├── CONTRIBUTING.md
└── .gitignore
```

---

## Development Strategy

### Phase 1 — Data Foundation

```text
Acquire
  -> Inspect
  -> Clean
  -> Align
  -> Feature Engineering
```

### Phase 2 — Baseline Evaluation

```text
Raw NWP
  -> Observed Rainfall
  -> Initial Verification
```

### Phase 3 — Regime Model

```text
Features
  -> Baselines
  -> Candidate Models
  -> Validation
```

### Phase 4 — Rainfall Correction

```text
Statistical Baseline
  -> Standard ML
  -> Regime-Aware ML
  -> Scientific Comparison
```

### Phase 5 — Probability and Uncertainty

```text
Corrected Forecast
  -> Heavy Rain Probability
  -> Uncertainty
  -> Risk
```

### Phase 6 — District Product

```text
Forecast Grid
  -> District Geometry
  -> Aggregation
  -> District Forecast
```

### Phase 7 — Application Integration

```text
Firebase Auth
  -> Django
  -> Celery
  -> ML Pipeline
  -> PostgreSQL/PostGIS
  -> Interface
```

---

## Engineering Principles

### Scientific correctness

Time, space, units, thresholds and evaluation procedures must be handled explicitly.

### No data leakage

Only information available at forecast time should be used as a model input.

### Baseline first

Every advanced approach must be compared against simpler baselines.

### Reproducibility

Dataset versions, preprocessing, model versions and evaluation procedures should be traceable.

### Measurable improvement

Forecast improvement must be demonstrated using observations and verification metrics.

### Minimal complexity

Do not add technologies or model complexity unless they solve a real problem.

---

## Team Integration

The project is organized as one pipeline:

```text
Data
  |
  v
Regime
  |
  v
Rainfall Correction
  |
  v
Probability / Uncertainty
  |
  v
Verification
  |
  v
District Product
  |
  v
Operational Interface
```

Six members own different stages, but no stage should be developed as an isolated project.

See `CONTRIBUTING.md` for the GitHub collaboration workflow.

---

## Expected Final Demonstration

The team should be able to show:

```text
1. Select a forecast period
2. Load NWP and meteorological data
3. Detect the weather regime
4. Generate corrected rainfall
5. Estimate heavy rainfall probability
6. Show uncertainty / confidence
7. Compare raw NWP with corrected forecast
8. Compare both against observations
9. Display verification metrics
10. Show the district-level result on a map
```

---

## Success Criteria

VARUNA-AI should demonstrate:

### Scientific

- Reliable data alignment
- Valid model evaluation
- Regime-wise performance analysis
- Measurable forecast improvement where achieved

### Technical

- Reproducible processing
- Stable ML inference
- Working database and geospatial pipeline
- Integrated application

### Operational

- Clear district-level forecast
- Understandable heavy-rainfall risk
- Transparent forecast provenance
- Useful map and verification views

---

## Project Vision

VARUNA-AI aims to transform rainfall forecast post-processing from a fixed correction process into an adaptive, measurable and scientifically verifiable system.

```text
UNDERSTAND
    ↓
CLASSIFY
    ↓
CORRECT
    ↓
ESTIMATE
    ↓
VERIFY
    ↓
DELIVER
```

> **VARUNA-AI — From Weather Regime to Reliable Rainfall Intelligence.**
