@echo off
echo Building Simple Bootstrap Launcher...

cd /d "%~dp0\.."

REM Try .venv first, then fallback to _env
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    set PYTHON_EXE=.venv\Scripts\python.exe
    echo Using .venv environment
) else if exist _env\Scripts\activate.bat (
    call _env\Scripts\activate.bat
    set PYTHON_EXE=_env\Scripts\python.exe
    echo Using _env environment
) else (
    echo Error: No virtual environment found (.venv or _env)
    pause
    exit /b 1
)

echo Cleaning build cache...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist

echo Building bootstrap...
%PYTHON_EXE% -m PyInstaller bootstrap\bootstrap.spec --noconfirm --clean

echo Creating launcher package...
if exist launcher_package.zip del launcher_package.zip

echo Getting version from git tag...
for /f "tokens=*" %%i in ('powershell -Command "git tag --list --sort=-version:refname | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' } | Select-Object -First 1"') do set GIT_VERSION=%%i
if "%GIT_VERSION%"=="" (
    echo Warning: No valid git tags found, using default version
    set GIT_VERSION=v1.0.0
)
echo Using version: %GIT_VERSION%

echo Cleaning Python cache files...
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo Stopping any Python processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul

timeout /t 2 /nobreak >nul

mkdir temp_launcher 2>nul

echo Creating temporary virtual environment for dependency bundling...
%PYTHON_EXE% -m venv temp_launcher\_runtime_env

echo Installing dependencies in virtual environment...
temp_launcher\_runtime_env\Scripts\python.exe -m pip install --upgrade pip
temp_launcher\_runtime_env\Scripts\python.exe -m pip install -r requirements.txt

echo Copying application files...
copy app.py temp_launcher\

echo Creating dynamic version.json...
echo { > temp_launcher\version.json
echo   "version": "%GIT_VERSION:~1%", >> temp_launcher\version.json
echo   "release_date": "%DATE%", >> temp_launcher\version.json
echo   "description": "FFT Minecraft Launcher with Bootstrap System" >> temp_launcher\version.json
echo } >> temp_launcher\version.json

echo Copying source files (excluding cache)...
robocopy src temp_launcher\src /E /XD __pycache__ .pytest_cache /XF *.pyc *.pyo *.pyd

echo Copying bundled Python runtime and dependencies...
robocopy temp_launcher\_runtime_env temp_launcher\_runtime_env /E /XD __pycache__ .pytest_cache /XF *.pyc *.pyo *.pyd

echo Creating launcher startup script...
echo @echo off > temp_launcher\launch.bat
echo cd /d "%%~dp0" >> temp_launcher\launch.bat
echo _runtime_env\Scripts\python.exe app.py >> temp_launcher\launch.bat

echo Creating zip package...
powershell -Command "Start-Sleep -Seconds 1; Compress-Archive -Path './temp_launcher/*' -DestinationPath './launcher_package.zip' -Force"

echo Cleaning up...
timeout /t 1 /nobreak >nul
rmdir /S /Q temp_launcher

echo Build complete!
echo Bootstrap: dist\FFTMinecraftLauncher.exe  
echo Launcher Package: launcher_package.zip
