@echo off
echo Building FFT Minecraft Launcher and Updater...

echo.
echo Activating virtual environment...
call _env\Scripts\activate.bat

echo.
echo Building main launcher...
_env\Scripts\python.exe -m PyInstaller FFTMinecraftLauncher.spec

echo.
echo Building updater...
_env\Scripts\python.exe -m PyInstaller updater.spec

echo.
echo Copying updater to dist folder...
copy dist\FFTLauncherUpdater.exe dist\FFTMinecraftLauncher\FFTLauncherUpdater.exe

echo.
echo Build complete!
echo Main launcher: dist\FFTMinecraftLauncher\FFTMinecraftLauncher.exe
echo Updater: dist\FFTMinecraftLauncher\FFTLauncherUpdater.exe
