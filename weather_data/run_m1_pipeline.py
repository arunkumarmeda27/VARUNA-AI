import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

STEPS = [
    ("Build aligned IMD and rainfall-error inputs from real source files", "weather_data/ingestion/build_real_imd_observations.py"),
    ("Build the real IMD/ERA5 ML dataset", "weather_data/build_real_ml_dataset.py"),
    ("Create lagged ERA5 rainfall features", "weather_data/add_rainfall_features.py"),
    ("Merge real ERA5 weather features", "weather_data/merge_weather_features.py"),
    ("Validate merged real weather dataset", "weather_data/validate_weather_merge.py"),
    ("Calculate real-data baseline backtest", "weather_data/m1_backtest_real_data.py"),
    ("Evaluate available model ladder on held-out real data", "weather_data/real_data_model_ladder_backtest.py"),
    ("Train and evaluate Model 3 on real processed data", "weather_data/train_model_v3.py"),
    ("Refresh real dataset metadata", "weather_data/create_ml_metadata.py"),
]

CI_SCRIPTS = [
    "weather_data/ingestion/build_real_imd_observations.py",
    "weather_data/real_data_model_ladder_backtest.py",
    "process_era5_weather_daily.py",
    "weather_data/build_real_ml_dataset.py",
    "weather_data/add_rainfall_features.py",
    "weather_data/merge_weather_features.py",
    "weather_data/validate_weather_merge.py",
    "weather_data/train_model_v3.py",
    "weather_data/feature_importance_v3.py",
    "weather_data/m1_backtest_real_data.py",
    "weather_data/create_ml_metadata.py",
    "weather_data/create_m1_handoff.py",
]

REAL_DATA_INPUTS = [
    f"weather_data/raw/imd_rainfall/RF25_ind{year}_rfp25.nc"
    for year in range(2021, 2026)
] + [
    "weather_data/raw/era5/ERA5_daily_tp_2021_2025_aligned.nc",
    "weather_data/processed/era5/ERA5_weather_daily_2021_2025.nc",
]


def check_scripts():
    print("=" * 70)
    print("VARUNA-AI M1 CI ORCHESTRATION CHECK")
    print("=" * 70)

    missing = []

    for script in CI_SCRIPTS:
        path = BASE_DIR / script

        if path.exists():
            print(f"[OK] {script}")
        else:
            print(f"[MISSING] {script}")
            missing.append(script)

    if missing:
        raise FileNotFoundError(
            "Missing required M1 scripts:\n" + "\n".join(missing)
        )

    print("\nAll M1 pipeline scripts are present.")


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


def run_local_pipeline():
    print("=" * 70)
    print("VARUNA-AI M1 REAL-DATA PIPELINE")
    print("REAL-DATA MODEL TRAINING AND EVALUATION")
    print("=" * 70)

    for name, script in STEPS:
        run_step(name, script)

    print("\n" + "=" * 70)
    print("M1 PIPELINE COMPLETE")
    print("=" * 70)
    print("Real-data model training and evaluation completed successfully.")


def run_ci_check():
    check_scripts()
    missing_data = [
        path for path in REAL_DATA_INPUTS if not (BASE_DIR / path).is_file()
    ]

    output_dir = (
        BASE_DIR
        / "weather_data"
        / "processed"
        / "real_ml"
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    report = output_dir / "M1_CI_ORCHESTRATION_REPORT.txt"

    data_status = (
        "Real-data status: unavailable; missing external inputs:\n"
        + "".join(f"- {path}\n" for path in missing_data)
        if missing_data
        else "Real-data inputs are present, but CI source-check mode did not run training or evaluation.\n"
    )

    report.write_text(
        "VARUNA-AI M1 CI ORCHESTRATION CHECK\n"
        "====================================\n\n"
        "Status: PASSED\n"
        "Mode: GitHub Actions CI validation\n\n"
        "The M1 source scripts were verified successfully.\n"
        "This CI mode does not execute data-dependent ingestion, training, or evaluation.\n"
        f"{data_status}\n"
        "Local real-data execution remains available through:\n"
        "python weather_data/run_m1_pipeline.py\n",
        encoding="utf-8",
    )

    print("\nCI orchestration check PASSED.")
    print(f"Report: {report}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--ci":
        run_ci_check()
    else:
        run_local_pipeline()


if __name__ == "__main__":
    main()