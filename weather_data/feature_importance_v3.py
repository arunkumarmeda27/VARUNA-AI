import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

FILE = r".\weather_data\processed\real_ml\master_real_weather_2021_2025.parquet"

print("=" * 60)
print("VARUNA-AI MODEL 3 FEATURE ANALYSIS")
print("=" * 60)

df = pd.read_parquet(FILE)

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

df = df.sort_values("time")

train = df[df["time"] < "2024-01-01"]

train = train.dropna(
    subset=features + [target]
)

MAX_ROWS = 750000

X = train[features].iloc[:MAX_ROWS]
y = train[target].iloc[:MAX_ROWS]

print("\nTraining rows:", len(X))
print("Features:", len(features))

model = HistGradientBoostingRegressor(
    max_iter=200,
    learning_rate=0.08,
    max_leaf_nodes=31,
    l2_regularization=1.0,
    random_state=42
)

print("\nTraining analysis model...")

model.fit(X, y)

print("\nCalculating permutation importance...")

from sklearn.inspection import permutation_importance

result = permutation_importance(
    model,
    X.iloc[:100000],
    y.iloc[:100000],
    n_repeats=3,
    random_state=42,
    scoring="r2",
    n_jobs=-1
)

importance = pd.DataFrame({
    "feature": features,
    "importance": result.importances_mean
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\n" + "=" * 60)
print("MODEL 3 FEATURE IMPORTANCE")
print("=" * 60)

print(
    importance.to_string(index=False)
)

print("\n" + "=" * 60)
print("WEATHER FEATURE IMPORTANCE")
print("=" * 60)

weather_features = [
    "temperature_c",
    "dewpoint_c",
    "relative_humidity",
    "u10",
    "v10",
    "wind_speed"
]

print(
    importance[
        importance["feature"].isin(weather_features)
    ].to_string(index=False)
)

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)