"""
Background Removal Module using rembg with ONNX Runtime
"""

import io
import os
from pathlib import Path
from kivy.utils import platform

# Set model directory BEFORE importing rembg
# On Android, use the app's internal storage
if platform == 'android':
    from android.storage import app_storage_path
    MODEL_DIR = Path(app_storage_path()) / "models"
else:
    MODEL_DIR = Path(__file__).parent / "models"

MODEL_DIR.mkdir(exist_ok=True)
os.environ["U2NET_HOME"] = str(MODEL_DIR)

from PIL import Image
from rembg import remove, new_session

# Global session for better performance
_session = None

MODEL_NAME = "u2net"
MODEL_FILE = MODEL_DIR / f"{MODEL_NAME}.onnx"


def check_model_exists():
    """Check if the model file exists locally"""
    return MODEL_FILE.exists()


def get_model_path():
    """Get the path where the model should be stored"""
    return str(MODEL_FILE)


def get_session():
    """Get or create rembg session with ONNX"""
    global _session
    if _session is None:
        if not check_model_exists():
            print(f"Model not found at {MODEL_FILE}")
            print("Downloading model (this only happens once)...")
            print(f"Or manually download from:")
            print(f"  https://github.com/danielgatis/rembg/releases/download/v0.0.0/{MODEL_NAME}.onnx")
            print(f"  and place it in: {MODEL_DIR}")
        _session = new_session(MODEL_NAME)
    return _session


def remove_background(image_path: str, output_path: str = None) -> Image.Image:
    """
    Remove background from an image file.
    
    Args:
        image_path: Path to input image
        output_path: Optional path to save result
        
    Returns:
        PIL Image with background removed
    """
    session = get_session()
    
    with open(image_path, "rb") as f:
        input_bytes = f.read()
    
    output_bytes = remove(input_bytes, session=session)
    result = Image.open(io.BytesIO(output_bytes))
    
    if output_path:
        result.save(output_path)
    
    return result


def remove_background_from_bytes(image_bytes: bytes) -> bytes:
    """
    Remove background from image bytes.
    
    Args:
        image_bytes: Input image as bytes
        
    Returns:
        Output image as PNG bytes
    """
    session = get_session()
    return remove(image_bytes, session=session)


def remove_background_pil(image: Image.Image) -> Image.Image:
    """
    Remove background from PIL Image.
    
    Args:
        image: Input PIL Image
        
    Returns:
        PIL Image with background removed
    """
    session = get_session()
    
    # Convert PIL to bytes
    img_buffer = io.BytesIO()
    image.save(img_buffer, format="PNG")
    input_bytes = img_buffer.getvalue()
    
    # Process
    output_bytes = remove(input_bytes, session=session)
    
    return Image.open(io.BytesIO(output_bytes))
