"""
VARUNA-AI: Geospatial and District Aggregation Unit Tests
Owner: Member 6 (Geospatial + Operational Interface Engineer)
"""

import pandas as pd
from geospatial.districts.district_geometry import get_districts_geojson, get_districts_geodataframe, DISTRICTS_METADATA
from geospatial.aggregation.grid_aggregator import GridToDistrictAggregator

def test_districts_geojson_validity():
    gj = get_districts_geojson()
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) == len(DISTRICTS_METADATA)

    for feat in gj["features"]:
        assert feat["type"] == "Feature"
        assert "district_name" in feat["properties"]
        assert "geometry" in feat
        assert feat["geometry"]["type"] == "Polygon"

def test_grid_to_district_aggregation():
    aggregator = GridToDistrictAggregator()

    # Create synthetic grid forecast points
    grid_df = pd.DataFrame([
        {
            "grid_id": "G_19.10_72.88",
            "latitude": 19.10,
            "longitude": 72.88,
            "nwp_rainfall": 40.0,
            "corrected_rainfall": 60.0,
            "heavy_rain_probability": 0.75,
            "prob_exceed_115mm": 0.20,
            "prob_exceed_204mm": 0.05,
            "uncertainty_lower_10pct": 45.0,
            "uncertainty_upper_90pct": 80.0,
            "predicted_regime": "ACTIVE_MONSOON",
            "regime_confidence": 0.85,
            "valid_time": "2026-08-30",
        },
        {
            "grid_id": "G_11.70_76.10",
            "latitude": 11.70,
            "longitude": 76.10,
            "nwp_rainfall": 80.0,
            "corrected_rainfall": 125.0,
            "heavy_rain_probability": 0.95,
            "prob_exceed_115mm": 0.65,
            "prob_exceed_204mm": 0.38,
            "uncertainty_lower_10pct": 100.0,
            "uncertainty_upper_90pct": 160.0,
            "predicted_regime": "OROGRAPHIC_RAINFALL",
            "regime_confidence": 0.90,
            "valid_time": "2026-08-30",
        }
    ])

    dist_df = aggregator.aggregate_forecast_to_districts(grid_df)

    assert not dist_df.empty
    assert "district_id" in dist_df.columns
    assert "corrected_mean_mm" in dist_df.columns
    assert "risk_code" in dist_df.columns
    assert "risk_label" in dist_df.columns
