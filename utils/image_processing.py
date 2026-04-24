"""
utils/image_processing.py — Image conversion helpers.
"""
import io
import numpy as np
from PIL import Image


def image_to_bytes(img_rgb: np.ndarray) -> bytes:
    """RGB numpy array → PNG bytes for st.download_button."""
    buf = io.BytesIO()
    Image.fromarray(img_rgb).save(buf, format="PNG")
    return buf.getvalue()


def pil_to_display(image: Image.Image, max_size: int = 800) -> Image.Image:
    """Resize PIL image for display while preserving aspect ratio."""
    w, h = image.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return image
