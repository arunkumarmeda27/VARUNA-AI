"""
VARUNA-AI: Geospatial and District Aggregation Unit Tests
Owner: Member 6 (Geospatial + Operational Interface Engineer)
"""

import pandas as pd
from geospatial.districts.district_geometry import get_districts_geojson, get_districts_geodataframe, DISTRICTS_METADATA
from geospatial.aggregation.grid_aggregator import GridToDistrictAggregator

def test_districts_geojson_validity():
    # Test base curated districts
    gj_base = get_districts_geojson(include_all_100=False)
    assert gj_base["type"] == "FeatureCollection"
    assert len(gj_base["features"]) == len(DISTRICTS_METADATA)

    # Test complete all-India 100 district collection
    gj_all = get_districts_geojson(include_all_100=True)
    assert gj_all["type"] == "FeatureCollection"
    assert len(gj_all["features"]) >= 100

    for feat in gj_all["features"]:
        assert feat["type"] == "Feature"
        props = feat["properties"]
        assert "district_name" in props
        assert "state" in props
        assert "zone" in props
        assert "centroid_lat" in props
        assert "centroid_lon" in props
        # Verify coordinates strictly within Indian geographical bounds
        assert 8.0 <= props["centroid_lat"] <= 38.0
        assert 68.0 <= props["centroid_lon"] <= 98.0
        assert "geometry" in feat
        assert feat["geometry"]["type"] == "Polygon"

    # Test GeoDataFrame conversion
    gdf = get_districts_geodataframe(include_all_100=True)
    assert len(gdf) == len(gj_all["features"])
    assert gdf.crs.to_string() == "EPSG:4326"


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
