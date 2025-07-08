#!/usr/bin/env pwsh
# FFT Minecraft Launcher Build Script
# Builds standalone FFTLauncher.exe executable

Write-Host "Building FFT Minecraft Launcher..." -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "Standalone Launcher Build" -ForegroundColor Cyan
Write-Host "- Single executable with all dependencies included" -ForegroundColor Cyan
Write-Host "- No bootstrap or self-update complexity" -ForegroundColor Cyan
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
    $gitVersion = "v2.0.0"
}
Write-Host "Using version: $gitVersion" -ForegroundColor Cyan

# Check if PyInstaller is installed
try {
    & $pythonExe -c "import PyInstaller; print('PyInstaller found')"
    Write-Host "PyInstaller found" -ForegroundColor Green
} catch {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    & $pythonExe -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install PyInstaller" -ForegroundColor Red
        exit 1
    }
    Write-Host "PyInstaller installed successfully" -ForegroundColor Green
}

# Build standalone launcher executable
Write-Host "Building standalone FFTLauncher.exe..." -ForegroundColor Yellow
Write-Host "Using spec file: scripts\specs\FFTLauncher.spec" -ForegroundColor Gray

$specFile = "scripts\specs\FFTLauncher.spec"
if (-not (Test-Path $specFile)) {
    Write-Host "Error: Spec file not found at $specFile" -ForegroundColor Red
    exit 1
}

& $pythonExe -m PyInstaller $specFile --noconfirm --clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: PyInstaller build failed" -ForegroundColor Red
    exit 1
}

# Check if executable was created
$exePath = "dist\FFTLauncher.exe"
if (Test-Path $exePath) {
    $fileInfo = Get-Item $exePath
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "BUILD COMPLETE!" -ForegroundColor Green
    Write-Host "STANDALONE LAUNCHER" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "Executable: $exePath" -ForegroundColor Cyan
    Write-Host "Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" -ForegroundColor Cyan
    Write-Host "Created: $($fileInfo.CreationTime)" -ForegroundColor Cyan
    Write-Host "Version: $gitVersion" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "FEATURES:" -ForegroundColor Yellow
    Write-Host "- Self-contained executable with all dependencies" -ForegroundColor White
    Write-Host "- Downloads and updates Minecraft modpack files" -ForegroundColor White
    Write-Host "- Launches Minecraft with FFT modpack" -ForegroundColor White
    Write-Host "- Enhanced logging system with log rotation" -ForegroundColor White
    Write-Host "- No bootstrap or self-update complexity" -ForegroundColor White
    Write-Host ""
    Write-Host "Ready to distribute!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
} else {
    Write-Host "Error: Executable not found at $exePath" -ForegroundColor Red
    Write-Host "Build may have failed - check the output above" -ForegroundColor Red
    exit 1
}
