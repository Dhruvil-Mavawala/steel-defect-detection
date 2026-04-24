import streamlit as st
import time
from utils.ui_components import load_css, sidebar_brand, sidebar_footer, feat_card, section_header, logo_img_tag
from utils.model import DEVICE

st.set_page_config(page_title="Steel Defect Pro", page_icon="assets/Steelmark_logo.svg", layout="wide")
load_css()

with st.sidebar:
    sidebar_brand()
    st.markdown("---")
    st.markdown(f"""
    <div class='sidebar-meta'>Device <code>{DEVICE.upper()}</code></div>
    <div class='sidebar-meta'>Models &nbsp; YOLOv8 + MobileNetV2</div>
    <div class='sidebar-meta'>Session scans &nbsp;
        <code style='color:#58a6ff'>{st.session_state.get('detection_count', 0)}</code>
    </div>""", unsafe_allow_html=True)
    sidebar_footer()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class='hero'>
    <div style='display:flex;align-items:center;gap:20px;margin-bottom:16px'>
        {logo_img_tag(72)}
        <div class='hero-title'>Steel Defect Pro</div>
    </div>
    <div class='hero-sub'>
        AI-powered surface defect analysis for industrial steel inspection.
        Upload an image, get instant results — severity, confidence, and bounding boxes.
    </div>
</div>
""", unsafe_allow_html=True)

# ── CTA ───────────────────────────────────────────────────────────────────────
col_cta, _ = st.columns([2, 5])
with col_cta:
    if st.button("🔍 Start Detection", use_container_width=True):
        st.toast("Opening Detection page…", icon="🔍")
        time.sleep(0.3)
        st.switch_page("pages/2_Detection.py")

st.markdown("<br>", unsafe_allow_html=True)

# ── Feature cards ─────────────────────────────────────────────────────────────
section_header("What you can do")
c1, c2, c3, c4 = st.columns(4)
cards = [
    ("🔍", "Detection",  "Upload any steel surface image and get instant AI-powered defect analysis with bounding boxes and confidence scores."),
    ("📋", "History",    "Every scan is saved to Firebase Firestore. Browse, filter by date or severity, and track your inspection log."),
    ("📊", "Dashboard",  "Live KPI metrics and interactive Plotly charts — defect rate, severity trends, and daily scan volume."),
    ("⚡", "Fast & Local","Runs on CPU with YOLOv8 + MobileNetV2. No cloud GPU needed. Deployable on Streamlit Cloud or Render."),
]
for col, (icon, title, desc) in zip([c1, c2, c3, c4], cards):
    with col:
        st.markdown(feat_card(icon, title, desc), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── How it works ──────────────────────────────────────────────────────────────
section_header("How it works")
steps = [
    ("Upload",    "Drop a JPG or PNG of a steel surface into the Detection page."),
    ("Classify",  "MobileNetV2 verifies the image is actually steel (≥85% confidence)."),
    ("Detect",    "YOLOv8 locates defects. Color analysis provides a rust-detection backup."),
    ("Store",     "Results — severity, confidence, defect area — are saved to Firebase."),
    ("Analyse",   "Visit the Dashboard to see trends, KPIs, and distribution charts."),
]
left, right = st.columns(2)
for i, (title, desc) in enumerate(steps, 1):
    col = left if i % 2 != 0 else right
    with col:
        st.markdown(f"""
        <div class='step'>
            <div class='step-num'>{i}</div>
            <div class='step-text'><b style='color:#e6edf3'>{title}</b> — {desc}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tech stack ────────────────────────────────────────────────────────────────
section_header("Tech stack")
t1, t2, t3, t4, t5 = st.columns(5)
stack = [
    ("🤖", "YOLOv8",       "Defect detection"),
    ("🧠", "MobileNetV2",  "Steel classifier"),
    ("🔥", "Firebase",     "Cloud storage"),
    ("📈", "Plotly",       "Analytics charts"),
    ("⚡", "Streamlit",    "Web interface"),
]
for col, (icon, name, role) in zip([t1, t2, t3, t4, t5], stack):
    with col:
        st.markdown(f"""
        <div class='glass-card' style='text-align:center;padding:18px 12px'>
            <div style='font-size:1.8rem'>{icon}</div>
            <div style='font-weight:700;color:#e6edf3;margin:8px 0 4px'>{name}</div>
            <div style='font-size:.78rem;color:#8b949e'>{role}</div>
        </div>""", unsafe_allow_html=True)
