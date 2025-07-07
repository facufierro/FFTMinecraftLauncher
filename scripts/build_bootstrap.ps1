#!/usr/bin/env pwsh
# FFT Minecraft Launcher Build Script
# Builds minimal bootstrap executable and creates self-contained launcher package

Write-Host "Building FFT Minecraft Launcher..." -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "New Minimal Bootstrap Architecture" -ForegroundColor Cyan
Write-Host "- Bootstrap: Minimal, stable, downloads & launches" -ForegroundColor Cyan
Write-Host "- Launcher: Full application, auto-updateable" -ForegroundColor Cyan
Write-Host ""

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

# Get version from git tag first
$gitVersion = git tag --list --sort=-version:refname | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' } | Select-Object -First 1
if (-not $gitVersion) {
    Write-Host "Warning: No valid git tags found, using default version" -ForegroundColor Yellow
    $gitVersion = "v1.0.0"
}
Write-Host "Using version: $gitVersion" -ForegroundColor Cyan

# Build bootstrap
Write-Host "Building minimal bootstrap executable..." -ForegroundColor Yellow
Write-Host "The bootstrap will never need rebuilding for app changes!" -ForegroundColor Cyan
& $pythonExe -m PyInstaller bootstrap\bootstrap.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Bootstrap build failed" -ForegroundColor Red
    exit 1
}

# Create bootstrap version file
Write-Host "Creating bootstrap version file..." -ForegroundColor Yellow
$versionNum = $gitVersion.TrimStart('v')
$releaseDate = Get-Date -Format "yyyy-MM-dd"
$bootstrapVersionInfo = @{
    version = $versionNum
    release_date = $releaseDate
    description = "Minimal Bootstrap for FFT Minecraft Launcher"
    architecture = "minimal-stable"
}
$bootstrapJsonContent = $bootstrapVersionInfo | ConvertTo-Json
[System.IO.File]::WriteAllText("bootstrap_version.json", $bootstrapJsonContent, [System.Text.UTF8Encoding]::new($false))
Write-Host "Bootstrap version: $versionNum (minimal-stable)" -ForegroundColor Cyan

# Create launcher package...
Write-Host "Creating self-contained launcher package..." -ForegroundColor Yellow
Write-Host "This package will be downloaded and updated by the bootstrap" -ForegroundColor Cyan
if (Test-Path "launcher_package.zip") { Remove-Item "launcher_package.zip" }

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

# Copy application files (launcher application, not bootstrap)
Write-Host "Copying launcher application files..." -ForegroundColor Yellow
Copy-Item "app.py" "temp_launcher\"

# Create version.json for launcher package
Write-Host "Creating launcher package version.json..." -ForegroundColor Yellow
$versionNum = $gitVersion.TrimStart('v')
$releaseDate = Get-Date -Format "yyyy-MM-dd"
$versionInfo = @{
    version = $versionNum
    release_date = $releaseDate
    description = "Self-contained FFT Minecraft Launcher Application"
    package_type = "launcher_application"
    bootstrap_compatible = $true
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
Write-Host "MINIMAL BOOTSTRAP ARCHITECTURE" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Bootstrap executable: dist\FFTMinecraftLauncher.exe" -ForegroundColor Cyan
Write-Host "Bootstrap version: bootstrap_version.json" -ForegroundColor Cyan
Write-Host "Launcher package: launcher_package.zip" -ForegroundColor Cyan
Write-Host ""
Write-Host "DEPLOYMENT:" -ForegroundColor Yellow
Write-Host "1. Upload both files to GitHub releases" -ForegroundColor White
Write-Host "2. Bootstrap downloads launcher_package.zip automatically" -ForegroundColor White
Write-Host "3. Launcher can update bootstrap.exe when needed" -ForegroundColor White
Write-Host ""
Write-Host "The bootstrap will remain stable across all future updates!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
