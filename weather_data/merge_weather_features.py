import xarray as xr
import pandas as pd
from pathlib import Path

WEATHER_FILE = Path(
    "weather_data/processed/era5/ERA5_weather_daily_2021_2025.nc"
)

MASTER_FILE = Path(
    "weather_data/processed/real_ml/master_real_features_2021_2025.parquet"
)

OUTPUT_FILE = Path(
    "weather_data/processed/real_ml/master_real_weather_2021_2025.parquet"
)

print("=" * 60)
print("VARUNA-AI WEATHER + RAINFALL MERGE")
print("=" * 60)

print("\nLoading weather dataset...")

weather = xr.open_dataset(WEATHER_FILE)

print("Weather dimensions:", dict(weather.sizes))
print("Weather variables:", list(weather.data_vars))

print("\nConverting weather data to DataFrame...")

weather_df = weather.to_dataframe().reset_index()

weather_df = weather_df.rename(
    columns={"time": "time"}
)

weather_df["time"] = pd.to_datetime(
    weather_df["time"]
).dt.normalize()

print("Weather rows:", len(weather_df))

print("\nLoading existing ML dataset...")

master = pd.read_parquet(MASTER_FILE)

master["time"] = pd.to_datetime(
    master["time"]
).dt.normalize()

print("Master rows:", len(master))

print("\nMatching coordinates...")

weather_df["latitude"] = weather_df["latitude"].round(2)
weather_df["longitude"] = weather_df["longitude"].round(2)

master["latitude"] = master["latitude"].round(2)
master["longitude"] = master["longitude"].round(2)

weather_columns = [
    "time",
    "latitude",
    "longitude",
    "temperature_c",
    "dewpoint_c",
    "relative_humidity",
    "u10",
    "v10",
    "wind_speed"
]

weather_df = weather_df[weather_columns]

print("\nMerging...")

merged = master.merge(
    weather_df,
    on=["time", "latitude", "longitude"],
    how="left",
    validate="many_to_one"
)

print("\nMerge complete.")

weather_features = [
    "temperature_c",
    "dewpoint_c",
    "relative_humidity",
    "u10",
    "v10",
    "wind_speed"
]

print("\nChecking missing weather values...")

for col in weather_features:
    missing = merged[col].isna().sum()
    print(f"{col}: {missing} missing")

print("\nRows before:", len(master))
print("Rows after :", len(merged))

print("\nSaving combined dataset...")

merged.to_parquet(
    OUTPUT_FILE,
    index=False
)

print("\nSaved:")
print(OUTPUT_FILE)

print("\nNew columns:")

for col in weather_features:
    print("-", col)

print("\n" + "=" * 60)
print("WEATHER + RAINFALL MERGE COMPLETE")
print("=" * 60)