@echo off
echo Building FFT Minecraft Launcher (Bootstrap Pattern)...

echo.
echo Activating virtual environment...
call _env\Scripts\activate.bat

echo.
echo Building bootstrap executable...
_env\Scripts\python.exe -m PyInstaller bootstrap.spec

echo.
echo Building launcher package...
_env\Scripts\python.exe -m PyInstaller launcher_package.spec

echo.
echo Copying additional files to launcher package...
copy app.py dist\launcher_package\ >nul
copy version.json dist\launcher_package\ >nul
if exist launcher_config.json copy launcher_config.json dist\launcher_package\ >nul

echo.
echo Creating launcher package zip...
if exist launcher_package.zip del launcher_package.zip
powershell -Command "Compress-Archive -Path './dist/launcher_package/*' -DestinationPath './launcher_package.zip' -Force"

echo.
echo Build complete!
echo Bootstrap: dist\FFTMinecraftLauncher.exe
echo Launcher Package: launcher_package.zip
echo.
echo To test locally:
echo 1. Copy dist\FFTMinecraftLauncher.exe to a test folder
echo 2. Copy launcher_package.zip contents to test_folder\launcher\
echo 3. Run FFTMinecraftLauncher.exe
