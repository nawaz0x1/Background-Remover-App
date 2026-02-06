"""
Download the u2net ONNX model and the ONNX Runtime Android AAR.
Run this before building the APK.
"""

import os
import sys
import urllib.request

# ── Model ──
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
MODEL_NAME = "u2net"
MODEL_FILE = os.path.join(MODEL_DIR, f"{MODEL_NAME}.onnx")
MODEL_URL = f"https://github.com/danielgatis/rembg/releases/download/v0.0.0/{MODEL_NAME}.onnx"

# ── ONNX Runtime Android AAR ──
LIBS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs")
ORT_VERSION = "1.22.0"
ORT_AAR_FILE = os.path.join(LIBS_DIR, f"onnxruntime-android-{ORT_VERSION}.aar")
ORT_AAR_URL = (
    f"https://repo1.maven.org/maven2/com/microsoft/onnxruntime/"
    f"onnxruntime-android/{ORT_VERSION}/onnxruntime-android-{ORT_VERSION}.aar"
)


def _download(url, dest, label):
    """Download a file with progress bar."""
    dest_dir = os.path.dirname(dest)
    os.makedirs(dest_dir, exist_ok=True)

    if os.path.exists(dest):
        size_mb = os.path.getsize(dest) / (1024 * 1024)
        print(f"[OK] {label} already exists: {dest} ({size_mb:.1f} MB)")
        return True

    print(f"Downloading {label} ...")
    print(f"  URL: {url}")
    print(f"  Destination: {dest}")
    print()

    try:
        def progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                mb = downloaded / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                sys.stdout.write(
                    f"\r  Progress: {percent:.1f}% ({mb:.1f}/{total_mb:.1f} MB)"
                )
                sys.stdout.flush()

        urllib.request.urlretrieve(url, dest, reporthook=progress)
        print()

        size_mb = os.path.getsize(dest) / (1024 * 1024)
        print(f"[OK] {label} downloaded ({size_mb:.1f} MB)")
        return True

    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        if os.path.exists(dest):
            os.remove(dest)
        print(f"\nManual download:")
        print(f"  1. Go to: {url}")
        print(f"  2. Save to: {dest}")
        return False


def download_model():
    """Download the ONNX model if not already present"""
    return _download(MODEL_URL, MODEL_FILE, f"{MODEL_NAME}.onnx model")


def download_onnxruntime_aar():
    """Download the ONNX Runtime Android AAR if not already present"""
    return _download(ORT_AAR_URL, ORT_AAR_FILE, f"onnxruntime-android-{ORT_VERSION}.aar")


if __name__ == "__main__":
    ok1 = download_model()
    ok2 = download_onnxruntime_aar()
    sys.exit(0 if (ok1 and ok2) else 1)
