#!/usr/bin/env pwsh
# FFT Minecraft Launcher Build Script
# Builds bootstrap executable and creates bundled launcher package

Write-Host "Building FFT Minecraft Launcher..." -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Change to project root
Set-Location (Split-Path $PSScriptRoot -Parent)

# Find Python executable
$pythonExe = $null
if (Test-Path ".venv\Scripts\python.exe") {
    $pythonExe = ".venv\Scripts\python.exe"
    Write-Host "Using .venv environment" -ForegroundColor Cyan
} elseif (Test-Path "_env\Scripts\python.exe") {
    $pythonExe = "_env\Scripts\python.exe"
    Write-Host "Using _env environment" -ForegroundColor Cyan
} else {
    Write-Host "Error: No virtual environment found (.venv or _env)" -ForegroundColor Red
    exit 1
}

# Clean build cache
Write-Host "Cleaning build cache..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# Build bootstrap
Write-Host "Building bootstrap executable..." -ForegroundColor Yellow
& $pythonExe -m PyInstaller bootstrap\bootstrap.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Bootstrap build failed" -ForegroundColor Red
    exit 1
}

# Clean up old package
Write-Host "Creating launcher package..." -ForegroundColor Yellow
if (Test-Path "launcher_package.zip") { Remove-Item "launcher_package.zip" }

# Get version from git tag
$gitVersion = git tag --list --sort=-version:refname | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' } | Select-Object -First 1
if (-not $gitVersion) {
    Write-Host "Warning: No valid git tags found, using default version" -ForegroundColor Yellow
    $gitVersion = "v1.0.0"
}
Write-Host "Using version: $gitVersion" -ForegroundColor Cyan

# Clean Python cache files
Write-Host "Cleaning Python cache files..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Name "__pycache__" | ForEach-Object { 
    if (Test-Path $_) { Remove-Item -Recurse -Force $_ }
}

# Stop any Python processes
Write-Host "Stopping any Python processes..." -ForegroundColor Yellow
Get-Process -Name "python*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "pythonw*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Wait longer for processes to fully terminate
Start-Sleep -Seconds 5

# Force garbage collection to release file handles
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()

# Create temp directory
if (Test-Path "temp_launcher") { 
    # Force remove with retry logic
    for ($i = 0; $i -lt 3; $i++) {
        try {
            Remove-Item -Recurse -Force "temp_launcher" -ErrorAction Stop
            break
        } catch {
            Write-Host "Retrying cleanup... ($($i+1)/3)" -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        }
    }
}
New-Item -ItemType Directory -Name "temp_launcher" | Out-Null

# Create bundled virtual environment
Write-Host "Creating bundled virtual environment..." -ForegroundColor Yellow
& $pythonExe -m venv temp_launcher\_runtime_env
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies in bundled environment..." -ForegroundColor Yellow
& temp_launcher\_runtime_env\Scripts\python.exe -m pip install --upgrade pip
& temp_launcher\_runtime_env\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Copy application files
Write-Host "Copying application files..." -ForegroundColor Yellow
Copy-Item "app.py" "temp_launcher\"

# Create version.json
Write-Host "Creating version.json..." -ForegroundColor Yellow
$versionNum = $gitVersion.TrimStart('v')
$releaseDate = Get-Date -Format "yyyy-MM-dd"
$versionInfo = @{
    version = $versionNum
    release_date = $releaseDate
    description = "FFT Minecraft Launcher with Bootstrap System"
}
# Create JSON without BOM to avoid parsing issues
$jsonContent = $versionInfo | ConvertTo-Json
[System.IO.File]::WriteAllText("temp_launcher\version.json", $jsonContent, [System.Text.UTF8Encoding]::new($false))

# Copy source files
Write-Host "Copying source files..." -ForegroundColor Yellow
$robocopyResult = robocopy src temp_launcher\src /E /XD __pycache__ .pytest_cache /XF *.pyc *.pyo *.pyd
if ($LASTEXITCODE -gt 7) {
    Write-Host "Warning: Some files may not have copied correctly" -ForegroundColor Yellow
}

# Create launcher startup script
Write-Host "Creating launcher startup script..." -ForegroundColor Yellow
@"
@echo off
cd /d "%~dp0"
_runtime_env\Scripts\python.exe app.py
"@ | Out-File "temp_launcher\launch.bat" -Encoding ASCII

# Ensure all file handles are released before zipping
Write-Host "Finalizing files..." -ForegroundColor Yellow
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()
Start-Sleep -Seconds 2

# Create zip package with retry logic
Write-Host "Creating zip package..." -ForegroundColor Yellow
$maxRetries = 3
for ($retry = 0; $retry -lt $maxRetries; $retry++) {
    try {
        if (Test-Path "launcher_package.zip") { Remove-Item "launcher_package.zip" -Force }
        Compress-Archive -Path './temp_launcher/*' -DestinationPath './launcher_package.zip' -Force -ErrorAction Stop
        Write-Host "Package created successfully!" -ForegroundColor Green
        break
    } catch {
        Write-Host "Retry $($retry + 1)/$maxRetries - Waiting for file handles to release..." -ForegroundColor Yellow
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
        Start-Sleep -Seconds 3
        if ($retry -eq ($maxRetries - 1)) {
            Write-Host "Error: Failed to create package after $maxRetries attempts" -ForegroundColor Red
            Write-Host $_.Exception.Message -ForegroundColor Red
            exit 1
        }
    }
}

# Clean up
Write-Host "Cleaning up..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
# Force cleanup with retry logic
for ($i = 0; $i -lt 3; $i++) {
    try {
        if (Test-Path "temp_launcher") {
            Remove-Item -Recurse -Force "temp_launcher" -ErrorAction Stop
        }
        break
    } catch {
        Write-Host "Cleanup retry $($i+1)/3..." -ForegroundColor Yellow
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
        Start-Sleep -Seconds 2
    }
}

# Success message
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "BUILD COMPLETE!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Bootstrap executable: dist\FFTMinecraftLauncher.exe" -ForegroundColor Cyan
Write-Host "Launcher package: launcher_package.zip" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now use the Release button to create a GitHub release" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Green
