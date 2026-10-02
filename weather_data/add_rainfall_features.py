from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT = (
    BASE_DIR
    / "weather_data"
    / "processed"
    / "real_ml"
    / "master_real_2021_2025.parquet"
)

OUTPUT = (
    BASE_DIR
    / "weather_data"
    / "processed"
    / "real_ml"
    / "master_real_features_2021_2025.parquet"
)

print("Loading dataset...")
df = pd.read_parquet(INPUT)

df = df.sort_values(
    ["latitude", "longitude", "time"]
).reset_index(drop=True)

print("Creating temporal rainfall features...")

group = df.groupby(
    ["latitude", "longitude"],
    group_keys=False
)

# Previous-day ERA5 rainfall
df["era5_rainfall_lag1"] = group["era5_rainfall"].shift(1)

# Previous 3-day rainfall
df["era5_rainfall_lag3"] = group["era5_rainfall"].shift(3)

# Previous 7-day rainfall
df["era5_rainfall_lag7"] = group["era5_rainfall"].shift(7)

# Rolling rainfall history
df["era5_rainfall_3day_sum"] = (
    group["era5_rainfall"]
    .transform(lambda x: x.shift(1).rolling(3).sum())
)

df["era5_rainfall_7day_sum"] = (
    group["era5_rainfall"]
    .transform(lambda x: x.shift(1).rolling(7).sum())
)

# Rolling mean
df["era5_rainfall_7day_mean"] = (
    group["era5_rainfall"]
    .transform(lambda x: x.shift(1).rolling(7).mean())
)

# Keep chronological order
df = df.sort_values(
    ["time", "latitude", "longitude"]
).reset_index(drop=True)

print("Removing rows without sufficient history...")

df = df.dropna(
    subset=[
        "era5_rainfall_lag1",
        "era5_rainfall_lag3",
        "era5_rainfall_lag7",
        "era5_rainfall_3day_sum",
        "era5_rainfall_7day_sum",
        "era5_rainfall_7day_mean",
    ]
)

print("Final rows:", len(df))

df.to_parquet(
    OUTPUT,
    index=False
)

print()
print("FEATURE DATASET CREATED")
print(OUTPUT)

print()
print("NEW FEATURES:")
for c in [
    "era5_rainfall_lag1",
    "era5_rainfall_lag3",
    "era5_rainfall_lag7",
    "era5_rainfall_3day_sum",
    "era5_rainfall_7day_sum",
    "era5_rainfall_7day_mean",
]:
    print("-", c)