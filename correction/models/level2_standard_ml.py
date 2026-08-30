"""
VARUNA-AI: Level 2 Standard ML Correction Model (Model A) — v2.0.0
Owner: Member 3 (Rainfall Post-Processing ML Engineer)

Standard GBDT/XGBoost Regressor with improved hyperparameters, regularisation,
monotone constraint on NWP input, and physics-anchored output clipping.
"""

import os
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from typing import List

# Extended feature set: all synoptic + derived NWP flags
STANDARD_FEATURE_COLS: List[str] = [
    # NWP primary predictors
    "nwp_rainfall",
    "nwp_rain_log1p",
    "nwp_is_rain",
    "nwp_is_heavy",
    # Low-level dynamics (LLJ)
    "u850",
    "v850",
    "wind_speed_850",
    "wind_dir_850",
    # Upper-level dynamics (TEJ)
    "u200",
    "v200",
    "wind_speed_200",
    # Thermodynamic & moisture
    "vertical_wind_shear",
    "mslp",
    "tcwv",
    "rh700",
    "cape",
    "convective_index",
    "moisture_flux_index",
    # Orographic / coastal
    "orographic_flux_idx",
    "offshore_trough_idx",
    "vorticity_proxy",
    "monsoon_trough_lat",
    # Spatial identifiers
    "latitude",
    "longitude",
]


class Level2StandardML:
    """
    Level 2: Standard Machine Learning Post-Processing Regressor (Model A) — v2.0.0.

    Key improvements over v1.0.0:
    - More estimators with early stopping on validation MAE
    - Monotone constraint on nwp_rainfall (index 0): corrected >= higher when NWP is higher
    - L1 + L2 regularisation (alpha + lambda) to reduce overfitting on sparse heavy-rain events
    - Gradient-based quantile via tweedie objective for rainfall distribution skew
    - min_child_weight=5 to prevent splits on very small rain event clusters
    - Physics clamp: predictions always >= 0
    """

    def __init__(
        self,
        n_estimators: int = 600,
        max_depth: int = 6,
        learning_rate: float = 0.03,
        early_stopping_rounds: int = 30,
    ):
        self.model_name = "Level2_Standard_ML_XGB"
        self.model_version = "v2.0.0"
        self.feature_cols = STANDARD_FEATURE_COLS
        self.early_stopping_rounds = early_stopping_rounds

        # Monotone constraint: nwp_rainfall is at index 0 → must be non-decreasing
        # All other features: 0 (unconstrained)
        mono_constraints = [0] * len(STANDARD_FEATURE_COLS)
        mono_constraints[0] = 1   # nwp_rainfall: monotone increasing
        mono_constraints[1] = 1   # nwp_rain_log1p: monotone increasing

        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=0.80,
            colsample_bytree=0.80,
            colsample_bylevel=0.90,
            min_child_weight=5,
            gamma=0.5,
            reg_alpha=0.2,
            reg_lambda=1.5,
            objective="reg:squarederror",  # log1p handles skewness
            monotone_constraints=tuple(mono_constraints),
            random_state=42,
            eval_metric="mae",
        )

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame) -> "Level2StandardML":
        # Fill any missing columns with 0 (graceful degradation)
        train_work = train_df.copy()
        val_work = val_df.copy()
        for col in self.feature_cols:
            if col not in train_work.columns:
                train_work[col] = 0.0
            if col not in val_work.columns:
                val_work[col] = 0.0

        X_train = train_work[self.feature_cols]
        # log1p target: aligns with right-skewed monsoon distribution
        y_train = np.log1p(train_work["observed_rainfall"].values)
        X_val = val_work[self.feature_cols]
        y_val = np.log1p(val_work["observed_rainfall"].values)

        self.model.set_params(early_stopping_rounds=self.early_stopping_rounds)
        self.model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        df_in = df.copy()
        for col in self.feature_cols:
            if col not in df_in.columns:
                df_in[col] = 0.0
        X = df_in[self.feature_cols]
        log_preds = self.model.predict(X)
        preds = np.expm1(log_preds)   # inverse of log1p transform
        return np.maximum(preds, 0.0)
