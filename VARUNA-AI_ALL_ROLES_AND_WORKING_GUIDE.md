# VARUNA-AI — Team Roles, Responsibilities & Working Guide

## SIH26080: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

This document defines **what each team member should do, what they are responsible for, what they must deliver, who they depend on, and how the six members work together**.

The project must be developed as **one integrated scientific system**, not as six independent mini-projects.

---

# 1. Complete Team Structure

| Member | Role | Owns |
|---|---|---|
| **1** | Meteorological Data Engineer | Weather/NWP data, cleaning, alignment, feature datasets |
| **2** | Weather Regime ML Engineer | Weather regime classification |
| **3** | Rainfall Post-Processing ML Engineer | NWP rainfall bias correction |
| **4** | Uncertainty, Risk & Verification Engineer | Heavy-rain probability, uncertainty, risk and scientific evaluation |
| **5** | Backend & ML Integration Engineer | Django, Firebase Authentication, APIs, database, model integration |
| **6** | Geospatial & Visualization Engineer | District processing, maps, charts and operational interface |

---

# 2. How the Team Works

The complete system is:

```text
                MEMBER 1
           DATA FOUNDATION
                  |
                  v
          CLEAN ML DATASET
                  |
          +-------+-------+
          |               |
          v               v
      MEMBER 2         MEMBER 3
    REGIME MODEL    RAINFALL MODEL
          |               |
          +-------+-------+
                  |
                  v
              MEMBER 4
       PROBABILITY + RISK
          + VERIFICATION
                  |
          +-------+-------+
          |               |
          v               v
      MEMBER 5         MEMBER 6
      BACKEND          GEO + UI
          |               |
          +-------+-------+
                  |
                  v
              VARUNA-AI
```

### The key rule

**Each member owns a component, but every component must connect to the next stage.**

No one should develop a feature without defining:

- Inputs
- Outputs
- Data format
- Dependencies
- Tests
- Handoff requirements

---

# 3. MEMBER 1 — Meteorological Data Engineer

## Main Goal

Build the **clean, reliable and reproducible scientific dataset** used by the entire ML pipeline.

## What This Member Does

### 1. Collect Data

Find and organize the available:

- NWP rainfall forecasts
- Historical observed rainfall
- Temperature
- Humidity
- Wind
- Pressure
- Geographic information
- Other relevant meteorological variables

### 2. Read Scientific Weather Files

Work with formats such as:

```text
GRIB
NetCDF
CSV
GeoJSON / Shapefile
```

Recommended tools:

```text
Python
Xarray
cfgrib
netCDF4
Pandas
GeoPandas
NumPy
```

### 3. Clean Data

Check for:

- Missing values
- Duplicate records
- Invalid values
- Incorrect units
- Broken timestamps
- Coordinate inconsistencies

### 4. Align Forecast and Observation

The forecast and observed rainfall must refer to the same:

```text
Location
+
Valid Time
```

Example:

```text
NWP Forecast
      |
      v
Valid Time = 15:00
      |
      v
Observed Rainfall at 15:00
```

### 5. Spatial Alignment

Ensure that different datasets can be compared spatially.

Possible methods:

- Regridding
- Interpolation
- Nearest-neighbour matching
- Grid aggregation

### 6. Feature Engineering

Create the features required by:

- Member 2
- Member 3
- Member 4

### 7. Dataset Splitting

Create:

```text
Training
Validation
Testing
```

Prefer chronological splits where appropriate so future information does not leak into training.

## What They Should NOT Do

They should not:

- Train the main application models without coordination.
- Change dataset definitions without informing Members 2–4.
- Mix training and testing periods.
- Ignore units or coordinate systems.
- Hand over undocumented datasets.

## Final Deliverables

```text
/data
/preprocessing
/features
/data_dictionary.md
dataset_description.md
preprocessing_pipeline.py
```

## Handoff to Team

Member 1 → Members 2, 3, 4

They provide:

```text
ML-ready dataset
Feature definitions
Units
Source information
Preprocessing rules
```

---

# 4. MEMBER 2 — Weather Regime ML Engineer

## Main Goal

Build **Model 1: Weather Regime Classifier**.

The model answers:

> **What type of weather situation is occurring?**

## Possible Regimes

Depending on available training labels and data:

- Active Monsoon
- Break Monsoon
- Monsoon Low / Depression
- Coastal Rainfall
- Orographic Rainfall
- Western Disturbance

The final classes must be based on the data actually available.

## What This Member Does

### 1. Define Classification Problem

Determine:

- Classes
- Labels
- Input features
- Output probabilities

### 2. Build Baselines

Start simple:

```text
Logistic Regression
Random Forest
```

Then test:

```text
XGBoost
```

### 3. Train the Classifier

Input:

```text
Weather Features
+
NWP Features
+
Geographical Features
```

Output:

```text
Predicted Regime
+
Class Probability
```

Example:

```text
Active Monsoon: 72%
Depression:     16%
Coastal:         7%
Break:           5%
```

### 4. Evaluate

Use:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion matrix
- Class-wise metrics

### 5. Handle Class Imbalance

Check whether some regimes have much fewer examples than others.

### 6. Package the Model

Create stable inference code that can be called by the backend.

## What They Should NOT Do

They should not:

- Depend on future weather information.
- Change labels casually after training starts.
- Give Member 3 only a model file without inference instructions.
- Evaluate only overall accuracy while ignoring rare regimes.

## Final Deliverables

```text
/regimes
    /training
    /inference
    /evaluation

regime_model
regime_inference.py
classification_report.md
confusion_matrix
```

## Handoff

Member 2 → Member 3

```text
Predicted Regime
Regime Probability
Inference Function
Model Version
```

Member 2 → Member 5

```text
Packaged Model
Required Inputs
Output Schema
Inference Instructions
```

---

# 5. MEMBER 3 — Rainfall Post-Processing ML Engineer

## Main Goal

Build **Model 2: Regime-Aware Rainfall Correction**.

This is the central rainfall ML component.

The model answers:

> **How should the raw NWP rainfall forecast be corrected under the current weather conditions?**

## Input

```text
Raw NWP Rainfall
+
Meteorological Features
+
Detected Weather Regime
+
Historical Forecast Error Features
```

## Output

```text
Corrected Rainfall Forecast
```

Example:

```text
Raw NWP:       42 mm
Regime:        Active Monsoon
Corrected:     61 mm
```

## What This Member Does

### 1. Establish Baseline

Start with:

```text
Raw NWP
```

This is the reference against which every model is compared.

### 2. Test Simple Correction

Evaluate:

```text
Statistical Bias Correction
Linear Regression
```

### 3. Test ML Models

Evaluate:

```text
Random Forest
XGBoost
```

### 4. Build Regime-Aware Correction

Use:

```text
Raw NWP
+
Weather Features
+
Regime Information
```

### 5. Compare Architectures

#### Unified model

```text
Forecast + Features + Regime
            |
            v
      Single ML Model
            |
            v
     Corrected Forecast
```

#### Regime-specific routing

```text
Regime
  |
  +-- Active Monsoon -> Model A
  +-- Depression -> Model B
  +-- Coastal -> Model C
```

Choose based on actual validation results.

### 6. Prevent Leakage

Only use information available at the forecast time.

### 7. Evaluate

Use:

- MAE
- RMSE
- Bias

Also analyze performance by regime.

## What They Should NOT Do

They should not:

- Claim improvement without comparison to raw NWP.
- Train on future observations.
- Choose a complex model just because it is newer.
- Ignore regime-wise performance.

## Final Deliverables

```text
/correction
    /baselines
    /models
    /evaluation

correction_inference.py
model_comparison.md
raw_vs_corrected_results
```

## Handoff

Member 3 → Member 4

```text
Corrected Forecast
Model predictions
Model metadata
Raw-vs-corrected results
```

Member 3 → Member 5

```text
Model
Inference code
Input schema
Output schema
Model version
```

---

# 6. MEMBER 4 — Uncertainty, Risk & Verification Engineer

## Main Goal

Answer three questions:

1. **How likely is heavy rainfall?**
2. **How reliable is the prediction?**
3. **Did VARUNA-AI actually improve the forecast?**

This member owns the project's scientific evidence.

---

## 6.1 Heavy Rainfall Probability

Build a probability product such as:

```text
P(Rainfall > Threshold)
```

Example:

```text
Heavy Rainfall Probability = 76%
```

The operational threshold must be defined and documented according to the relevant project requirements.

---

## 6.2 Uncertainty

The output should not necessarily be only:

```text
Forecast = 86 mm
```

It should support an uncertainty representation such as:

```text
Forecast = 86 mm
Range = 76–94 mm
Confidence = High
```

The chosen uncertainty method must be validated.

---

## 6.3 Risk Engine

Convert validated rainfall/probability information into:

```text
Low
Moderate
High
Extreme
```

Risk rules must be documented and based on appropriate thresholds.

---

## 6.4 Scientific Verification

Compare:

```text
Raw NWP
    vs
VARUNA-AI
    vs
Observed Rainfall
```

Calculate:

### Continuous Metrics

```text
RMSE
MAE
Bias
```

### Event Metrics

```text
ETS
CSI
POD
FAR
```

### Spatial Metric

```text
FSS
```

where applicable.

---

## 6.5 Regime-Wise Evaluation

This should be a major project output.

Example:

```text
                    Raw NWP     VARUNA-AI
Active Monsoon         X             X
Break Monsoon          X             X
Low Pressure           X             X
Depression             X             X
```

The goal is to identify:

- Where the model improves.
- How much it improves.
- Which regimes remain difficult.

## What They Should NOT Do

They should not:

- Create arbitrary confidence values.
- Report only metrics that look good.
- Hide poor regime-wise performance.
- Change thresholds to artificially improve results.

## Final Deliverables

```text
/probability
/uncertainty
/verification
/evaluation_report
/charts
```

## Handoff

Member 4 → Member 5

```text
Probability output
Uncertainty output
Risk output
Verification results
```

Member 4 → Member 6

```text
Charts
Metrics
Risk categories
Confidence information
```

---

# 7. MEMBER 5 — Backend & ML Integration Engineer

## Main Goal

Turn the scientific components into **one working application**.

This member does not own the ML research.

They own:

> **Integration, application workflow and system communication.**

---

## 7.1 Django Application

Responsibilities:

- Routing
- Protected pages
- Database models
- Application workflows
- API endpoints
- Processing status

---

## 7.2 Firebase Authentication

Firebase is used primarily for:

- User registration
- Secure sign-in
- User identity
- Authentication tokens

Architecture:

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
Django
```

Firebase is not the core scientific database.

---

## 7.3 Model Integration

Connect:

```text
Model 1
Regime
   ↓
Model 2
Corrected Rainfall
   ↓
Model 3 / Probability
Risk + Uncertainty
```

---

## 7.4 Database

Use:

```text
PostgreSQL
PostGIS
```

Potential entities:

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

---

## 7.5 Background Processing

Use:

```text
Celery
Redis
```

Example:

```text
User Request
    |
    v
Django
    |
    v
Celery Task
    |
    v
Data Processing
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

## 7.6 API Contract

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

The final schema should be version-controlled and agreed upon by Members 5 and 6.

## What They Should NOT Do

They should not:

- Rewrite ML models inside API routes.
- Modify model logic without the model owner's agreement.
- Store large scientific datasets in Firebase by default.
- Wait until the end to integrate the models.
- Build APIs without stable input/output contracts.

## Final Deliverables

```text
/backend
/api
/authentication
/database
/tasks
API documentation
integration tests
```

---

# 8. MEMBER 6 — Geospatial & Visualization Engineer

## Main Goal

Turn scientific output into a **usable district-level forecast product**.

This role includes both:

- Geospatial processing
- Visualization/interface

---

## 8.1 Grid-to-District Processing

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

Possible approaches:

- Area-weighted aggregation
- Mean
- Maximum
- Threshold-based classification

The team must document the selected method.

---

## 8.2 Map

Use a geospatial map to show:

- District boundaries
- Rainfall forecast
- Corrected rainfall
- Heavy rainfall probability
- Risk
- Observed rainfall where available

Recommended map technology:

```text
Leaflet
```

---

## 8.3 Forecast View

For a selected district:

```text
RAW NWP
    ↓
DETECTED REGIME
    ↓
AI CORRECTION
    ↓
CORRECTED FORECAST
    ↓
HEAVY RAIN PROBABILITY
    ↓
UNCERTAINTY
    ↓
RISK
```

---

## 8.4 Verification View

Display:

```text
Raw NWP
    vs
VARUNA-AI
    vs
Observed Rainfall
```

Also display:

- RMSE
- MAE
- Bias
- CSI
- POD
- FAR
- FSS where applicable

## What They Should NOT Do

They should not:

- Create charts using fake results.
- Hide verification results.
- Treat the map as decoration only.
- Hard-code forecast outputs.
- Build UI before the API contract is agreed.

## Final Deliverables

```text
/dashboard
/templates
/static
/maps
/charts
/district_views
```

---

# 9. Member-to-Member Handoff Rules

## Member 1 → Member 2

```text
Dataset
Feature definitions
Labels
Preprocessing rules
```

## Member 1 → Member 3

```text
Clean NWP dataset
Weather features
Historical errors
```

## Member 1 → Member 4

```text
Observed rainfall
Forecast data
Event labels
Evaluation dataset
```

## Member 2 → Member 3

```text
Predicted regime
Regime probability
Inference function
```

## Member 3 → Member 4

```text
Corrected rainfall
Model output
Raw-vs-corrected predictions
```

## Members 2, 3, 4 → Member 5

```text
Model files
Inference functions
Input schemas
Output schemas
Model versions
```

## Member 5 → Member 6

```text
API endpoints
Forecast JSON
Map data
Verification data
Risk data
```

---

# 10. Shared Data Contract

All members should use agreed field names.

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

Do not rename fields independently.

Any schema change must be communicated to the affected members.

---

# 11. Git Workflow

Use one shared repository:

```text
varuna-ai/
```

Recommended branches:

```text
main
develop
feature/member-1-data
feature/member-2-regime
feature/member-3-correction
feature/member-4-verification
feature/member-5-backend
feature/member-6-ui
```

General workflow:

```text
Create Branch
    ↓
Implement
    ↓
Test
    ↓
Commit
    ↓
Pull Request
    ↓
Code Review
    ↓
Merge
```

No direct experimental changes should be pushed to `main`.

---

# 12. Integration Rules

Every component must define:

### Input

What does it receive?

### Output

What does it produce?

### Version

Which model/data version generated it?

### Validation

How do we know it is correct?

Example:

```text
Model 2
Input:
raw_nwp_rainfall
regime
weather_features

Output:
corrected_rainfall

Validation:
MAE / RMSE / Bias
```

---

# 13. Development Order

## Stage 1 — Data Foundation

Member 1 establishes:

```text
Dataset
Preprocessing
Alignment
Feature Pipeline
```

## Stage 2 — First ML Models

Members 2 and 3 build:

```text
Regime Model
Rainfall Correction Model
```

## Stage 3 — Scientific Evaluation

Member 4 builds:

```text
Verification
Probability
Uncertainty
```

## Stage 4 — Integration

Member 5 connects:

```text
Models
Database
Authentication
Backend
```

## Stage 5 — Product

Member 6 connects:

```text
District Processing
Map
Charts
Operational Interface
```

---

# 14. First End-to-End Milestone

Do not attempt the complete polished system first.

The first milestone should be:

```text
Real Dataset
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
Simple Map
```

Once this works, improve each component.

---

# 15. What the Full System Should Produce

For a district, the final system should be able to provide something similar to:

```text
District: Example District

Weather Regime:
Active Monsoon

Regime Confidence:
81%

Raw NWP:
42 mm

VARUNA-AI Corrected:
61 mm

Expected Range:
54–68 mm

Heavy Rain Probability:
76%

Risk:
High

Model Version:
v1.x

Verification:
Available for historical period
```

These values are illustrative only. The actual system must display model-generated results.

---

# 16. Definition of Done for Each Member

## Member 1

Done when:

```text
Data is reproducibly ingested,
cleaned,
aligned,
documented,
and available to ML members.
```

## Member 2

Done when:

```text
Regime classifier is trained,
validated,
packaged,
and callable by inference code.
```

## Member 3

Done when:

```text
Correction model is validated against the raw NWP baseline
and produces reproducible corrected forecasts.
```

## Member 4

Done when:

```text
Probability,
uncertainty,
risk,
and scientific verification
are reproducibly calculated.
```

## Member 5

Done when:

```text
All models can be triggered through the application,
results are stored,
and APIs return stable outputs.
```

## Member 6

Done when:

```text
District results are correctly mapped,
visualized,
and connected to backend data.
```

---

# 17. Common Mistakes to Avoid

## Mistake 1

Six members build six disconnected demos.

### Correct approach

Build one pipeline.

---

## Mistake 2

The UI is finished before the ML outputs are stable.

### Correct approach

Build a functional data → model → output path first.

---

## Mistake 3

Using fake metrics.

### Correct approach

Display only measured results.

---

## Mistake 4

Training on future information.

### Correct approach

Use strict time-aware dataset splitting.

---

## Mistake 5

Adding technologies just to look advanced.

### Correct approach

Every technology must have a clear engineering purpose.

---

## Mistake 6

Only showing overall model accuracy.

### Correct approach

Show performance by weather regime and rainfall event type.

---

# 18. Team Communication

Every member should report:

```text
What I completed
What I am currently doing
What is blocked
What another member needs from me
```

A short daily technical sync is enough.

Suggested format:

```text
Member 1:
Dataset aligned up to date X.
Waiting for regime labels.

Member 2:
Classifier baseline complete.
Need final feature schema.

Member 3:
Correction baseline complete.
Waiting for regime inference output.

Member 4:
Verification pipeline working.
Need corrected forecasts.

Member 5:
Database/API skeleton ready.
Waiting for model input schemas.

Member 6:
District geometry pipeline ready.
Waiting for API response format.
```

---

# 19. Final Team Architecture

```text
                       MEMBER 1
                  DATA FOUNDATION
                          |
             +------------+------------+
             |                         |
             v                         v
         MEMBER 2                 MEMBER 3
       REGIME MODEL            CORRECTION MODEL
             |                         |
             +------------+------------+
                          |
                          v
                      MEMBER 4
             PROBABILITY + UNCERTAINTY
                  + VERIFICATION
                          |
                 +--------+--------+
                 |                 |
                 v                 v
             MEMBER 5         MEMBER 6
             BACKEND          GEO + UI
                 |                 |
                 +--------+--------+
                          |
                          v
                      VARUNA-AI
```

---

# 20. Final Team Rule

The six members are not six independent developers working on six unrelated features.

They are six parts of one scientific pipeline:

```text
DATA
  ↓
REGIME
  ↓
CORRECTION
  ↓
PROBABILITY
  ↓
VERIFICATION
  ↓
DISTRICT PRODUCT
```

The most important team objective is:

> **Make the complete chain work end-to-end using real data before adding advanced features.**

Once the basic chain is working, the team can improve model accuracy, uncertainty estimation, spatial processing, interface quality and performance without breaking the architecture.

