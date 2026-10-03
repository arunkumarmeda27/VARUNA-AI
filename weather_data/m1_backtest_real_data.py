import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from verification.metrics import (
    calculate_continuous_metrics,
    calculate_categorical_scores,
)

DATASET = (
    PROJECT_ROOT
    / "weather_data"
    / "processed"
    / "real_ml"
    / "master_real_weather_2021_2025.parquet"
)

OUTPUT = (
    PROJECT_ROOT
    / "weather_data"
    / "processed"
    / "real_ml"
    / "M1_REAL_DATA_BACKTEST_RESULTS.txt"
)

print("=" * 60)
print("VARUNA-AI M1 REAL-DATA BACKTEST")
print("TASK 1.2 - HONEST VERIFICATION")
print("=" * 60)

print("\nLoading dataset...")
df = pd.read_parquet(DATASET)

required = [
    "time",
    "imd_rainfall",
    "era5_rainfall",
]

missing = [c for c in required if c not in df.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")

df = df.dropna(
    subset=[
        "imd_rainfall",
        "era5_rainfall",
    ]
).copy()

df["time"] = pd.to_datetime(df["time"])

print("Rows:", len(df))
print("Start:", df["time"].min())
print("End:", df["time"].max())

print("\nCalculating continuous metrics...")

obs = df["imd_rainfall"].to_numpy(dtype=float)
pred = df["era5_rainfall"].to_numpy(dtype=float)

continuous = calculate_continuous_metrics(
    obs,
    pred
)

print("\nCONTINUOUS METRICS")
print("-" * 60)

for key, value in continuous.items():
    print(f"{key}: {value}")

print("\nCalculating categorical metrics...")

thresholds = [1.0, 2.5, 10.0]

categorical_results = []

for threshold in thresholds:

    result = calculate_categorical_scores(
        obs,
        pred,
        threshold
    )

    categorical_results.append(result)

    print("\nThreshold:", threshold, "mm")

    print("POD:", result["POD"])
    print("CSI:", result["CSI"])
    print("FAR:", result["FAR"])
    print("Frequency Bias:", result["Frequency_Bias"])

print("\nYear-wise evaluation...")

year_results = []

for year in sorted(df["time"].dt.year.unique()):

    year_df = df[
        df["time"].dt.year == year
    ]

    year_obs = year_df[
        "imd_rainfall"
    ].to_numpy(dtype=float)

    year_pred = year_df[
        "era5_rainfall"
    ].to_numpy(dtype=float)

    metrics = calculate_continuous_metrics(
        year_obs,
        year_pred
    )

    year_results.append(
        {
            "year": int(year),
            **metrics,
        }
    )

print("\nYEAR-WISE RESULTS")
print("-" * 60)

for result in year_results:

    print(
        f"{result['year']} | "
        f"MAE={result['MAE']} | "
        f"RMSE={result['RMSE']} | "
        f"Bias={result['Mean_Bias']} | "
        f"Correlation={result['Correlation']}"
    )

print("\nSaving results...")

lines = []

lines.append("VARUNA-AI M1 REAL-DATA BACKTEST")
lines.append("=" * 60)
lines.append("")
lines.append("Dataset:")
lines.append(str(DATASET))
lines.append("")
lines.append(f"Rows evaluated: {len(df)}")
lines.append(f"Start: {df['time'].min()}")
lines.append(f"End: {df['time'].max()}")
lines.append("")

lines.append("CONTINUOUS METRICS")
lines.append("-" * 60)

for key, value in continuous.items():
    lines.append(f"{key}: {value}")

lines.append("")
lines.append("CATEGORICAL METRICS")
lines.append("-" * 60)

for result in categorical_results:

    lines.append(
        f"Threshold {result['Threshold_mm']} mm"
    )

    lines.append(
        f"POD: {result['POD']}"
    )

    lines.append(
        f"CSI: {result['CSI']}"
    )

    lines.append(
        f"FAR: {result['FAR']}"
    )

    lines.append(
        f"Frequency Bias: {result['Frequency_Bias']}"
    )

    lines.append("")

lines.append("YEAR-WISE RESULTS")
lines.append("-" * 60)

for result in year_results:

    lines.append(
        f"{result['year']} | "
        f"MAE={result['MAE']} | "
        f"RMSE={result['RMSE']} | "
        f"Bias={result['Mean_Bias']} | "
        f"Correlation={result['Correlation']}"
    )

OUTPUT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print("\n" + "=" * 60)
print("M1 BACKTEST COMPLETE")
print("=" * 60)

print("\nResults saved:")
print(OUTPUT)