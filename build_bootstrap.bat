@echo off
echo Building Simple Bootstrap Launcher...

call _env\Scripts\activate.bat

echo Cleaning build cache...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist

echo Building bootstrap...
_env\Scripts\python.exe -m PyInstaller bootstrap.spec --noconfirm --clean

echo Creating launcher package...
if exist launcher_package.zip del launcher_package.zip
mkdir temp_launcher 2>nul
copy app.py temp_launcher\
copy version.json temp_launcher\
xcopy /E /I src temp_launcher\src\

powershell -Command "Compress-Archive -Path './temp_launcher/*' -DestinationPath './launcher_package.zip' -Force"
rmdir /S /Q temp_launcher

echo Build complete!
echo Bootstrap: dist\FFTMinecraftLauncher.exe  
echo Launcher Package: launcher_package.zip
