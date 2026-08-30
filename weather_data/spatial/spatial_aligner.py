"""
VARUNA-AI: Spatial Alignment Module
Owner: Member 1 (Data Foundation / Data Engineer)
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Optional

class SpatialAligner:
    """
    Standardizes differing grid resolutions (e.g. 0.50 deg NWP vs 0.25 deg IMD observation)
    to a common regular spatial reference grid across the Indian domain.
    """

    DEFAULT_LAT_BOUNDS = (8.0, 37.0)
    DEFAULT_LON_BOUNDS = (68.0, 97.0)

    @classmethod
    def generate_reference_grid(
        cls,
        resolution_deg: float = 0.50,
        lat_bounds: Tuple[float, float] = DEFAULT_LAT_BOUNDS,
        lon_bounds: Tuple[float, float] = DEFAULT_LON_BOUNDS,
    ) -> pd.DataFrame:
        """Generates regular grid points with unique grid_id."""
        lats = np.arange(lat_bounds[0], lat_bounds[1] + resolution_deg / 2, resolution_deg)
        lons = np.arange(lon_bounds[0], lon_bounds[1] + resolution_deg / 2, resolution_deg)

        grid_points: List[dict] = []
        for lat in lats:
            for lon in lons:
                grid_id = f"G_{round(lat, 2):.2f}_{round(lon, 2):.2f}"
                grid_points.append({
                    "grid_id": grid_id,
                    "latitude": round(lat, 2),
                    "longitude": round(lon, 2),
                })

        return pd.DataFrame(grid_points)

    @classmethod
    def snap_to_nearest_grid(
        cls,
        df: pd.DataFrame,
        ref_grid: pd.DataFrame,
        lat_col: str = "latitude",
        lon_col: str = "longitude",
    ) -> pd.DataFrame:
        """
        Maps arbitrary lat/lon coordinates to nearest reference grid centroids.
        """
        from scipy.spatial import cKDTree

        ref_coords = ref_grid[["latitude", "longitude"]].values
        tree = cKDTree(ref_coords)

        target_coords = df[[lat_col, lon_col]].values
        distances, indices = tree.query(target_coords)

        df_snapped = df.copy()
        df_snapped["grid_id"] = ref_grid.iloc[indices]["grid_id"].values
        df_snapped["latitude_grid"] = ref_grid.iloc[indices]["latitude"].values
        df_snapped["longitude_grid"] = ref_grid.iloc[indices]["longitude"].values
        df_snapped["grid_distance_deg"] = distances

        return df_snapped
