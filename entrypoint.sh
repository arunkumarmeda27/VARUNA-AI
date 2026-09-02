#!/bin/bash
set -e

echo "================================================================================"
echo "                   VARUNA-AI: STARTING CONTAINER INITIALIZATION                 "
echo "                 Smart India Hackathon 2026 | Problem: SIH26080                 "
echo "================================================================================"

# Fast boot flag support (FAST_BOOT=1 or SKIP_TRAINING=1)
if [ "${FAST_BOOT}" = "1" ] || [ "${SKIP_TRAINING}" = "1" ]; then
    echo "[INFO] FAST_BOOT enabled: Bypassing offline training checks."
else
    # 1. Generate master dataset if not already present
    if [ ! -f "weather_data/processed/train_v1.0.0.parquet" ]; then
        echo "[1/4] Generating validated meteorological master datasets (2018-2024)..."
        python -m weather_data.master_dataset_builder
    else
        echo "[1/4] Master datasets verified."
    fi

    # 2. Train weather regime classifier if model artifact missing
    if [ ! -f "regimes/models/regime_xgb_artifact.joblib" ]; then
        echo "[2/4] Training synoptic weather regime classifier..."
        python -m regimes.evaluation.evaluate_regimes
    else
        echo "[2/4] Regime classifier artifact verified."
    fi

    # 3. Train rainfall correction model ladder if missing
    if [ ! -f "correction/artifacts/level3_regime_aware_xgb.joblib" ]; then
        echo "[3/4] Training rainfall post-processing model ladder (Levels 0-3)..."
        python -m correction.evaluation.evaluate_correction
    else
        echo "[3/4] Correction model ladder artifacts verified."
    fi

    # 4. Verify pipeline benchmarks
    if [ ! -f "verification/verification_matrix.json" ]; then
        echo "[4/4] Running scientific verification suite..."
        python -m verification.verify
    else
        echo "[4/4] Verification benchmarks verified."
    fi
fi

# 5. Run Django database migrations
echo "[+] Applying database migrations..."
python manage.py makemigrations backend --noinput 2>/dev/null || true
python manage.py migrate --noinput

echo "================================================================================"
echo "       VARUNA-AI INITIALIZATION COMPLETE - LAUNCHING OPERATIONAL SERVER         "
echo "               Accessible at: http://localhost:8000                             "
echo "================================================================================"

# Execute the passed command (default: runserver or custom e.g. pytest, gunicorn)
exec "$@"

