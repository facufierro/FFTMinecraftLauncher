# FFT Minecraft Launcher Build Script
# This script builds the launcher into a standalone executable

param(
    [switch]$Clean,
    [switch]$Debug,
    [string]$OutputDir = "dist"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$SpecFile = Join-Path $ScriptDir "specs\FFTLauncher.spec"
$BuildDir = Join-Path $ProjectRoot "build"
$DistDir = Join-Path $ProjectRoot $OutputDir

Write-Host "FFT Minecraft Launcher Build Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Spec File: $SpecFile" -ForegroundColor Gray
Write-Host "Output Directory: $DistDir" -ForegroundColor Gray
Write-Host ""

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path $BuildDir) {
        Remove-Item $BuildDir -Recurse -Force
        Write-Host "Removed build directory" -ForegroundColor Green
    }
    if (Test-Path $DistDir) {
        Remove-Item $DistDir -Recurse -Force
        Write-Host "Removed dist directory" -ForegroundColor Green
    }
    Write-Host ""
}

# Check if virtual environment exists
$VenvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "Error: Virtual environment not found at $VenvPath" -ForegroundColor Red
    Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Yellow
    Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (-not (Test-Path $ActivateScript)) {
    Write-Host "Error: Virtual environment activation script not found" -ForegroundColor Red
    exit 1
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& $ActivateScript

# Check if PyInstaller is installed
try {
    $null = Get-Command pyinstaller -ErrorAction Stop
    Write-Host "PyInstaller found" -ForegroundColor Green
} catch {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install PyInstaller" -ForegroundColor Red
        exit 1
    }
    Write-Host "PyInstaller installed successfully" -ForegroundColor Green
}

# Check if spec file exists
if (-not (Test-Path $SpecFile)) {
    Write-Host "Error: Spec file not found at $SpecFile" -ForegroundColor Red
    Write-Host "Please ensure the spec file exists in scripts/specs/" -ForegroundColor Yellow
    exit 1
}

# Set working directory to project root
Push-Location $ProjectRoot

try {
    # Build the executable
    Write-Host "Building FFTLauncher.exe..." -ForegroundColor Yellow
    Write-Host "Using spec file: $SpecFile" -ForegroundColor Gray
    
    $PyInstallerArgs = @(
        "--clean"
        "--noconfirm"
        $SpecFile
    )
    
    if ($Debug) {
        $PyInstallerArgs += "--debug=all"
        Write-Host "Debug mode enabled" -ForegroundColor Yellow
    }
    
    Write-Host "Running PyInstaller with arguments: $($PyInstallerArgs -join ' ')" -ForegroundColor Gray
    Write-Host ""
    
    & pyinstaller @PyInstallerArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: PyInstaller build failed" -ForegroundColor Red
        exit 1
    }
    
    # Check if executable was created
    $ExePath = Join-Path $DistDir "FFTLauncher.exe"
    if (Test-Path $ExePath) {
        $FileInfo = Get-Item $ExePath
        Write-Host ""
        Write-Host "Build completed successfully!" -ForegroundColor Green
        Write-Host "=============================" -ForegroundColor Green
        Write-Host "Executable: $ExePath" -ForegroundColor Cyan
        Write-Host "Size: $([math]::Round($FileInfo.Length / 1MB, 2)) MB" -ForegroundColor Cyan
        Write-Host "Created: $($FileInfo.CreationTime)" -ForegroundColor Cyan
        Write-Host ""
        
        # Test the executable
        Write-Host "Testing executable..." -ForegroundColor Yellow
        try {
            $TestProcess = Start-Process -FilePath $ExePath -ArgumentList "--version" -PassThru -NoNewWindow -Wait
            if ($TestProcess.ExitCode -eq 0) {
                Write-Host "Executable test passed" -ForegroundColor Green
            } else {
                Write-Host "Warning: Executable test returned exit code $($TestProcess.ExitCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "Warning: Could not test executable: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "Build Summary:" -ForegroundColor Cyan
        Write-Host "- Executable created at: $ExePath" -ForegroundColor White
        Write-Host "- Ready to distribute!" -ForegroundColor White
        
    } else {
        Write-Host "Error: Executable not found at expected location: $ExePath" -ForegroundColor Red
        exit 1
    }
    
} finally {
    # Return to original directory
    Pop-Location
}

Write-Host ""
Write-Host "Build process completed!" -ForegroundColor Green
