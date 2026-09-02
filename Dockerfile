# VARUNA-AI: Operational & Scientific Evaluation Dockerfile
# Base Image: Official Python 3.12 Slim (Debian Bookworm)
FROM python:3.12-slim

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app \
    PORT=8000


# Set working directory
WORKDIR /app

# Install minimal system dependencies:
# - libgomp1: required by XGBoost for OpenMP multiprocessing
# - curl: required for Docker container healthcheck
# - sqlite3: database inspection tool
# - dos2unix: fixes Windows CRLF line ending issues in shell scripts
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    sqlite3 \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and packaging tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Layer-cached Python dependencies installation
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire application codebase into image
COPY . /app/

# Normalize line endings and ensure entrypoint execution permissions
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose Django operational server port
EXPOSE 8000

# Container Healthcheck verifying the REST API is live
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

# Container initialization entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command: launch Django development/evaluation server on 0.0.0.0:8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

