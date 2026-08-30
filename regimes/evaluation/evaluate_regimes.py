"""
VARUNA-AI: Weather Regime Evaluation Module
Owner: Member 2 (Weather Regime Classification Engineer)

Evaluates regime classifiers against held-out Test dataset (2024),
producing confusion matrices, F1 scores, Brier skill scores, and classification reports.
"""

import os
import json
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, log_loss

from regimes.inference.regime_classifier import RegimeClassifier

PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "weather_data", "processed")
EVAL_OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evaluation")

class RegimeEvaluator:
    """
    Evaluates Weather Regime Classification on independent test set.
    """

    def __init__(self, data_version: str = "v1.0.0"):
        self.data_version = data_version
        self.classifier = RegimeClassifier()
        os.makedirs(EVAL_OUT_DIR, exist_ok=True)

    def evaluate_test_set(self) -> dict:
        test_path = os.path.join(PROCESSED_DATA_DIR, f"test_{self.data_version}.parquet")
        test_df = pd.read_parquet(test_path)

        preds_df = self.classifier.predict_dataframe(test_df)
        y_true = preds_df["true_regime"]
        y_pred = preds_df["predicted_regime"]

        classes = self.classifier.classes
        cm = confusion_matrix(y_true, y_pred, labels=classes)
        clf_rep = classification_report(y_true, y_pred, labels=classes, output_dict=True, zero_division=0)

        prob_cols = [f"prob_{cls_name.lower()}" for cls_name in classes]
        y_probs = preds_df[prob_cols].values

        # Convert y_true to one-hot for Brier Multi-Class score
        y_cat = pd.Categorical(y_true, categories=classes)
        y_true_onehot = pd.get_dummies(y_cat).values
        brier_score = float(np.mean(np.sum((y_probs - y_true_onehot)**2, axis=1)))

        results = {
            "test_period": "2024-06-01 to 2024-09-30",
            "test_samples": len(test_df),
            "overall_accuracy": float(accuracy_score(y_true, y_pred)),
            "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
            "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
            "brier_score": brier_score,
            "classes": classes,
            "confusion_matrix": cm.tolist(),
            "per_class_metrics": {
                cls: {
                    "precision": float(clf_rep[cls]["precision"]),
                    "recall": float(clf_rep[cls]["recall"]),
                    "f1-score": float(clf_rep[cls]["f1-score"]),
                    "support": int(clf_rep[cls]["support"]),
                }
                for cls in classes if cls in clf_rep
            },
        }

        # Save machine-readable evaluation report
        out_path = os.path.join(EVAL_OUT_DIR, "regime_evaluation_report.json")
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

        return results

if __name__ == "__main__":
    from regimes.training.train_classifier import RegimeModelTrainer
    trainer = RegimeModelTrainer()
    trainer.run_training_pipeline()

    evaluator = RegimeEvaluator()
    results = evaluator.evaluate_test_set()
    print("Test Set Regime Evaluation:")
    print(f"Accuracy: {results['overall_accuracy']:.4f}")
    print(f"Macro F1: {results['macro_f1']:.4f}")
    print(f"Brier Score: {results['brier_score']:.4f}")
