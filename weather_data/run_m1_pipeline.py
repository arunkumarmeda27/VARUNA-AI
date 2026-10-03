import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

STEPS = [
    ("Train and evaluate Model 3 on real processed data", "weather_data/train_model_v3.py"),
]

CI_SCRIPTS = [
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

    output_dir = (
        BASE_DIR
        / "weather_data"
        / "processed"
        / "real_ml"
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    report = output_dir / "M1_CI_ORCHESTRATION_REPORT.txt"

    report.write_text(
        "VARUNA-AI M1 CI ORCHESTRATION CHECK\n"
        "====================================\n\n"
        "Status: PASSED\n"
        "Mode: GitHub Actions CI validation\n\n"
        "The M1 pipeline scripts were verified successfully.\n"
        "Real IMD and ERA5 datasets are intentionally not stored\n"
        "in the Git repository because weather_data/raw/ is ignored.\n\n"
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