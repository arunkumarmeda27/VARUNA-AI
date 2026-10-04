import pandas as pd
from pathlib import Path

FILE = Path(
    r".\weather_data\processed\real_ml\master_real_weather_2021_2025.parquet"
)

OUTPUT = Path(
    r".\weather_data\processed\real_ml\VARUNA_AI_ML_DATASET_METADATA.txt"
)

print("=" * 60)
print("VARUNA-AI FINAL ML DATASET METADATA")
print("=" * 60)

df = pd.read_parquet(FILE)

print("\nDataset loaded.")
print("Rows:", len(df))
print("Columns:", len(df.columns))

lines = []

lines.append("VARUNA-AI FINAL ML DATASET")
lines.append("=" * 60)
lines.append("")
lines.append(f"Rows: {len(df)}")
lines.append(f"Columns: {len(df.columns)}")
lines.append(f"Date start: {df['time'].min()}")
lines.append(f"Date end: {df['time'].max()}")
lines.append("")

lines.append("COLUMNS")
lines.append("-" * 60)

for col in df.columns:
    lines.append(
        f"{col} | dtype={df[col].dtype} | missing={df[col].isna().sum()}"
    )

lines.append("")
lines.append("WEATHER FEATURES")
lines.append("-" * 60)

weather_features = [
    "temperature_c",
    "dewpoint_c",
    "relative_humidity",
    "u10",
    "v10",
    "wind_speed"
]

for col in weather_features:
    lines.append(
        f"{col}: min={df[col].min():.4f}, "
        f"mean={df[col].mean():.4f}, "
        f"max={df[col].max():.4f}"
    )

lines.append("")
lines.append("RAINFALL FEATURES")
lines.append("-" * 60)

rainfall_features = [
    "era5_rainfall",
    "era5_rainfall_log1p",
    "era5_is_rain",
    "era5_is_heavy",
    "era5_rainfall_lag1",
    "era5_rainfall_lag3",
    "era5_rainfall_lag7",
    "era5_rainfall_3day_sum",
    "era5_rainfall_7day_sum",
    "era5_rainfall_7day_mean"
]

for col in rainfall_features:
    if col in df.columns:
        lines.append(col)

lines.append("")
lines.append("TARGET")
lines.append("-" * 60)
lines.append("rainfall_error")
lines.append(
    "Formula: observed rainfall - ERA5/NWP rainfall forecast"
)

lines.append("")
lines.append("QUALITY CHECKS")
lines.append("-" * 60)

weather_missing = df[weather_features].isna().sum().sum()

duplicates = df.duplicated(
    subset=["time", "latitude", "longitude"]
).sum()

lines.append(f"Weather missing values: {weather_missing}")
lines.append(f"Duplicate time/location rows: {duplicates}")

lines.append("")
lines.append("FINAL STATUS")
lines.append("-" * 60)
lines.append("ML-ready dataset generated successfully.")

OUTPUT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print("\nMetadata saved:")
print(OUTPUT)

print("\n" + "=" * 60)
print("METADATA GENERATION COMPLETE")
print("=" * 60)