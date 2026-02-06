"""
Background Removal Module – direct ONNX inference (no rembg/scipy).

Desktop : uses the Python ``onnxruntime`` package.
Android : uses the Java ONNX Runtime Android AAR via pyjnius
          (onnxruntime-android Gradle dependency – no cross-compilation
          of the Python package needed).
"""

import io
import os

import numpy as np
from PIL import Image

from kivy.utils import platform

# ---------------------------------------------------------------------------
# Model directory – always relative to *this* file so the bundled model
# inside the APK is found on Android too.
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(_THIS_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_NAME = "u2net"
MODEL_FILE = os.path.join(MODEL_DIR, f"{MODEL_NAME}.onnx")

# Global ONNX session (lazy loaded)
_session = None

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def check_model_exists() -> bool:
    return os.path.isfile(MODEL_FILE)


def get_model_path() -> str:
    return MODEL_FILE


# ---------------------------------------------------------------------------
# Pre / post-processing  (shared between Android and desktop)
# ---------------------------------------------------------------------------

_INPUT_SIZE = (320, 320)  # U2Net expected input


def _normalise(img_array: np.ndarray) -> np.ndarray:
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    return (img_array.astype(np.float32) / 255.0 - mean) / std


def _preprocess(image: Image.Image) -> np.ndarray:
    img = image.convert("RGB").resize(_INPUT_SIZE, Image.LANCZOS)
    arr = _normalise(np.array(img))            # (H, W, 3) float32
    arr = arr.transpose(2, 0, 1)               # (3, H, W)
    return np.expand_dims(arr, axis=0).astype(np.float32)  # (1, 3, H, W)


def _postprocess(mask: np.ndarray, original_size: tuple) -> np.ndarray:
    mask = np.squeeze(mask)
    ma, mi = mask.max(), mask.min()
    if ma - mi > 1e-6:
        mask = (mask - mi) / (ma - mi)
    else:
        mask = np.zeros_like(mask)
    mask = (mask * 255).astype(np.uint8)
    mask_img = Image.fromarray(mask, mode="L")
    mask_img = mask_img.resize(original_size, Image.LANCZOS)
    return np.array(mask_img)


# =========================================================================
# Android – Java ONNX Runtime via pyjnius
# (follows https://github.com/aicelen/Onnx-Kivy-Android pattern)
# =========================================================================

class _AndroidOnnxSession:
    """Thin wrapper that mimics the Python onnxruntime.InferenceSession API
    while calling the Java ONNX Runtime Android library via pyjnius."""

    def __init__(self, model_path: str):
        from jnius import autoclass

        # Java classes
        self._OnnxTensor = autoclass("ai.onnxruntime.OnnxTensor")
        self._ByteBuffer = autoclass("java.nio.ByteBuffer")
        self._ByteOrder  = autoclass("java.nio.ByteOrder")
        self._HashMap     = autoclass("java.util.HashMap")

        OrtEnvironment    = autoclass("ai.onnxruntime.OrtEnvironment")
        OrtSessionOptions = autoclass("ai.onnxruntime.OrtSession$SessionOptions")

        self._env = OrtEnvironment.getEnvironment()
        opts = OrtSessionOptions()
        opts.setIntraOpNumThreads(2)
        opts.setInterOpNumThreads(1)

        print(f"[BG Remover] Opening ONNX session: {model_path}")
        self._session = self._env.createSession(model_path, opts)

        # Cache input / output names (preserves model order)
        self._input_name   = list(self._session.getInputNames())[0]
        self._output_names = list(self._session.getOutputNames())
        print(f"[BG Remover] inputs={self._input_name}  outputs={self._output_names}")

    # -- mimic onnxruntime.InferenceSession.get_inputs() --
    class _InputMeta:
        def __init__(self, name: str):
            self.name = name

    def get_inputs(self):
        return [self._InputMeta(self._input_name)]

    # -- mimic onnxruntime.InferenceSession.run() --
    def run(self, _output_names, input_dict: dict):
        jmap = self._HashMap()

        for name, value in input_dict.items():
            arr = np.ascontiguousarray(value, dtype=np.float32)
            buf_bytes = arr.ravel().tobytes()
            jbb = self._ByteBuffer.wrap(buf_bytes)
            jbb.order(self._ByteOrder.nativeOrder())
            fbuf = jbb.asFloatBuffer()
            tensor = self._OnnxTensor.createTensor(
                self._env, fbuf, list(arr.shape)
            )
            jmap.put(name, tensor)

        results = self._session.run(jmap)

        output_list = []
        for out_name in self._output_names:
            tensor_obj = results.get(out_name).get()

            # Read shape from tensor metadata
            shape = [int(s) for s in tensor_obj.getInfo().getShape()]

            raw = bytes(tensor_obj.getByteBuffer().array())
            np_arr = np.frombuffer(raw, dtype=np.float32).copy()
            np_arr = np_arr.reshape(shape)

            output_list.append(np_arr)
            tensor_obj.close()

        results.close()
        return output_list


# =========================================================================
# Desktop – normal Python onnxruntime
# =========================================================================

def _create_desktop_session(model_path: str):
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(
        model_path, sess_options=opts, providers=["CPUExecutionProvider"]
    )


# =========================================================================
# Unified session loader
# =========================================================================

def get_session():
    """Get or create the ONNX inference session (platform-aware)."""
    global _session
    if _session is not None:
        return _session

    if not check_model_exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_FILE}.\n"
            f"Download from: https://github.com/danielgatis/rembg/releases/"
            f"download/v0.0.0/{MODEL_NAME}.onnx\n"
            f"and place it in: {MODEL_DIR}"
        )

    if platform == "android":
        _session = _AndroidOnnxSession(MODEL_FILE)
    else:
        _session = _create_desktop_session(MODEL_FILE)

    return _session


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def remove_background(image_path: str, output_path: str = None) -> Image.Image:
    image = Image.open(image_path).convert("RGBA")
    result = remove_background_pil(image)
    if output_path:
        result.save(output_path)
    return result


def remove_background_from_bytes(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    result = remove_background_pil(image)
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    return buf.getvalue()


def remove_background_pil(image: Image.Image) -> Image.Image:
    session = get_session()
    rgb = image.convert("RGB")
    original_size = rgb.size  # (W, H)

    tensor = _preprocess(rgb)
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: tensor})

    # U2Net returns multiple outputs; the first (d1) is the best mask
    mask = _postprocess(outputs[0], original_size)

    rgba = image.convert("RGBA")
    r, g, b, _ = rgba.split()
    alpha = Image.fromarray(mask, mode="L")
    return Image.merge("RGBA", (r, g, b, alpha))
