import pandas as pd

FILE = r".\weather_data\processed\real_ml\master_real_weather_2021_2025.parquet"

print("=" * 60)
print("VARUNA-AI WEATHER MERGE VALIDATION")
print("=" * 60)

df = pd.read_parquet(FILE)

print("\nROWS:", len(df))
print("COLUMNS:", len(df.columns))

weather_features = [
    "temperature_c",
    "dewpoint_c",
    "relative_humidity",
    "u10",
    "v10",
    "wind_speed"
]

print("\nWEATHER FEATURE CHECK")
print("-" * 60)

for col in weather_features:
    print(f"\n{col}")
    print("  Missing:", df[col].isna().sum())
    print("  Min    :", df[col].min())
    print("  Mean   :", df[col].mean())
    print("  Max    :", df[col].max())

print("\nDUPLICATE CHECK")
print("-" * 60)

duplicates = df.duplicated(
    subset=["time", "latitude", "longitude"]
).sum()

print("Duplicate time/location rows:", duplicates)

print("\nDATE RANGE")
print("-" * 60)

print("Start:", df["time"].min())
print("End  :", df["time"].max())

print("\nFINAL WEATHER FEATURES")
print("-" * 60)

for col in weather_features:
    print("-", col)

print("\n" + "=" * 60)
print("VALIDATION COMPLETE")
print("=" * 60)