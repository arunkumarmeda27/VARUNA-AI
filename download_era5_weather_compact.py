import cdsapi
from pathlib import Path

OUTPUT_DIR = Path("weather_data/raw/era5/weather")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = cdsapi.Client()

for year in ["2021", "2022", "2023", "2024", "2025"]:

    output_file = OUTPUT_DIR / f"ERA5_weather_{year}.nc"

    if output_file.exists():
        print(f"\nSKIPPING {year} - already exists")
        continue

    print("\n" + "=" * 60)
    print(f"DOWNLOADING ERA5 WEATHER: {year}")
    print("=" * 60)

    client.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",

            "variable": [
                "2m_temperature",
                "2m_dewpoint_temperature",
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
            ],

            "year": year,

            "month": [
                "01", "02", "03", "04", "05", "06",
                "07", "08", "09", "10", "11", "12"
            ],

            "day": [
                "01", "02", "03", "04", "05", "06",
                "07", "08", "09", "10",
                "11", "12", "13", "14", "15",
                "16", "17", "18", "19", "20",
                "21", "22", "23", "24", "25",
                "26", "27", "28", "29", "30", "31"
            ],

            "time": [
                "00:00",
                "06:00",
                "12:00",
                "18:00"
            ],

            "area": [
                35.0,
                66.5,
                6.5,
                100.0
            ],

            "format": "netcdf",
        },
        str(output_file)
    )

    print(f"COMPLETED: {output_file}")

print("\n" + "=" * 60)
print("ALL ERA5 WEATHER DOWNLOADS COMPLETE")
print("=" * 60)