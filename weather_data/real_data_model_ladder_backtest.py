import hashlib
import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from correction.baselines.level1_quantile_mapping import Level1QuantileMapping
from verification.metrics import calculate_continuous_metrics


DATA_FILE = (
    BASE_DIR
    / "weather_data"
    / "processed"
    / "real_ml"
    / "master_real_weather_2021_2025.parquet"
)
OUTPUT_DIR = BASE_DIR / "weather_data" / "processed" / "real_ml"
ARTIFACT_PATH = OUTPUT_DIR / "real_data_level1_eqm.joblib"
METRICS_PATH = OUTPUT_DIR / "M1_REAL_MODEL_LADDER_BACKTEST_2025.json"
REPORT_PATH = OUTPUT_DIR / "M1_REAL_MODEL_LADDER_BACKTEST_2025.md"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as data_file:
        for chunk in iter(lambda: data_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _period_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    return calculate_continuous_metrics(actual, predicted)


def evaluate_real_model_ladder() -> dict:
    if not DATA_FILE.is_file():
        raise FileNotFoundError(
            f"Required real processed dataset is missing: {DATA_FILE}"
        )

    df = pd.read_parquet(DATA_FILE)
    required = ["time", "imd_rainfall", "era5_rainfall"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(
            f"Real held-out evaluation is missing required columns: {missing}"
        )

    for column in ("imd_rainfall", "era5_rainfall"):
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise TypeError(
                f"Real evaluation column '{column}' must be numeric; "
                f"found {df[column].dtype}."
            )

    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    if df["time"].isna().any():
        raise ValueError("Real evaluation data contains invalid timestamps.")
    values = df[["imd_rainfall", "era5_rainfall"]].to_numpy(dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("Real evaluation data contains missing or non-finite values.")

    df = df.sort_values("time", kind="mergesort")
    training = df[df["time"] < "2024-01-01"]
    validation = df[
        (df["time"] >= "2024-01-01") & (df["time"] < "2025-01-01")
    ]
    test = df[df["time"] >= "2025-01-01"]
    if training.empty or validation.empty or test.empty:
        raise ValueError(
            "Real chronological evaluation requires non-empty training "
            "(<2024), validation (2024), and test (>=2025) periods."
        )

    level1 = Level1QuantileMapping().fit(
        training["era5_rainfall"].to_numpy(dtype=np.float64),
        training["imd_rainfall"].to_numpy(dtype=np.float64),
    )

    validation_observed = validation["imd_rainfall"].to_numpy(dtype=np.float64)
    validation_raw = validation["era5_rainfall"].to_numpy(dtype=np.float64)
    test_observed = test["imd_rainfall"].to_numpy(dtype=np.float64)
    test_raw = test["era5_rainfall"].to_numpy(dtype=np.float64)

    results = {
        "dataset": DATA_FILE.name,
        "dataset_sha256": _sha256(DATA_FILE),
        "target": "imd_rainfall",
        "raw_forecast": "era5_rainfall",
        "split": {
            "training_period": [
                training["time"].min().isoformat(),
                training["time"].max().isoformat(),
            ],
            "validation_period": [
                validation["time"].min().isoformat(),
                validation["time"].max().isoformat(),
            ],
            "test_period": [
                test["time"].min().isoformat(),
                test["time"].max().isoformat(),
            ],
            "rows": {
                "training": len(training),
                "validation": len(validation),
                "test": len(test),
            },
        },
        "levels": {
            "level0_raw_era5": {
                "status": "evaluated",
                "validation": _period_metrics(validation_observed, validation_raw),
                "test": _period_metrics(test_observed, test_raw),
            },
            "level1_empirical_quantile_mapping": {
                "status": "evaluated",
                "training_source": "real IMD rainfall paired with real ERA5 rainfall",
                "validation": _period_metrics(
                    validation_observed,
                    level1.predict(validation_raw),
                ),
                "test": _period_metrics(
                    test_observed,
                    level1.predict(test_raw),
                ),
                "artifact": ARTIFACT_PATH.name,
            },
            "level2_standard_ml": {
                "status": "unavailable",
                "reason": (
                    "The real processed dataset lacks the required NWP and "
                    "pressure-level/synoptic feature set; existing Level 2 "
                    "artifact training provenance is not tied to this real dataset."
                ),
            },
            "level3_regime_aware_ml": {
                "status": "unavailable",
                "reason": (
                    "The real processed dataset lacks the required pressure-level "
                    "features and observed regime labels/probabilities; existing "
                    "Level 3 artifact training provenance is not tied to this "
                    "real dataset."
                ),
            },
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(level1, ARTIFACT_PATH)
    METRICS_PATH.write_text(
        json.dumps(results, indent=2, allow_nan=False),
        encoding="utf-8",
    )

    lines = [
        "# M1 Real-Data Model Ladder Backtest",
        "",
        "This report evaluates only levels supported by real data and real training.",
        "",
        f"- Dataset: `{DATA_FILE.name}`",
        f"- Dataset SHA-256: `{results['dataset_sha256']}`",
        f"- Train rows: {len(training)}",
        f"- Validation rows: {len(validation)}",
        f"- Test rows: {len(test)}",
        f"- Test period: {results['split']['test_period'][0]} to {results['split']['test_period'][1]}",
        "",
        "| Level | Status | Validation MAE | Validation RMSE | Test MAE | Test RMSE |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for key, label in (
        ("level0_raw_era5", "Level 0 raw ERA5"),
        ("level1_empirical_quantile_mapping", "Level 1 empirical quantile mapping"),
    ):
        level = results["levels"][key]
        lines.append(
            f"| {label} | {level['status']} | "
            f"{level['validation']['MAE']} | {level['validation']['RMSE']} | "
            f"{level['test']['MAE']} | {level['test']['RMSE']} |"
        )
    for key, label in (
        ("level2_standard_ml", "Level 2 standard ML"),
        ("level3_regime_aware_ml", "Level 3 regime-aware ML"),
    ):
        level = results["levels"][key]
        lines.append(f"| {label} | unavailable | n/a | n/a | n/a | n/a |")
        lines.extend(["", f"{label} unavailable: {level['reason']}"])
    lines.extend(
        [
            "",
            "Level 1 was fitted on the real training period only. Validation and test metrics are calculated from held-out real IMD/ERA5 rows. No sample or synthetic rows are used.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Real dataset: {DATA_FILE}")
    print(f"Dataset SHA-256: {results['dataset_sha256']}")
    print(f"Level 0 validation: {results['levels']['level0_raw_era5']['validation']}")
    print(f"Level 0 test: {results['levels']['level0_raw_era5']['test']}")
    print(
        "Level 1 validation: "
        f"{results['levels']['level1_empirical_quantile_mapping']['validation']}"
    )
    print(f"Level 1 test: {results['levels']['level1_empirical_quantile_mapping']['test']}")
    print("Levels 2 and 3: unavailable from current real data/artifact provenance.")
    print(f"Level 1 artifact: {ARTIFACT_PATH}")
    print(f"Metrics: {METRICS_PATH}")
    print(f"Report: {REPORT_PATH}")
    return results


if __name__ == "__main__":
    evaluate_real_model_ladder()