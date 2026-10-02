import xarray as xr
import os

base = r".\weather_data\raw"

imd_file = os.path.join(
    base, "imd_rainfall", "IMD_Rainfall_2020_2025.nc"
)

era5_dir = os.path.join(base, "era5")

print("Opening IMD reference grid...")
imd = xr.open_dataset(imd_file)

# IMD is the reference grid
target_lat = imd["LATITUDE"]
target_lon = imd["LONGITUDE"]

# Keep only the region available in BOTH datasets
target_lat = target_lat.sel(
    LATITUDE=slice(6.5, 35.0)
)

target_lon = target_lon.sel(
    LONGITUDE=slice(66.5, 100.0)
)

print("Target grid:")
print("Latitude:", float(target_lat.min()), "to", float(target_lat.max()))
print("Longitude:", float(target_lon.min()), "to", float(target_lon.max()))
print("Latitude points:", target_lat.size)
print("Longitude points:", target_lon.size)

for year in range(2021, 2026):

    input_file = os.path.join(
        era5_dir,
        f"ERA5_daily_tp_{year}.nc"
    )

    output_file = os.path.join(
        era5_dir,
        f"ERA5_daily_tp_{year}_aligned.nc"
    )

    print()
    print("====================================")
    print("PROCESSING", year)
    print("====================================")

    ds = xr.open_dataset(input_file)

    # Select exact common IMD grid points
    aligned = ds.sel(
        latitude=target_lat.values,
        longitude=target_lon.values
    )

    aligned.to_netcdf(output_file)

    print("DONE")
    print("Output:", output_file)
    print("Shape:", aligned["rainfall"].shape)
    print("Dates:", aligned.time.values[0], "to", aligned.time.values[-1])