<# 
.SYNOPSIS
    Build script for BG Remover Android APK (Windows)

.DESCRIPTION
    Downloads the ONNX model and builds the Android APK.
    Note: Android builds require WSL (Windows Subsystem for Linux) or a Linux VM.
    This script handles model download on Windows and can invoke WSL for building.

.EXAMPLE
    .\build.ps1              # Download model + build via WSL
    .\build.ps1 -Model       # Only download the model
    .\build.ps1 -Clean       # Clean build artifacts
    .\build.ps1 -Release     # Build release APK via WSL
#>

param(
    [switch]$Model,
    [switch]$Release,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

function Write-Log($msg) { Write-Host "[BUILD] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

# ---- Download Model ----
function Download-Model {
    Write-Log "Checking ONNX model..."
    python download_model.py
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Model download failed."
    }
    if (-not (Test-Path "models\u2net.onnx")) {
        Write-Err "Model file not found at models\u2net.onnx"
    }
    Write-Log "Model ready."
}

# ---- Clean ----
function Clean-Build {
    Write-Log "Cleaning build artifacts..."
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .buildozer
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue bin
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue __pycache__
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue ui\__pycache__
    Write-Log "Clean done."
}

# ---- Build via WSL ----
function Build-APK {
    param([string]$Type = "debug")
    
    Write-Log "Building Android APK ($Type) via WSL..."
    Write-Host ""
    Write-Host "NOTE: Android builds require WSL with buildozer installed." -ForegroundColor Cyan
    Write-Host "  Setup WSL:  wsl --install" -ForegroundColor Cyan
    Write-Host "  In WSL run: sudo apt update && sudo apt install -y python3-pip build-essential git openjdk-17-jdk" -ForegroundColor Cyan  
    Write-Host "  Then:       pip install buildozer cython" -ForegroundColor Cyan
    Write-Host ""
    
    # Convert Windows path to WSL path
    $WslPath = $ScriptDir -replace '\\','/' -replace '^([A-Z]):','/mnt/$1'
    $WslPath = $WslPath.ToLower() -replace '/mnt/([a-z])','/mnt/$1'
    
    if ($Type -eq "release") {
        wsl bash -c "cd '$WslPath' && bash build.sh release"
    } else {
        wsl bash -c "cd '$WslPath' && bash build.sh debug"
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Build failed. Make sure WSL is set up with buildozer."
    }
}

# ---- Main ----
if ($Clean) {
    Clean-Build
} elseif ($Model) {
    Download-Model
} else {
    Download-Model
    Build-APK -Type $(if ($Release) { "release" } else { "debug" })
}
