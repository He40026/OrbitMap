@echo off
title Orbit Visualizer
cd /d "%~dp0"
echo Starting Orbit Visualizer...
echo.

REM ---- Find Python (python first, then the py launcher) ----
set "PY=python"
where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python not found.
        echo Install Python 3.8+ from https://www.python.org/downloads/
        echo and make sure "Add python.exe to PATH" is checked.
        pause
        exit /b 1
    )
    set "PY=py -3"
)

REM ---- Install dependencies if missing ----
%PY% -c "import flask, numpy, PIL" >nul 2>nul
if errorlevel 1 (
    echo First run: installing dependencies from requirements.txt...
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies. Please run manually:
        echo   %PY% -m pip install -r requirements.txt
        pause
        exit /b 1
    )
)

REM ---- Map tiles are optional ----
if not exist "static\tiles\esri\0\0\0.png" (
    echo Note: real Esri satellite tiles not found - placeholder map will be used.
    echo To download real tiles once [needs internet], run:
    echo   %PY% scripts\download_esri_tiles.py
    echo.
)

echo Starting server...
%PY% app.py
pause
