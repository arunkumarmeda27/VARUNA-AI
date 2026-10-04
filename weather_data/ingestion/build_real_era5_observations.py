import xarray as xr
import pandas as pd
import numpy as np
import os
import glob
import pyarrow as pa
import pyarrow.parquet as pq


INPUT_DIR = r"weather_data\raw\era5"
OUTPUT_DIR = r"weather_data\processed\era5_yearly"

START_YEAR = 2021
END_YEAR = 2025

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------
# Check files
# ---------------------------------------------------------

for year in range(START_YEAR, END_YEAR + 1):

    file = os.path.join(
        INPUT_DIR,
        f"era5_{year}.grib"
    )

    if not os.path.exists(file):
        raise FileNotFoundError(
            f"Missing REAL ERA5 file: {file}"
        )

print("REAL ERA5 files found:")

for year in range(START_YEAR, END_YEAR + 1):
    print(f" - era5_{year}.grib")


# ---------------------------------------------------------
# Process one year at a time
# ---------------------------------------------------------

for year in range(START_YEAR, END_YEAR + 1):

    print("\n" + "=" * 70)
    print(f"PROCESSING REAL ERA5 {year}")
    print("=" * 70)

    input_file = os.path.join(
        INPUT_DIR,
        f"era5_{year}.grib"
    )

    output_file = os.path.join(
        OUTPUT_DIR,
        f"era5_observations_{year}.parquet"
    )

    # Remove an incomplete previous output if present
    if os.path.exists(output_file):
        os.remove(output_file)

    ds = xr.open_dataset(
        input_file,
        engine="cfgrib"
    )

    print("Raw dimensions:", dict(ds.sizes))

    # -----------------------------------------------------
    # Stack time + step into one forecast dimension
    # -----------------------------------------------------

    tp = ds["tp"].stack(
        forecast=("time", "step")
    )

    valid_time = ds["valid_time"].stack(
        forecast=("time", "step")
    )

    print(
        "Raw valid_time:",
        valid_time.min().values,
        "to",
        valid_time.max().values
    )

    writer = None

    # -----------------------------------------------------
    # Process ONE DAY at a time
    # -----------------------------------------------------

    dates = pd.date_range(
        start=f"{year}-01-01",
        end=f"{year}-12-31",
        freq="D"
    )

    total_rows = 0

    for day_number, day in enumerate(dates, start=1):

        day_start = np.datetime64(
            day.strftime("%Y-%m-%dT00:00:00")
        )

        day_end = day_start + np.timedelta64(
            23, "h"
        )

        # IMPORTANT:
        # Select actual valid_time values.
        mask = (
            (valid_time >= day_start)
            &
            (valid_time <= day_end)
        )

        indices = np.flatnonzero(
            mask.values
        )

        if len(indices) == 0:
            continue

        # Select ONLY the valid forecast hours
        tp_day = tp.isel(
            forecast=indices
        )

        valid_day = valid_time.isel(
            forecast=indices
        )

        # -------------------------------------------------
        # Convert selected data to pandas
        # -------------------------------------------------

        df = tp_day.to_dataframe(
            name="tp"
        ).reset_index()

        valid_values = (
            valid_day.values
        )

        # Repeat valid_time for every grid point
        grid_size = (
            ds.sizes["latitude"]
            * ds.sizes["longitude"]
        )

        df["valid_time"] = np.repeat(
            valid_values,
            grid_size
        )

        # Metres -> millimetres
        df["observed_rainfall"] = (
            df["tp"] * 1000.0
        )

        df = df[
            [
                "valid_time",
                "latitude",
                "longitude",
                "observed_rainfall"
            ]
        ]

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if df["observed_rainfall"].isna().any():
            raise RuntimeError(
                f"{year}-{day.strftime('%m-%d')}: "
                "NULL rainfall detected."
            )

        if (
            df["observed_rainfall"] < 0
        ).any():
            raise RuntimeError(
                f"{year}-{day.strftime('%m-%d')}: "
                "negative rainfall detected."
            )

        # -------------------------------------------------
        # Write daily chunk into Parquet
        # -------------------------------------------------

        table = pa.Table.from_pandas(
            df,
            preserve_index=False
        )

        if writer is None:

            writer = pq.ParquetWriter(
                output_file,
                table.schema,
                compression="snappy"
            )

        writer.write_table(table)

        total_rows += len(df)

        # Progress every 30 days
        if day_number % 30 == 0 or day_number == len(dates):

            print(
                f"{year}: "
                f"day {day_number}/{len(dates)} | "
                f"rows written: {total_rows:,}"
            )

        del df
        del table
        del tp_day
        del valid_day
        del indices

    if writer is not None:
        writer.close()

    ds.close()

    # -----------------------------------------------------
    # Final yearly verification
    # -----------------------------------------------------

    print("\nYEAR COMPLETE")

    print(
        "Output:",
        output_file
    )

    print(
        "Rows:",
        f"{total_rows:,}"
    )

    size_mb = (
        os.path.getsize(output_file)
        / (1024 * 1024)
    )

    print(
        "File size:",
        f"{size_mb:.2f} MB"
    )

    # Verify Parquet
    check = pd.read_parquet(
        output_file
    )

    print(
        "Verified start:",
        check["valid_time"].min()
    )

    print(
        "Verified end:",
        check["valid_time"].max()
    )

    print(
        "Verified unique times:",
        check["valid_time"].nunique()
    )

    print(
        "Rainfall range:",
        check["observed_rainfall"].min(),
        "to",
        check["observed_rainfall"].max(),
        "mm"
    )

    del check


print("\n" + "=" * 70)
print("ALL REAL ERA5 OBSERVATION FILES PROCESSED")
print("=" * 70)

for year in range(START_YEAR, END_YEAR + 1):

    output_file = os.path.join(
        OUTPUT_DIR,
        f"era5_observations_{year}.parquet"
    )

    size_mb = (
        os.path.getsize(output_file)
        / (1024 * 1024)
    )

    print(
        f"{year}: {size_mb:.2f} MB"
    )

print("\nNO SYNTHETIC DATA USED.")