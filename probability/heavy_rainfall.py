"""
VARUNA-AI: Heavy Rainfall Probability Estimation Module
Owner: Member 4 (Probability + Uncertainty + Verification Engineer)

Estimates calibrated probabilities of exceeding critical IMD rainfall thresholds:
- Moderate Rain (>= 15.6 mm/day)
- Heavy Rain (>= 64.5 mm/day)
- Very Heavy Rain (>= 115.6 mm/day)
- Extremely Heavy Rain (>= 204.5 mm/day)
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Any
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
import xgboost as xgb

from weather_data.metadata.data_dictionary import OPERATIONAL_THRESHOLDS

PROB_MODELS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")

class HeavyRainfallProbabilityEstimator:
    """
    Calibrated probabilistic models for operational rainfall exceedance.
    """

    THRESHOLDS = {
        "MODERATE": 15.6,
        "HEAVY": 64.5,
        "VERY_HEAVY": 115.6,
        "EXTREMELY_HEAVY": 204.5,
    }

    def __init__(self, artifacts_dir: str = PROB_MODELS_DIR):
        self.artifacts_dir = artifacts_dir
        self.models: Dict[str, Any] = {}
        os.makedirs(self.artifacts_dir, exist_ok=True)
        self.load_models()

    def train_probability_models(self, train_df: pd.DataFrame, val_df: pd.DataFrame):
        """
        Trains calibrated probabilistic classifiers for each IMD threshold.
        """
        feature_cols = [
            "nwp_rainfall",
            "nwp_rain_log1p",
            "tcwv",
            "rh700",
            "cape",
            "wind_speed_850",
            "vertical_wind_shear",
            "vorticity_proxy",
            "moisture_flux_index",
        ]

        X_train = train_df[feature_cols].copy()
        X_val = val_df[feature_cols].copy()

        for name, thresh in self.THRESHOLDS.items():
            y_train = (train_df["observed_rainfall"] >= thresh).astype(int)
            y_val = (val_df["observed_rainfall"] >= thresh).astype(int)

            if y_train.sum() >= 5:  # Ensure positive samples exist
                base_clf = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=4,
                    learning_rate=0.05,
                    eval_metric="logloss",
                    random_state=42,
                )
                calibrator = CalibratedClassifierCV(estimator=base_clf, cv=3, method="sigmoid")
                calibrator.fit(X_train, y_train)

                self.models[name] = {
                    "model": calibrator,
                    "threshold": thresh,
                    "features": feature_cols,
                }
                joblib.dump(self.models[name], os.path.join(self.artifacts_dir, f"prob_{name.lower()}.joblib"))

    def load_models(self):
        for name in self.THRESHOLDS.keys():
            path = os.path.join(self.artifacts_dir, f"prob_{name.lower()}.joblib")
            if os.path.exists(path):
                self.models[name] = joblib.load(path)

    def estimate_probabilities(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes calibrated probability of exceeding each operational threshold.
        """
        df_out = df.copy()

        for name, thresh in self.THRESHOLDS.items():
            col_name = f"prob_exceed_{thresh:.1f}mm"
            if name in self.models:
                m_info = self.models[name]
                feat_cols = m_info["features"]
                # Fill missing
                X = df_out.copy()
                for c in feat_cols:
                    if c not in X.columns:
                        X[c] = 0.0
                probs = m_info["model"].predict_proba(X[feat_cols])[:, 1]
                df_out[col_name] = np.round(probs, 4)
            else:
                # Fallback: logistic CDF based on corrected rainfall and threshold
                pred_rain = df_out.get("corrected_rainfall", df_out.get("nwp_rainfall", 0.0))
                # Smooth sigmoid around threshold with physical scale
                scale = max(5.0, thresh * 0.25)
                heuristic_prob = 1.0 / (1.0 + np.exp(-(pred_rain - thresh) / scale))
                df_out[col_name] = np.round(np.clip(heuristic_prob, 0.0, 1.0), 4)

        # Primary heavy rainfall probability (>= 64.5 mm)
        df_out["heavy_rain_probability"] = df_out[f"prob_exceed_64.5mm"]

        # IMD Warning / Risk Level Assignment
        def _get_risk_category(row) -> str:
            p_ext = row.get(f"prob_exceed_204.5mm", 0.0)
            p_vh = row.get(f"prob_exceed_115.6mm", 0.0)
            p_h = row.get(f"prob_exceed_64.5mm", 0.0)
            p_m = row.get(f"prob_exceed_15.6mm", 0.0)
            corrected_rain = float(row.get("corrected_rainfall", row.get("nwp_rainfall", 0.0)))

            # Use the rainfall amount as the primary decision gate; probability is only a supporting signal.
            if corrected_rain >= 204.5 or (p_ext >= 0.35 and corrected_rain >= 64.5):
                return "RED_ALERT (Warning / Evacuation Preparedness)"
            elif corrected_rain >= 115.6 or (p_vh >= 0.30 and corrected_rain >= 64.5) or (p_h >= 0.55 and corrected_rain >= 35.5):
                return "ORANGE_ALERT (Alert / Be Prepared)"
            elif corrected_rain >= 64.5 or (p_h >= 0.25 and corrected_rain >= 15.6) or (p_m >= 0.60 and corrected_rain >= 15.6):
                return "YELLOW_ALERT (Watch / Be Updated)"
            else:
                return "GREEN_ALERT (No Warning / Normal Operations)"

        df_out["operational_risk_level"] = df_out.apply(_get_risk_category, axis=1)
        return df_out
