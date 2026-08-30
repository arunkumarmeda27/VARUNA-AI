"""
VARUNA-AI: Rigorous Scientific Ablation Study & Regime-Wise Verification Engine
Smart India Hackathon 2026 | Problem Statement: SIH26080
Central Research Question:
"Can explicitly identifying the prevailing weather regime and using that information
during rainfall post-processing improve raw NWP rainfall forecasts, especially for heavy
and very heavy rainfall events?"

Explicitly compares 4 configurations on the independent test dataset (2024):
  Config 0: Raw NWP (Level 0 Baseline)
  Config 1: Empirical Quantile Mapping / EQM (Level 1 Statistical Baseline)
  Config 2: Standard ML without Regime features (Level 2 ML Baseline — Model A)
  Config 3: VARUNA-AI Regime-Aware ML (Level 3 Regime-Aware Model — Model B)
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

from verification.metrics import VerificationMetrics
from correction.models.correction_engine import CorrectionEngine
from regimes.inference.regime_classifier import RegimeClassifier
from weather_data.metadata.data_dictionary import IMD_PRECIP_THRESHOLDS, WEATHER_REGIMES

PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "weather_data", "processed")
EXPERIMENTS_DIR = os.path.join(os.path.dirname(__file__))

class ScientificAblationStudy:
    """
    Executes reproducible scientific ablation experiment and exports rigorous metric tables.
    """

    def __init__(self, data_version: str = "v1.0.0"):
        self.data_version = data_version
        self.engine = CorrectionEngine()
        self.regime_classifier = RegimeClassifier()

    def run_ablation_experiment(self) -> dict:
        test_path = os.path.join(PROCESSED_DATA_DIR, f"test_{self.data_version}.parquet")
        if not os.path.exists(test_path):
            raise FileNotFoundError(f"Test dataset not found at {test_path}. Build master dataset first.")

        test_df = pd.read_parquet(test_path)
        test_df = self.regime_classifier.predict_dataframe(test_df)

        y_true = test_df["observed_rainfall"].values
        raw_nwp = test_df["nwp_rainfall"].values

        # Generate predictions across model ladder
        ladder_preds = self.engine.predict_ladder(test_df)
        pred_l0 = ladder_preds["level0_raw_nwp"]
        pred_l1 = ladder_preds["level1_quantile_mapping"]
        pred_l2 = ladder_preds["level2_standard_ml"]
        pred_l3 = ladder_preds["level3_regime_aware_ml"]

        models = {
            "Config0_Raw_NWP": pred_l0,
            "Config1_Quantile_Mapping_EQM": pred_l1,
            "Config2_Standard_ML_ModelA": pred_l2,
            "Config3_Regime_Aware_ML_ModelB": pred_l3,
        }

        # 1. Overall Continuous Metrics
        continuous_summary = {}
        for m_name, preds in models.items():
            continuous_summary[m_name] = VerificationMetrics.continuous_metrics(y_true, preds)

        # 2. Categorical & Extreme Rain Verification across Thresholds
        thresholds = [2.5, 15.6, 64.5, 115.6, 204.5]
        categorical_summary = {thresh: {} for thresh in thresholds}
        for thresh in thresholds:
            for m_name, preds in models.items():
                cat = VerificationMetrics.categorical_scores(y_true, preds, threshold=thresh)
                categorical_summary[thresh][m_name] = {
                    "POD": cat["POD"],
                    "FAR": cat["FAR"],
                    "CSI": cat["CSI"],
                    "ETS": cat["ETS"],
                    "Frequency_Bias": cat["Frequency_Bias"],
                    "Hits": cat["Hits"],
                    "Misses": cat["Misses"],
                    "False_Alarms": cat["False_Alarms"],
                }

        # 3. Regime-Stratified Breakdown (Performance evaluated separately for each regime)
        regime_breakdown = {}
        unique_regimes = sorted(test_df["true_regime"].unique())
        for reg in unique_regimes:
            mask = (test_df["true_regime"] == reg).values
            n_samples = int(np.sum(mask))
            if n_samples > 0:
                y_sub = y_true[mask]
                regime_breakdown[reg] = {
                    "sample_count": n_samples,
                    "models": {}
                }
                for m_name, preds in models.items():
                    p_sub = preds[mask]
                    cont = VerificationMetrics.continuous_metrics(y_sub, p_sub)
                    cat_64 = VerificationMetrics.categorical_scores(y_sub, p_sub, threshold=64.5)
                    regime_breakdown[reg]["models"][m_name] = {
                        "MAE": cont["MAE"],
                        "RMSE": cont["RMSE"],
                        "Mean_Bias": cont["Mean_Bias"],
                        "Correlation": cont["Correlation"],
                        "CSI_64.5mm": cat_64["CSI"],
                        "POD_64.5mm": cat_64["POD"],
                    }

        # 4. Spatial Scale Verification (Fractions Skill Score)
        fss_scales = [1, 3, 5]
        fss_summary = {}
        for scale in fss_scales:
            fss_summary[f"scale_{scale}x{scale}"] = {
                m_name: VerificationMetrics.fractions_skill_score(y_true, preds, threshold=64.5, window_size=scale)
                for m_name, preds in models.items()
            }

        # 5. Scientific Hypothesis Evaluation & Delta Gains
        m_l0 = continuous_summary["Config0_Raw_NWP"]
        m_l2 = continuous_summary["Config2_Standard_ML_ModelA"]
        m_l3 = continuous_summary["Config3_Regime_Aware_ML_ModelB"]

        csi_l0_64 = categorical_summary[64.5]["Config0_Raw_NWP"]["CSI"]
        csi_l2_64 = categorical_summary[64.5]["Config2_Standard_ML_ModelA"]["CSI"]
        csi_l3_64 = categorical_summary[64.5]["Config3_Regime_Aware_ML_ModelB"]["CSI"]

        pod_l0_64 = categorical_summary[64.5]["Config0_Raw_NWP"]["POD"]
        pod_l3_64 = categorical_summary[64.5]["Config3_Regime_Aware_ML_ModelB"]["POD"]

        delta_rmse_b_vs_a_pct = round(((m_l2["RMSE"] - m_l3["RMSE"]) / m_l2["RMSE"]) * 100.0, 2)
        delta_mae_b_vs_a_pct = round(((m_l2["MAE"] - m_l3["MAE"]) / m_l2["MAE"]) * 100.0, 2)
        total_rmse_reduction_pct = round(((m_l0["RMSE"] - m_l3["RMSE"]) / m_l0["RMSE"]) * 100.0, 2)
        csi_gain_heavy_rain_pct = round(((csi_l3_64 - csi_l0_64) / max(1e-4, csi_l0_64)) * 100.0, 2)

        ablation_results = {
            "experiment_id": "EXP_ABLATION_2026_01",
            "experiment_name": "SIH26080 Scientific Ablation & Regime-Wise Verification",
            "dataset_version": self.data_version,
            "test_period": "2024-06-01 to 2024-09-30",
            "test_sample_count": len(test_df),
            "research_hypothesis": "Explicit weather regime identification provides measurable skill gains over standard NWP post-processing.",
            "hypothesis_supported": bool(m_l3["RMSE"] < m_l2["RMSE"] and m_l3["MAE"] < m_l2["MAE"]),
            "overall_continuous_metrics": continuous_summary,
            "categorical_metrics_by_threshold": categorical_summary,
            "regime_stratified_verification": regime_breakdown,
            "spatial_fractions_skill_score": fss_summary,
            "scientific_delta_gains": {
                "RMSE_reduction_ModelB_vs_ModelA_pct": delta_rmse_b_vs_a_pct,
                "MAE_reduction_ModelB_vs_ModelA_pct": delta_mae_b_vs_a_pct,
                "Total_RMSE_reduction_VARUNA_vs_RawNWP_pct": total_rmse_reduction_pct,
                "CSI_heavy_rain_gain_vs_RawNWP_pct": csi_gain_heavy_rain_pct,
                "POD_heavy_rain_gain_vs_RawNWP": round(pod_l3_64 - pod_l0_64, 3),
            },
            "timestamp": datetime.now().isoformat(),
        }

        # Save machine-readable JSON artifact
        out_json = os.path.join(EXPERIMENTS_DIR, "ablation_study_results.json")
        with open(out_json, "w") as f:
            json.dump(ablation_results, f, indent=2)

        return ablation_results

if __name__ == "__main__":
    study = ScientificAblationStudy()
    results = study.run_ablation_experiment()

    print("================================================================================")
    print("      VARUNA-AI: SCIENTIFIC ABLATION STUDY & REGIME-WISE VERIFICATION          ")
    print("================================================================================")
    print(f"Test Period: {results['test_period']} ({results['test_sample_count']} grid-days)")
    print(f"Hypothesis Supported: {results['hypothesis_supported']}")
    print("\n--- Model Ladder Overall Continuous Verification ---")
    for m_name, metrics in results["overall_continuous_metrics"].items():
        print(f"  {m_name:32s} | MAE: {metrics['MAE']:5.2f} mm | RMSE: {metrics['RMSE']:5.2f} mm | Bias: {metrics['Mean_Bias']:6.2f} mm | r: {metrics['Correlation']:.3f}")

    print("\n--- Heavy Rainfall Verification (Threshold >= 64.5 mm) ---")
    for m_name, metrics in results["categorical_metrics_by_threshold"][64.5].items():
        print(f"  {m_name:32s} | CSI: {metrics['CSI']:.3f} | POD: {metrics['POD']:.3f} | FAR: {metrics['FAR']:.3f} | Bias: {metrics['Frequency_Bias']:.2f}")

    print("\n--- Regime-Stratified Performance (MAE / RMSE in mm) ---")
    for reg, reg_data in results["regime_stratified_verification"].items():
        print(f"  Regime: {reg:<24s} (N = {reg_data['sample_count']:3d})")
        for m_name, m_stats in reg_data["models"].items():
            print(f"    - {m_name:<30s}: MAE = {m_stats['MAE']:5.2f} | RMSE = {m_stats['RMSE']:5.2f} | CSI(64.5mm) = {m_stats['CSI_64.5mm']:.3f}")

    print("\n--- Scientific Gains Summary ---")
    gains = results["scientific_delta_gains"]
    print(f"  Model B (Regime-Aware) vs Model A (Standard ML) RMSE Gain: {gains['RMSE_reduction_ModelB_vs_ModelA_pct']}%")
    print(f"  VARUNA-AI vs Raw NWP Total RMSE Reduction:                {gains['Total_RMSE_reduction_VARUNA_vs_RawNWP_pct']}%")
    print(f"  Heavy Rain CSI Relative Improvement:                      {gains['CSI_heavy_rain_gain_vs_RawNWP_pct']}%")
    print("================================================================================")
