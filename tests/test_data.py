"""
VARUNA-AI: Data Foundation and Quality Assurance Tests
Owner: Member 1 (Data Foundation / Data Engineer)
"""

import pytest
import numpy as np
import pandas as pd
from weather_data.preprocessing.validator import DataValidator
from weather_data.temporal.temporal_aligner import TemporalAligner
from weather_data.spatial.spatial_aligner import SpatialAligner
from weather_data.features.synoptic_features import SynopticFeatureEngineer

def test_data_validator_non_negativity():
    df = pd.DataFrame({
        "observed_rainfall": [-5.0, 10.0, 0.0, -0.5],
        "nwp_rainfall": [12.0, -2.0, 5.0, 0.0],
        "mslp": [1000.0, 1005.0, 990.0, 1010.0],
    })
    validator = DataValidator()
    clean_df, report = validator.validate_dataframe(df)

    assert (clean_df["observed_rainfall"] >= 0.0).all()
    assert (clean_df["nwp_rainfall"] >= 0.0).all()
    assert report["negative_rainfall_fixed"] == 3

def test_data_leakage_assertion():
    # Valid ordering: init <= valid
    valid_df = pd.DataFrame({
        "forecast_init_time": ["2026-06-01 00:00:00"],
        "valid_time": ["2026-06-02 00:00:00"],
    })
    assert DataValidator.verify_no_future_leakage(valid_df) is True

    # Invalid ordering: init > valid (future leakage)
    invalid_df = pd.DataFrame({
        "forecast_init_time": ["2026-06-03 00:00:00"],
        "valid_time": ["2026-06-02 00:00:00"],
    })
    with pytest.raises(ValueError, match="Data Leakage Error"):
        DataValidator.verify_no_future_leakage(invalid_df)

def test_temporal_chronological_splits():
    dates = pd.date_range("2018-06-01", "2024-09-30", freq="D")
    df = pd.DataFrame({"valid_time": dates, "value": range(len(dates))})

    train_df, val_df, test_df = TemporalAligner.create_chronological_splits(
        df, time_col="valid_time", train_end_year=2022, val_year=2023, test_year=2024
    )

    assert pd.to_datetime(train_df["valid_time"]).dt.year.max() <= 2022
    assert (pd.to_datetime(val_df["valid_time"]).dt.year == 2023).all()
    assert (pd.to_datetime(test_df["valid_time"]).dt.year == 2024).all()

def test_spatial_reference_grid_generation():
    grid = SpatialAligner.generate_reference_grid(resolution_deg=1.0, lat_bounds=(10.0, 15.0), lon_bounds=(70.0, 75.0))
    assert len(grid) > 0
    assert "grid_id" in grid.columns
    assert "latitude" in grid.columns
    assert "longitude" in grid.columns
