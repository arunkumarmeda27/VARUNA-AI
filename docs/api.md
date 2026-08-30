# VARUNA-AI REST API Specification

All endpoints return JSON and are rooted at `/api/v1/`.

## Endpoints

### 1. Health & Diagnostic
`GET /api/v1/health/`
Returns system status, active database connection, and loaded model components.

```json
{
  "status": "HEALTHY",
  "service": "VARUNA-AI Forecast Engine",
  "version": "v1.0.0",
  "database": "CONNECTED",
  "models_loaded": {
    "regime_classifier": true,
    "quantile_mapping": true,
    "standard_ml": true,
    "regime_aware_ml": true,
    "heavy_rain_probability": true,
    "conformal_quantiles": true
  }
}
```

### 2. Latest Operational Forecast
`GET /api/v1/forecasts/latest/`
Returns latest forecast cycle, detected synoptic regime, district forecasts, and Leaflet-ready GeoJSON feature layer.

### 3. District Forecast Details
`GET /api/v1/districts/{district_id}/forecast/`
Returns detailed forecast intelligence for a specific district (e.g. `DIST_MH_MUM`), including raw NWP, corrected rainfall, 80% conformal uncertainty interval, and IMD risk alerts.

### 4. Weather Regime Diagnostics
`GET /api/v1/regimes/`
Returns regime classification confusion matrix, multi-class log loss, Brier score, and per-class precision/recall.

### 5. Verification Benchmarks
`GET /api/v1/verification/`
Returns full verification matrices comparing Raw NWP vs Level 1 vs Level 2 vs Level 3 across continuous, categorical, and spatial FSS scores.

### 6. Model Registry & Provenance
`GET /api/v1/models/`
Returns version hashes, feature lists, training periods, and provenance metadata for all 6 pipeline components.
