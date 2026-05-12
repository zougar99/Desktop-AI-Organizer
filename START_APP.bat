@echo off
title Desktop AI Organizer
cd /d "%~dp0"

echo ============================================
echo     Desktop AI Organizer - Starting...
echo ============================================
echo.

REM Check if Python is installed
py -3 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3 is not installed or not in PATH!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Install dependencies if needed
echo [*] Checking dependencies...
py -3 -m pip install customtkinter Pillow matplotlib --quiet 2>nul

echo [*] Launching application...
echo.
py -3 app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application crashed. Check the error above.
    pause
)
