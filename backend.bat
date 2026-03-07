@echo off
title CiteAgent - Backend Server
color 0A

echo ============================================
echo   CiteAgent Backend  ^|  FastAPI + Uvicorn
echo ============================================
echo.

cd /d "%~dp0backend"

if not exist venv (
    echo [1/3] Creating Python virtual environment...
    python -m venv venv
)

echo.
echo [2/3] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ERROR: pip install failed. Make sure Python is installed and in PATH.
    pause
    exit /b 1
)

echo.
echo [3/3] Starting backend server on http://localhost:8000 ...
echo       API docs: http://localhost:8000/docs
echo.
python main.py

echo.
echo  Server stopped.
pause
