"""
VARUNA-AI: Level 3 Regime-Aware ML Correction Model (Model B)
Owner: Member 3 (Rainfall Post-Processing ML Engineer)

Regime-Aware GBDT/XGBoost Regressor explicitly integrating synoptic regime
probabilities, regime interactions, and domain-informed physics (Model B).
"""

import os
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from typing import List, Dict, Any

from correction.models.level2_standard_ml import STANDARD_FEATURE_COLS
from weather_data.metadata.data_dictionary import WEATHER_REGIMES

REGIME_PROB_COLS: List[str] = [f"prob_{r.lower()}" for r in WEATHER_REGIMES]
REGIME_INTERACTION_COLS: List[str] = [
    "monsoon_trough_lat",
    "vorticity_proxy",
    "moisture_flux_index",
    "orographic_flux_idx",
    "offshore_trough_idx",
    "convective_index",
]

REGIME_AWARE_FEATURE_COLS: List[str] = (
    STANDARD_FEATURE_COLS + REGIME_PROB_COLS + REGIME_INTERACTION_COLS
)

class Level3RegimeAwareML:
    """
    Level 3: Regime-Aware Machine Learning Post-Processing Regressor (Model B).
    """

    def __init__(self, n_estimators: int = 250, max_depth: int = 6, learning_rate: float = 0.04):
        self.model_name = "Level3_Regime_Aware_ML_XGB"
        self.model_version = "v1.0.0"
        self.feature_cols = REGIME_AWARE_FEATURE_COLS
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="reg:squarederror",
            random_state=42,
        )

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame) -> "Level3RegimeAwareML":
        X_train = train_df[self.feature_cols]
        y_train = train_df["observed_rainfall"]
        X_val = val_df[self.feature_cols]
        y_val = val_df["observed_rainfall"]

        self.model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        # Fallback for any missing feature columns with 0.0
        df_in = df.copy()
        for col in self.feature_cols:
            if col not in df_in.columns:
                df_in[col] = 0.0

        X = df_in[self.feature_cols]
        preds = self.model.predict(X)
        return np.maximum(preds, 0.0)
