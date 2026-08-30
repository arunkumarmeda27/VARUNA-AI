# VARUNA-AI System Architecture

## 1. Executive Summary
**VARUNA-AI** is a scientific meteorological post-processing and verification platform developed for the Smart India Hackathon (SIH26080).
The system addresses the core research question:
> **"Can explicitly identifying the prevailing weather regime and using that information during rainfall post-processing improve raw NWP rainfall forecasts, especially for heavy and very heavy rainfall events?"**

---

## 2. Six-Member Modular Engineering Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │       DATA SOURCES (IMD / NCMRWF / GFS)      │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
                                   ┌──────────────────────────────────────┐
                                   │   MEMBER 1: DATA FOUNDATION          │
                                   │   (weather_data/)                    │
                                   │   - Physical bounds validation       │
                                   │   - Temporal/spatial grid alignment  │
                                   │   - Anti-leakage chronological split │
                                   └──────────────────┬───────────────────┘
                                                      │ Clean Master Dataset
                                                      ▼
                                   ┌──────────────────────────────────────┐
                                   │   MEMBER 2: REGIME CLASSIFIER        │
                                   │   (regimes/)                         │
                                   │   - Synoptic index extraction        │
                                   │   - Multi-class Softmax GBDT/XGB     │
                                   │   - Calibrated class probabilities   │
                                   └──────────────────┬───────────────────┘
                                                      │ Regime Probabilities & Labels
                                                      ▼
                                   ┌──────────────────────────────────────┐
                                   │   MEMBER 3: RAINFALL CORRECTION      │
                                   │   (correction/)                      │
                                   │   - Model Ladder (Levels 0, 1, 2, 3) │
                                   │   - Regime-coupled GBDT Regressor    │
                                   │   - Physical zero-bounding           │
                                   └──────────────────┬───────────────────┘
                                                      │ Corrected Grids
                                                      ▼
                      ┌───────────────────────────────┴───────────────────────────────┐
                      │                                                               │
                      ▼                                                               ▼
  ┌──────────────────────────────────────┐                        ┌──────────────────────────────────────┐
  │   MEMBER 4: PROBABILITY & METRICS    │                        │   MEMBER 6: GEOSPATIAL ENGINE        │
  │   (probability/, verification/)      │                        │   (geospatial/, dashboard/)          │
  │   - IMD Heavy Rain Probabilities     │                        │   - District boundary GeoJSON        │
  │   - Conformal Prediction Intervals   │                        │   - Point-in-polygon aggregation     │
  │   - Continuous / Categorical / FSS   │                        │   - Leaflet & ECharts UI Console     │
  └──────────────────┬───────────────────┘                        └──────────────────┬───────────────────┘
                     │                                                               │
                     └────────────────────────────────┬──────────────────────────────┘
                                                      │
                                                      ▼
                                   ┌──────────────────────────────────────┐
                                   │   MEMBER 5: BACKEND INTEGRATION      │
                                   │   (backend/)                         │
                                   │   - Django REST Framework API        │
                                   │   - SQLite/PostGIS database          │
                                   │   - Provenance audit trail           │
                                   └──────────────────────────────────────┘
```

---

## 3. The 4-Tier Model Ladder

| Tier Level | Model Specification | Inputs | Purpose |
| :--- | :--- | :--- | :--- |
| **Level 0** | Raw NWP | $R_{nwp}$ | Uncorrected baseline physics |
| **Level 1** | Empirical Quantile Mapping (EQM) | $R_{nwp}$, historical ECDF | Corrects systematic drizzle and climatological shift |
| **Level 2** | Standard ML (Model A) | $R_{nwp}$, local $u, v, P, q$ | Machine learning without regime information |
| **Level 3** | **VARUNA-AI Regime-Aware (Model B)** | $R_{nwp}$, local weather, **$P(\text{Regime})$, synoptic interactions** | **Explicitly tests research hypothesis** |

---

## 4. Verification Framework
The system executes a verification pipeline covering:
1. **Continuous Metrics**: MAE, RMSE, Mean Bias, Pearson Correlation ($r$).
2. **Categorical Metrics**: $2 \times 2$ Contingency Tables (Hits, False Alarms, Misses, Correct Negatives), POD, FAR, CSI, ETS, Frequency Bias across IMD thresholds ($2.5, 15.6, 64.5, 115.6, 204.5\text{ mm}$).
3. **Spatial Metrics**: Fractions Skill Score (FSS) over spatial neighborhood radii ($w = 1, 3, 5$).
4. **Stratified Analysis**: Performance reported separately across all 6 synoptic weather regimes.
