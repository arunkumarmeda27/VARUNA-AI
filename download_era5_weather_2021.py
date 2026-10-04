import cdsapi
from pathlib import Path

client = cdsapi.Client()

out_dir = Path("weather_data/raw/era5")
out_dir.mkdir(parents=True, exist_ok=True)

months = [
    "01", "02", "03", "04", "05", "06",
    "07", "08", "09", "10", "11", "12"
]

days = [
    "01", "02", "03", "04", "05",
    "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15",
    "16", "17", "18", "19", "20",
    "21", "22", "23", "24", "25",
    "26", "27", "28", "29", "30", "31"
]

for month in months:

    output = out_dir / f"ERA5_weather_daily_2021_{month}.nc"

    if output.exists():
        print(f"SKIPPING {month}: already exists")
        continue

    print("=" * 60)
    print(f"DOWNLOADING ERA5 WEATHER: 2021-{month}")
    print("=" * 60)

    client.retrieve(
        "derived-era5-single-levels-daily-statistics",
        {
            "product_type": "reanalysis",

            "variable": [
                "2m_temperature",
                "2m_dewpoint_temperature",
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
                "mean_sea_level_pressure",
            ],

            "year": "2021",
            "month": month,
            "day": days,

            "daily_statistic": "daily_mean",

            "time_zone": "UTC+00:00",
            "frequency": "6_hourly",

            "area": [35, 65, 5, 100],

            "format": "netcdf",
        },
        str(output),
    )

    print(f"COMPLETED: {output}")

print("=" * 60)
print("ALL 2021 MONTHS COMPLETE")
print("=" * 60)