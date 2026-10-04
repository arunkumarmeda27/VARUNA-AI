import xarray as xr
import numpy as np
from pathlib import Path

INPUT_DIR = Path("weather_data/raw/era5/weather")
OUTPUT_DIR = Path("weather_data/processed/era5")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

files = sorted(INPUT_DIR.glob("ERA5_weather_*.nc"))

if len(files) != 5:
    raise FileNotFoundError(f"Expected 5 files, found {len(files)}")

daily_files = []

for file in files:
    year = file.stem.split("_")[-1]

    print("=" * 60)
    print(f"PROCESSING {year}")
    print("=" * 60)

    ds = xr.open_dataset(file)
    ds = ds.rename({"valid_time": "time"})
    ds = ds.sortby("time")

    daily = ds[["t2m", "d2m", "u10", "v10"]].resample(time="1D").mean()

    daily["temperature_c"] = daily["t2m"] - 273.15
    daily["dewpoint_c"] = daily["d2m"] - 273.15

    t = daily["temperature_c"]
    td = daily["dewpoint_c"]

    es = 6.112 * np.exp((17.67 * t) / (t + 243.5))
    e = 6.112 * np.exp((17.67 * td) / (td + 243.5))

    daily["relative_humidity"] = ((e / es) * 100).clip(0, 100)

    daily["wind_speed"] = np.sqrt(
        daily["u10"] ** 2 + daily["v10"] ** 2
    )

    daily = daily[
        [
            "temperature_c",
            "dewpoint_c",
            "relative_humidity",
            "u10",
            "v10",
            "wind_speed"
        ]
    ]

    output = OUTPUT_DIR / f"ERA5_weather_daily_{year}.nc"

    daily.to_netcdf(output)
    daily_files.append(output)

    print(f"Saved: {output}")
    print(f"Days: {daily.sizes['time']}")
    print(f"Grid: {daily.sizes['latitude']} x {daily.sizes['longitude']}")

print("=" * 60)
print("COMBINING 2021-2025")
print("=" * 60)

datasets = [xr.open_dataset(file) for file in daily_files]

combined = xr.concat(datasets, dim="time").sortby("time")

output = OUTPUT_DIR / "ERA5_weather_daily_2021_2025.nc"

combined.to_netcdf(output)

print(f"Saved: {output}")
print("Dimensions:", dict(combined.sizes))
print("Variables:", list(combined.data_vars))
print("Start:", combined.time.values[0])
print("End:", combined.time.values[-1])
print("=" * 60)
print("WEATHER DAILY PROCESSING COMPLETE")
print("=" * 60)