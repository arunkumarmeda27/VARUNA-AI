import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

FILE = r".\weather_data\processed\real_ml\master_real_weather_2021_2025.parquet"

print("=" * 60)
print("VARUNA-AI MODEL 3")
print("TEMPORAL + WEATHER FEATURES")
print("LIGHTWEIGHT TRAINING")
print("=" * 60)

print("\nLoading dataset...")

df = pd.read_parquet(FILE)

print("Total rows:", len(df))

features = [
    "latitude",
    "longitude",
    "month",
    "day_of_year",
    "day_of_year_sin",
    "day_of_year_cos",

    "era5_rainfall",
    "era5_rainfall_log1p",
    "era5_is_rain",
    "era5_is_heavy",

    "era5_rainfall_lag1",
    "era5_rainfall_lag3",
    "era5_rainfall_lag7",
    "era5_rainfall_3day_sum",
    "era5_rainfall_7day_sum",
    "era5_rainfall_7day_mean",

    "temperature_c",
    "dewpoint_c",
    "relative_humidity",
    "u10",
    "v10",
    "wind_speed"
]

target = "rainfall_error"

missing_features = [
    col for col in features + [target]
    if col not in df.columns
]

if missing_features:
    raise ValueError(
        f"Missing columns: {missing_features}"
    )

df = df.dropna(
    subset=features + [target]
).sort_values("time")

print("Usable rows:", len(df))
print("Feature count:", len(features))

print("\nCreating chronological split...")

train = df[
    df["time"] < "2024-01-01"
]

validation = df[
    (df["time"] >= "2024-01-01") &
    (df["time"] < "2025-01-01")
]

test = df[
    df["time"] >= "2025-01-01"
]

print("TRAIN:", train.shape)
print("VALIDATION:", validation.shape)
print("TEST:", test.shape)

X_train = train[features]
y_train = train[target]

X_val = validation[features]
y_val = validation[target]

X_test = test[features]
y_test = test[target]

MAX_TRAIN_ROWS = 750000

if len(X_train) > MAX_TRAIN_ROWS:
    print(
        f"\nUsing {MAX_TRAIN_ROWS} training rows "
        f"for lightweight training..."
    )

    X_train = X_train.iloc[:MAX_TRAIN_ROWS]
    y_train = y_train.iloc[:MAX_TRAIN_ROWS]

print("\nTraining rows used:", len(X_train))

print("\n" + "=" * 60)
print("TRAINING MODEL 3...")
print("=" * 60)

model = HistGradientBoostingRegressor(
    max_iter=200,
    learning_rate=0.08,
    max_leaf_nodes=31,
    l2_regularization=1.0,
    random_state=42
)

model.fit(X_train, y_train)

print("\nMODEL TRAINING COMPLETE")

print("\nPredicting 2024 validation data...")

val_predictions = model.predict(X_val)

mae = mean_absolute_error(
    y_val,
    val_predictions
)

rmse = np.sqrt(
    mean_squared_error(
        y_val,
        val_predictions
    )
)

r2 = r2_score(
    y_val,
    val_predictions
)

print("\n" + "=" * 60)
print("MODEL 3 RESULTS - 2024")
print("=" * 60)

print("MAE :", mae)
print("RMSE:", rmse)
print("R2  :", r2)

print("\n" + "=" * 60)
print("2025 TEST EVALUATION")
print("=" * 60)

test_predictions = model.predict(X_test)

test_mae = mean_absolute_error(
    y_test,
    test_predictions
)

test_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        test_predictions
    )
)

test_r2 = r2_score(
    y_test,
    test_predictions
)

print("TEST MAE :", test_mae)
print("TEST RMSE:", test_rmse)
print("TEST R2  :", test_r2)

print("\n" + "=" * 60)
print("MODEL 3 COMPLETE")
print("=" * 60)