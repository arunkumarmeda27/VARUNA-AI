import cdsapi
import os


# VARUNA-AI M1: Real ERA5 monsoon data download

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "raw"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "era5_monsoon_2024.grib"
)


os.makedirs(OUTPUT_DIR, exist_ok=True)

client = cdsapi.Client()

dataset = "reanalysis-era5-single-levels"

request = {
    "product_type": ["reanalysis"],
    "variable": ["total_precipitation"],
    "year": ["2024"],
    "month": [
        "06",
        "07",
        "08",
        "09"
    ],
    "day": [
        "01", "02", "03", "04", "05", "06", "07",
        "08", "09", "10", "11", "12", "13", "14",
        "15", "16", "17", "18", "19", "20", "21",
        "22", "23", "24", "25", "26", "27", "28",
        "29", "30", "31"
    ],
    "time": [
        "00:00",
        "01:00",
        "02:00",
        "03:00",
        "04:00",
        "05:00",
        "06:00",
        "07:00",
        "08:00",
        "09:00",
        "10:00",
        "11:00",
        "12:00",
        "13:00",
        "14:00",
        "15:00",
        "16:00",
        "17:00",
        "18:00",
        "19:00",
        "20:00",
        "21:00",
        "22:00",
        "23:00"
    ],
    "area": [
        35, 65, 5, 100
    ],
    "data_format": "grib",
    "download_format": "unarchived"
}

print("Starting ERA5 monsoon download...")
print("Period: June-September 2024")
print("Variable: Total precipitation")
print("Region: India")
print(f"Output: {OUTPUT_FILE}")

client.retrieve(
    dataset,
    request,
    OUTPUT_FILE
)

print()
print("ERA5 monsoon download completed successfully!")
print(f"Saved to: {OUTPUT_FILE}")