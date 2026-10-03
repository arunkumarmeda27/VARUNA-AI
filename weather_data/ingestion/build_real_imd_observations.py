from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "weather_data" / "raw"
IMD_DIR = RAW_DIR / "imd_rainfall"
ERA5_FILE = RAW_DIR / "era5" / "ERA5_daily_tp_2021_2025_aligned.nc"
IMD_OUTPUT = IMD_DIR / "IMD_Rainfall_2021_2025_aligned.nc"
ERROR_OUTPUT = (
    RAW_DIR / "error" / "Rainfall_Error_IMD_minus_ERA5_2021_2025.nc"
)
START_YEAR = 2021
END_YEAR = 2025


def _matches_existing(path: Path, variable_name: str, expected: xr.DataArray) -> bool:
    if not path.is_file():
        return False

    with xr.open_dataset(path) as existing_dataset:
        if variable_name not in existing_dataset:
            return False
        existing = existing_dataset[variable_name].load()

    if existing.dims != expected.dims:
        return False
    for coordinate in expected.dims:
        if coordinate not in existing.coords or not np.array_equal(
            existing[coordinate].values,
            expected[coordinate].values,
        ):
            return False
    return np.array_equal(
        existing.values,
        expected.values,
        equal_nan=True,
    )


def _save_or_verify(
    path: Path,
    variable_name: str,
    expected: xr.DataArray,
) -> None:
    if path.exists():
        if not _matches_existing(path, variable_name, expected):
            raise RuntimeError(
                f"Existing real-data output differs from source-derived data; "
                f"left untouched: {path}"
            )
        print(f"Verified existing output without rewriting: {path}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    xr.Dataset({variable_name: expected}).to_netcdf(path)
    print(f"Created from real source files: {path}")


def build_real_imd_observations() -> None:
    if not ERA5_FILE.is_file():
        raise FileNotFoundError(
            f"Required aligned real ERA5 grid is missing: {ERA5_FILE}"
        )

    with xr.open_dataset(ERA5_FILE) as era5_dataset:
        if "rainfall" not in era5_dataset:
            raise ValueError(
                f"Aligned ERA5 input has no 'rainfall' variable: {ERA5_FILE}"
            )
        target_latitude = era5_dataset["latitude"].values
        target_longitude = era5_dataset["longitude"].values
        era5 = era5_dataset["rainfall"].load()

    imd_parts = []
    reference_latitude = None
    reference_longitude = None

    for year in range(START_YEAR, END_YEAR + 1):
        source_path = IMD_DIR / f"RF25_ind{year}_rfp25.nc"
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Required real IMD rainfall file is missing: {source_path}"
            )

        with xr.open_dataset(source_path) as source:
            required_dimensions = {"TIME", "LATITUDE", "LONGITUDE"}
            if not required_dimensions.issubset(source.dims):
                raise ValueError(
                    f"IMD file has incompatible dimensions: {source_path}; "
                    f"expected {sorted(required_dimensions)}, found {dict(source.sizes)}"
                )
            if "RAINFALL" not in source.data_vars:
                raise ValueError(
                    f"IMD file has no RAINFALL data variable: {source_path}"
                )
            units = str(source["RAINFALL"].attrs.get("units", "")).strip().lower()
            if units not in {"mm", "millimeter", "millimeters", "millimetre", "millimetres"}:
                raise ValueError(
                    f"IMD rainfall units must be millimetres in {source_path}; "
                    f"found {units!r}"
                )

            source_time = pd.DatetimeIndex(source["TIME"].values)
            expected_time = pd.date_range(
                start=f"{year}-01-01",
                end=f"{year}-12-31",
                freq="D",
            )
            if not source_time.equals(expected_time):
                raise ValueError(
                    f"IMD dates do not cover the complete calendar year {year}: "
                    f"{source_path}"
                )

            latitude = source["LATITUDE"].values
            longitude = source["LONGITUDE"].values
            if reference_latitude is None:
                reference_latitude = latitude
                reference_longitude = longitude
            elif not np.array_equal(latitude, reference_latitude) or not np.array_equal(
                longitude,
                reference_longitude,
            ):
                raise ValueError(
                    f"IMD grid differs between annual files: {source_path}"
                )

            try:
                rainfall = source["RAINFALL"].sel(
                    LATITUDE=target_latitude,
                    LONGITUDE=target_longitude,
                ).load()
            except KeyError as exc:
                raise ValueError(
                    f"IMD grid does not contain the aligned ERA5 coordinates: "
                    f"{source_path}"
                ) from exc

            values = rainfall.values
            if np.any(values[np.isfinite(values)] < 0):
                raise ValueError(
                    f"Real IMD rainfall contains negative observations: {source_path}"
                )

            imd_parts.append(
                rainfall.rename(
                    {
                        "TIME": "time",
                        "LATITUDE": "latitude",
                        "LONGITUDE": "longitude",
                    }
                )
            )

    imd = xr.concat(imd_parts, dim="time", join="exact").sortby("time")
    if not pd.DatetimeIndex(imd["time"].values).is_unique:
        raise ValueError("Combined real IMD data contains duplicate timestamps.")

    try:
        imd, era5 = xr.align(imd, era5, join="exact", copy=False)
    except ValueError as exc:
        raise ValueError(
            "Real IMD and ERA5 coordinates/timestamps do not align exactly."
        ) from exc

    error = imd - era5
    error.name = "rainfall_error"
    error.attrs.update(
        {
            "long_name": "IMD minus ERA5 daily rainfall error",
            "units": "mm",
            "description": "Observed IMD rainfall minus ERA5 rainfall",
        }
    )

    _save_or_verify(IMD_OUTPUT, "rainfall", imd)
    _save_or_verify(ERROR_OUTPUT, "rainfall_error", error)


if __name__ == "__main__":
    build_real_imd_observations()