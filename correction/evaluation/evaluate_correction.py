"""
VARUNA-AI: Rainfall Correction Evaluation and Model Ladder Pipeline
Owner: Member 3 (Rainfall Post-Processing ML Engineer)

Trains and evaluates all levels of the model ladder (Level 0 through Level 3),
quantifying scientific gains across continuous metrics and regime-stratified subsets.
"""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.stats import pearsonr

from correction.baselines.level0_raw_nwp import Level0RawNWP
from correction.baselines.level1_quantile_mapping import Level1QuantileMapping
from correction.models.level2_standard_ml import Level2StandardML
from correction.models.level3_regime_aware_ml import Level3RegimeAwareML
from regimes.inference.regime_classifier import RegimeClassifier

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
EVAL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evaluation")
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "weather_data", "processed")

def calc_continuous_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Calculates MAE, RMSE, Mean Bias, and Pearson Correlation coefficient."""
    mae = float(np.mean(np.abs(y_pred - y_true)))
    rmse = float(np.sqrt(np.mean((y_pred - y_true)**2)))
    bias = float(np.mean(y_pred - y_true))
    corr, _ = pearsonr(y_true, y_pred) if len(y_true) > 1 and np.std(y_pred) > 1e-6 and np.std(y_true) > 1e-6 else (0.0, 0.0)
    return {
        "MAE": round(mae, 3),
        "RMSE": round(rmse, 3),
        "Mean_Bias": round(bias, 3),
        "Correlation": round(float(corr), 3),
    }

class CorrectionEvaluator:
    """
    Orchestrates post-processing model training, artifact saving, and scientific evaluation.
    """

    def __init__(self, data_version: str = "v1.0.0"):
        self.data_version = data_version
        self.regime_classifier = RegimeClassifier()
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        os.makedirs(EVAL_DIR, exist_ok=True)

    def run_training_and_evaluation(self) -> dict:
        train_path = os.path.join(PROCESSED_DATA_DIR, f"train_{self.data_version}.parquet")
        val_path = os.path.join(PROCESSED_DATA_DIR, f"val_{self.data_version}.parquet")
        test_path = os.path.join(PROCESSED_DATA_DIR, f"test_{self.data_version}.parquet")

        train_df = pd.read_parquet(train_path)
        val_df = pd.read_parquet(val_path)
        test_df = pd.read_parquet(test_path)

        # Enrich training, val, and test data with regime probabilities
        logger.info("Enriching splits with weather regime predictions...")
        train_df = self.regime_classifier.predict_dataframe(train_df)
        val_df = self.regime_classifier.predict_dataframe(val_df)
        test_df = self.regime_classifier.predict_dataframe(test_df)

        # 1. Level 0: Raw NWP
        level0 = Level0RawNWP()

        # 2. Level 1: Quantile Mapping
        logger.info("Fitting Level 1 Empirical Quantile Mapping...")
        level1 = Level1QuantileMapping()
        level1.fit(train_df["nwp_rainfall"].values, train_df["observed_rainfall"].values)
        joblib.dump(level1, os.path.join(ARTIFACTS_DIR, "level1_eqm.joblib"))

        # 3. Level 2: Standard ML (Model A)
        logger.info("Fitting Level 2 Standard ML (Model A)...")
        level2 = Level2StandardML()
        level2.fit(train_df, val_df)
        joblib.dump(level2, os.path.join(ARTIFACTS_DIR, "level2_standard_xgb.joblib"))

        # 4. Level 3: Regime-Aware ML (Model B)
        logger.info("Fitting Level 3 Regime-Aware ML (Model B)...")
        level3 = Level3RegimeAwareML()
        level3.fit(train_df, val_df)
        joblib.dump(level3, os.path.join(ARTIFACTS_DIR, "level3_regime_aware_xgb.joblib"))

        # 5. Predictions on Test Dataset (2024)
        y_test_true = test_df["observed_rainfall"].values
        pred_l0 = level0.predict(test_df)
        pred_l1 = level1.predict(test_df["nwp_rainfall"].values)
        pred_l2 = level2.predict(test_df)
        pred_l3 = level3.predict(test_df)

        # Overall Continuous Metrics across ladder
        m_l0 = calc_continuous_metrics(y_test_true, pred_l0)
        m_l1 = calc_continuous_metrics(y_test_true, pred_l1)
        m_l2 = calc_continuous_metrics(y_test_true, pred_l2)
        m_l3 = calc_continuous_metrics(y_test_true, pred_l3)

        # Hypothesis A vs B Relative Improvements
        mae_gain_b_vs_a = round(((m_l2["MAE"] - m_l3["MAE"]) / m_l2["MAE"]) * 100.0, 2)
        rmse_gain_b_vs_a = round(((m_l2["RMSE"] - m_l3["RMSE"]) / m_l2["RMSE"]) * 100.0, 2)
        rmse_gain_b_vs_raw = round(((m_l0["RMSE"] - m_l3["RMSE"]) / m_l0["RMSE"]) * 100.0, 2)

        # Regime-stratified evaluation on test set
        regimes = sorted(test_df["true_regime"].unique())
        regime_eval = {}
        for reg in regimes:
            mask = (test_df["true_regime"] == reg).values
            if np.sum(mask) > 0:
                regime_eval[reg] = {
                    "sample_count": int(np.sum(mask)),
                    "Level0_Raw": calc_continuous_metrics(y_test_true[mask], pred_l0[mask]),
                    "Level1_EQM": calc_continuous_metrics(y_test_true[mask], pred_l1[mask]),
                    "Level2_StdML": calc_continuous_metrics(y_test_true[mask], pred_l2[mask]),
                    "Level3_RegimeAware": calc_continuous_metrics(y_test_true[mask], pred_l3[mask]),
                }

        report = {
            "test_period": "2024-06-01 to 2024-09-30",
            "test_samples": len(test_df),
            "model_ladder_overall_metrics": {
                "Level0_Raw_NWP": m_l0,
                "Level1_Quantile_Mapping": m_l1,
                "Level2_Standard_ML_ModelA": m_l2,
                "Level3_Regime_Aware_ModelB": m_l3,
            },
            "scientific_gains": {
                "MAE_improvement_ModelB_vs_ModelA_pct": mae_gain_b_vs_a,
                "RMSE_improvement_ModelB_vs_ModelA_pct": rmse_gain_b_vs_a,
                "RMSE_improvement_VARUNA_vs_RawNWP_pct": rmse_gain_b_vs_raw,
                "hypothesis_supported": bool(m_l3["RMSE"] < m_l2["RMSE"]),
            },
            "regime_stratified_metrics": regime_eval,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Save report
        out_path = os.path.join(EVAL_DIR, "correction_evaluation_report.json")
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)

        return report

if __name__ == "__main__":
    evaluator = CorrectionEvaluator()
    rep = evaluator.run_training_and_evaluation()
    print("Rainfall Post-Processing Evaluation Complete!")
    print("Model Ladder Overall Results:")
    for lvl, metrics in rep["model_ladder_overall_metrics"].items():
        print(f"  {lvl:30s} -> MAE: {metrics['MAE']:5.2f} mm | RMSE: {metrics['RMSE']:5.2f} mm | Bias: {metrics['Mean_Bias']:5.2f} mm | r: {metrics['Correlation']:.3f}")
    print("\nScientific Gain (Hypothesis A vs B):")
    print(f"  RMSE Reduction (Model B vs Model A): {rep['scientific_gains']['RMSE_improvement_ModelB_vs_ModelA_pct']}%")
    print(f"  Total RMSE Reduction (VARUNA vs Raw NWP): {rep['scientific_gains']['RMSE_improvement_VARUNA_vs_RawNWP_pct']}%")
