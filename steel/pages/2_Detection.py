import streamlit as st
from PIL import Image
import time

from utils.ui_components import (
    load_css, sidebar_brand, sidebar_footer,
    result_summary_card, SEV_COLORS,
)
from utils.model import detect_defect, DEVICE
from utils.firebase import save_detection
from utils.image_processing import image_to_bytes

st.set_page_config(
    page_title="Detection · Steel Defect Pro",
    page_icon="🔍",
    layout="wide",
)
load_css()

if "detection_count" not in st.session_state:
    st.session_state.detection_count = 0

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_brand()
    st.markdown("---")
    st.markdown(f"""
    <div class='sidebar-meta'>Device <code>{DEVICE.upper()}</code></div>
    <div class='sidebar-meta'>Models &nbsp; YOLOv8 + MobileNetV2</div>
    <div class='sidebar-meta'>Session scans &nbsp;
        <code style='color:#58a6ff'>{st.session_state.detection_count}</code>
    </div>""", unsafe_allow_html=True)
    sidebar_footer()

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class='anim-1' style='margin-bottom:24px'>
    <div style='font-size:1.8rem;font-weight:800;color:#e6edf3;margin-bottom:6px'>
        🔍 Defect Detection
    </div>
    <div style='color:#8b949e;font-size:.92rem'>
        Upload a steel surface image — AI analyses it for defects in seconds
    </div>
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Upload zone ───────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload Image",
    type=["jpg", "jpeg", "png"],
    help="Drag & drop or browse a JPG / PNG steel surface image",
)

if not uploaded:
    st.markdown("""
    <div class='upload-zone'>
        <div class='upload-icon'>📂</div>
        <div class='upload-text'>
            <b>Drag & drop</b> a steel surface image here<br>
            or use the file picker above &nbsp;·&nbsp; JPG / PNG supported
        </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── Load image ────────────────────────────────────────────────────────────────
image = Image.open(uploaded).convert("RGB")

# ── Side-by-side image columns ────────────────────────────────────────────────
col_orig, col_proc = st.columns(2, gap="large")

with col_orig:
    st.markdown("""
    <div style='font-size:.72rem;font-weight:700;letter-spacing:.1em;
                text-transform:uppercase;color:#8b949e;margin-bottom:10px'>
        <span style='display:inline-block;width:8px;height:8px;border-radius:50%;
                     background:#58a6ff;margin-right:6px'></span>
        Original Image
    </div>""", unsafe_allow_html=True)
    st.image(image, use_column_width=True)

# ── Detection pipeline ────────────────────────────────────────────────────────
progress_ph = st.empty()
status_ph   = st.empty()

bar = progress_ph.progress(0, text="Initialising…")

# Stage 1 — pre-processing
status_ph.info("🔄 Pre-processing image…")
for i in range(1, 26):
    bar.progress(i, text="Pre-processing…")
    time.sleep(0.010)

# Stage 2 — classifier
status_ph.info("🧠 Running steel classifier…")
for i in range(26, 45):
    bar.progress(i, text="Classifying material…")
    time.sleep(0.010)

# Stage 3 — YOLO (actual inference)
status_ph.info("🤖 Running YOLO defect detection…")
with st.spinner("🔬 Analysing surface… please wait"):
    result = detect_defect(image)
    st.session_state.detection_count += 1

# Stage 4 — post-processing
for i in range(55, 91):
    bar.progress(i, text="Post-processing results…")
    time.sleep(0.006)

# Stage 5 — finalising
status_ph.info("💾 Finalising…")
for i in range(91, 101):
    bar.progress(i, text="Finalising…")
    time.sleep(0.008)

progress_ph.empty()
status_ph.empty()

st.toast("Detection complete!", icon="✅")

# ── Show processed image ──────────────────────────────────────────────────────
sev        = result["severity"]
dot_color  = "#f85149" if result["defect_detected"] else "#3fb950"
proc_label = "Detected Output" + (" — Defects Highlighted" if result["defect_detected"] else " — No Defects")

with col_proc:
    st.markdown(f"""
    <div style='font-size:.72rem;font-weight:700;letter-spacing:.1em;
                text-transform:uppercase;color:#8b949e;margin-bottom:10px'>
        <span style='display:inline-block;width:8px;height:8px;border-radius:50%;
                     background:{dot_color};margin-right:6px'></span>
        {proc_label}
    </div>""", unsafe_allow_html=True)
    st.image(result["processed_image"], use_column_width=True)

st.markdown("---")

# ── Result summary card ───────────────────────────────────────────────────────
result_summary_card(result)

# ── Action buttons (only if steel) ────────────────────────────────────────────
if result["is_steel"]:
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    col_dl, col_reset, _ = st.columns([2, 2, 5])

    with col_dl:
        st.download_button(
            "⬇️ Download Result",
            data=image_to_bytes(result["processed_image"]),
            file_name="steel_detection_result.png",
            mime="image/png",
            use_container_width=True,
        )

    with col_reset:
        if st.button("🔄 New Scan", use_container_width=True):
            st.rerun()

    # Auto-save to Firebase (silent, no UI clutter)
    try:
        save_detection(result)
    except Exception:
        pass  # Silent fail — don't clutter UI with save errors
