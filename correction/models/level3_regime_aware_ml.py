"""
VARUNA-AI: Level 3 Regime-Aware ML Correction Model
Owner: Member 3 (Rainfall Post-Processing ML Engineer)

Level 3 regime-aware rainfall post-processing model.

This implementation requires the complete real-data feature set.
Missing features are rejected explicitly instead of being replaced
with artificial zero values.
"""

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from typing import List

from correction.models.level2_standard_ml import STANDARD_FEATURE_COLS
from weather_data.metadata.data_dictionary import WEATHER_REGIMES


REGIME_PROB_COLS: List[str] = [
    f"prob_{r.lower()}"
    for r in WEATHER_REGIMES
]

REGIME_INTERACTION_COLS: List[str] = [
    "monsoon_trough_lat",
    "vorticity_proxy",
    "moisture_flux_index",
    "orographic_flux_idx",
    "offshore_trough_idx",
    "convective_index",
]


_seen = set()
_full_cols: List[str] = []

for col in (
    STANDARD_FEATURE_COLS
    + REGIME_PROB_COLS
    + REGIME_INTERACTION_COLS
):
    if col not in _seen:
        _seen.add(col)
        _full_cols.append(col)

REGIME_AWARE_FEATURE_COLS: List[str] = _full_cols


class Level3RegimeAwareML:
    """
    Level 3: Regime-Aware Machine Learning rainfall correction model.

    Uses real meteorological and regime features.

    Missing required features are rejected explicitly.
    No synthetic zero-filling is performed.
    """

    def __init__(
        self,
        n_estimators: int = 700,
        max_depth: int = 7,
        learning_rate: float = 0.025,
        early_stopping_rounds: int = 40,
    ):
        self.model_name = "Level3_Regime_Aware_ML_XGB"
        self.model_version = "v4.0.0"

        self.feature_cols = REGIME_AWARE_FEATURE_COLS
        self.early_stopping_rounds = early_stopping_rounds
        self._trained = False

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

    def _validate_features(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        require_target: bool = True,
    ) -> None:
        """
        Validate that every required real feature exists.

        Missing features are NOT replaced with zero.
        """

        missing_features = [
            col
            for col in self.feature_cols
            if col not in df.columns
        ]

        if missing_features:
            raise ValueError(
                f"{dataset_name} is missing required Level 3 "
                f"features: {missing_features}"
            )

        if require_target and "observed_rainfall" not in df.columns:
            raise ValueError(
                f"{dataset_name} is missing required target "
                "'observed_rainfall'."
            )

        feature_values = df[
            self.feature_cols
        ].to_numpy(dtype=np.float64)

        if not np.isfinite(feature_values).all():
            raise ValueError(
                f"{dataset_name} contains NaN or infinite values "
                "in Level 3 features."
            )

        if require_target:
            target_values = df[
                "observed_rainfall"
            ].to_numpy(dtype=np.float64)

            if not np.isfinite(target_values).all():
                raise ValueError(
                    f"{dataset_name} contains NaN or infinite "
                    "values in observed_rainfall."
                )

            if (target_values < 0).any():
                raise ValueError(
                    f"{dataset_name} contains negative "
                    "observed rainfall values."
                )

    def fit(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
    ) -> "Level3RegimeAwareML":
        """
        Train Level 3 using real training and validation data.
        """

        self._validate_features(
            train_df,
            "Training dataset",
            require_target=True,
        )

        self._validate_features(
            val_df,
            "Validation dataset",
            require_target=True,
        )

        X_train = train_df[
            self.feature_cols
        ]

        X_val = val_df[
            self.feature_cols
        ]

        y_train_log = np.log1p(
            train_df[
                "observed_rainfall"
            ].to_numpy(dtype=np.float64)
        )

        y_val_log = np.log1p(
            val_df[
                "observed_rainfall"
            ].to_numpy(dtype=np.float64)
        )

        self.model.fit(
            X_train,
            y_train_log,
            eval_set=[
                (X_val, y_val_log)
            ],
            verbose=False,
        )

        self._trained = True

        return self

    def predict(
        self,
        df: pd.DataFrame,
    ) -> np.ndarray:
        """
        Generate corrected rainfall predictions.

        Missing features cause an explicit error.
        """

        self._validate_features(
            df,
            "Prediction dataset",
            require_target=False,
        )

        X = df[
            self.feature_cols
        ]

        log_preds = self.model.predict(X)

        preds = np.expm1(log_preds)

        return np.maximum(
            preds,
            0.0,
        )

    def save(
        self,
        path: str,
    ) -> None:
        """Save trained model."""
        joblib.dump(
            self,
            path,
        )

    @classmethod
    def load(
        cls,
        path: str,
    ) -> "Level3RegimeAwareML":
        """Load trained model."""
        return joblib.load(path)