"""
VARUNA-AI: Level 2 Standard ML Correction Model
Owner: Member 3 (Rainfall Post-Processing ML Engineer)

Level 2 Standard ML rainfall post-processing model.

Uses only features that are actually available in the real
2021-2025 VARUNA-AI ML-ready dataset.

No synthetic pressure-level features.
No missing-feature zero filling.
"""

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from typing import List


STANDARD_FEATURE_COLS: List[str] = [
    "nwp_rainfall",
    "nwp_rain_log1p",
    "nwp_is_rain",
    "nwp_is_heavy",

    "temperature_c",
    "dewpoint_c",
    "relative_humidity",
    "u10",
    "v10",
    "wind_speed",

    "wind_speed_10m",
    "wind_dir_10m",
    "temperature_dewpoint_spread",
    "moisture_index",

    "day_of_year_sin",
    "day_of_year_cos",

    "latitude",
    "longitude",
]


class Level2StandardML:

    def __init__(
        self,
        n_estimators: int = 600,
        max_depth: int = 6,
        learning_rate: float = 0.03,
        early_stopping_rounds: int = 30,
    ):
        self.model_name = "Level2_Standard_ML_XGB"
        self.model_version = "v4.0.0"

        self.feature_cols = STANDARD_FEATURE_COLS
        self.early_stopping_rounds = early_stopping_rounds

        mono_constraints = [0] * len(
            STANDARD_FEATURE_COLS
        )

        mono_constraints[0] = 1
        mono_constraints[1] = 1

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
            objective="reg:squarederror",
            monotone_constraints=tuple(
                mono_constraints
            ),
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

        missing_features = [
            col
            for col in self.feature_cols
            if col not in df.columns
        ]

        if missing_features:
            raise ValueError(
                f"{dataset_name} is missing required "
                f"Level 2 real-data features: "
                f"{missing_features}"
            )

        if require_target:
            if "imd_rainfall" not in df.columns:
                raise ValueError(
                    f"{dataset_name} is missing the real "
                    "'imd_rainfall' target column."
                )

        feature_values = (
            df[self.feature_cols]
            .to_numpy(dtype=np.float64)
        )

        if not np.isfinite(feature_values).all():
            raise ValueError(
                f"{dataset_name} contains NaN or infinite "
                "values in Level 2 features."
            )

        if require_target:
            target_values = (
                df["imd_rainfall"]
                .to_numpy(dtype=np.float64)
            )

            if not np.isfinite(
                target_values
            ).all():
                raise ValueError(
                    f"{dataset_name} contains NaN or "
                    "infinite values in imd_rainfall."
                )

            if (target_values < 0).any():
                raise ValueError(
                    f"{dataset_name} contains negative "
                    "IMD rainfall values."
                )

    def fit(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
    ) -> "Level2StandardML":

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

        y_train = np.log1p(
            train_df["imd_rainfall"]
            .to_numpy(dtype=np.float64)
        )

        y_val = np.log1p(
            val_df["imd_rainfall"]
            .to_numpy(dtype=np.float64)
        )

        self.model.fit(
            X_train,
            y_train,
            eval_set=[
                (X_val, y_val)
            ],
            verbose=False,
        )

        return self

    def predict(
        self,
        df: pd.DataFrame,
    ) -> np.ndarray:

        self._validate_features(
            df,
            "Prediction dataset",
            require_target=False,
        )

        X = df[
            self.feature_cols
        ]

        log_predictions = (
            self.model.predict(X)
        )

        predictions = np.expm1(
            log_predictions
        )

        predictions = np.maximum(
            predictions,
            0.0,
        )

        return predictions

    def save(
        self,
        path: str,
    ) -> None:

        joblib.dump(
            self,
            path,
        )

    @classmethod
    def load(
        cls,
        path: str,
    ) -> "Level2StandardML":

        return joblib.load(path)