"""
VARUNA-AI: Synoptic Feature Engineering Unit Tests
Owner: Member 1 & Member 2
"""

import numpy as np
import pandas as pd
from weather_data.features.synoptic_features import SynopticFeatureEngineer

def test_synoptic_feature_computation():
    df = pd.DataFrame({
        "u850": [15.0],
        "v850": [5.0],
        "u200": [-25.0],
        "v200": [0.0],
        "mslp": [998.0],
        "tcwv": [60.0],
        "rh700": [85.0],
        "cape": [2000.0],
        "latitude": [18.5],
        "longitude": [73.8],
        "nwp_rainfall": [45.0],
    })

    feat_df = SynopticFeatureEngineer.compute_all_features(df)

    # 1. Wind speed at 850 hPa
    assert np.isclose(feat_df["wind_speed_850"].iloc[0], np.sqrt(15.0**2 + 5.0**2))

    # 2. Vertical wind shear
    expected_shear = np.sqrt((-25.0 - 15.0)**2 + (0.0 - 5.0)**2)
    assert np.isclose(feat_df["vertical_wind_shear"].iloc[0], expected_shear)

    # 3. Moisture flux index
    expected_mf = (feat_df["wind_speed_850"].iloc[0] * 60.0) / 100.0
    assert np.isclose(feat_df["moisture_flux_index"].iloc[0], expected_mf)

    # 4. Log1p transformation
    assert np.isclose(feat_df["nwp_rain_log1p"].iloc[0], np.log1p(45.0))
