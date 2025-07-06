@echo off
echo Building FFT Minecraft Launcher (Bootstrap Pattern)...

echo.
echo Activating virtual environment...
call _env\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment
    exit /b 1
)

echo.
echo Building bootstrap executable...
_env\Scripts\python.exe -m PyInstaller bootstrap.spec --noconfirm
if errorlevel 1 (
    echo Bootstrap build failed
    exit /b 1
)

echo.
echo Building launcher package...
_env\Scripts\python.exe -m PyInstaller launcher_package.spec --noconfirm
if errorlevel 1 (
    echo Launcher package build failed
    exit /b 1
)

echo.
echo Copying additional files...
if exist dist\launcher_package\ (
    copy app.py dist\launcher_package\ >nul 2>&1
    copy version.json dist\launcher_package\ >nul 2>&1
    if exist launcher_config.json copy launcher_config.json dist\launcher_package\ >nul 2>&1
)

echo.
echo Creating launcher package zip...
if exist launcher_package.zip del launcher_package.zip >nul 2>&1
powershell -Command "try { Compress-Archive -Path './dist/launcher_package/*' -DestinationPath './launcher_package.zip' -Force; Write-Host 'Zip created successfully' } catch { Write-Host 'Zip creation failed:' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo Zip creation failed
    exit /b 1
)

echo.
echo Build complete!
echo Bootstrap: dist\FFTMinecraftLauncher.exe
echo Launcher Package: launcher_package.zip
