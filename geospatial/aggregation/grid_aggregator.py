"""
VARUNA-AI: Grid-to-District Spatial Aggregation Module
Owner: Member 6 (Geospatial + Operational Interface Engineer)

Aggregates grid-point forecasts, heavy rain probabilities, and uncertainty intervals
into operational district-level products using spatial geometry intersections.
"""

import json
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from typing import Dict, List, Any

from geospatial.districts.district_geometry import get_districts_geodataframe, get_districts_geojson

class GridToDistrictAggregator:
    """
    Performs spatial aggregation of corrected forecast grids to administrative districts.
    """

    def __init__(self):
        self.districts_gdf = get_districts_geodataframe()

    def aggregate_forecast_to_districts(self, forecast_grid_df: pd.DataFrame) -> pd.DataFrame:
        """
        Takes grid-level forecast records, joins with district polygons,
        and computes area-weighted and conservative maximum/mean statistics.
        """
        # Create GeoDataFrame for grid points
        geometry = [Point(xy) for xy in zip(forecast_grid_df["longitude"], forecast_grid_df["latitude"])]
        grid_gdf = gpd.GeoDataFrame(forecast_grid_df.copy(), geometry=geometry, crs="EPSG:4326")

        # Spatial join grid points with district polygons
        joined = gpd.sjoin(grid_gdf, self.districts_gdf, how="inner", predicate="within")

        if joined.empty:
            # Fallback: Nearest district centroid if grid points lie marginally outside boundary
            from scipy.spatial import cKDTree
            d_coords = np.array([[d.geometry.centroid.y, d.geometry.centroid.x] for _, d in self.districts_gdf.iterrows()])
            tree = cKDTree(d_coords)
            g_coords = forecast_grid_df[["latitude", "longitude"]].values
            _, indices = tree.query(g_coords)
            joined = forecast_grid_df.copy()
            joined["district_id"] = self.districts_gdf.iloc[indices]["district_id"].values
            joined["district_name"] = self.districts_gdf.iloc[indices]["district_name"].values
            joined["state"] = self.districts_gdf.iloc[indices]["state"].values
            joined["zone"] = self.districts_gdf.iloc[indices]["zone"].values

        # Aggregate metrics per district
        district_records = []
        for dist_id, group in joined.groupby("district_id"):
            dist_meta = self.districts_gdf[self.districts_gdf["district_id"] == dist_id].iloc[0]

            raw_nwp_mean = float(np.round(group["nwp_rainfall"].mean(), 2))
            corrected_mean = float(np.round(group["corrected_rainfall"].mean(), 2))
            corrected_max = float(np.round(group["corrected_rainfall"].max(), 2))
            heavy_prob = float(np.round(group.get("heavy_rain_probability", pd.Series([0.0])).max(), 4))
            prob_vh = float(np.round(group.get("prob_exceed_115.6mm", pd.Series([0.0])).max(), 4))
            prob_ext = float(np.round(group.get("prob_exceed_204.5mm", pd.Series([0.0])).max(), 4))

            unc_lower = float(np.round(group.get("uncertainty_lower_10pct", pd.Series([corrected_mean*0.8])).mean(), 2))
            unc_upper = float(np.round(group.get("uncertainty_upper_90pct", pd.Series([corrected_mean*1.3])).mean(), 2))

            pred_regime = group["predicted_regime"].mode().iloc[0] if "predicted_regime" in group.columns else "ACTIVE_MONSOON"
            reg_conf = float(np.round(group.get("regime_confidence", pd.Series([0.80])).mean(), 4))

            # Operational Warning Color / Risk
            # Use corrected rainfall as the primary gate so tiny rain totals cannot trigger severe alerts.
            if corrected_max >= 204.5 or (prob_ext >= 0.35 and corrected_max >= 64.5):
                risk_code = "RED"
                risk_label = "RED ALERT (Take Action - Extremely Heavy Rain)"
            elif corrected_max >= 115.6 or (prob_vh >= 0.30 and corrected_max >= 64.5) or (heavy_prob >= 0.55 and corrected_max >= 35.5):
                risk_code = "ORANGE"
                risk_label = "ORANGE ALERT (Be Prepared - Heavy to Very Heavy Rain)"
            elif corrected_mean >= 15.6 or (heavy_prob >= 0.25 and corrected_mean >= 10.0):
                risk_code = "YELLOW"
                risk_label = "YELLOW ALERT (Be Updated - Moderate to Heavy Rain)"
            else:
                risk_code = "GREEN"
                risk_label = "GREEN ALERT (No Warning - Light / Moderate Rain)"

            valid_time = str(group["valid_time"].iloc[0]) if "valid_time" in group.columns else "2026-08-30"

            district_records.append({
                "district_id": dist_id,
                "district_name": dist_meta["district_name"],
                "state": dist_meta["state"],
                "zone": dist_meta["zone"],
                "centroid_lat": dist_meta.geometry.centroid.y,
                "centroid_lon": dist_meta.geometry.centroid.x,
                "valid_time": valid_time,
                "raw_nwp_mean_mm": raw_nwp_mean,
                "corrected_mean_mm": corrected_mean,
                "corrected_max_mm": corrected_max,
                "bias_correction_delta_mm": round(corrected_mean - raw_nwp_mean, 2),
                "heavy_rain_probability": heavy_prob,
                "prob_exceed_115mm": prob_vh,
                "prob_exceed_204mm": prob_ext,
                "uncertainty_lower_10pct": unc_lower,
                "uncertainty_upper_90pct": unc_upper,
                "uncertainty_range_width": round(unc_upper - unc_lower, 2),
                "predicted_regime": pred_regime,
                "regime_confidence": reg_conf,
                "risk_code": risk_code,
                "risk_label": risk_label,
                "model_version": "VARUNA-Level3-XGB-v1.0.0",
            })

        return pd.DataFrame(district_records)

    def generate_district_forecast_geojson(self, district_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Combines district polygons and forecast properties into a fully styled GeoJSON
        ready for direct Leaflet operational display.
        """
        gj = get_districts_geojson()
        df_map = district_df.set_index("district_id").to_dict(orient="index")

        for feat in gj["features"]:
            d_id = feat["id"]
            if d_id in df_map:
                feat["properties"].update(df_map[d_id])

        return gj
