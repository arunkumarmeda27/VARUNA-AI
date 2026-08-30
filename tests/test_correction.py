"""
VARUNA-AI: Rainfall Correction Model Tests
Owner: Member 3 (Rainfall Post-Processing ML Engineer)
"""

import numpy as np
import pandas as pd
from correction.baselines.level0_raw_nwp import Level0RawNWP
from correction.baselines.level1_quantile_mapping import Level1QuantileMapping
from correction.models.correction_engine import RainfallCorrectionEngine

def test_level0_raw_nwp():
    df = pd.DataFrame({"nwp_rainfall": [0.0, 15.5, -4.0, 120.0]})
    l0 = Level0RawNWP()
    preds = l0.predict(df)
    assert (preds >= 0.0).all()
    assert preds[1] == 15.5
    assert preds[2] == 0.0

def test_level1_quantile_mapping():
    nwp_train = np.array([0.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0])
    obs_train = np.array([0.0, 0.5, 3.0,  8.0, 25.0, 65.0, 140.0])

    eqm = Level1QuantileMapping()
    eqm.fit(nwp_train, obs_train)

    test_nwp = np.array([2.0, 10.0, 50.0])
    preds = eqm.predict(test_nwp)
    assert len(preds) == 3
    assert (preds >= 0.0).all()

def test_correction_engine_pipeline():
    engine = RainfallCorrectionEngine()
    df = pd.DataFrame({
        "valid_time": ["2026-07-15"],
        "nwp_rainfall": [45.0],
        "nwp_rain_log1p": [np.log1p(45.0)],
        "nwp_is_rain": [1.0],
        "nwp_is_heavy": [0.0],
        "u850": [18.0],
        "v850": [4.0],
        "u200": [-28.0],
        "v200": [0.0],
        "wind_speed_850": [18.4],
        "wind_speed_200": [28.0],
        "vertical_wind_shear": [46.0],
        "mslp": [1000.0],
        "tcwv": [58.0],
        "rh700": [82.0],
        "cape": [1800.0],
        "monsoon_trough_lat": [22.0],
        "vorticity_proxy": [2.5],
        "moisture_flux_index": [10.6],
        "orographic_flux_idx": [18.0],
        "offshore_trough_idx": [5.0],
        "convective_index": [1.47],
        "latitude": [19.0],
        "longitude": [72.85],
    })

    out_df = engine.process_forecast(df)

    assert "predicted_regime" in out_df.columns
    assert "corrected_rainfall" in out_df.columns
    assert "bias_correction_delta" in out_df.columns
    assert (out_df["corrected_rainfall"] >= 0.0).all()
