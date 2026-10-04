"""
VARUNA-AI: Real ML-Ready Dataset Builder
Owner: Member 1 - Meteorological Data Engineer

Builds a leakage-safe tabular dataset from the verified
2021-2025 IMD and ERA5 aligned NetCDF datasets.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr


BASE_DIR = Path(__file__).resolve().parent.parent

IMD_FILE = (
    BASE_DIR
    / "weather_data"
    / "raw"
    / "imd_rainfall"
    / "IMD_Rainfall_2021_2025_aligned.nc"
)

ERA5_FILE = (
    BASE_DIR
    / "weather_data"
    / "raw"
    / "era5"
    / "ERA5_daily_tp_2021_2025_aligned.nc"
)

ERROR_FILE = (
    BASE_DIR
    / "weather_data"
    / "raw"
    / "error"
    / "Rainfall_Error_IMD_minus_ERA5_2021_2025.nc"
)

OUTPUT_DIR = BASE_DIR / "weather_data" / "processed" / "real_ml"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def rainfall_category(values):
    return np.select(
        [
            values < 2.5,
            values < 15.6,
            values < 64.5,
            values < 115.6,
            values < 204.5,
        ],
        [
            "NO_RAIN",
            "LIGHT_TO_MODERATE",
            "MODERATE_TO_HEAVY",
            "HEAVY_RAIN",
            "VERY_HEAVY_RAIN",
        ],
        default="EXTREMELY_HEAVY_RAIN",
    )


def main():

    print("=" * 60)
    print("VARUNA-AI REAL ML DATASET BUILDER")
    print("=" * 60)

    print("\nOpening verified datasets...")

    imd = xr.open_dataset(IMD_FILE)
    era5 = xr.open_dataset(ERA5_FILE)
    error = xr.open_dataset(ERROR_FILE)

    print("IMD:", IMD_FILE)
    print("ERA5:", ERA5_FILE)
    print("ERROR:", ERROR_FILE)

    # ---------------------------------------------------------
    # 1. Verify dimensions
    # ---------------------------------------------------------

    print("\nChecking dimensions...")

    assert imd.rainfall.dims == era5.rainfall.dims
    assert imd.rainfall.dims == error.rainfall_error.dims

    assert imd.sizes["time"] == era5.sizes["time"]
    assert imd.sizes["time"] == error.sizes["time"]

    assert imd.sizes["latitude"] == era5.sizes["latitude"]
    assert imd.sizes["longitude"] == era5.sizes["longitude"]

    print("Dimensions: OK")

    # ---------------------------------------------------------
    # 2. Verify coordinates
    # ---------------------------------------------------------

    print("\nChecking coordinates...")

    np.testing.assert_array_equal(
        imd.time.values,
        era5.time.values,
    )

    np.testing.assert_array_equal(
        imd.time.values,
        error.time.values,
    )

    np.testing.assert_array_equal(
        imd.latitude.values,
        era5.latitude.values,
    )

    np.testing.assert_array_equal(
        imd.longitude.values,
        era5.longitude.values,
    )

    print("Time: OK")
    print("Latitude: OK")
    print("Longitude: OK")

    # ---------------------------------------------------------
    # 3. Convert to DataFrame
    # ---------------------------------------------------------

    print("\nConverting aligned NetCDF data to tabular format...")

    ds = xr.Dataset(
        {
            "imd_rainfall": imd.rainfall,
            "era5_rainfall": era5.rainfall,
            "rainfall_error": error.rainfall_error,
        }
    )

    df = ds.to_dataframe().reset_index()

    print("Initial rows:", len(df))

    # ---------------------------------------------------------
    # 4. Remove rows where IMD observation is unavailable
    # ---------------------------------------------------------

    print("\nFiltering usable observation/forecast pairs...")

    valid_mask = (
        df["imd_rainfall"].notna()
        & df["era5_rainfall"].notna()
        & df["rainfall_error"].notna()
    )

    df = df.loc[valid_mask].copy()

    print("Valid rows:", len(df))

    # ---------------------------------------------------------
    # 5. Verify rainfall error
    # ---------------------------------------------------------

    print("\nVerifying rainfall error...")

    calculated_error = (
        df["imd_rainfall"] - df["era5_rainfall"]
    )

    max_difference = np.max(
        np.abs(
            calculated_error.values
            - df["rainfall_error"].values
        )
    )

    print("Maximum error difference:", max_difference)

    if max_difference > 1e-5:
        raise ValueError(
            "Rainfall error verification failed."
        )

    print("Rainfall error: VERIFIED")

    # ---------------------------------------------------------
    # 6. Add useful ML features
    # ---------------------------------------------------------

    print("\nCreating ML features...")

    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df["day"] = df["time"].dt.day
    df["day_of_year"] = df["time"].dt.dayofyear

    # Cyclic representation of annual seasonality
    df["day_of_year_sin"] = np.sin(
        2 * np.pi * df["day_of_year"] / 365.25
    )

    df["day_of_year_cos"] = np.cos(
        2 * np.pi * df["day_of_year"] / 365.25
    )

    # Forecast rainfall transformations
    df["era5_rainfall_log1p"] = np.log1p(
        df["era5_rainfall"]
    )

    df["era5_is_rain"] = (
        df["era5_rainfall"] >= 2.5
    ).astype(np.int8)

    df["era5_is_heavy"] = (
        df["era5_rainfall"] >= 64.5
    ).astype(np.int8)

    # Observation categories
    df["imd_category"] = rainfall_category(
        df["imd_rainfall"].values
    )

    df["era5_category"] = rainfall_category(
        df["era5_rainfall"].values
    )

    # Target-oriented flags
    df["imd_is_rain"] = (
        df["imd_rainfall"] >= 2.5
    ).astype(np.int8)

    df["imd_is_heavy"] = (
        df["imd_rainfall"] >= 64.5
    ).astype(np.int8)

    # ---------------------------------------------------------
    # 7. Sort deterministically
    # ---------------------------------------------------------

    df = df.sort_values(
        ["time", "latitude", "longitude"]
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # 8. Select final columns
    # ---------------------------------------------------------

    columns = [
        "time",
        "latitude",
        "longitude",

        "year",
        "month",
        "day",
        "day_of_year",
        "day_of_year_sin",
        "day_of_year_cos",

        "imd_rainfall",
        "era5_rainfall",
        "rainfall_error",

        "imd_category",
        "era5_category",

        "imd_is_rain",
        "imd_is_heavy",

        "era5_is_rain",
        "era5_is_heavy",
        "era5_rainfall_log1p",
    ]

    df = df[columns]

    # ---------------------------------------------------------
    # 9. Final integrity checks
    # ---------------------------------------------------------

    print("\nRunning final integrity checks...")

    if df["time"].duplicated().any():
        # Same date is expected at multiple grid cells.
        pass

    if df[["latitude", "longitude"]].isna().any().any():
        raise ValueError("Missing spatial coordinates found.")

    if (df["imd_rainfall"] < 0).any():
        raise ValueError("Negative IMD rainfall found.")

    if (df["era5_rainfall"] < 0).any():
        raise ValueError("Negative ERA5 rainfall found.")

    print("Integrity checks: PASSED")

    # ---------------------------------------------------------
    # 10. Save full ML dataset
    # ---------------------------------------------------------

    master_path = OUTPUT_DIR / "master_real_2021_2025.parquet"

    print("\nSaving:")
    print(master_path)

    df.to_parquet(
        master_path,
        index=False,
    )

    # ---------------------------------------------------------
    # 11. Chronological split
    # ---------------------------------------------------------

    train = df[df["year"] <= 2023].copy()
    validation = df[df["year"] == 2024].copy()
    test = df[df["year"] == 2025].copy()

    train_path = OUTPUT_DIR / "train_real_2021_2023.parquet"
    validation_path = OUTPUT_DIR / "validation_real_2024.parquet"
    test_path = OUTPUT_DIR / "test_real_2025.parquet"

    train.to_parquet(train_path, index=False)
    validation.to_parquet(validation_path, index=False)
    test.to_parquet(test_path, index=False)

    # ---------------------------------------------------------
    # 12. Print summary
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("DATASET COMPLETE")
    print("=" * 60)

    print("MASTER:", master_path)
    print("TRAIN:", train_path)
    print("VALIDATION:", validation_path)
    print("TEST:", test_path)

    print("\nROWS")
    print("Master:", len(df))
    print("Train:", len(train))
    print("Validation:", len(validation))
    print("Test:", len(test))

    print("\nTIME RANGES")

    print(
        "Train:",
        train["time"].min(),
        "to",
        train["time"].max(),
    )

    print(
        "Validation:",
        validation["time"].min(),
        "to",
        validation["time"].max(),
    )

    print(
        "Test:",
        test["time"].min(),
        "to",
        test["time"].max(),
    )

    print("\nCOLUMNS:")
    for column in df.columns:
        print(" -", column)

    print("\nMember 1 real ML dataset successfully created.")


if __name__ == "__main__":
    main()