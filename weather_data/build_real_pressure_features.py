"""
VARUNA-AI: Real Weather Feature Builder

Builds the real-data feature dataset used by the VARUNA-AI
correction pipeline.

This version uses the real ERA5 weather variables already present
in the ML-ready dataset:

    temperature_c
    dewpoint_c
    relative_humidity
    u10
    v10
    wind_speed
    era5_rainfall

No synthetic meteorological values are generated.
No unavailable pressure-level variables are required.
No missing feature is silently replaced with zero.
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

REAL_DATASET = (
    BASE_DIR
    / "weather_data"
    / "processed"
    / "real_ml"
    / "master_real_weather_2021_2025.parquet"
)

OUTPUT = (
    BASE_DIR
    / "weather_data"
    / "processed"
    / "real_ml"
    / "master_real_weather_2021_2025_features.parquet"
)


# ---------------------------------------------------------------------
# REQUIRED REAL-DATA COLUMNS
# ---------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "time",
    "latitude",
    "longitude",
    "imd_rainfall",
    "era5_rainfall",
    "temperature_c",
    "dewpoint_c",
    "relative_humidity",
    "u10",
    "v10",
    "wind_speed",
]


# ---------------------------------------------------------------------
# FEATURE VALIDATION
# ---------------------------------------------------------------------

def validate_columns(df):
    """Ensure the real ML dataset contains required columns."""

    missing = [
        col
        for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            "Real ML dataset is missing required columns:\n"
            + "\n".join(f"  - {col}" for col in missing)
        )


def validate_no_missing(df, columns):
    """Fail explicitly if required real-data features contain NaNs."""

    missing_summary = (
        df[columns]
        .isna()
        .sum()
    )

    missing_summary = (
        missing_summary[
            missing_summary > 0
        ]
        .sort_values(
            ascending=False
        )
    )

    if not missing_summary.empty:
        raise ValueError(
            "Required real-data features contain missing values:\n"
            f"{missing_summary}"
        )


# ---------------------------------------------------------------------
# FEATURE ENGINEERING
# ---------------------------------------------------------------------

def build_real_features(df):
    """
    Build additional features only from variables that actually exist
    in the real ERA5/IMD dataset.
    """

    result = df.copy()

    # -------------------------------------------------------------
    # NWP rainfall aliases
    # -------------------------------------------------------------

    result["nwp_rainfall"] = (
        result["era5_rainfall"]
        .astype("float32")
    )

    result["nwp_rain_log1p"] = (
        np.log1p(
            result["nwp_rainfall"]
        )
        .astype("float32")
    )

    result["nwp_is_rain"] = (
        result["nwp_rainfall"] > 0.1
    ).astype("int8")

    result["nwp_is_heavy"] = (
        result["nwp_rainfall"] >= 64.5
    ).astype("int8")

    # -------------------------------------------------------------
    # Real near-surface wind features
    # -------------------------------------------------------------

    result["wind_speed_10m"] = np.sqrt(
        result["u10"] ** 2
        +
        result["v10"] ** 2
    ).astype("float32")

    result["wind_dir_10m"] = (
        np.arctan2(
            -result["u10"],
            -result["v10"],
        )
        * 180.0
        / np.pi
    ) % 360.0

    result["wind_dir_10m"] = (
        result["wind_dir_10m"]
        .astype("float32")
    )

    # -------------------------------------------------------------
    # Temperature / moisture derived features
    # -------------------------------------------------------------

    result["temperature_dewpoint_spread"] = (
        result["temperature_c"]
        -
        result["dewpoint_c"]
    ).astype("float32")

    # -------------------------------------------------------------
    # Simple real moisture indicator
    #
    # Relative humidity is already available from ERA5.
    # This is only a normalized feature, not synthetic data.
    # -------------------------------------------------------------

    result["moisture_index"] = (
        result["relative_humidity"] / 100.0
    ).astype("float32")

    # -------------------------------------------------------------
    # Existing calendar features are retained.
    # Create them only if they are absent.
    # -------------------------------------------------------------

    result["time"] = pd.to_datetime(
        result["time"],
        errors="raise",
    )

    if "year" not in result.columns:
        result["year"] = (
            result["time"]
            .dt.year
            .astype("int16")
        )

    if "month" not in result.columns:
        result["month"] = (
            result["time"]
            .dt.month
            .astype("int8")
        )

    if "day" not in result.columns:
        result["day"] = (
            result["time"]
            .dt.day
            .astype("int8")
        )

    if "day_of_year" not in result.columns:
        result["day_of_year"] = (
            result["time"]
            .dt.dayofyear
            .astype("int16")
        )

    if "day_of_year_sin" not in result.columns:
        result["day_of_year_sin"] = np.sin(
            2.0
            * np.pi
            * result["day_of_year"]
            / 365.25
        ).astype("float32")

    if "day_of_year_cos" not in result.columns:
        result["day_of_year_cos"] = np.cos(
            2.0
            * np.pi
            * result["day_of_year"]
            / 365.25
        ).astype("float32")

    return result


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    print("=" * 78)
    print("VARUNA-AI REAL WEATHER FEATURE BUILDER")
    print("=" * 78)

    print()
    print("Loading real ML dataset...")
    print(REAL_DATASET)

    if not REAL_DATASET.exists():
        raise FileNotFoundError(
            f"Real ML dataset not found:\n{REAL_DATASET}"
        )

    df = pd.read_parquet(
        REAL_DATASET
    )

    print()
    print(f"Rows loaded: {len(df):,}")
    print(f"Columns loaded: {len(df.columns)}")

    validate_columns(df)

    df["time"] = pd.to_datetime(
        df["time"],
        errors="raise",
    )

    print()
    print("DATE RANGE")
    print("-" * 40)
    print(f"Start: {df['time'].min()}")
    print(f"End:   {df['time'].max()}")

    print()
    print("VALIDATING REAL INPUT FEATURES")
    print("-" * 40)

    for col in REQUIRED_COLUMNS:
        print(
            f"OK   {col:<30} "
            f"missing={df[col].isna().sum():,}"
        )

    validate_no_missing(
        df,
        REQUIRED_COLUMNS,
    )

    # -------------------------------------------------------------
    # Build features
    # -------------------------------------------------------------

    print()
    print("BUILDING REAL FEATURES")
    print("-" * 40)

    result = build_real_features(
        df
    )

    # -------------------------------------------------------------
    # Validate generated features
    # -------------------------------------------------------------

    generated_features = [
        "nwp_rainfall",
        "nwp_rain_log1p",
        "nwp_is_rain",
        "nwp_is_heavy",
        "wind_speed_10m",
        "wind_dir_10m",
        "temperature_dewpoint_spread",
        "moisture_index",
    ]

    print()
    print("GENERATED REAL-DATA FEATURES")
    print("-" * 40)

    for col in generated_features:
        missing_count = (
            result[col]
            .isna()
            .sum()
        )

        print(
            f"{'OK' if missing_count == 0 else 'ERROR':<5} "
            f"{col:<35} "
            f"missing={missing_count:,}"
        )

    validate_no_missing(
        result,
        generated_features,
    )

    # -------------------------------------------------------------
    # Final global validation
    # -------------------------------------------------------------

    total_missing = (
        result
        .isna()
        .sum()
        .sum()
    )

    print()
    print("FINAL DATASET VALIDATION")
    print("-" * 40)
    print(
        f"Rows:             {len(result):,}"
    )
    print(
        f"Columns:          {len(result.columns)}"
    )
    print(
        f"Missing values:   {total_missing:,}"
    )

    if total_missing != 0:
        raise ValueError(
            "Final real feature dataset contains missing values."
        )

    # -------------------------------------------------------------
    # Save
    # -------------------------------------------------------------

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("Saving...")
    print(OUTPUT)

    result.to_parquet(
        OUTPUT,
        index=False,
    )

    # -------------------------------------------------------------
    # Final confirmation
    # -------------------------------------------------------------

    print()
    print("=" * 78)
    print("REAL FEATURE DATASET CREATED SUCCESSFULLY")
    print("=" * 78)

    print(
        f"Output:          {OUTPUT}"
    )
    print(
        f"Rows:            {len(result):,}"
    )
    print(
        f"Columns:         {len(result.columns)}"
    )
    print(
        f"Missing values:  {result.isna().sum().sum():,}"
    )

    print()
    print("Important:")
    print(
        "No synthetic pressure-level values were generated."
    )
    print(
        "No unavailable ERA5 variables were replaced with zero."
    )
    print(
        "All weather features originate from the real ML dataset."
    )


if __name__ == "__main__":
    main()