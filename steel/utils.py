"""
utils.py — Model loading, image preprocessing, and defect detection logic.
"""
import streamlit as st
import torch
import torch.nn as nn
import cv2
import numpy as np
from PIL import Image
from torchvision import models
from ultralytics import YOLO
import io

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ── Thresholds ────────────────────────────────────────────────────────────────
STEEL_THRESHOLD  = 0.85
YOLO_CONF        = 0.40
YOLO_IOU         = 0.50
MIN_BOX_AREA     = 1500
MAX_BOX_RATIO    = 0.50
MIN_COLOR_AREA   = 1000
DEFECT_MIN_RATIO = 0.01
SEV_LOW_MAX      = 0.03
SEV_MED_MAX      = 0.10


# ── Model loaders (cached) ────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading classifier…")
def load_classifier():
    m = models.mobilenet_v2(weights=None)
    m.classifier[1] = nn.Linear(m.last_channel, 2)
    m.load_state_dict(torch.load("steel_classifier.pth", map_location=DEVICE))
    m.to(DEVICE).eval()
    return m


@st.cache_resource(show_spinner="Loading YOLO…")
def load_yolo():
    return YOLO("best.pt")


# ── Preprocessing ─────────────────────────────────────────────────────────────
def pil_to_tensor(image: Image.Image) -> torch.Tensor:
    """
    PIL RGB → 1CHW float32 tensor.
    Uses tobytes() to avoid the torchvision numpy bridge
    ('Numpy is not available' error on broken installs).
    With a clean numpy==1.26.4 install this path is also safe.
    """
    img = image.resize((224, 224)).convert("RGB")
    raw = img.tobytes()                                          # flat HWC uint8
    t   = torch.frombuffer(bytearray(raw), dtype=torch.uint8)
    t   = t.reshape(224, 224, 3).permute(2, 0, 1).float() / 255.0  # CHW
    return t.unsqueeze(0)                                        # 1CHW


# ── Core detection ────────────────────────────────────────────────────────────
def detect_defect(image: Image.Image) -> dict:
    """
    Run steel classification → YOLO → color-based backup.
    image must be a PIL RGB image.
    Returns a result dict consumed by app.py.
    """
    classifier = load_classifier()
    yolo       = load_yolo()

    # 1. Steel probability ─────────────────────────────────────────────────────
    with torch.no_grad():
        logits     = classifier(pil_to_tensor(image).to(DEVICE))
        steel_prob = torch.softmax(logits, dim=1)[0][1].item()

    # Keep everything in RGB — cv2 functions that need BGR get explicit conversion
    img_rgb          = np.asarray(image.convert("RGB"), dtype=np.uint8).copy()
    img_h, img_w     = img_rgb.shape[:2]
    img_draw         = img_rgb.copy()          # draw on RGB; display directly with st.image
    total_pixel_area = img_h * img_w

    if steel_prob < STEEL_THRESHOLD:
        return _result(steel_prob, False, False, "None", 0.0, img_draw, 0)

    # 2. YOLO detection ────────────────────────────────────────────────────────
    # YOLO accepts RGB numpy arrays natively
    preds      = yolo.predict(source=img_rgb, conf=YOLO_CONF, iou=YOLO_IOU, verbose=False)
    yolo_area  = 0
    yolo_count = 0

    if preds[0].boxes is not None:
        for box in preds[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            area = (x2 - x1) * (y2 - y1)
            if area < MIN_BOX_AREA or conf < 0.5 or area > MAX_BOX_RATIO * total_pixel_area:
                continue
            yolo_count += 1
            yolo_area  += area
            cv2.rectangle(img_draw, (x1, y1), (x2, y2), (0, 255, 80), 2)
            cv2.putText(
                img_draw, f"{conf:.2f}", (x1, max(y1 - 6, 10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 80), 1,
            )

    # 3. Color-based rust backup ───────────────────────────────────────────────
    # cvtColor needs BGR for COLOR_BGR2HSV; convert explicitly here only
    img_bgr   = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    hsv       = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    rust_mask = cv2.inRange(hsv, np.array([5, 50, 50], dtype=np.uint8),
                                 np.array([25, 255, 255], dtype=np.uint8))
    kernel    = np.ones((5, 5), np.uint8)
    rust_mask = cv2.morphologyEx(rust_mask, cv2.MORPH_OPEN,  kernel)
    rust_mask = cv2.morphologyEx(rust_mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(rust_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    color_area  = 0
    for cnt in contours:
        x, y, wc, hc = cv2.boundingRect(cnt)
        area = wc * hc
        if area < MIN_COLOR_AREA:
            continue
        color_area += area
        cv2.rectangle(img_draw, (x, y), (x + wc, y + hc), (255, 120, 0), 2)

    # 4. Final decision ────────────────────────────────────────────────────────
    defect_area     = max(yolo_area, color_area)
    defect_ratio    = defect_area / total_pixel_area
    defect_detected = defect_ratio >= DEFECT_MIN_RATIO
    severity        = _severity(defect_ratio) if defect_detected else "None"

    return _result(
        steel_prob, True, defect_detected, severity,
        round(defect_ratio * 100, 2), img_draw, yolo_count,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────
def _severity(ratio: float) -> str:
    if ratio < SEV_LOW_MAX:  return "Low"
    if ratio < SEV_MED_MAX:  return "Medium"
    return "High"


def _result(steel_prob, is_steel, defect_detected, severity,
            defect_area, processed_image, yolo_boxes) -> dict:
    return {
        "steel_prob":      steel_prob,
        "is_steel":        is_steel,
        "defect_detected": defect_detected,
        "severity":        severity,
        "defect_area":     defect_area,
        "processed_image": processed_image,
        "yolo_boxes":      yolo_boxes,
    }


def image_to_bytes(img_rgb: np.ndarray) -> bytes:
    """Convert RGB numpy array → PNG bytes for st.download_button."""
    buf = io.BytesIO()
    Image.fromarray(img_rgb).save(buf, format="PNG")
    return buf.getvalue()
