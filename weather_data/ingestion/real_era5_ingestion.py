"""
Real ERA5 ingestion for VARUNA-AI.

M1 responsibility:
- Read real ERA5 GRIB data from weather_data/raw/
- Convert precipitation from metres to millimetres
- Convert the GRIB dataset into a tabular DataFrame
- Save the real-data slice separately from the existing synthetic dataset

Do NOT overwrite the synthetic master dataset yet.
"""

import glob
import os

import pandas as pd
import xarray as xr


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw")
OUTPUT_DIR = os.path.join(BASE_DIR, "processed")

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "era5_real_slice_v1.0.0.parquet",
)


def find_grib_file():
    """Find the first ERA5 GRIB file in weather_data/raw/."""
    files = glob.glob(os.path.join(RAW_DIR, "*.grib"))

    if not files:
        raise FileNotFoundError(
            f"No GRIB files found in {RAW_DIR}"
        )

    return files[0]


def ingest_era5():
    """Read ERA5 GRIB and convert precipitation to tabular data."""

    grib_file = find_grib_file()

    print(f"Reading ERA5 file:")
    print(grib_file)

    ds = xr.open_dataset(
        grib_file,
        engine="cfgrib",
    )

    if "tp" not in ds.data_vars:
        raise ValueError(
            "ERA5 file does not contain the expected 'tp' precipitation variable."
        )

    # ERA5 total precipitation (tp) is in metres.
    # Convert metres -> millimetres.
    precipitation_mm = ds["tp"] * 1000.0

    df = precipitation_mm.to_dataframe(
        name="observed_rainfall"
    ).reset_index()

    # Keep only the fields needed for the first real-data slice.
    columns = [
        "valid_time",
        "latitude",
        "longitude",
        "observed_rainfall",
    ]

    df = df[columns]

    # Remove missing observations.
    df = df.dropna(
        subset=[
            "valid_time",
            "latitude",
            "longitude",
            "observed_rainfall",
        ]
    )

    # Ensure rainfall cannot be negative.
    df["observed_rainfall"] = df["observed_rainfall"].clip(
        lower=0
    )

    # Sort for reproducible downstream processing.
    df = df.sort_values(
        [
            "valid_time",
            "latitude",
            "longitude",
        ]
    ).reset_index(drop=True)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("ERA5 real-data ingestion successful!")
    print(f"Rows: {len(df)}")
    print(f"Output: {OUTPUT_FILE}")
    print()
    print("Columns:")
    print(df.columns.tolist())
    print()
    print("Rainfall statistics (mm):")
    print(df["observed_rainfall"].describe())


if __name__ == "__main__":
    ingest_era5()