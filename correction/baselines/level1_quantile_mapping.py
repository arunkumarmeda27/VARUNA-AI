"""
VARUNA-AI: Level 1 Statistical Bias Correction — Empirical Quantile Mapping (EQM)
Owner: Member 3 (Rainfall Post-Processing ML Engineer)

Maps empirical cumulative distribution function (ECDF) of raw NWP forecasts
to the ECDF of historical observed rainfall distributions.
"""

import numpy as np
import pandas as pd
from scipy import interpolate
from typing import Dict, Any

class Level1QuantileMapping:
    """
    Level 1 Baseline: Non-parametric Empirical Quantile Mapping (EQM).
    Adjusts systematic distributional shifts and drizzle overestimation.
    """

    def __init__(self, n_quantiles: int = 100):
        self.n_quantiles = n_quantiles
        self.model_name = "Level1_Quantile_Mapping"
        self.model_version = "v1.0.0"
        self.quantiles = np.linspace(0.001, 0.999, n_quantiles)
        self.nwp_q: np.ndarray = np.array([])
        self.obs_q: np.ndarray = np.array([])
        self.mapping_func = None

    def fit(self, nwp_train: np.ndarray, obs_train: np.ndarray) -> "Level1QuantileMapping":
        """Calculates empirical quantile pairs from training data."""
        clean_nwp = np.maximum(nwp_train, 0.0)
        clean_obs = np.maximum(obs_train, 0.0)

        self.nwp_q = np.quantile(clean_nwp, self.quantiles)
        self.obs_q = np.quantile(clean_obs, self.quantiles)

        # Ensure strictly monotonic NWP quantiles for interpolation
        unique_nwp_q, unique_indices = np.unique(self.nwp_q, return_index=True)
        corresponding_obs_q = self.obs_q[unique_indices]

        # Monotonic piecewise linear interpolation with linear extrapolation
        self.mapping_func = interpolate.interp1d(
            unique_nwp_q,
            corresponding_obs_q,
            kind="linear",
            bounds_error=False,
            fill_value="extrapolate",
        )
        return self

    def predict(self, nwp_input: np.ndarray) -> np.ndarray:
        """Applies quantile transfer function and enforces non-negativity."""
        if self.mapping_func is None:
            raise ValueError("Level1QuantileMapping model has not been fitted.")
        raw_vals = np.maximum(nwp_input, 0.0)
        corrected = self.mapping_func(raw_vals)
        return np.maximum(corrected, 0.0)
