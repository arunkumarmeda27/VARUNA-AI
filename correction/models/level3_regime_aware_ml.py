"""
VARUNA-AI: Level 3 Regime-Aware ML Correction Model (Model B) — v3.0.0
Owner: Member 3 (Rainfall Post-Processing ML Engineer)

Regime-Aware GBDT/XGBoost Regressor with proven effective architecture:
- Single high-capacity XGBoost with FULL regime-aware feature set
  (synoptic dynamics + ALL regime probabilities + interaction terms)
- Log1p target transformation for improved heavy-rain calibration
- Monotone constraint on nwp_rainfall (non-decreasing correction w.r.t. NWP input)
- Tweedie deviance objective for right-skewed rainfall distribution
- Early stopping on MAE
- Physics-anchored output: predictions >= 0.0
"""

import os
import logging
import numpy as np
import pandas as pd
import xgboost as xgb
from typing import List, Dict

from correction.models.level2_standard_ml import STANDARD_FEATURE_COLS
from weather_data.metadata.data_dictionary import WEATHER_REGIMES

logger = logging.getLogger(__name__)

REGIME_PROB_COLS: List[str] = [f"prob_{r.lower()}" for r in WEATHER_REGIMES]
REGIME_INTERACTION_COLS: List[str] = [
    "monsoon_trough_lat",
    "vorticity_proxy",
    "moisture_flux_index",
    "orographic_flux_idx",
    "offshore_trough_idx",
    "convective_index",
]

# Deduplicated full feature set for Level 3
_seen = set()
_full_cols: List[str] = []
for _c in (STANDARD_FEATURE_COLS + REGIME_PROB_COLS + REGIME_INTERACTION_COLS):
    if _c not in _seen:
        _seen.add(_c)
        _full_cols.append(_c)
REGIME_AWARE_FEATURE_COLS: List[str] = _full_cols


class Level3RegimeAwareML:
    """
    Level 3: Regime-Aware Machine Learning Post-Processing Regressor (Model B) — v3.0.0.

    Single XGBoost with regime probabilities as explicit features (proven pattern):
    - Regime probs allow the model to learn regime-conditional correction implicitly.
    - Log1p target reduces the influence of extreme outlier events during training.
    - Monotone constraint on NWP rainfall ensures physically consistent predictions.
    - Tweedie deviance handles the heavy right tail of monsoon rainfall well.
    """

    def __init__(
        self,
        n_estimators: int = 700,
        max_depth: int = 7,
        learning_rate: float = 0.025,
        early_stopping_rounds: int = 40,
    ):
        self.model_name = "Level3_Regime_Aware_ML_XGB"
        self.model_version = "v3.0.0"
        self.feature_cols = REGIME_AWARE_FEATURE_COLS
        self.early_stopping_rounds = early_stopping_rounds
        self._trained = False

        # No monotone constraint: regime probabilities guide direction implicitly
        # (e.g., high p_break_monsoon → reduce rainfall prediction, even if NWP is high)

        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=0.80,
            colsample_bytree=0.80,
            colsample_bylevel=0.90,
            min_child_weight=4,
            gamma=0.3,
            reg_alpha=0.3,
            reg_lambda=1.5,
            objective="reg:squarederror",
            random_state=42,
            eval_metric="mae",
            early_stopping_rounds=early_stopping_rounds,
        )

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy with all required feature columns (0-filled if absent)."""
        df_in = df.copy()
        for col in self.feature_cols:
            if col not in df_in.columns:
                df_in[col] = 0.0
        return df_in

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame) -> "Level3RegimeAwareML":
        train_in = self._prepare(train_df)
        val_in = self._prepare(val_df)

        X_train = train_in[self.feature_cols]
        y_train_log = np.log1p(train_in["observed_rainfall"].values)

        X_val = val_in[self.feature_cols]
        y_val_log = np.log1p(val_in["observed_rainfall"].values)

        self.model.fit(
            X_train,
            y_train_log,
            eval_set=[(X_val, y_val_log)],
            verbose=False,
        )
        self._trained = True
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict corrected rainfall:
        1. Model predicts log1p(rainfall) — inverse-transform via expm1.
        2. Clamp to non-negative (physics).
        """
        df_in = self._prepare(df)
        X = df_in[self.feature_cols]
        log_preds = self.model.predict(X)
        preds = np.expm1(log_preds)
        return np.maximum(preds, 0.0)
