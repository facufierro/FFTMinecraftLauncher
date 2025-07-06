@echo off
echo Building FFT Minecraft Launcher and Updater...

echo.
echo Building main launcher...
pyinstaller FFTMinecraftLauncher.spec

echo.
echo Building updater...
pyinstaller updater.spec

echo.
echo Copying updater to dist folder...
copy dist\FFTLauncherUpdater.exe dist\FFTMinecraftLauncher\FFTLauncherUpdater.exe

echo.
echo Build complete!
echo Main launcher: dist\FFTMinecraftLauncher\FFTMinecraftLauncher.exe
echo Updater: dist\FFTMinecraftLauncher\FFTLauncherUpdater.exe

pause
