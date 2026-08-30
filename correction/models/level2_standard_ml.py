"""
VARUNA-AI: Level 2 Standard ML Correction Model (Model A)
Owner: Member 3 (Rainfall Post-Processing ML Engineer)

Standard GBDT/XGBoost Regressor using NWP precipitation and local meteorological features,
WITHOUT explicit weather regime information (Model A).
"""

import os
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from typing import List, Dict, Any

STANDARD_FEATURE_COLS: List[str] = [
    "nwp_rainfall",
    "nwp_rain_log1p",
    "nwp_is_rain",
    "nwp_is_heavy",
    "u850",
    "v850",
    "wind_speed_850",
    "u200",
    "v200",
    "wind_speed_200",
    "vertical_wind_shear",
    "mslp",
    "tcwv",
    "rh700",
    "cape",
    "latitude",
    "longitude",
]

class Level2StandardML:
    """
    Level 2: Standard Machine Learning Post-Processing Regressor (Model A).
    """

    def __init__(self, n_estimators: int = 200, max_depth: int = 5, learning_rate: float = 0.05):
        self.model_name = "Level2_Standard_ML_XGB"
        self.model_version = "v1.0.0"
        self.feature_cols = STANDARD_FEATURE_COLS
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="reg:squarederror",
            random_state=42,
        )

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame) -> "Level2StandardML":
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
        X = df[self.feature_cols]
        preds = self.model.predict(X)
        return np.maximum(preds, 0.0)
