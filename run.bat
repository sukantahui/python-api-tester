@echo off
setlocal
cd /d "%~dp0"

echo [PyRestForge] Starting Desktop API Testing Studio...

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" src\main.py %*
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        python src\main.py %*
    ) else (
        echo [ERROR] Python not found. Please run setup.bat first to initialize virtual environment.
        pause
    )
)
