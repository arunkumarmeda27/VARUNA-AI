"""
VARUNA-AI: Master Model Training & Evaluation Pipeline with Named District Dataset
Trains:
1. Weather Regime Classifier (XGBoost + Logistic Regression)
2. Level 1 Empirical Quantile Mapping (EQM)
3. Level 2 Standard ML Regressor (Model A)
4. Level 3 VARUNA-AI Regime-Aware ML Regressor (Model B)
5. Calibrated Heavy Rain Exceedance Probability Estimators (Moderate, Heavy, Very Heavy, Extremely Heavy)
6. Conformal Quantile Estimator (q10, q50, q90 + 80% Split Conformal Calibration)
7. Full Scientific Verification & Benchmark Suite
"""

import os
import sys
import json
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, f1_score, classification_report
from scipy.stats import pearsonr
import xgboost as xgb

# Set up paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VARUNA-TRAIN")

CSV_PATH = os.path.join(PROJECT_ROOT, "VARUNA_AI_100_district_sample_named.csv")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "weather_data", "processed")
CORRECTION_ARTIFACTS = os.path.join(PROJECT_ROOT, "correction", "artifacts")
REGIMES_MODELS_DIR = os.path.join(PROJECT_ROOT, "regimes", "models")
REGIMES_ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "regimes", "artifacts")
PROB_ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "probability", "artifacts")
UNCERTAINTY_ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "uncertainty", "artifacts")
VERIFICATION_DIR = os.path.join(PROJECT_ROOT, "verification")
REGIMES_EVAL_DIR = os.path.join(PROJECT_ROOT, "regimes", "evaluation")

for d in [PROCESSED_DIR, CORRECTION_ARTIFACTS, REGIMES_MODELS_DIR, REGIMES_ARTIFACTS_DIR, 
          PROB_ARTIFACTS_DIR, UNCERTAINTY_ARTIFACTS_DIR, VERIFICATION_DIR, REGIMES_EVAL_DIR]:
    os.makedirs(d, exist_ok=True)

from correction.baselines.level1_quantile_mapping import Level1QuantileMapping
from correction.models.level2_standard_ml import Level2StandardML
from correction.models.level3_regime_aware_ml import Level3RegimeAwareML
from probability.heavy_rainfall import HeavyRainfallProbabilityEstimator
from uncertainty.conformal_quantiles import ConformalQuantileEstimator
from regimes.training.features import REGIME_FEATURE_COLS

def train_all():
    logger.info(f"Loading Named District Dataset from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    logger.info(f"Loaded {len(df)} districts with {len(df.columns)} features.")

    # 1. Identify dominant regime
    prob_cols = [
        "prob_active_monsoon", "prob_break_monsoon", "prob_monsoon_low_depression",
        "prob_coastal_rainfall", "prob_orographic_rainfall", "prob_western_disturbance"
    ]
    df["true_regime"] = df[prob_cols].idxmax(axis=1).str.replace("prob_", "").str.upper()
    logger.info(f"Regime counts:\n{df['true_regime'].value_counts()}")

    # Ensure required features exist
    for col in REGIME_FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0.0

    # Ensure nwp_rain_log1p
    if "nwp_rain_log1p" not in df.columns:
        df["nwp_rain_log1p"] = np.log1p(np.maximum(0, df["nwp_rainfall"]))

    # 2. Train / Val / Test Split (70% / 15% / 15%)
    train_df, test_val_df = train_test_split(df, test_size=0.30, random_state=42, stratify=df["true_regime"])
    val_df, test_df = train_test_split(test_val_df, test_size=0.50, random_state=42, stratify=test_val_df["true_regime"])

    logger.info(f"Splits created: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    # Save to Parquet
    train_df.to_parquet(os.path.join(PROCESSED_DIR, "train_v1.0.0.parquet"), index=False)
    val_df.to_parquet(os.path.join(PROCESSED_DIR, "val_v1.0.0.parquet"), index=False)
    test_df.to_parquet(os.path.join(PROCESSED_DIR, "test_v1.0.0.parquet"), index=False)
    df.to_parquet(os.path.join(PROCESSED_DIR, "master_v1.0.0.parquet"), index=False)

    # 3. Train Regime Classifier
    logger.info("--- [1/6] Training Weather Regime Classifier ---")
    classes = sorted(df["true_regime"].unique())
    class_to_idx = {cls: i for i, cls in enumerate(classes)}
    idx_to_class = {i: cls for i, cls in enumerate(classes)}

    y_train_reg = train_df["true_regime"].map(class_to_idx).values
    y_val_reg = val_df["true_regime"].map(class_to_idx).values
    y_test_reg = test_df["true_regime"].map(class_to_idx).values

    X_train_reg = train_df[REGIME_FEATURE_COLS]
    X_val_reg = val_df[REGIME_FEATURE_COLS]
    X_test_reg = test_df[REGIME_FEATURE_COLS]

    regime_model = xgb.XGBClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        num_class=len(classes),
        random_state=42,
        eval_metric="mlogloss",
    )
    regime_model.fit(X_train_reg, y_train_reg, eval_set=[(X_val_reg, y_val_reg)], verbose=False)

    reg_test_preds = regime_model.predict(X_test_reg)
    reg_acc = accuracy_score(y_test_reg, reg_test_preds)
    reg_f1 = f1_score(y_test_reg, reg_test_preds, average="weighted")
    logger.info(f"Regime Classifier Test Accuracy: {reg_acc*100:.2f}%, F1-Score: {reg_f1:.3f}")

    regime_artifact = {
        "model": regime_model,
        "classes": classes,
        "class_to_idx": class_to_idx,
        "idx_to_class": idx_to_class,
        "feature_cols": REGIME_FEATURE_COLS,
        "model_version": "v1.0.0",
        "accuracy": float(reg_acc),
        "f1_score": float(reg_f1),
    }
    joblib.dump(regime_artifact, os.path.join(REGIMES_MODELS_DIR, "regime_xgb_artifact.joblib"))
    joblib.dump(regime_artifact, os.path.join(REGIMES_ARTIFACTS_DIR, "regime_classifier.joblib"))

    # Save Regime Evaluation Report
    reg_report = {
        "overall_accuracy": float(reg_acc),
        "weighted_f1": float(reg_f1),
        "classes": classes,
        "classification_report": classification_report(y_test_reg, reg_test_preds, target_names=classes, output_dict=True, zero_division=0)
    }
    with open(os.path.join(REGIMES_EVAL_DIR, "regime_evaluation_report.json"), "w") as f:
        json.dump(reg_report, f, indent=2)

    # 4. Train Level 1: Empirical Quantile Mapping
    logger.info("--- [2/6] Training Level 1 Empirical Quantile Mapping ---")
    level1 = Level1QuantileMapping()
    level1.fit(train_df["nwp_rainfall"].values, train_df["observed_rainfall"].values)
    joblib.dump(level1, os.path.join(CORRECTION_ARTIFACTS, "level1_eqm.joblib"))

    # 5. Train Level 2: Standard ML (Model A)
    logger.info("--- [3/6] Training Level 2 Standard ML (Model A) ---")
    level2 = Level2StandardML(n_estimators=300, max_depth=5, learning_rate=0.03)
    level2.fit(train_df, val_df)
    joblib.dump(level2, os.path.join(CORRECTION_ARTIFACTS, "level2_standard_xgb.joblib"))

    # 6. Train Level 3: VARUNA-AI Regime-Aware ML (Model B)
    logger.info("--- [4/6] Training Level 3 Regime-Aware ML (Model B) ---")
    level3 = Level3RegimeAwareML(n_estimators=400, max_depth=6, learning_rate=0.025)
    level3.fit(train_df, val_df)
    joblib.dump(level3, os.path.join(CORRECTION_ARTIFACTS, "level3_regime_aware_xgb.joblib"))

    # 7. Train Heavy Rainfall Probability Estimators
    logger.info("--- [5/6] Training Heavy Rainfall Probability Estimators ---")
    prob_estimator = HeavyRainfallProbabilityEstimator(artifacts_dir=PROB_ARTIFACTS_DIR)
    prob_estimator.train_probability_models(train_df, val_df)

    # 8. Train Conformal Quantile Estimators
    logger.info("--- [6/6] Training Conformal Quantiles & Uncertainty Estimator ---")
    unc_estimator = ConformalQuantileEstimator(artifacts_dir=UNCERTAINTY_ARTIFACTS_DIR)
    unc_estimator.fit_quantiles(train_df, val_df)

    # 9. Evaluate Model Ladder on Held-Out Test Set
    logger.info("--- Evaluating Full Model Ladder on Test Set ---")
    y_test = test_df["observed_rainfall"].values
    pred_l0 = np.maximum(0, test_df["nwp_rainfall"].values)
    pred_l1 = level1.predict(test_df["nwp_rainfall"].values)
    pred_l2 = level2.predict(test_df)
    pred_l3 = level3.predict(test_df)

    def calc_metrics(y_true, y_pred, name):
        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        bias = float(np.mean(y_pred - y_true))
        r, _ = pearsonr(y_true, y_pred) if np.std(y_pred) > 1e-5 and np.std(y_true) > 1e-5 else (0.0, 0.0)
        return {
            "Model": name,
            "MAE": round(mae, 2),
            "RMSE": round(rmse, 2),
            "Mean_Bias": round(bias, 2),
            "Correlation": round(float(r), 3)
        }

    m0 = calc_metrics(y_test, pred_l0, "Level 0 (Raw NWP)")
    m1 = calc_metrics(y_test, pred_l1, "Level 1 (EQM)")
    m2 = calc_metrics(y_test, pred_l2, "Level 2 (Standard ML)")
    m3 = calc_metrics(y_test, pred_l3, "Level 3 (VARUNA-AI Regime-Aware)")

    results_df = pd.DataFrame([m0, m1, m2, m3])
    logger.info(f"\nModel Ladder Verification Results on Named Dataset:\n{results_df.to_string(index=False)}")

    results_df.to_csv(os.path.join(VERIFICATION_DIR, "results.csv"), index=False)

    # Compute Contingency Metrics (CSI, ETS, POD, FAR) at 15.6mm and 64.5mm thresholds
    def calc_contingency(y_true, y_pred, thresh=64.5):
        hits = np.sum((y_true >= thresh) & (y_pred >= thresh))
        false_alarms = np.sum((y_true < thresh) & (y_pred >= thresh))
        misses = np.sum((y_true >= thresh) & (y_pred < thresh))
        correct_neg = np.sum((y_true < thresh) & (y_pred < thresh))
        total = hits + false_alarms + misses + correct_neg

        csi = hits / (hits + false_alarms + misses) if (hits + false_alarms + misses) > 0 else 1.0
        pod = hits / (hits + misses) if (hits + misses) > 0 else 1.0
        far = false_alarms / (hits + false_alarms) if (hits + false_alarms) > 0 else 0.0

        expected_hits = ((hits + misses) * (hits + false_alarms)) / total if total > 0 else 0
        ets = (hits - expected_hits) / (hits + false_alarms + misses - expected_hits) if (hits + false_alarms + misses - expected_hits) != 0 else 0.5
        return {
            "CSI": round(float(csi), 3),
            "POD": round(float(pod), 3),
            "FAR": round(float(far), 3),
            "ETS": round(float(ets), 3)
        }

    cat_metrics = []
    for thresh in [2.5, 15.6, 64.5, 115.6]:
        cat_metrics.append({"Threshold_mm": thresh, "Model": "Raw_NWP", **calc_contingency(y_test, pred_l0, thresh)})
        cat_metrics.append({"Threshold_mm": thresh, "Model": "Level1_EQM", **calc_contingency(y_test, pred_l1, thresh)})
        cat_metrics.append({"Threshold_mm": thresh, "Model": "Level2_Std_ML", **calc_contingency(y_test, pred_l2, thresh)})
        cat_metrics.append({"Threshold_mm": thresh, "Model": "VARUNA_AI_Level3", **calc_contingency(y_test, pred_l3, thresh)})

    matrix = {
        "continuous_metrics": {
            "Raw_NWP": m0,
            "Level1_Quantile_Mapping": m1,
            "Level2_Standard_ML": m2,
            "VARUNA_AI_Level3_Regime_Aware": m3,
        },
        "categorical_metrics": cat_metrics,
        "dataset_summary": {
            "source_csv": CSV_PATH,
            "total_districts": len(df),
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "test_samples": len(test_df),
        }
    }
    with open(os.path.join(VERIFICATION_DIR, "verification_matrix.json"), "w") as f:
        json.dump(matrix, f, indent=2)

    logger.info("All models trained and persisted successfully!")
    return matrix

if __name__ == "__main__":
    train_all()
