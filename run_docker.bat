@echo off
echo =====================================================================
echo           VARUNA-AI: One-Click Docker Container Runner
echo       Smart India Hackathon 2026 ^| Meteorological AI Platform
echo =====================================================================
echo.
echo [1/2] Building and launching VARUNA-AI container...
docker compose up --build -d
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Falling back to standard docker run...
    docker build -t varuna-ai .
    docker run -d --name varuna_ai_container -p 8000:8000 varuna-ai
)
echo.
echo [2/2] Container is running!
echo Platform Dashboard: http://localhost:8000
echo Operational Login:  http://localhost:8000/login/
echo Health Diagnostic:  http://localhost:8000/api/v1/health/
echo.
echo To view live logs: docker compose logs -f
echo To stop:          docker compose down
echo =====================================================================
pause
