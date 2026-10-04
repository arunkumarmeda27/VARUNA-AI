import cdsapi
from pathlib import Path

OUT = Path("weather_data/raw/era5")
OUT.mkdir(parents=True, exist_ok=True)

client = cdsapi.Client()

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

        "year": "2021",
        "month": "01",

        "day": [
            "01", "02", "03", "04", "05",
            "06", "07", "08", "09", "10",
            "11", "12", "13", "14", "15",
            "16", "17", "18", "19", "20",
            "21", "22", "23", "24", "25",
            "26", "27", "28", "29", "30",
            "31",
        ],

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

    str(OUT / "ERA5_pressure_2021_01.grib"),
)

print("PRESSURE-LEVEL DOWNLOAD COMPLETE")