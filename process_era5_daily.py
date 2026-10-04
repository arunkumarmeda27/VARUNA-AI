import xarray as xr
import numpy as np
import pandas as pd
import os
import sys

# Get year from command line
if len(sys.argv) < 2:
    print("ERROR: Please provide a year.")
    print("Example: python .\\process_era5_daily.py 2022")
    sys.exit(1)

YEAR = int(sys.argv[1])

base = r".\weather_data\raw\era5"
input_file = os.path.join(base, f"era5_{YEAR}.grib")
output_file = os.path.join(base, f"ERA5_daily_tp_{YEAR}.nc")

print("====================================")
print("PROCESSING ERA5", YEAR)
print("====================================")
print("Opening:", input_file)

if not os.path.exists(input_file):
    print("ERROR: Input file does not exist:")
    print(input_file)
    sys.exit(1)

ds = xr.open_dataset(input_file, engine="cfgrib")

# ERA5 total precipitation: metres -> millimetres
tp = ds["tp"] * 1000

print("TP shape:", tp.shape)
print("Grid:", tp.sizes["latitude"], "x", tp.sizes["longitude"])

# Flatten time and step into valid-time dimension
values = tp.values.reshape(
    -1,
    tp.sizes["latitude"],
    tp.sizes["longitude"]
)

valid_times = ds["valid_time"].values.reshape(-1)
valid_times = pd.DatetimeIndex(valid_times)

# Sort chronologically
order = np.argsort(valid_times)

values = values[order]
valid_times = valid_times[order]

# Remove duplicate valid times
keep = ~valid_times.duplicated()

values = values[keep]
valid_times = valid_times[keep]

print("Unique valid times:", len(valid_times))
print("Valid range:", valid_times[0], "to", valid_times[-1])

# Create accumulated precipitation DataArray
accumulated = xr.DataArray(
    values,
    dims=["time", "latitude", "longitude"],
    coords={
        "time": valid_times,
        "latitude": ds["latitude"],
        "longitude": ds["longitude"],
    },
    name="tp_accumulated_mm",
)

# Convert accumulated precipitation to hourly rainfall
hourly = accumulated.diff("time")

# Remove negative values caused by accumulation reset
hourly = xr.where(hourly < 0, 0, hourly)

hourly.name = "rainfall"

# Calculate daily rainfall
daily = hourly.resample(time="1D").sum()

# Keep only requested calendar year
daily = daily.sel(
    time=slice(
        f"{YEAR}-01-01",
        f"{YEAR}-12-31"
    )
)

daily.name = "rainfall"

daily.attrs["units"] = "mm"
daily.attrs["long_name"] = "ERA5 daily total precipitation"
daily.attrs["source"] = "ERA5"

# Save output
daily.to_netcdf(output_file)

print()
print("====================================")
print("DONE")
print("====================================")
print("Output:", output_file)
print("DATES:", daily.time.values[0], "to", daily.time.values[-1])
print("NUMBER OF DAYS:", daily.sizes["time"])
print("GRID:", daily.sizes["latitude"], "x", daily.sizes["longitude"])
print("MAX DAILY RAINFALL:", float(daily.max()), "mm")