"""
Background Removal Module – direct ONNX inference (no rembg/scipy).

This avoids heavy dependencies (rembg, scipy, scikit-image) that cannot
be cross-compiled for Android.  We run U2Net inference directly via
onnxruntime + numpy + Pillow.
"""

import io
import os
from pathlib import Path

import numpy as np
from PIL import Image

from kivy.utils import platform

# ---------------------------------------------------------------------------
# Model directory
# ---------------------------------------------------------------------------
if platform == "android":
    try:
        from android.storage import app_storage_path
        MODEL_DIR = Path(app_storage_path()) / "models"
    except ImportError:
        MODEL_DIR = Path(__file__).parent / "models"
else:
    MODEL_DIR = Path(__file__).parent / "models"

MODEL_DIR.mkdir(exist_ok=True)

MODEL_NAME = "u2net"
MODEL_FILE = MODEL_DIR / f"{MODEL_NAME}.onnx"

# Global ONNX session (lazy loaded)
_session = None

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def check_model_exists() -> bool:
    """Check if the ONNX model file exists locally."""
    return MODEL_FILE.exists()


def get_model_path() -> str:
    """Return the expected model file path."""
    return str(MODEL_FILE)


def get_session():
    """Get or create the ONNX‑Runtime inference session."""
    global _session
    if _session is None:
        import onnxruntime as ort

        if not check_model_exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_FILE}.\n"
                f"Download from: https://github.com/danielgatis/rembg/releases/download/v0.0.0/{MODEL_NAME}.onnx\n"
                f"and place it in: {MODEL_DIR}"
            )

        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        # Prefer CPU on Android (GPU EP may not be available)
        providers = ["CPUExecutionProvider"]
        _session = ort.InferenceSession(str(MODEL_FILE), sess_options=opts, providers=providers)
    return _session


# ---------------------------------------------------------------------------
# Pre/post-processing (replaces rembg + scipy + scikit-image)
# ---------------------------------------------------------------------------

_INPUT_SIZE = (320, 320)  # U2Net expected input


def _normalise(img_array: np.ndarray) -> np.ndarray:
    """Normalise an RGB image array to [0, 1] with ImageNet-style mean/std."""
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img = img_array.astype(np.float32) / 255.0
    img = (img - mean) / std
    return img


def _preprocess(image: Image.Image) -> np.ndarray:
    """Resize, normalise and reshape to NCHW float32 tensor."""
    img = image.convert("RGB").resize(_INPUT_SIZE, Image.LANCZOS)
    arr = np.array(img)                       # (H, W, 3)
    arr = _normalise(arr)                      # (H, W, 3) float32
    arr = arr.transpose(2, 0, 1)               # (3, H, W)
    arr = np.expand_dims(arr, axis=0)          # (1, 3, H, W)
    return arr


def _postprocess(mask: np.ndarray, original_size: tuple) -> np.ndarray:
    """Convert raw model output to a uint8 alpha mask at original resolution."""
    # mask may come as (1, 1, 320, 320) or (1, 320, 320) – squeeze to 2-D
    mask = np.squeeze(mask)

    # Normalise to 0-255
    ma, mi = mask.max(), mask.min()
    if ma - mi > 1e-6:
        mask = (mask - mi) / (ma - mi)
    else:
        mask = np.zeros_like(mask)

    mask = (mask * 255).astype(np.uint8)

    # Resize back to original image dimensions
    mask_img = Image.fromarray(mask, mode="L")
    mask_img = mask_img.resize(original_size, Image.LANCZOS)
    return np.array(mask_img)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def remove_background(image_path: str, output_path: str = None) -> Image.Image:
    """
    Remove background from an image file.

    Args:
        image_path: Path to the input image.
        output_path: Optional path to save the result (PNG).

    Returns:
        PIL RGBA Image with background removed.
    """
    image = Image.open(image_path).convert("RGBA")
    result = remove_background_pil(image)
    if output_path:
        result.save(output_path)
    return result


def remove_background_from_bytes(image_bytes: bytes) -> bytes:
    """Remove background from raw image bytes; returns PNG bytes."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    result = remove_background_pil(image)
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    return buf.getvalue()


def remove_background_pil(image: Image.Image) -> Image.Image:
    """
    Remove background from a PIL Image.

    Args:
        image: Input PIL Image (any mode).

    Returns:
        PIL RGBA Image with background removed.
    """
    session = get_session()
    rgb = image.convert("RGB")
    original_size = rgb.size  # (W, H)

    # Run inference
    tensor = _preprocess(rgb)
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: tensor})

    # U2Net returns multiple outputs; the first (d1) is the best mask
    mask = _postprocess(outputs[0], original_size)

    # Apply mask as alpha channel
    rgba = image.convert("RGBA")
    r, g, b, _ = rgba.split()
    alpha = Image.fromarray(mask, mode="L")
    result = Image.merge("RGBA", (r, g, b, alpha))
    return result
