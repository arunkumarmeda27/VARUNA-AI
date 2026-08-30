"""
VARUNA-AI: Synoptic Meteorological Feature Engineering
Owner: Member 1 (Data Foundation) & Member 2 (Weather Regime Classification)
"""

import numpy as np
import pandas as pd
from typing import List

class SynopticFeatureEngineer:
    """
    Computes domain-informed physical meteorological features
    governing Indian Monsoon precipitation dynamics and weather regimes.
    """

    @staticmethod
    def compute_all_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes all synoptic and local kinematic/thermodynamic indices.
        """
        df_feat = df.copy()

        # 1. Low-Level Jet (LLJ) Wind Speed at 850 hPa
        if "u850" in df_feat.columns and "v850" in df_feat.columns:
            df_feat["wind_speed_850"] = np.sqrt(df_feat["u850"]**2 + df_feat["v850"]**2)
            # LLJ Direction in degrees (meteorological convention: direction from which wind blows)
            df_feat["wind_dir_850"] = (np.arctan2(-df_feat["u850"], -df_feat["v850"]) * 180.0 / np.pi) % 360.0

        # 2. Upper-Tropospheric Wind Speed at 200 hPa (Tropical Easterly Jet)
        if "u200" in df_feat.columns and "v200" in df_feat.columns:
            df_feat["wind_speed_200"] = np.sqrt(df_feat["u200"]**2 + df_feat["v200"]**2)

        # 3. Deep Tropospheric Vertical Wind Shear (200 hPa minus 850 hPa)
        if all(col in df_feat.columns for col in ["u850", "v850", "u200", "v200"]):
            du = df_feat["u200"] - df_feat["u850"]
            dv = df_feat["v200"] - df_feat["v850"]
            df_feat["vertical_wind_shear"] = np.sqrt(du**2 + dv**2)

        # 4. Low-level Relative Vorticity Proxy (approximated from local wind field and latitude)
        if "v850" in df_feat.columns and "u850" in df_feat.columns and "latitude" in df_feat.columns:
            # Cyclonic shear signature
            df_feat["vorticity_proxy"] = (df_feat["v850"] - df_feat["u850"] * 0.3) * np.sin(np.radians(df_feat["latitude"]))

        # 5. Moisture Flux Index (LLJ wind speed * Total Column Water Vapour)
        if "wind_speed_850" in df_feat.columns and "tcwv" in df_feat.columns:
            df_feat["moisture_flux_index"] = df_feat["wind_speed_850"] * df_feat["tcwv"] / 100.0

        # 6. Orographic Flow Index (westerly wind component impacting Western Ghats: 8°N-21°N, 72°E-77°E)
        if "u850" in df_feat.columns and "latitude" in df_feat.columns and "longitude" in df_feat.columns:
            is_western_ghats = (
                (df_feat["latitude"] >= 8.0) & (df_feat["latitude"] <= 21.0) &
                (df_feat["longitude"] >= 72.5) & (df_feat["longitude"] <= 77.0)
            )
            df_feat["orographic_flux_idx"] = np.where(is_western_ghats, np.maximum(df_feat["u850"], 0.0), 0.0)

        # 7. Offshore Trough Pressure Index (MSLP depression along West Coast vs inland)
        if "mslp" in df_feat.columns and "longitude" in df_feat.columns:
            # West coast longitude typically 72-76E, inland 77-80E
            df_feat["offshore_trough_idx"] = np.where(
                df_feat["longitude"] <= 76.0,
                1008.0 - df_feat["mslp"],
                0.0
            ).clip(-10.0, 15.0)

        # 8. Thermodynamic Instability / Convective Metric
        if "cape" in df_feat.columns and "rh700" in df_feat.columns:
            df_feat["convective_index"] = (df_feat["cape"] / 1000.0) * (df_feat["rh700"] / 100.0)

        # 9. NWP Log Transformation and Exceedance Flag
        if "nwp_rainfall" in df_feat.columns:
            df_feat["nwp_rain_log1p"] = np.log1p(df_feat["nwp_rainfall"])
            df_feat["nwp_is_rain"] = (df_feat["nwp_rainfall"] >= 2.5).astype(float)
            df_feat["nwp_is_heavy"] = (df_feat["nwp_rainfall"] >= 64.5).astype(float)

        return df_feat
