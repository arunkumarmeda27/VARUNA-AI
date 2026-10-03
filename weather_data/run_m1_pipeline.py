import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

STEPS = [
    ("Process ERA5 weather daily", "process_era5_weather_daily.py"),
    ("Build real ML dataset", "weather_data/build_real_ml_dataset.py"),
    ("Add rainfall history features", "weather_data/add_rainfall_features.py"),
    ("Merge weather features", "weather_data/merge_weather_features.py"),
    ("Validate weather merge", "weather_data/validate_weather_merge.py"),
    ("Train Model 3", "weather_data/train_model_v3.py"),
    ("Calculate feature importance", "weather_data/feature_importance_v3.py"),
    ("Run M1 real-data backtest", "weather_data/m1_backtest_real_data.py"),
    ("Create ML metadata", "weather_data/create_ml_metadata.py"),
    ("Create M1 handoff document", "weather_data/create_m1_handoff.py"),
]


def run_step(name, script):
    print("\n" + "=" * 70)
    print(f"M1 PIPELINE STEP: {name}")
    print("=" * 70)

    script_path = BASE_DIR / script

    if not script_path.exists():
        raise FileNotFoundError(
            f"Required script not found: {script_path}"
        )

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=BASE_DIR,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"M1 pipeline stopped because '{script}' failed."
        )

    print(f"\nCOMPLETED: {name}")


def main():
    print("=" * 70)
    print("VARUNA-AI M1 REAL-DATA PIPELINE")
    print("MEMBER 1 - DATA FOUNDATION / DATA ENGINEERING")
    print("=" * 70)

    for name, script in STEPS:
        run_step(name, script)

    print("\n" + "=" * 70)
    print("M1 PIPELINE COMPLETE")
    print("=" * 70)
    print("All Member 1 real-data processing stages completed successfully.")


if __name__ == "__main__":
    main()