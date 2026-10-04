import xarray as xr
import pandas as pd

INPUT = r"weather_data\raw\era5\era5_2021.grib"
OUTPUT = r"weather_data\processed\nwp_test_2021_jan01.parquet"

ds = xr.open_dataset(INPUT, engine="cfgrib")

# Keep only forecasts whose valid time is 2021-01-01
valid_time = ds.valid_time

mask = (
    (valid_time >= pd.Timestamp("2021-01-01 00:00:00")) &
    (valid_time <  pd.Timestamp("2021-01-02 00:00:00"))
)

selected = ds.tp.where(mask)

# Convert metres to millimetres
rainfall_mm = selected * 1000.0

df = rainfall_mm.to_dataframe(name="nwp_rainfall").reset_index()

# Remove missing values
df = df.dropna(subset=["nwp_rainfall"])

# Rename forecast initialization time
df = df.rename(columns={"time": "forecast_init_time"})

# Keep required columns
df = df[
    [
        "forecast_init_time",
        "step",
        "valid_time",
        "latitude",
        "longitude",
        "nwp_rainfall",
    ]
]

df.to_parquet(OUTPUT, index=False)

print("NWP TEST FILE CREATED")
print("Output:", OUTPUT)
print("Rows:", len(df))
print("Columns:", list(df.columns))
print("Valid time:", df.valid_time.min(), "to", df.valid_time.max())
print("Latitude:", df.latitude.min(), "to", df.latitude.max())
print("Longitude:", df.longitude.min(), "to", df.longitude.max())
print("Rainfall mm:", df.nwp_rainfall.min(), "to", df.nwp_rainfall.max())