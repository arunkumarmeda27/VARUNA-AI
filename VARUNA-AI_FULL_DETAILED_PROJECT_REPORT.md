# VARUNA-AI
## Regime-Aware AI System for Monsoon Rainfall Forecast Post-Processing

**Detailed Project Report**

---

# 1. Executive Summary

VARUNA-AI is a scientific and engineering system designed to improve the usability of rainfall forecasts produced by Numerical Weather Prediction (NWP) models.

Rainfall forecast errors vary across meteorological conditions such as active monsoon, break monsoon, monsoon lows and depressions, coastal rainfall, orographic rainfall, and western disturbances. A single correction method may therefore not perform equally well in every situation.

VARUNA-AI introduces a **regime-aware post-processing pipeline**. The system identifies the prevailing weather regime and then uses regime information, raw NWP forecasts, meteorological features, and historical forecast-error patterns to perform adaptive machine-learning-based rainfall correction.

The system then:

- Estimates heavy rainfall probability.
- Verifies forecasts against observations.
- Calculates scientific verification metrics.
- Produces district-level interpretations from grid-level information.
- Presents results through an operational analytical interface.

VARUNA-AI does not replace an NWP model. It acts as an **intelligent post-processing, verification, and operational interpretation layer**.

> **The core idea is to adapt forecast correction to the prevailing meteorological situation instead of assuming that one correction strategy works equally well everywhere.**

---

# 2. Problem Statement

## SIH26080: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

Rainfall forecast errors over India vary according to weather regimes, including:

- Active monsoon
- Break monsoon
- Monsoon lows and depressions
- Orographic rainfall
- Coastal rainfall
- Western disturbances

A single bias-correction method may not work equally well across all these situations.

The challenge is to build an AI/ML-based rainfall post-processing system that:

1. Identifies the prevailing weather regime.
2. Applies an appropriate correction to raw NWP rainfall forecasts.
3. Improves grid-level or district-level rainfall forecasts.
4. Improves forecasting of heavy and very heavy rainfall.
5. Provides probability estimates for operational rainfall thresholds.
6. Demonstrates improvement through scientific verification.

---

# 3. Project Objectives

## Primary Objectives

### 3.1 Weather Regime Classification

Identify the meteorological situation associated with a forecast.

Candidate regimes include:

- Active monsoon
- Break monsoon
- Monsoon low/depression
- Coastal rainfall
- Orographic rainfall
- Western disturbance

### 3.2 Adaptive Rainfall Post-Processing

Improve raw NWP rainfall forecasts by incorporating regime information.

### 3.3 Heavy Rainfall Probability

Estimate the probability that rainfall will exceed selected operational thresholds.

### 3.4 Scientific Verification

Compare:

```text
Raw NWP Forecast
        vs
Corrected Forecast
        vs
Observed Rainfall
```

### 3.5 District-Level Product

Convert or interpret gridded forecast information at district level.

---

# 4. Project Scope

The project focuses on the post-processing stage of rainfall forecasting.

```text
NWP Forecast
    |
    v
Scientific Data Preparation
    |
    v
Weather Regime Identification
    |
    v
Adaptive ML Correction
    |
    v
Corrected Rainfall Forecast
    |
    +-------------------+
    |                   |
    v                   v
Heavy Rainfall      Scientific
Probability         Verification
    |                   |
    +---------+---------+
              |
              v
   District-Level Forecast Product
```

The project does not attempt to simulate the entire atmosphere or replace the physical NWP model.

The NWP system generates the initial forecast. VARUNA-AI improves its operational interpretation through post-processing.

---

# 5. Why This Problem Matters

Rainfall forecasts affect:

- Disaster management
- Flood preparedness
- Agriculture
- Reservoir operations
- Urban drainage planning
- Transportation
- Emergency response

The value of improved post-processing is not only lower numerical error.

A better forecast can provide earlier and more reliable warning of potentially dangerous rainfall.

Example:

```text
Raw Forecast:
Moderate rainfall

Actual Event:
Very heavy rainfall

Operational Risk:
Insufficient preparedness
```

A useful corrected output could instead indicate:

```text
High probability of heavy rainfall

Operational Meaning:
Elevated risk requiring attention
```

---

# 6. Core Scientific Concept

A generic correction system assumes:

```text
All Weather Conditions
        |
        v
One Correction Model
        |
        v
Corrected Forecast
```

VARUNA-AI introduces meteorological context:

```text
Weather Conditions
        |
        v
Regime Classification
        |
        v
Regime-Aware Processing
        |
        v
Corrected Forecast
```

The central question becomes:

> **What weather regime is occurring, and how has the forecast system historically behaved under similar conditions?**

---

# 7. System Architecture

```text
                        DATA SOURCES
                             |
          +------------------+------------------+
          |                  |                  |
       NWP DATA         OBSERVATIONS        GEO DATA
          |                  |                  |
          +------------------+------------------+
                             |
                             v
                  SCIENTIFIC DATA PIPELINE
                             |
                Xarray + NumPy + Pandas
                             |
                             v
                TEMPORAL / SPATIAL ALIGNMENT
                             |
                             v
                    FEATURE ENGINEERING
                             |
                             v
                  WEATHER REGIME CLASSIFIER
                             |
                             v
                 REGIME-AWARE CORRECTION
                             |
                             v
                  CORRECTED RAINFALL OUTPUT
                             |
                 +-----------+-----------+
                 |                       |
                 v                       v
          HEAVY RAIN PROBABILITY    VERIFICATION
                 |                       |
                 +-----------+-----------+
                             |
                             v
                   DISTRICT-LEVEL PRODUCT
                             |
                             v
                    POSTGRESQL + POSTGIS
                             |
                             v
                           DJANGO
                             |
                 +-----------+-----------+
                 |                       |
                 v                       v
               LEAFLET                 ECHARTS
```

---

# 8. Data Requirements

## 8.1 NWP Data

Possible input variables may include:

- Rainfall forecasts
- Temperature
- Humidity
- Wind components
- Pressure-related variables
- Forecast lead time
- Other available meteorological variables

The exact dataset depends on the data available for the project.

## 8.2 Observed Rainfall

Observed rainfall is required for:

- Model training
- Historical error analysis
- Forecast verification
- Heavy rainfall event evaluation

## 8.3 Geographic Data

Possible requirements include:

- District boundaries
- Forecast grid coordinates
- Elevation or terrain information where relevant
- Coastal proximity information where relevant

---

# 9. Data Engineering Pipeline

## 9.1 Data Ingestion

Input formats may include:

```text
GRIB
NetCDF
CSV
GeoJSON / Shapefile
```

Recommended tooling:

```text
cfgrib
netCDF4
pandas
geopandas
```

## 9.2 Data Standardization

The pipeline should validate:

- Variable names
- Units
- Missing values
- Timestamps
- Coordinate systems
- Latitude ordering
- Longitude conventions
- Forecast lead times

## 9.3 Temporal Alignment

Forecast values must be compared with observations at the same valid time.

```text
Forecast Initialization
        +
Forecast Lead Time
        |
        v
Forecast Valid Time
        |
        v
Matching Observation
```

## 9.4 Spatial Alignment

Different datasets may have different resolutions.

```text
Forecast Grid
      |
      v
Spatial Alignment
      |
      v
Observation Grid / Point
```

Possible methods include:

- Nearest-neighbour matching
- Interpolation
- Regridding
- Grid aggregation

The selected method must be documented.

---

# 10. Weather Regime Classification

The regime classifier receives meteorological and geographical features.

```text
Meteorological Variables
        +
NWP Forecast Features
        +
Geographical Features
        |
        v
Feature Engineering
        |
        v
Regime Classification Model
        |
        v
Predicted Weather Regime
```

Example:

```text
Active Monsoon:       0.71
Depression:           0.17
Coastal Rainfall:     0.06
Break Monsoon:        0.04
Other:                0.02
```

Selected regime:

```text
ACTIVE MONSOON
```

---

# 11. Regime Classification Model Strategy

The project should follow a baseline-first approach.

```text
Baseline:
Logistic Regression

Alternative:
Random Forest

Candidate:
XGBoost
```

Evaluation may include:

- Accuracy
- Precision
- Recall
- F1 score
- Confusion matrix
- Class-wise performance

Class imbalance must be analyzed because some regimes may occur less frequently.

---

# 12. Rainfall Bias Correction

The correction stage uses:

```text
Raw NWP Rainfall
        +
Predicted Regime
        +
Meteorological Features
        +
Historical Error Features
        |
        v
Correction Model
        |
        v
Corrected Rainfall Forecast
```

The purpose is to reduce systematic or regime-dependent forecast errors.

---

# 13. Model Experiment Strategy

The project should compare multiple approaches.

```text
Experiment 0:
Raw NWP Forecast

Experiment 1:
Statistical Bias Correction

Experiment 2:
Linear Regression

Experiment 3:
Random Forest

Experiment 4:
XGBoost

Experiment 5:
Regime-Aware ML Correction
```

The final approach should be selected through verification, not assumption.

---

# 14. Regime-Aware Model Designs

## Design A: Unified Model

```text
Raw Forecast
      +
Meteorological Features
      +
Regime Feature
      |
      v
Single ML Model
      |
      v
Corrected Forecast
```

## Design B: Regime-Specific Routing

```text
Regime Classifier
       |
       v
Model Router
       |
       +-- Active Monsoon -> Model A
       +-- Depression -> Model B
       +-- Coastal -> Model C
```

The final design depends on experimental results and data availability.

---

# 15. Heavy Rainfall Probability

For a selected threshold T, the system estimates:

```text
P(Rainfall > T)
```

Possible output:

```text
Heavy Rainfall Probability: 0.64
```

This can support operational interpretation.

```text
Corrected Rainfall
        +
Meteorological Features
        |
        v
Probability Estimation
        |
        v
Threshold Exceedance Probability
```

---

# 16. Forecast Verification

Verification is a core component.

```text
Raw NWP Forecast
        |
        +----------------+
                         |
                         v
                  Observed Rainfall
                         ^
                         |
        +----------------+
        |
Corrected Forecast
```

The goal is to determine whether post-processing produces measurable improvement.

---

# 17. Verification Metrics

## RMSE

Measures the magnitude of prediction errors.

```text
Lower RMSE
=
Closer forecast values
```

## ETS

Equitable Threat Score evaluates event prediction while accounting for random chance.

## CSI

Critical Success Index evaluates successful event detection.

## POD

Probability of Detection measures how often actual events were forecast.

```text
Higher POD
=
More actual events detected
```

## FAR

False Alarm Ratio measures how often predicted events did not occur.

```text
Lower FAR
=
Fewer false alarms
```

## FSS

Fractions Skill Score evaluates spatial forecast skill.

---

# 18. Scientific Evaluation Questions

The project should answer:

1. Does regime-aware processing reduce RMSE compared with raw NWP?
2. Does it improve heavy rainfall event detection?
3. Does improvement differ across weather regimes?
4. Does it reduce systematic bias?
5. Does it improve spatial representation?
6. Which correction approach performs best?
7. Which weather regimes remain difficult?

---

# 19. District-Level Processing

Forecast grids must be interpreted using district boundaries.

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
District-Level Product
```

Possible aggregation approaches:

- Area-weighted average
- Mean
- Maximum
- Threshold-based risk classification

The final method should be documented based on the available data and operational requirement.

---

# 20. Scientific Data Stack

## Python

Primary language for scientific computing and application logic.

## Xarray

Used for multidimensional datasets:

```text
Time
Latitude
Longitude
Forecast Lead Time
Pressure Level
Meteorological Variables
```

## NumPy

Numerical operations.

## Pandas

Tabular data and reports.

## Dask

Used only when dataset size requires chunked or parallel processing.

---

# 21. Machine Learning Stack

## Scikit-learn

Used for:

- Preprocessing
- Baselines
- Validation
- Evaluation

## XGBoost

Used as a candidate model for:

- Regime classification
- Rainfall correction
- Heavy rainfall probability

XGBoost should be validated against simpler baselines.

---

# 22. Geospatial Stack

```text
GeoPandas
Shapely
Rasterio
PostgreSQL
PostGIS
```

Responsibilities:

```text
GeoPandas -> Vector geospatial processing
Shapely   -> Geometry operations
Rasterio  -> Raster/grid processing
PostGIS   -> Persistent spatial operations
```

---

# 23. Application Architecture

## Django

Django manages:

- Application workflows
- Routing
- User access
- Database models
- Operational interface
- Integration with scientific modules

## Celery + Redis

Used for long-running operations.

```text
Django Request
      |
      v
Celery Task
      |
      v
Scientific Processing
      |
      v
ML Inference
      |
      v
Verification
      |
      v
Database
```

---

# 24. Firebase Integration

Firebase is included as a supporting application technology.

## Primary Use

```text
Firebase Authentication
```

Responsibilities:

- User registration
- Secure sign-in
- Authentication tokens
- Optional identity providers

Flow:

```text
User
  |
  v
Firebase Authentication
  |
  v
Authenticated Identity
  |
  v
Django Application
```

Firebase is **not** the primary scientific database.

---

# 25. Why Firebase Is Not the Core Data Platform

VARUNA-AI requires:

```text
Rainfall Grid
      +
District Boundary
      |
      v
Spatial Query
      |
      v
District Aggregation
```

It also requires relational scientific records.

Therefore:

```text
PostgreSQL + PostGIS
```

remain the primary scientific and geospatial storage layer.

Responsibility separation:

```text
Firebase
    -> User identity

Django
    -> Application workflow

PostgreSQL/PostGIS
    -> Scientific and geospatial data
```

---

# 26. User Interface

The interface should be operational and analytical.

Use:

```text
Django Templates
HTML
CSS
Vanilla JavaScript
```

Avoid:

- Marketing-style pages
- Excessive gradients
- Decorative cards
- Unnecessary animations
- Features unrelated to forecasting

The interface should focus on:

```text
Information
    ->
Interpretation
    ->
Verification
    ->
Decision Support
```

---

# 27. Visualization

## Leaflet

Used for:

- District boundaries
- Forecast layers
- Corrected rainfall
- Heavy rainfall probability
- Geographic inspection

## Apache ECharts

Used for:

- Forecast comparison
- Time series
- Verification metrics
- Probability trends
- Regime statistics

---

# 28. Database Design

Suggested entities:

```text
forecast_runs
raw_forecasts
observations
regime_predictions
corrected_forecasts
probability_products
verification_metrics
district_boundaries
```

Relationship:

```text
forecast_run
    |
    +-- raw_forecasts
    +-- regime_predictions
    +-- corrected_forecasts
    +-- probability_products
    +-- verification_metrics
```

---

# 29. Security Model

```text
User Login
    |
    v
Firebase Authentication
    |
    v
Authentication Token
    |
    v
Django Validation
    |
    v
Authorized Access
```

Django remains responsible for protected application operations and authorization rules.

---

# 30. Testing Strategy

## Unit Tests

Test:

- Data transformations
- Feature engineering
- Model inputs
- Metric calculations
- Spatial calculations

## Integration Tests

Test:

- Data ingestion
- ML pipeline
- Database operations
- Authentication integration
- Background processing

## Validation Tests

Test:

- Forecast-observation alignment
- Threshold classification
- District aggregation
- Verification reproducibility

Framework:

```text
Pytest
```

---

# 31. Repository Structure

```text
varuna-ai/
|
├── config/
|
├── authentication/
|   └── firebase/
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
|
├── verification/
|   ├── continuous.py
|   ├── categorical.py
|   └── spatial.py
|
├── geospatial/
|   ├── districts/
|   ├── grids/
|   └── aggregation/
|
├── tasks/
|
├── dashboard/
|   ├── templates/
|   └── static/
|
├── tests/
|
├── docker/
|
├── requirements/
|
└── README.md
```

---

# 32. Deployment

Docker can provide a reproducible environment.

```text
Docker Compose
      |
      +-- Django
      +-- PostgreSQL + PostGIS
      +-- Redis
      +-- Celery Worker
```

Nginx may be used as a reverse proxy.

The deployment should remain simple unless a genuine scaling requirement exists.

---

# 33. Technology Responsibility Matrix

| Technology | Responsibility |
|---|---|
| Python | Core implementation |
| Xarray | Multidimensional weather data |
| NumPy | Numerical computation |
| Pandas | Tabular analysis |
| Dask | Large data processing when required |
| cfgrib | GRIB reading |
| netCDF4 | NetCDF reading |
| Scikit-learn | ML preprocessing and evaluation |
| XGBoost | Candidate predictive models |
| GeoPandas | Vector geospatial processing |
| Shapely | Geometry operations |
| Rasterio | Grid/raster processing |
| PostgreSQL | Structured data |
| PostGIS | Spatial operations |
| Django | Application workflow |
| Firebase Auth | User identity |
| Celery | Background computation |
| Redis | Task infrastructure |
| Leaflet | Maps |
| ECharts | Scientific charts |
| Pytest | Testing |
| Docker | Reproducible deployment |
| Nginx | Reverse proxy |
| Git | Version control |

---

# 34. Risks and Challenges

## Data Availability

High-quality historical forecast and observation data may be required.

**Mitigation:**

- Define requirements early.
- Build reproducible ingestion.
- Document data sources and periods.

## Data Alignment

Datasets may differ in time, resolution, coordinates, and units.

**Mitigation:**

- Explicit alignment procedures.
- Automated validation checks.

## Class Imbalance

Some weather regimes may be rare.

**Mitigation:**

- Analyze class distribution.
- Use class-wise evaluation.

## Extreme Event Scarcity

Heavy rainfall events may occur less frequently.

**Mitigation:**

- Use event-specific metrics.
- Evaluate threshold performance separately.

## Overfitting

Models may perform well on training data but fail on unseen periods.

**Mitigation:**

- Temporal validation.
- Strict train/test separation.
- Baseline comparison.

## Spatial Errors

Incorrect grid-to-district processing can produce misleading results.

**Mitigation:**

- Validate geometries.
- Document aggregation.
- Test representative districts.

---

# 35. Development Phases

## Phase 1: Data Foundation

```text
Data acquisition
    ->
Data inspection
    ->
GRIB/NetCDF ingestion
    ->
Temporal alignment
    ->
Spatial alignment
```

## Phase 2: Baseline Evaluation

```text
Raw NWP
    ->
Observation comparison
    ->
Verification metrics
```

## Phase 3: Regime Classification

```text
Feature design
    ->
Baseline models
    ->
Candidate models
    ->
Evaluation
```

## Phase 4: Bias Correction

```text
Statistical baseline
    ->
Standard ML
    ->
Regime-aware ML
    ->
Comparison
```

## Phase 5: Heavy Rainfall Probability

```text
Threshold definition
    ->
Probability estimation
    ->
Event verification
```

## Phase 6: District Product

```text
Forecast grid
    ->
District geometry
    ->
Aggregation
    ->
Operational product
```

## Phase 7: Application Integration

```text
Django
    ->
Firebase Authentication
    ->
Celery
    ->
Database
    ->
Operational interface
```

## Phase 8: Final Verification

```text
Raw vs Corrected
    ->
Metric comparison
    ->
Regime-wise analysis
    ->
Final report
```

---

# 36. Final Architecture

```text
                             USER
                              |
                              v
                       FIREBASE AUTH
                              |
                              v
                           DJANGO
                              |
              +---------------+---------------+
              |                               |
              v                               v
       APPLICATION FLOW               PROCESSING REQUEST
                                              |
                                              v
                                           CELERY
                                              |
                                              v
                                            REDIS
                                              |
                                              v
                    SCIENTIFIC PROCESSING PIPELINE
                                              |
             +--------------------------------+-------------------------------+
             |                                |                               |
           NWP DATA                     OBSERVATIONS                       GEO DATA
             |                                |                               |
             +--------------------------------+-------------------------------+
                                              |
                                              v
                              XARRAY / NUMPY / PANDAS
                                              |
                                              v
                              TEMPORAL / SPATIAL ALIGNMENT
                                              |
                                              v
                                  FEATURE ENGINEERING
                                              |
                                              v
                               WEATHER REGIME CLASSIFICATION
                                              |
                                              v
                              REGIME-AWARE BIAS CORRECTION
                                              |
                                              v
                                CORRECTED RAINFALL FORECAST
                                              |
                              +---------------+---------------+
                              |                               |
                              v                               v
                     HEAVY RAIN PROBABILITY              VERIFICATION
                              |                               |
                              +---------------+---------------+
                                              |
                                              v
                                  POSTGRESQL + POSTGIS
                                              |
                                              v
                                     DJANGO INTERFACE
                                              |
                              +---------------+---------------+
                              |                               |
                              v                               v
                           LEAFLET                         ECHARTS
```

---

# 37. Success Criteria

VARUNA-AI should demonstrate:

## Technical Success

- Successful scientific data ingestion.
- Reproducible preprocessing.
- Working regime classification.
- Working forecast correction.
- Heavy rainfall probability output.
- District-level product.

## Scientific Success

- Comparison against raw NWP.
- Appropriate verification metrics.
- Reproducible evaluation.
- Regime-wise performance analysis.

## Engineering Success

- Modular architecture.
- Automated testing of critical components.
- Reproducible environment.
- Clear responsibility separation.

---

# 38. Final Conclusion

VARUNA-AI is designed as a scientifically grounded rainfall forecast post-processing system.

Its core workflow combines:

```text
Weather Regime Understanding
        +
Scientific Data Processing
        +
Adaptive Machine Learning
        +
Rainfall Forecast Correction
        +
Heavy Rainfall Probability
        +
Scientific Verification
        +
Geospatial District Interpretation
```

The system deliberately separates responsibilities:

```text
Firebase
    -> User identity

Django
    -> Application workflow

Python + Xarray
    -> Scientific weather processing

Machine Learning
    -> Regime classification and adaptive correction

PostgreSQL + PostGIS
    -> Scientific and geospatial data

Celery
    -> Long-running computation

Leaflet
    -> Geographical interpretation

ECharts
    -> Scientific visualization
```

The strength of VARUNA-AI does not come from using a large number of frameworks.

It comes from:

1. A scientifically valid data pipeline.
2. Correct spatial and temporal alignment.
3. Regime-aware forecast correction.
4. Rigorous comparison with baseline methods.
5. Measurable verification of forecast skill.
6. A useful district-level operational product.

> **VARUNA-AI succeeds when it can demonstrate, with reproducible scientific evidence, that meteorological regime awareness improves the post-processing and operational interpretation of rainfall forecasts.**
