import numpy as np
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = (
    BASE_DIR
    / "weather_data"
    / "processed"
    / "real_ml"
    / "master_real_weather_2021_2025.parquet"
)
ARTIFACT_DIR = BASE_DIR / "weather_data" / "processed" / "real_ml" / "model3"
FEATURES = [
    "latitude",
    "longitude",
    "month",
    "day_of_year",
    "day_of_year_sin",
    "day_of_year_cos",

    "era5_rainfall",
    "era5_rainfall_log1p",
    "era5_is_rain",
    "era5_is_heavy",

    "era5_rainfall_lag1",
    "era5_rainfall_lag3",
    "era5_rainfall_lag7",
    "era5_rainfall_3day_sum",
    "era5_rainfall_7day_sum",
    "era5_rainfall_7day_mean",

    "temperature_c",
    "dewpoint_c",
    "relative_humidity",
    "u10",
    "v10",
    "wind_speed"
]

TARGET = "rainfall_error"
MAX_TRAIN_ROWS = 750_000
RANDOM_STATE = 42


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as data_file:
        for chunk in iter(lambda: data_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _metrics(actual, predicted):
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def train_model():
    if not DATA_FILE.is_file():
        raise FileNotFoundError(
            f"Required real processed dataset is missing: {DATA_FILE}"
        )

    try:
        df = pd.read_parquet(DATA_FILE)
    except Exception as exc:
        raise RuntimeError(
            f"Could not read real processed dataset {DATA_FILE}: {exc}"
        ) from exc

    required = ["time", *FEATURES, TARGET]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(
            f"Real dataset is missing required columns: {missing}"
        )
    if df.empty:
        raise ValueError("Real processed dataset contains no rows.")

    for column in FEATURES + [TARGET]:
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise TypeError(
                f"Required model column '{column}' must be numeric; "
                f"found {df[column].dtype}."
            )

    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    if df["time"].isna().any():
        raise ValueError("Real dataset contains missing or invalid timestamps.")

    model_values = df[FEATURES + [TARGET]].to_numpy(dtype=np.float64)
    if not np.isfinite(model_values).all():
        raise ValueError(
            "Real dataset contains missing or non-finite model values."
        )

    df = df.sort_values("time", kind="mergesort")
    train = df[df["time"] < "2024-01-01"]
    validation = df[
        (df["time"] >= "2024-01-01") & (df["time"] < "2025-01-01")
    ]
    test = df[df["time"] >= "2025-01-01"]
    if train.empty or validation.empty or test.empty:
        raise ValueError(
            "Chronological training requires non-empty train (<2024), "
            "validation (2024), and test (>=2025) periods; got "
            f"{len(train)}, {len(validation)}, and {len(test)} rows."
        )

    if len(train) > MAX_TRAIN_ROWS:
        train = train.sample(n=MAX_TRAIN_ROWS, random_state=RANDOM_STATE)
        train = train.sort_values("time", kind="mergesort")

    X_train, y_train = train[FEATURES], train[TARGET]
    X_validation, y_validation = validation[FEATURES], validation[TARGET]
    X_test, y_test = test[FEATURES], test[TARGET]

    model = HistGradientBoostingRegressor(
        max_iter=200,
        learning_rate=0.08,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=RANDOM_STATE,
    )
    model.fit(X_train, y_train)

    validation_metrics = _metrics(
        y_validation, model.predict(X_validation)
    )
    test_metrics = _metrics(y_test, model.predict(X_test))
    dataset_hash = _sha256(DATA_FILE)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACT_DIR / "model3_hist_gradient_boosting.joblib"
    metadata_path = ARTIFACT_DIR / "training_metadata.json"
    metrics_path = ARTIFACT_DIR / "evaluation_metrics.json"
    joblib.dump(model, model_path)

    metadata = {
        "model": "HistGradientBoostingRegressor",
        "dataset": DATA_FILE.name,
        "dataset_sha256": dataset_hash,
        "features": FEATURES,
        "target": TARGET,
        "train_period": [
            train["time"].min().isoformat(),
            train["time"].max().isoformat(),
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
            "train_used": len(train),
            "validation": len(validation),
            "test": len(test),
        },
        "random_state": RANDOM_STATE,
        "max_train_rows": MAX_TRAIN_ROWS,
        "model_parameters": model.get_params(),
        "runtime_versions": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    metrics = {
        "validation": validation_metrics,
        "test": test_metrics,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8"
    )
    metrics_path.write_text(
        json.dumps(metrics, indent=2, allow_nan=False), encoding="utf-8"
    )

    print(f"Training dataset: {DATA_FILE}")
    print(f"Dataset SHA-256: {dataset_hash}")
    print(f"Rows (train/validation/test): {len(train)}/{len(validation)}/{len(test)}")
    print(f"Features: {len(FEATURES)}")
    print(f"Validation metrics: {json.dumps(validation_metrics, sort_keys=True)}")
    print(f"Test metrics: {json.dumps(test_metrics, sort_keys=True)}")
    print(f"Model artifact: {model_path}")
    print(f"Training metadata: {metadata_path}")
    print(f"Evaluation metrics: {metrics_path}")


if __name__ == "__main__":
    train_model()