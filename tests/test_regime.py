"""
VARUNA-AI: Weather Regime Inference Tests
Owner: Member 2 (Weather Regime Classification Engineer)
"""

import numpy as np
import pandas as pd
from regimes.inference.regime_classifier import RegimeClassifier

def test_regime_classifier_inference():
    clf = RegimeClassifier()
    sample_features = {
        "u850": 18.0,
        "v850": 4.0,
        "u200": -28.0,
        "v200": 0.0,
        "wind_speed_850": 18.4,
        "wind_speed_200": 28.0,
        "vertical_wind_shear": 46.0,
        "mslp": 1000.0,
        "tcwv": 58.0,
        "rh700": 82.0,
        "cape": 1800.0,
        "monsoon_trough_lat": 22.0,
        "vorticity_proxy": 2.5,
        "moisture_flux_index": 10.6,
        "orographic_flux_idx": 18.0,
        "offshore_trough_idx": 5.0,
        "convective_index": 1.47,
    }

    result = clf.predict_single(sample_features)

    assert "regime" in result
    assert "regime_confidence" in result
    assert "regime_probabilities" in result
    assert result["regime"] in clf.classes
    assert 0.0 <= result["regime_confidence"] <= 1.0

    # Probabilities must sum to ~1.0
    total_prob = sum(result["regime_probabilities"].values())
    assert np.isclose(total_prob, 1.0, atol=1e-3)
