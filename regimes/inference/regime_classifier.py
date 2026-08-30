"""
VARUNA-AI: Weather Regime Inference Module
Owner: Member 2 (Weather Regime Classification Engineer)

Provides machine-readable weather regime predictions and calibrated class probabilities.
Interface contract for Member 3 (Post-Processing) and Member 5 (Backend API).
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Union

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
MODEL_ARTIFACT_PATH = os.path.join(MODELS_DIR, "regime_xgb_artifact.joblib")

class RegimeClassifier:
    """
    Inference service for Weather Regime Classification.
    """

    def __init__(self, artifact_path: str = MODEL_ARTIFACT_PATH):
        if not os.path.exists(artifact_path):
            raise FileNotFoundError(f"Model artifact not found at {artifact_path}. Train the model first.")
        self.artifact = joblib.load(artifact_path)
        self.model = self.artifact["model"]
        self.classes = self.artifact["classes"]
        self.idx_to_class = self.artifact["idx_to_class"]
        self.feature_cols = self.artifact["feature_cols"]
        self.model_version = self.artifact["model_version"]

    def predict_single(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Inference for a single meteorological feature vector.
        """
        df = pd.DataFrame([features])
        # Ensure all feature columns exist, fallback to 0.0 if missing with warning
        for col in self.feature_cols:
            if col not in df.columns:
                df[col] = 0.0

        X = df[self.feature_cols]
        probs = self.model.predict_proba(X)[0]
        pred_idx = int(np.argmax(probs))
        predicted_regime = self.idx_to_class[pred_idx]
        confidence = float(probs[pred_idx])

        prob_dict = {
            self.idx_to_class[i]: float(round(probs[i], 4))
            for i in range(len(self.classes))
        }

        return {
            "regime": predicted_regime,
            "regime_confidence": confidence,
            "regime_probabilities": prob_dict,
            "model_version": self.model_version,
        }

    def predict_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Batch inference for DataFrame. Appends predicted_regime and regime probabilities.
        """
        df_in = df.copy()
        for col in self.feature_cols:
            if col not in df_in.columns:
                df_in[col] = 0.0

        X = df_in[self.feature_cols]
        probs = self.model.predict_proba(X)
        pred_indices = np.argmax(probs, axis=1)

        df_in["predicted_regime"] = [self.idx_to_class[i] for i in pred_indices]
        df_in["regime_confidence"] = np.max(probs, axis=1)

        # Add per-class probability columns
        for i, cls_name in enumerate(self.classes):
            df_in[f"prob_{cls_name.lower()}"] = probs[:, i]

        df_in["regime_model_version"] = self.model_version
        return df_in
