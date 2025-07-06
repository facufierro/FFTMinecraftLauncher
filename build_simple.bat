@echo off
echo Building FFT Minecraft Launcher (Simple Build)...

echo.
echo Activating virtual environment...
call _env\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment
    exit /b 1
)

echo.
echo Building main launcher...
_env\Scripts\python.exe -m PyInstaller FFTMinecraftLauncher.spec --noconfirm
if errorlevel 1 (
    echo Build failed
    exit /b 1
)

echo.
echo Build complete!
echo Launcher: dist\FFTMinecraftLauncher.exe
