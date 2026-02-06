"""
Download the u2net ONNX model for background removal.
Run this before building the APK to include the model in the package.
"""

import os
import sys
import urllib.request

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
MODEL_NAME = "u2net"
MODEL_FILE = os.path.join(MODEL_DIR, f"{MODEL_NAME}.onnx")
MODEL_URL = f"https://github.com/danielgatis/rembg/releases/download/v0.0.0/{MODEL_NAME}.onnx"


def download_model():
    """Download the ONNX model if not already present"""
    os.makedirs(MODEL_DIR, exist_ok=True)

    if os.path.exists(MODEL_FILE):
        size_mb = os.path.getsize(MODEL_FILE) / (1024 * 1024)
        print(f"[OK] Model already exists: {MODEL_FILE} ({size_mb:.1f} MB)")
        return True

    print(f"Downloading {MODEL_NAME}.onnx ...")
    print(f"  URL: {MODEL_URL}")
    print(f"  Destination: {MODEL_FILE}")
    print()

    try:
        def progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                mb = downloaded / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                sys.stdout.write(f"\r  Progress: {percent:.1f}% ({mb:.1f}/{total_mb:.1f} MB)")
                sys.stdout.flush()

        urllib.request.urlretrieve(MODEL_URL, MODEL_FILE, reporthook=progress)
        print()

        size_mb = os.path.getsize(MODEL_FILE) / (1024 * 1024)
        print(f"[OK] Downloaded successfully ({size_mb:.1f} MB)")
        return True

    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        if os.path.exists(MODEL_FILE):
            os.remove(MODEL_FILE)
        print(f"\nManual download:")
        print(f"  1. Go to: {MODEL_URL}")
        print(f"  2. Save to: {MODEL_FILE}")
        return False


if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)
