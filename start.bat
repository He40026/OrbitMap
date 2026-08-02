@echo off
title Orbit Visualizer
cd /d "%~dp0"
echo Starting Orbit Visualizer...
echo.
REM Map tiles are optional. Without them the app uses an offline placeholder map.
if not exist "static\tiles\esri\0\0\0.png" (
    echo Note: real Esri satellite tiles not found - placeholder map will be used.
    echo To download real tiles once (needs internet), run:
    echo   python scripts\download_esri_tiles.py
    echo.
)
echo Starting server...
python app.py
pause
