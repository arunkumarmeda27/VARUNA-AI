"""
VARUNA-AI: Heavy Rainfall Probability and Uncertainty Unit Tests
Owner: Member 4
"""

import numpy as np
import pandas as pd
from probability.heavy_rainfall import HeavyRainfallProbabilityEstimator
from uncertainty.conformal_quantiles import ConformalQuantileEstimator

def test_heavy_rainfall_probability_estimator():
    estimator = HeavyRainfallProbabilityEstimator()
    df = pd.DataFrame({
        "nwp_rainfall": [85.0, 10.0],
        "corrected_rainfall": [110.0, 5.0],
        "tcwv": [65.0, 40.0],
        "rh700": [90.0, 50.0],
        "cape": [2500.0, 800.0],
        "wind_speed_850": [22.0, 8.0],
        "vertical_wind_shear": [50.0, 20.0],
        "vorticity_proxy": [4.0, 0.5],
        "moisture_flux_index": [14.0, 3.2],
        "nwp_rain_log1p": [np.log1p(85.0), np.log1p(10.0)],
    })

    res_df = estimator.estimate_probabilities(df)

    assert "heavy_rain_probability" in res_df.columns
    assert "operational_risk_level" in res_df.columns
    # High rainfall case should have significantly higher probability than low rainfall case
    assert res_df["heavy_rain_probability"].iloc[0] > res_df["heavy_rain_probability"].iloc[1]
    assert 0.0 <= res_df["heavy_rain_probability"].iloc[0] <= 1.0

def test_conformal_uncertainty_estimator():
    unc = ConformalQuantileEstimator()
    df = pd.DataFrame({
        "corrected_rainfall": [50.0, 120.0],
        "nwp_rainfall": [40.0, 95.0],
        "nwp_rain_log1p": [np.log1p(40.0), np.log1p(95.0)],
        "tcwv": [55.0, 65.0],
        "rh700": [80.0, 92.0],
        "cape": [1500.0, 3000.0],
        "wind_speed_850": [15.0, 25.0],
        "vertical_wind_shear": [40.0, 55.0],
        "vorticity_proxy": [2.0, 5.0],
    })

    out_df = unc.estimate_uncertainty(df)

    assert "uncertainty_lower_10pct" in out_df.columns
    assert "uncertainty_median_50pct" in out_df.columns
    assert "uncertainty_upper_90pct" in out_df.columns

    for _, row in out_df.iterrows():
        assert row["uncertainty_lower_10pct"] <= row["uncertainty_median_50pct"] <= row["uncertainty_upper_90pct"]
        assert row["uncertainty_range_width"] >= 0.0
