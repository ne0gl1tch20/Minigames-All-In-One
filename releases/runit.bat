@echo off
title Minigames All-In-One Launcher Runner
color 0A

:: ---------------- Check for Python ----------------
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python is not installed. Downloading Python 3.12...

    :: Download Python 3.12 installer (Windows x64) to temp folder
    set "PYTHON_INSTALLER=%TEMP%\python-3.12.0-amd64.exe"
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe -OutFile '%PYTHON_INSTALLER%'"

    :: Install silently with PATH added
    echo Installing Python 3.12 silently...
    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

    :: Wait a few seconds to ensure PATH is updated
    timeout /t 5 >nul

    :: Verify installation
    python --version >nul 2>&1
    IF ERRORLEVEL 1 (
        echo Python installation failed. Please install manually:
        echo https://www.python.org/downloads/release/python-3120/
        pause
        exit /b
    )
)

:: ---------------- Upgrade pip ----------------
echo Upgrading pip...
python -m ensurepip --upgrade
python -m pip install --upgrade pip

:: ---------------- Install essential libraries ----------------
echo Installing essential libraries...
python -m pip install --upgrade pygame librosa PySide6 numpy pycryptodome

:: ---------------- Run main.py ----------------
echo Running main.py...
python main.py

pause
