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
echo Copying app files to launcher package...
copy app.py dist\launcher_package\
copy version.json dist\launcher_package\

echo.
echo Creating launcher package zip...
if exist launcher_package.zip del launcher_package.zip
powershell -Command "Compress-Archive -Path './dist/launcher_package/*' -DestinationPath './launcher_package.zip' -Force"

echo.
echo Build complete!
echo Bootstrap: dist\FFTMinecraftLauncher.exe
echo Launcher Package: launcher_package.zip
echo.
echo To distribute:
echo 1. Give users: FFTMinecraftLauncher.exe (bootstrap)
echo 2. Upload to GitHub: launcher_package.zip (gets auto-downloaded by bootstrap)

pause
