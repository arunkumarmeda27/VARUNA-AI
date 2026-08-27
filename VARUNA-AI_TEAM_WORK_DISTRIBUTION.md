# VARUNA-AI — Team Work Distribution

## SIH26080: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

**Team Size:** 6 Members

---

## 1. Team Structure

VARUNA-AI should be developed as one connected system, not as six separate mini-projects.

| Member | Role | Primary Ownership |
|---|---|---|
| Member 1 | Meteorological Data Engineer | Weather/NWP data, cleaning, alignment, feature datasets |
| Member 2 | Weather Regime ML Engineer | Weather regime classification |
| Member 3 | Rainfall Post-Processing ML Engineer | AI rainfall bias correction |
| Member 4 | Uncertainty, Risk & Verification Engineer | Heavy-rain probability, uncertainty, risk, scientific evaluation |
| Member 5 | Backend & ML Integration Engineer | Django, Firebase Auth, APIs, database, model integration |
| Member 6 | Geospatial & Visualization Engineer | District processing, maps, charts, operational UI |

---

## 2. Overall Dependency

```text
                    MEMBER 1
              METEOROLOGICAL DATA
                       |
                       v
              ML-READY DATASET
                       |
             +---------+---------+
             |                   |
             v                   v
         MEMBER 2             MEMBER 3
      REGIME CLASSIFIER    RAINFALL CORRECTION
             |                   |
             +---------+---------+
                       |
                       v
                   MEMBER 4
        PROBABILITY + UNCERTAINTY
                 + VERIFICATION
                       |
             +---------+---------+
             |                   |
             v                   v
         MEMBER 5             MEMBER 6
       BACKEND/ML            GEO + UI
       INTEGRATION
             |                   |
             +---------+---------+
                       |
                       v
                  VARUNA-AI
```

Members must integrate continuously rather than waiting until the final stage.

---

## 3. Member 1 — Meteorological Data Engineer

### Primary Responsibility

Own the scientific data foundation.

### Responsibilities

- Collect historical observed rainfall.
- Collect NWP rainfall forecasts.
- Collect available weather variables such as temperature, humidity, wind and pressure.
- Handle missing values and invalid records.
- Standardize units and timestamps.
- Align NWP forecasts with observations by valid time.
- Align spatial grids.
- Create training, validation and testing datasets.
- Engineer common features for the ML models.
- Prevent future-data leakage through chronological splitting.
- Maintain a data dictionary and source documentation.

### Technologies

```text
Python
Xarray
Pandas
NumPy
Dask when required
cfgrib
netCDF4
GeoPandas
```

### Deliverables

```text
data/
preprocessing/
feature_generation/
data_dictionary.md
dataset_notes.md
```

### Handoff

Provide stable, ML-ready datasets and feature definitions to Members 2, 3 and 4.

---

## 4. Member 2 — Weather Regime ML Engineer

### Primary Responsibility

Build **Model 1: Weather Regime Classifier**.

### Objective

Answer:

> What type of weather situation is happening?

### Candidate Regimes

Depending on available data:

- Active monsoon
- Break monsoon
- Monsoon low/depression
- Coastal rainfall
- Orographic rainfall
- Western disturbance

### Responsibilities

- Define usable regime classes.
- Select and engineer regime features.
- Establish baseline classifiers.
- Train candidate ML models.
- Handle class imbalance.
- Generate regime probabilities/confidence.
- Produce confusion matrices and class-wise metrics.
- Package model inference code.

### Technologies

```text
Python
Scikit-learn
XGBoost
Pandas
NumPy
```

### Deliverables

```text
regimes/
regime_inference.py
regime_metrics/
evaluation_report.md
```

### Handoff

Supply predicted regime and confidence to Member 3.

Provide packaged inference to Member 5.

---

## 5. Member 3 — Rainfall Post-Processing ML Engineer

### Primary Responsibility

Build **Model 2: Regime-Aware Rainfall Correction**.

### Objective

Answer:

> How should the raw NWP rainfall forecast be corrected?

### Input

```text
Raw NWP Rainfall
+
Meteorological Features
+
Detected Weather Regime
+
Historical Forecast Error Features
```

### Output

```text
Corrected Rainfall Forecast
```

Example:

```text
Raw NWP:       42 mm
Regime:        Active Monsoon
AI Corrected:  61 mm
```

### Responsibilities

- Establish raw NWP baseline.
- Test statistical correction.
- Test linear regression.
- Test random forest.
- Test XGBoost.
- Test regime-aware correction.
- Compare unified versus regime-specific approaches.
- Prevent forecast-time information leakage.
- Measure MAE, RMSE and bias.
- Analyze correction performance by regime.

### Technologies

```text
Python
XGBoost
Scikit-learn
Pandas
NumPy
Xarray
```

### Deliverables

```text
correction/
    baselines/
    models/
    evaluation/

correction_inference.py
model_comparison_report.md
```

### Handoff

Provide corrected forecasts and inference code to Members 4 and 5.

Provide required output definitions to Member 6.

---

## 6. Member 4 — Uncertainty, Risk & Verification Engineer

### Primary Responsibility

Own heavy-rainfall probability, uncertainty, risk and scientific proof.

### A. Heavy Rainfall Probability

Estimate:

```text
P(Rainfall > Threshold)
```

Example:

```text
Heavy Rain Probability: 76%
```

### B. Uncertainty

Produce a forecast with an interpretable range.

Example:

```text
Forecast: 86 mm
Prediction Range: 76–94 mm
Confidence: High
```

### C. Risk Engine

Use documented and validated thresholds to classify:

```text
Low
Moderate
High
Extreme
```

### D. Scientific Verification

Compare:

```text
Raw NWP
    vs
VARUNA-AI
    vs
Observed Rainfall
```

Calculate:

- RMSE
- MAE
- Bias
- ETS
- CSI
- POD
- FAR
- FSS

### E. Regime-Wise Evaluation

Example:

```text
                         RAW NWP     VARUNA-AI
Active Monsoon              X            X
Break Monsoon               X            X
Low Pressure                X            X
Depression                  X            X
```

Answer:

> Does regime-aware correction actually improve forecast skill, and under which regimes?

### Technologies

```text
Python
Scikit-learn
Pandas
NumPy
Matplotlib
```

### Deliverables

```text
probability/
uncertainty/
verification/
evaluation_report/
scientific_charts/
```

### Handoff

Provide probability, uncertainty, risk and verification results to Members 5 and 6.

---

## 7. Member 5 — Backend & ML Integration Engineer

### Primary Responsibility

Turn all scientific components into one working application.

The backend member integrates models rather than owning the model research.

### Responsibilities

#### Django

- Application routing
- Protected pages
- Database models
- Forecast operations
- APIs
- Application workflows

#### Firebase

Use Firebase primarily for:

- Authentication
- User identity
- Login
- Authentication tokens

Firebase is not the scientific database.

#### Model Integration

Connect:

```text
Model 1 -> Regime
Model 2 -> Corrected Rainfall
Model 3 -> Probability / Risk
```

#### Database

Manage:

```text
forecast_runs
raw_forecasts
observations
regime_predictions
corrected_forecasts
probability_products
verification_metrics
district_data
```

#### Background Processing

Use:

```text
Celery
Redis
```

for long-running scientific operations.

#### API Contracts

Define stable JSON responses for Member 6.

Example:

```json
{
  "district": "Example District",
  "regime": "Active Monsoon",
  "regime_confidence": 0.81,
  "raw_nwp_mm": 42,
  "corrected_rainfall_mm": 61,
  "heavy_rain_probability": 0.76,
  "risk": "High"
}
```

### Technologies

```text
Python
Django
PostgreSQL
PostGIS
Celery
Redis
Firebase Authentication
```

### Deliverables

```text
backend/
api/
authentication/
database/
tasks/
API documentation
```

### Handoff

Provide stable APIs and integration endpoints to Member 6.

---

## 8. Member 6 — Geospatial & Visualization Engineer

### Primary Responsibility

Own the district-level product and operational interface.

### A. Grid-to-District Processing

```text
Forecast Grid
      +
District Boundary
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

Possible aggregation methods:

- Area-weighted
- Mean
- Maximum
- Threshold-based classification

The selected approach must be documented and validated.

### B. Map

Use Leaflet for:

- District boundaries
- Rainfall layers
- Corrected forecast
- Heavy rainfall probability
- Risk zones
- Observation comparison

### C. Forecast View

For each district show:

```text
Raw NWP
   ↓
Detected Regime
   ↓
AI Correction
   ↓
Corrected Rainfall
   ↓
Heavy Rain Probability
   ↓
Uncertainty
   ↓
Risk
```

### D. Verification Interface

Display:

- Raw vs corrected vs observed rainfall
- RMSE
- MAE
- Bias
- CSI
- POD
- FAR
- FSS where applicable

### Technologies

```text
Django Templates
HTML
CSS
Vanilla JavaScript
Leaflet
Apache ECharts
GeoPandas
PostGIS
```

### Deliverables

```text
dashboard/
templates/
static/
maps/
charts/
district_views/
```

---

## 9. Member-to-Member Handoffs

### Member 1 → Members 2, 3, 4

```text
Clean ML-ready dataset
Feature definitions
Data dictionary
```

### Member 2 → Member 3

```text
Detected regime
Regime probability
Inference function
```

### Member 3 → Member 4

```text
Corrected rainfall
Model outputs
Raw-vs-corrected results
```

### Members 2, 3, 4 → Member 5

```text
Models
Inference code
Input/output contracts
Model versions
```

### Member 5 → Member 6

```text
Stable APIs
Forecast data
Map data
Verification data
Risk data
```

---

## 10. Shared Data Contract

All members should agree on a common schema.

Example:

```text
forecast_id
valid_time
latitude
longitude
district_id
raw_nwp_rainfall
regime
regime_confidence
corrected_rainfall
heavy_rain_probability
prediction_lower
prediction_upper
risk_level
model_version
```

The final schema should be version-controlled.

---

## 11. Git Repository Ownership

Suggested structure:

```text
varuna-ai/
|
├── data/
├── weather_data/
├── regimes/
├── correction/
├── probability/
├── verification/
├── geospatial/
├── backend/
├── dashboard/
├── authentication/
├── tasks/
├── tests/
├── docs/
└── README.md
```

Members should work mainly inside their assigned module while contributing to shared interfaces and integration tests.

---

## 12. Development Workflow

Use short integration cycles.

### Step 1

Member 1 creates the first clean dataset.

### Step 2

Member 2 trains the first regime classifier.

### Step 3

Member 3 builds the first rainfall correction baseline.

### Step 4

Member 4 builds the first verification pipeline.

### Step 5

Member 5 integrates the models.

### Step 6

Member 6 connects district processing and visualization.

Then continuously repeat:

```text
Improve
   ↓
Integrate
   ↓
Verify
   ↓
Visualize
   ↓
Test
```

Do not postpone integration until the end.

---

## 13. First End-to-End Milestone

The first complete milestone should prove this chain using a small controlled dataset:

```text
Real Weather Dataset
       ↓
Regime Prediction
       ↓
Rainfall Correction
       ↓
Heavy Rain Probability
       ↓
Verification
       ↓
District Result
       ↓
Map
```

After this works, improve dataset scale and model sophistication.

---

## 14. What Each Member Should Be Able to Demonstrate

### Member 1

> Our weather and observation datasets are correctly processed, aligned and reproducible.

### Member 2

> Our system can identify the prevailing weather regime and quantify classification performance.

### Member 3

> Our post-processing model improves the raw NWP rainfall forecast.

### Member 4

> Our system quantifies uncertainty and provides scientific evidence of forecast improvement.

### Member 5

> All analytical components operate together through one application.

### Member 6

> Scientific outputs become an operational district-level map, forecast product and analytical interface.

---

## 15. Shared Team Rule

Do not build six isolated mini-projects.

The dependency is:

```text
Member 1
   ↓
Members 2, 3, 4
   ↓
Member 5
   ↓
Member 6
```

Feedback must also move in both directions.

Example:

```text
Member 4 discovers a data issue
        ↓
Member 1 updates preprocessing
        ↓
Models retrained
        ↓
Backend updated
        ↓
Dashboard refreshed
```

---

## 16. Definition of Done

The project is technically complete when this entire path works:

```text
NWP + Observations
        ↓
Correctly Processed Dataset
        ↓
Weather Regime Classification
        ↓
Regime-Aware Rainfall Correction
        ↓
Heavy Rainfall Probability
        ↓
Uncertainty / Confidence
        ↓
Scientific Verification
        ↓
Grid-to-District Processing
        ↓
Operational Map + Forecast
```

The team must be able to demonstrate:

```text
Raw NWP Forecast
        vs
VARUNA-AI Forecast
        vs
Observed Rainfall
```

with reproducible evaluation results.

---

## 17. Final Team Principle

The goal is not for each member to finish an independent feature.

The goal is to build one scientifically coherent system:

> **Data → Regime → Correction → Probability → Verification → District Product**

Each member owns one stage, but the success of VARUNA-AI depends on the quality of the complete chain.
