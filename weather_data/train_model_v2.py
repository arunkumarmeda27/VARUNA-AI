from pathlib import Path
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = (
    BASE_DIR / "weather_data" / "processed" / "real_ml"
    / "master_real_features_2021_2025.parquet"
)

FEATURES = [
    "latitude", "longitude", "month", "day_of_year",
    "day_of_year_sin", "day_of_year_cos",
    "era5_rainfall", "era5_rainfall_log1p",
    "era5_is_rain", "era5_is_heavy",
    "era5_rainfall_lag1", "era5_rainfall_lag3",
    "era5_rainfall_lag7", "era5_rainfall_3day_sum",
    "era5_rainfall_7day_sum", "era5_rainfall_7day_mean"
]

TARGET = "rainfall_error"

BASELINE_MAE = 3.920653508538636
BASELINE_RMSE = 10.394668266220188
BASELINE_R2 = 0.13762711610735667

print("=" * 60)
print("VARUNA-AI MODEL 2")
print("TEMPORAL RAINFALL FEATURES")
print("LIGHTWEIGHT VALIDATION")
print("=" * 60)

print("\nLoading dataset...")
df = pd.read_parquet(DATA_FILE)
print("Total rows:", len(df))

missing = [c for c in FEATURES + [TARGET, "year"] if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

df = df.dropna(subset=FEATURES + [TARGET]).copy()
print("Usable rows:", len(df))

print("\nCreating chronological split...")
train = df[df["year"] <= 2023].copy()
validation = df[df["year"] == 2024].copy()
test = df[df["year"] == 2025].copy()

print("TRAIN:", train.shape)
print("VALIDATION:", validation.shape)
print("TEST:", test.shape)

SAMPLE_SIZE = 750_000
if len(train) > SAMPLE_SIZE:
    train = train.sample(n=SAMPLE_SIZE, random_state=42)

X_train = train[FEATURES]
y_train = train[TARGET]
X_validation = validation[FEATURES]
y_validation = validation[TARGET]
X_test = test[FEATURES]
y_test = test[TARGET]

print("\nTraining rows used:", len(X_train))
print("Feature count:", len(FEATURES))

print("\n" + "=" * 60)
print("TRAINING MODEL 2...")
print("=" * 60)

model = RandomForestRegressor(
    n_estimators=20,
    max_depth=20,
    max_samples=0.8,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print("\nMODEL TRAINING COMPLETE")

print("\nPredicting 2024 validation data...")
validation_pred = model.predict(X_validation)

mae = mean_absolute_error(y_validation, validation_pred)
rmse = mean_squared_error(y_validation, validation_pred) ** 0.5
r2 = r2_score(y_validation, validation_pred)

print("\n" + "=" * 60)
print("MODEL 2 RESULTS - 2024")
print("=" * 60)
print("MAE :", mae)
print("RMSE:", rmse)
print("R2  :", r2)

print("\n" + "=" * 60)
print("MODEL 1 vs MODEL 2")
print("=" * 60)
print("MAE difference :", mae - BASELINE_MAE)
print("RMSE difference:", rmse - BASELINE_RMSE)
print("R2 difference  :", r2 - BASELINE_R2)

print("\n" + "=" * 60)
print("FEATURE IMPORTANCE")
print("=" * 60)

importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)

print(importance.to_string(index=False))

print("\n" + "=" * 60)
print("2025 TEST EVALUATION")
print("=" * 60)

test_pred = model.predict(X_test)

test_mae = mean_absolute_error(y_test, test_pred)
test_rmse = mean_squared_error(y_test, test_pred) ** 0.5
test_r2 = r2_score(y_test, test_pred)

print("TEST MAE :", test_mae)
print("TEST RMSE:", test_rmse)
print("TEST R2  :", test_r2)

print("\n" + "=" * 60)
print("MODEL 2 COMPLETE")
print("=" * 60)
