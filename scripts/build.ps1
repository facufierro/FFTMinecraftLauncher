#!/usr/bin/env pwsh
# FFT Minecraft Launcher Build Script
# Builds FFTLauncher.exe and Updater.exe executables

param(
    [string]$Target = "all",  # "launcher", "updater", or "all"
    [switch]$Clean = $false
)

Write-Host "Building FFT Applications..." -ForegroundColor Green
Write-Host "===========================" -ForegroundColor Green

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

# Clean build cache if requested
if ($Clean) {
    Write-Host "Cleaning build cache..." -ForegroundColor Yellow
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
}

# Get version from git tag
$gitVersion = git tag --list --sort=-version:refname | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' } | Select-Object -First 1
if (-not $gitVersion) {
    Write-Host "Warning: No valid git tags found, using default version" -ForegroundColor Yellow
    $gitVersion = "v2.0.0"
}
Write-Host "Using version: $gitVersion" -ForegroundColor Cyan

# Check if PyInstaller is installed
try {
    & $pythonExe -c "import PyInstaller; print('PyInstaller found')"
} catch {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    & $pythonExe -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install PyInstaller" -ForegroundColor Red
        exit 1
    }
}

function Build-Application {
    param(
        [string]$AppName,
        [string]$SpecFile,
        [string]$ExpectedExe,
        [string]$Description
    )
    
    Write-Host ""
    Write-Host "Building $AppName..." -ForegroundColor Yellow
    Write-Host "Using spec file: $SpecFile" -ForegroundColor Gray
    
    if (-not (Test-Path $SpecFile)) {
        Write-Host "Error: Spec file not found at $SpecFile" -ForegroundColor Red
        return $false
    }
    
    & $pythonExe -m PyInstaller $SpecFile --noconfirm --clean
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: $AppName build failed" -ForegroundColor Red
        return $false
    }
    
    if (Test-Path $ExpectedExe) {
        $fileInfo = Get-Item $ExpectedExe
        Write-Host "✓ $AppName built successfully" -ForegroundColor Green
        Write-Host "  File: $ExpectedExe" -ForegroundColor Cyan
        Write-Host "  Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" -ForegroundColor Cyan
        return $true
    } else {
        Write-Host "Error: $AppName executable not found at $ExpectedExe" -ForegroundColor Red
        return $false
    }
}

$buildResults = @()

# Build Launcher
if ($Target -eq "launcher" -or $Target -eq "all") {
    $success = Build-Application -AppName "FFT Launcher" -SpecFile "scripts\specs\FFTLauncher.spec" -ExpectedExe "dist\FFTLauncher.exe" -Description "Main Minecraft launcher"
    $buildResults += @{ Name = "FFT Launcher"; Success = $success; Path = "dist\FFTLauncher.exe" }
}

# Build Updater
if ($Target -eq "updater" -or $Target -eq "all") {
    $success = Build-Application -AppName "Updater" -SpecFile "scripts\specs\Updater.spec" -ExpectedExe "dist\Updater.exe" -Description "GitHub-based app updater"
    $buildResults += @{ Name = "Updater"; Success = $success; Path = "dist\Updater.exe" }
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "BUILD SUMMARY" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

$allSuccessful = $true
foreach ($result in $buildResults) {
    if ($result.Success) {
        Write-Host "✓ $($result.Name): SUCCESS" -ForegroundColor Green
        if (Test-Path $result.Path) {
            $fileInfo = Get-Item $result.Path
            Write-Host "  Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" -ForegroundColor Cyan
        }
    } else {
        Write-Host "✗ $($result.Name): FAILED" -ForegroundColor Red
        $allSuccessful = $false
    }
}

Write-Host ""
Write-Host "Version: $gitVersion" -ForegroundColor Cyan

if ($allSuccessful) {
    Write-Host "All builds completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Some builds failed - check the output above" -ForegroundColor Red
    exit 1
}

Write-Host "==========================================" -ForegroundColor Green
