@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo =======================================================
echo   PyRestForge - Environment Setup & Installation
echo =======================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10+ is required but was not found in PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment (.venv)...
if not exist ".venv" (
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)
echo [OK] Virtual environment ready.
echo.

echo [2/3] Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
echo.

echo [3/3] Installing dependencies from requirements.txt...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation encountered errors.
    pause
    exit /b 1
)

echo.
echo =======================================================
echo   [SUCCESS] PyRestForge Setup Completed Successfully!
echo   Run 'run.bat' or 'python src\main.py' to start the app.
echo =======================================================
echo.
pause
