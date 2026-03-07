@echo off
title CiteAgent - Frontend Server
color 0B

echo ============================================
echo   CiteAgent Frontend  ^|  React + Vite
echo ============================================
echo.

cd /d "%~dp0frontend2"

echo [1/2] Installing npm dependencies...
call npm install --legacy-peer-deps
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ERROR: npm install failed. Make sure Node.js is installed and in PATH.
    pause
    exit /b 1
)

echo.
echo [2/2] Starting frontend server...
echo.
call npm run dev

echo.
echo  Server stopped.
pause
