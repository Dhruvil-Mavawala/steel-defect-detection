"""
app.py — Entry point. Sets page config and redirects to Home.
All pages live in /pages/. Run with: streamlit run app.py
"""
import streamlit as st
from utils.ui_components import load_css, sidebar_brand, sidebar_footer
from utils.model import DEVICE

st.set_page_config(
    page_title="Steel Defect Pro",
    page_icon="🔩",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()

# ── Session state ─────────────────────────────────────────────────────────────
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

# ── Redirect to Home ──────────────────────────────────────────────────────────
st.switch_page("pages/1_Home.py")
