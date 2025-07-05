@echo off
title FFT Minecraft Launcher

echo Installing/updating dependencies...
python -m pip install -r requirements.txt

echo.
echo Starting launcher...
python app.py

if errorlevel 1 (
    echo.
    echo Error occurred. Press any key to exit...
    pause >nul
)
