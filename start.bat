@echo off
title Orbit Visualizer
cd /d "%~dp0"
echo Starting Orbit Visualizer...
echo.

REM Check if Esri tiles exist
set ESRIDIR=static\tiles\esri\0\0
if exist "%ESRIDIR%\0.png" goto :start

echo [1/3] Esri satellite tiles not found.
echo       Run scripts\download_esri_tiles.py to download them (requires internet once).
echo.
set /p choice="Download Esri tiles now? (y/n, default=n): "
if /i "%choice%"=="y" (
    echo.
    echo Downloading tiles - this needs internet access (VPN if outside CN)...
    echo Only needs to run ONCE.
    echo.
    python scripts\download_esri_tiles.py
    if errorlevel 1 (
        echo.
        echo Download failed. Generating placeholder map tiles instead.
        python scripts\generate_tiles.py
    )
) else (
    echo Generating placeholder map tiles...
    python scripts\generate_tiles.py
)
echo.

:start
echo [2/3] Starting server...
python app.py
pause
