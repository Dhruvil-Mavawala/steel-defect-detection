"""
utils/model.py — Model loading and defect detection logic.

Classification: dual-threshold with YOLO tiebreaker
  >= 0.85            → Steel (high confidence)
  <= 0.60            → Not Steel (high confidence)
  0.60 < prob < 0.85 → uncertain: Steel only if YOLO finds >= 2 valid defect boxes

Defect detection: YOLO-only, unchanged
  conf >= 0.6, area >= 3% of image, >= 2 valid boxes → Defect
  Color-based rust backup runs independently
"""
import streamlit as st
import torch
import torch.nn as nn
import cv2
import numpy as np
from PIL import Image
from torchvision import models
from ultralytics import YOLO

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

STEEL_HIGH       = 0.85   # >= this → definitely steel
STEEL_LOW        = 0.60   # <= this → definitely not steel
                          # between  → YOLO tiebreaker

YOLO_CONF        = 0.40   # initial YOLO inference threshold (pre-filter)
YOLO_IOU         = 0.50
MAX_BOX_RATIO    = 0.50
MIN_COLOR_AREA   = 1000
DEFECT_MIN_RATIO = 0.01
SEV_LOW_MAX      = 0.03
SEV_MED_MAX      = 0.10

# ── Post-inference YOLO filters ───────────────────────────────────────────────
YOLO_MIN_CONF    = 0.6
YOLO_MIN_AREA_PC = 0.03
YOLO_MIN_BOXES   = 2


@st.cache_resource(show_spinner="Loading classifier…")
def load_classifier():
    m = models.mobilenet_v2(weights=None)
    m.classifier[1] = nn.Linear(m.last_channel, 2)
    m.load_state_dict(torch.load("steel_classifier.pth", map_location=DEVICE))
    return m.to(DEVICE).eval()


@st.cache_resource(show_spinner="Loading YOLO…")
def load_yolo():
    return YOLO("best.pt")


def _pil_to_tensor(image: Image.Image) -> torch.Tensor:
    """PIL RGB → 1CHW float32 — no torchvision numpy bridge."""
    img = image.resize((224, 224)).convert("RGB")
    t   = torch.frombuffer(bytearray(img.tobytes()), dtype=torch.uint8)
    return t.reshape(224, 224, 3).permute(2, 0, 1).float().div(255.0).unsqueeze(0)


def detect_defect(image: Image.Image) -> dict:
    """Full pipeline: dual-threshold steel classification → YOLO → color backup."""
    classifier = load_classifier()
    yolo       = load_yolo()

    # ── Steel probability ─────────────────────────────────────────────────────
    with torch.no_grad():
        logits     = classifier(_pil_to_tensor(image).to(DEVICE))
        steel_prob = torch.softmax(logits, dim=1)[0][1].item()

    img_rgb      = np.asarray(image.convert("RGB"), dtype=np.uint8).copy()
    img_h, img_w = img_rgb.shape[:2]
    img_draw     = img_rgb.copy()
    total_px     = img_h * img_w

    # ── YOLO detection (always runs — needed for tiebreaker + defect result) ──
    # Filters per box:
    #   conf >= 0.6          — discard low-confidence noise
    #   area >= 3% of image  — discard tiny specks
    #   area <= 50% of image — discard implausibly large boxes
    MIN_REL_AREA = YOLO_MIN_AREA_PC * total_px

    preds      = yolo.predict(source=img_rgb, conf=YOLO_CONF, iou=YOLO_IOU, verbose=False)
    yolo_area  = 0
    yolo_count = 0

    if preds[0].boxes is not None:
        for box in preds[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            area = (x2 - x1) * (y2 - y1)

            if conf < YOLO_MIN_CONF or area < MIN_REL_AREA or area > MAX_BOX_RATIO * total_px:
                continue

            yolo_count += 1
            yolo_area  += area
            cv2.rectangle(img_draw, (x1, y1), (x2, y2), (0, 255, 80), 2)
            cv2.putText(img_draw, f"{conf:.2f}", (x1, max(y1 - 6, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 80), 1)

    # ── Dual-threshold steel classification ───────────────────────────────────
    # Zone 1 (>= 0.85): high confidence → Steel, no further checks.
    # Zone 2 (<= 0.60): high confidence → Not Steel, return immediately.
    # Zone 3 (0.60–0.85): uncertain → use YOLO as tiebreaker.
    #   If YOLO already found >= 2 valid defect boxes the image is almost
    #   certainly steel (non-steel objects don't produce steel defect hits).
    #   Otherwise treat as Not Steel to avoid false positives.
    if steel_prob >= STEEL_HIGH:
        is_steel = True
    elif steel_prob <= STEEL_LOW:
        is_steel = False
    else:
        # Uncertain range: trust YOLO over the classifier
        is_steel = yolo_count >= YOLO_MIN_BOXES

    if not is_steel:
        return _pack(steel_prob, False, False, "None", 0.0, img_draw, 0)

    # ── Color-based rust backup ───────────────────────────────────────────────
    hsv       = cv2.cvtColor(cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2HSV)
    mask      = cv2.inRange(hsv, np.array([5, 50, 50], np.uint8), np.array([25, 255, 255], np.uint8))
    k         = np.ones((5, 5), np.uint8)
    mask      = cv2.morphologyEx(cv2.morphologyEx(mask, cv2.MORPH_OPEN, k), cv2.MORPH_CLOSE, k)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    color_area  = 0
    for cnt in contours:
        x, y, wc, hc = cv2.boundingRect(cnt)
        area = wc * hc
        if area < MIN_COLOR_AREA:
            continue
        color_area += area
        cv2.rectangle(img_draw, (x, y), (x + wc, y + hc), (255, 120, 0), 2)

    # ── Final defect decision ─────────────────────────────────────────────────
    # YOLO path: >= 2 valid boxes required.
    # Color path: rust area ratio-based (single region is enough).
    yolo_defect  = yolo_count >= YOLO_MIN_BOXES
    color_defect = (color_area / total_px) >= DEFECT_MIN_RATIO

    if yolo_defect:
        ratio    = yolo_area / total_px
        detected = True
    elif color_defect:
        ratio    = color_area / total_px
        detected = True
    else:
        ratio    = max(yolo_area, color_area) / total_px
        detected = False

    severity = _sev(ratio) if detected else "None"

    return _pack(steel_prob, True, detected, severity, round(ratio * 100, 2), img_draw, yolo_count)


def _sev(r: float) -> str:
    return "Low" if r < SEV_LOW_MAX else ("Medium" if r < SEV_MED_MAX else "High")


def _pack(steel_prob, is_steel, defect_detected, severity, defect_area, img, boxes) -> dict:
    return dict(steel_prob=steel_prob, is_steel=is_steel, defect_detected=defect_detected,
                severity=severity, defect_area=defect_area, processed_image=img, yolo_boxes=boxes)
