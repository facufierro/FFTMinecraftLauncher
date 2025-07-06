@echo off
echo Building Simple Bootstrap Launcher...

echo.
echo Activating virtual environment...
call _env\Scripts\activate.bat

echo.
echo Building bootstrap...
_env\Scripts\python.exe -m PyInstaller simple_bootstrap.spec --noconfirm

echo.
echo Creating launcher package (as zip, not exe)...
if exist launcher_package.zip del launcher_package.zip
mkdir temp_launcher 2>nul
copy app.py temp_launcher\
copy version.json temp_launcher\
xcopy /E /I src temp_launcher\src\
if exist launcher_config.json copy launcher_config.json temp_launcher\

powershell -Command "Compress-Archive -Path './temp_launcher/*' -DestinationPath './launcher_package.zip' -Force"
rmdir /S /Q temp_launcher

echo.
echo Build complete!
echo Bootstrap: dist\FFTMinecraftLauncher.exe
echo Launcher Package: launcher_package.zip
echo.
echo Users download: FFTMinecraftLauncher.exe
echo GitHub releases: launcher_package.zip (auto-downloaded by bootstrap)
