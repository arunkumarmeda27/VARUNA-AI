import cdsapi
from pathlib import Path
import calendar
import time

OUT = Path("weather_data/raw/era5/pressure")
OUT.mkdir(parents=True, exist_ok=True)

client = cdsapi.Client()

for year in range(2021, 2026):

    for month in range(1, 13):

        output = OUT / f"ERA5_pressure_{year}_{month:02d}.grib"

        if output.exists() and output.stat().st_size > 1_000_000:
            print(f"SKIPPING {year}-{month:02d} — already exists")
            continue

        days = calendar.monthrange(year, month)[1]

        day_list = [
            f"{day:02d}"
            for day in range(1, days + 1)
        ]

        print()
        print("=" * 60)
        print(f"DOWNLOADING PRESSURE DATA: {year}-{month:02d}")
        print("=" * 60)

        client.retrieve(
            "reanalysis-era5-pressure-levels",
            {
                "product_type": "reanalysis",

                "variable": [
                    "u_component_of_wind",
                    "v_component_of_wind",
                    "relative_humidity",
                ],

                "pressure_level": [
                    "200",
                    "700",
                    "850",
                ],

                "year": str(year),
                "month": f"{month:02d}",
                "day": day_list,

                "time": [
                    "00:00",
                    "06:00",
                    "12:00",
                    "18:00",
                ],

                "area": [
                    35,
                    65,
                    5,
                    100,
                ],

                "format": "grib",
            },

            str(output),
        )

        print(f"COMPLETED: {output}")

        time.sleep(2)

print()
print("=" * 60)
print("ALL PRESSURE-LEVEL DATA DOWNLOADED")
print("=" * 60)