# VARUNA-AI Deployment & Operational Guide

## 1. Local Development Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.10 - 3.14)
- PostgreSQL with PostGIS (optional, SQLite default for standalone testing)

### Installation
```bash
# 1. Clone repository
git clone https://github.com/arunkumarmeda27/VARUNA-AI.git
cd VARUNA-AI

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build Master Datasets and Train Models
python -m weather_data.master_dataset_builder
python -m regimes.evaluation.evaluate_regimes
python -m correction.evaluation.evaluate_correction
python -m verification.verify

# 4. Run Django Migrations
python manage.py makemigrations backend
python manage.py migrate

# 5. Start Operational Forecasting Server
python manage.py runserver 127.0.0.1:8000
```
Open `http://127.0.0.1:8000` in your browser.

---

## 2. Docker Deployment
```bash
docker-compose up --build -d
```

---

## 3. Automated Test Execution
```bash
python -m pytest -v tests/
```
