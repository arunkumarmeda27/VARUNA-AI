"""
VARUNA-AI: Weather Regime Feature Definitions
Owner: Member 2 (Weather Regime Classification Engineer)
"""

from typing import List

# Key synoptic predictors for weather regime identification
REGIME_FEATURE_COLS: List[str] = [
    "u850",
    "v850",
    "u200",
    "v200",
    "wind_speed_850",
    "wind_speed_200",
    "vertical_wind_shear",
    "mslp",
    "tcwv",
    "rh700",
    "cape",
    "monsoon_trough_lat",
    "vorticity_proxy",
    "moisture_flux_index",
    "orographic_flux_idx",
    "offshore_trough_idx",
    "convective_index",
]

TARGET_REGIME_COL: str = "true_regime"
