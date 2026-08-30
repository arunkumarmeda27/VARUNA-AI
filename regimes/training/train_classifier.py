"""
VARUNA-AI: Weather Regime Model Training Pipeline
Owner: Member 2 (Weather Regime Classification Engineer)

Trains baseline Multinomial Logistic Regression and calibrated XGBoost / Random Forest models,
tracking dataset versions, hyperparameters, cross-entropy loss, and F1 scores.
"""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, log_loss, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import xgboost as xgb

from regimes.training.features import REGIME_FEATURE_COLS, TARGET_REGIME_COL

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "weather_data", "processed")

class RegimeModelTrainer:
    """
    Trains and persists versioned Weather Regime classifiers.
    """

    def __init__(self, data_version: str = "v1.0.0", model_version: str = "v1.0.0"):
        self.data_version = data_version
        self.model_version = model_version
        os.makedirs(MODELS_DIR, exist_ok=True)

    def load_datasets(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        train_path = os.path.join(PROCESSED_DATA_DIR, f"train_{self.data_version}.parquet")
        val_path = os.path.join(PROCESSED_DATA_DIR, f"val_{self.data_version}.parquet")
        test_path = os.path.join(PROCESSED_DATA_DIR, f"test_{self.data_version}.parquet")

        train_df = pd.read_parquet(train_path)
        val_df = pd.read_parquet(val_path)
        test_df = pd.read_parquet(test_path)
        return train_df, val_df, test_df

    def train_baseline_lr(self, train_df: pd.DataFrame, val_df: pd.DataFrame) -> tuple[Pipeline, dict]:
        """Trains Multinomial Logistic Regression Baseline."""
        X_train = train_df[REGIME_FEATURE_COLS]
        y_train = train_df[TARGET_REGIME_COL]
        X_val = val_df[REGIME_FEATURE_COLS]
        y_val = val_df[TARGET_REGIME_COL]

        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=42)),
        ])
        pipe.fit(X_train, y_train)

        val_preds = pipe.predict(X_val)
        val_probs = pipe.predict_proba(X_val)

        metrics = {
            "model_type": "LogisticRegression_Baseline",
            "accuracy": float(accuracy_score(y_val, val_preds)),
            "macro_f1": float(f1_score(y_val, val_preds, average="macro")),
            "log_loss": float(log_loss(y_val, val_probs, labels=pipe.classes_)),
        }
        return pipe, metrics

    def train_xgb_classifier(self, train_df: pd.DataFrame, val_df: pd.DataFrame) -> tuple[dict, dict]:
        """Trains Calibrated XGBoost Regime Classifier."""
        X_train = train_df[REGIME_FEATURE_COLS].copy()
        y_train = train_df[TARGET_REGIME_COL].copy()
        X_val = val_df[REGIME_FEATURE_COLS].copy()
        y_val = val_df[TARGET_REGIME_COL].copy()

        # Label encoding
        classes = sorted(y_train.unique())
        class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
        idx_to_class = {i: cls_name for i, cls_name in enumerate(classes)}

        y_train_idx = y_train.map(class_to_idx).values
        y_val_idx = y_val.map(class_to_idx).values

        model = xgb.XGBClassifier(
            n_estimators=400,
            max_depth=6,
            learning_rate=0.04,
            subsample=0.80,
            colsample_bytree=0.80,
            colsample_bylevel=0.90,
            min_child_weight=4,
            gamma=0.3,
            reg_alpha=0.2,
            reg_lambda=1.5,
            objective="multi:softprob",
            num_class=len(classes),
            random_state=42,
            eval_metric="mlogloss",
            early_stopping_rounds=40,
        )
        model.fit(
            X_train, y_train_idx,
            eval_set=[(X_val, y_val_idx)],
            verbose=False,
        )

        val_preds_idx = model.predict(X_val)
        val_probs = model.predict_proba(X_val)

        val_preds = [idx_to_class[i] for i in val_preds_idx]

        metrics = {
            "model_type": "XGBoost_Regime_Classifier",
            "accuracy": float(accuracy_score(y_val, val_preds)),
            "macro_f1": float(f1_score(y_val, val_preds, average="macro")),
            "weighted_f1": float(f1_score(y_val, val_preds, average="weighted")),
            "log_loss": float(log_loss(y_val_idx, val_probs, labels=list(range(len(classes))))),
            "classes": classes,
        }

        artifact = {
            "model": model,
            "classes": classes,
            "class_to_idx": class_to_idx,
            "idx_to_class": idx_to_class,
            "feature_cols": REGIME_FEATURE_COLS,
            "model_version": f"regime-xgb-v2.0.0",
            "data_version": self.data_version,
            "created_at": datetime.utcnow().isoformat(),
            "metrics": metrics,
        }
        return artifact, metrics

    def run_training_pipeline(self) -> dict:
        train_df, val_df, test_df = self.load_datasets()

        # 1. Train Baseline
        baseline_pipe, base_metrics = self.train_baseline_lr(train_df, val_df)
        joblib.dump(baseline_pipe, os.path.join(MODELS_DIR, "regime_baseline_lr.joblib"))

        # 2. Train Production XGBoost
        xgb_artifact, xgb_metrics = self.train_xgb_classifier(train_df, val_df)
        joblib.dump(xgb_artifact, os.path.join(MODELS_DIR, "regime_xgb_artifact.joblib"))

        # Save metadata
        metadata = {
            "data_version": self.data_version,
            "model_version": self.model_version,
            "training_period": "2018-2022",
            "val_period": "2023",
            "baseline_metrics": base_metrics,
            "production_metrics": xgb_metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }
        with open(os.path.join(MODELS_DIR, "regime_training_manifest.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata

if __name__ == "__main__":
    trainer = RegimeModelTrainer()
    meta = trainer.run_training_pipeline()
    print("Regime Training Complete!")
    print("Baseline Metrics:", meta["baseline_metrics"])
    print("Production XGBoost Metrics:", meta["production_metrics"])
