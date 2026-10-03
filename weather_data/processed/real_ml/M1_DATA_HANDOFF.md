# VARUNA-AI — Member 1 Data Handoff

## Role

Member 1 — Data Foundation / Data Engineer

## Final ML Dataset

File:

weather_data/processed/real_ml/master_real_weather_2021_2025.parquet

Rows:

8,723,845

Columns:

31

Time period:

2021-01-08 to 2025-12-31

## Data Pipeline

ERA5 data
    ->
Rainfall processing
    ->
Temporal rainfall features
    ->
Daily weather aggregation
    ->
Temperature / humidity / wind derivation
    ->
Spatial and temporal alignment
    ->
Final ML-ready dataset

## Rainfall Features

era5_rainfall
era5_rainfall_log1p
era5_is_rain
era5_is_heavy
era5_rainfall_lag1
era5_rainfall_lag3
era5_rainfall_lag7
era5_rainfall_3day_sum
era5_rainfall_7day_sum
era5_rainfall_7day_mean

## Weather Features

temperature_c
dewpoint_c
relative_humidity
u10
v10
wind_speed

## Temporal Features

month
day_of_year
day_of_year_sin
day_of_year_cos

## Spatial Features

latitude
longitude

## Target

rainfall_error

Definition:

rainfall_error = observed rainfall - NWP/ERA5 rainfall forecast

## Weather Feature Meaning

temperature_c
    Daily mean 2-metre temperature in Celsius.

dewpoint_c
    Daily mean 2-metre dewpoint temperature in Celsius.

relative_humidity
    Relative humidity derived from temperature and dewpoint.

u10
    Daily mean 10-metre east-west wind component.

v10
    Daily mean 10-metre north-south wind component.

wind_speed
    Wind speed derived from u10 and v10.

## Data Quality

Weather missing values:
0

Duplicate time/location rows:
0

All six weather variables were successfully aligned with the existing ML dataset.

## Model Validation

Model 1:

MAE: 3.921
RMSE: 10.395
R2: 0.138

Model 2 — temporal rainfall features:

MAE: 3.592
RMSE: 9.991
R2: 0.203

Model 3 — temporal + weather features:

MAE: 4.278
RMSE: 9.937
R2: 0.212

2025 Model 3 test:

MAE: 4.388
RMSE: 9.811
R2: 0.175

## Weather Feature Analysis

Permutation importance showed:

relative_humidity: 0.1853
wind_speed: 0.0873
dewpoint_c: 0.0671
u10: 0.0669
v10: 0.0231
temperature_c: 0.0194

The analysis indicates that relative humidity was the strongest weather feature in the tested Model 3 configuration.

## How To Load The Dataset

Python:

import pandas as pd

df = pd.read_parquet(
    "weather_data/processed/real_ml/master_real_weather_2021_2025.parquet"
)

print(df.shape)
print(df.head())

## Important

This dataset is the final M1 data handoff dataset.

Members working on modelling should use this dataset instead of recreating the rainfall and weather preprocessing pipeline.

Member 1 data-engineering pipeline is complete through the ML-ready dataset stage.
