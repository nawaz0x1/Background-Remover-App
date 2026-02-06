#!/bin/bash
# ============================================================
# Build script for BG Remover Android APK
# 
# Prerequisites (Ubuntu/WSL):
#   sudo apt update
#   sudo apt install -y python3-pip python3-venv \
#       build-essential git zip unzip openjdk-17-jdk \
#       autoconf libtool pkg-config zlib1g-dev \
#       libncurses5-dev libncursesw5-dev libtinfo5 \
#       cmake libffi-dev libssl-dev
#   pip install buildozer cython
#
# Usage:
#   chmod +x build.sh
#   ./build.sh          # Full build (download model + build APK)
#   ./build.sh debug    # Debug APK
#   ./build.sh release  # Release APK
#   ./build.sh model    # Only download the model
#   ./build.sh clean    # Clean build artifacts
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[BUILD]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ---- Step 1: Download model ----
download_model() {
    log "Checking ONNX model..."
    python3 download_model.py
    if [ $? -ne 0 ]; then
        error "Model download failed. Cannot build without the model."
    fi
    
    if [ ! -f "models/u2net.onnx" ]; then
        error "Model file not found at models/u2net.onnx"
    fi
    
    log "Model ready."
}

# ---- Step 2: Check dependencies ----
check_deps() {
    log "Checking build dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        error "python3 not found. Install Python 3."
    fi
    
    if ! command -v buildozer &> /dev/null; then
        warn "buildozer not found. Installing..."
        pip install buildozer
    fi
    
    if ! command -v java &> /dev/null; then
        error "Java not found. Install JDK: sudo apt install openjdk-17-jdk"
    fi
    
    log "Dependencies OK."
}

# ---- Step 3: Build APK ----
build_apk() {
    local build_type="${1:-debug}"
    
    log "Building Android APK ($build_type)..."
    log "This may take a while on first build (downloads Android SDK/NDK)..."
    echo ""
    
    if [ "$build_type" = "release" ]; then
        buildozer android release
    else
        buildozer android debug
    fi
    
    echo ""
    log "Build complete!"
    
    # Find the APK
    APK=$(find bin/ -name "*.apk" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    if [ -n "$APK" ]; then
        SIZE=$(du -h "$APK" | cut -f1)
        log "APK: $APK ($SIZE)"
        echo ""
        echo "  To install on device:"
        echo "    adb install $APK"
        echo ""
        echo "  Or copy the APK to your phone and install manually."
    fi
}

# ---- Step 4: Clean ----
clean() {
    log "Cleaning build artifacts..."
    rm -rf .buildozer/
    rm -rf bin/
    rm -rf __pycache__/
    rm -rf ui/__pycache__/
    log "Clean done."
}

# ---- Main ----
case "${1:-build}" in
    model)
        download_model
        ;;
    debug|build)
        check_deps
        download_model
        build_apk debug
        ;;
    release)
        check_deps
        download_model
        build_apk release
        ;;
    clean)
        clean
        ;;
    *)
        echo "Usage: $0 {debug|release|model|clean}"
        echo ""
        echo "  debug   - Download model + build debug APK (default)"
        echo "  release - Download model + build release APK"
        echo "  model   - Only download the ONNX model"
        echo "  clean   - Remove build artifacts"
        exit 1
        ;;
esac
