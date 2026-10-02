import cdsapi
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

output_file = RAW_DIR / "era5_test_june_2024.grib"

client = cdsapi.Client()

dataset = "reanalysis-era5-single-levels"

request = {
    "product_type": ["reanalysis"],
    "variable": [
        "total_precipitation",
    ],
    "year": ["2024"],
    "month": ["06"],
    "day": ["01"],
    "time": [
        "00:00",
        "06:00",
        "12:00",
        "18:00",
    ],
    "data_format": "grib",
    "download_format": "unarchived",
    "area": [20, 70, 10, 80],
}

print("Starting ERA5 test download...")
print(f"Output: {output_file}")

client.retrieve(
    dataset,
    request,
    str(output_file),
)

print("ERA5 test download completed!")
print(f"File exists: {output_file.exists()}")
print(f"File size: {output_file.stat().st_size / 1024:.2f} KB")