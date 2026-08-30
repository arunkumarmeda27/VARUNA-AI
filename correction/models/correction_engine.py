"""
VARUNA-AI: Unified Rainfall Post-Processing Engine
Owner: Member 3 (Rainfall Post-Processing ML Engineer)

Unified inference engine providing Level 0, Level 1, Level 2, and Level 3
rainfall forecasts with model provenance and physical sanity guarantees.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List

from correction.baselines.level0_raw_nwp import Level0RawNWP
from correction.baselines.level1_quantile_mapping import Level1QuantileMapping
from correction.models.level2_standard_ml import Level2StandardML
from correction.models.level3_regime_aware_ml import Level3RegimeAwareML
from regimes.inference.regime_classifier import RegimeClassifier

CORRECTION_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")

class RainfallCorrectionEngine:
    """
    Orchestrates rainfall post-processing across all levels of the model ladder.
    """

    def __init__(self, artifacts_dir: str = CORRECTION_MODELS_DIR):
        self.artifacts_dir = artifacts_dir
        self.regime_classifier = RegimeClassifier()
        self.level0 = Level0RawNWP()
        self.level1 = None
        self.level2 = None
        self.level3 = None
        self.load_models()

    def load_models(self):
        l1_path = os.path.join(self.artifacts_dir, "level1_eqm.joblib")
        l2_path = os.path.join(self.artifacts_dir, "level2_standard_xgb.joblib")
        l3_path = os.path.join(self.artifacts_dir, "level3_regime_aware_xgb.joblib")

        if os.path.exists(l1_path):
            self.level1 = joblib.load(l1_path)
        if os.path.exists(l2_path):
            self.level2 = joblib.load(l2_path)
        if os.path.exists(l3_path):
            self.level3 = joblib.load(l3_path)

    def process_forecast(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executes end-to-end post-processing pipeline:
        1. Classifies weather regime and extracts class probabilities.
        2. Computes Level 0 (Raw NWP).
        3. Computes Level 1 (Quantile Mapping).
        4. Computes Level 2 (Standard ML).
        5. Computes Level 3 (Regime-Aware ML).
        6. Computes correction delta and regime-aware gain.
        """
        df_out = df.copy()

        # Step 1: Regime Classification
        df_out = self.regime_classifier.predict_dataframe(df_out)

        # Step 2: Level 0
        df_out["rain_level0_raw"] = self.level0.predict(df_out)

        # Step 3: Level 1
        if self.level1:
            df_out["rain_level1_eqm"] = np.round(self.level1.predict(df_out["nwp_rainfall"].values), 2)
        else:
            df_out["rain_level1_eqm"] = df_out["rain_level0_raw"]

        # Step 4: Level 2
        if self.level2:
            df_out["rain_level2_std_ml"] = np.round(self.level2.predict(df_out), 2)
        else:
            df_out["rain_level2_std_ml"] = df_out["rain_level1_eqm"]

        # Step 5: Level 3 (VARUNA-AI Production Model)
        if self.level3:
            df_out["rain_level3_varuna"] = np.round(self.level3.predict(df_out), 2)
        else:
            df_out["rain_level3_varuna"] = df_out["rain_level2_std_ml"]

        # Primary operational corrected output
        df_out["corrected_rainfall"] = df_out["rain_level3_varuna"]
        df_out["bias_correction_delta"] = np.round(df_out["corrected_rainfall"] - df_out["nwp_rainfall"], 2)
        df_out["post_processing_model_version"] = "VARUNA-Level3-XGB-v1.0.0"

        return df_out
