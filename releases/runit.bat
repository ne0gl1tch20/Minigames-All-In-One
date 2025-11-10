@echo off
title Minigames All-In-One Launcher Runner
color 0A

:: ---------------- Check for Python ----------------
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python is not installed.
    echo Please install Python 3.12 from:
    echo https://www.python.org/downloads/release/python-3120/
    pause
    exit /b
)

:: ---------------- Upgrade pip ----------------
echo Upgrading pip...
python -m ensurepip --upgrade
python -m pip install --upgrade pip

:: ---------------- Install essential libraries ----------------
echo Installing essential libraries...
python -m pip install --upgrade pygame librosa PySide6 numpy

:: ---------------- Navigate to scripts folder ----------------
cd scripts

:: ---------------- Run main.py ----------------
echo Running main.py...
python main.py

pause
