import streamlit as st
import pandas as pd
import time

from utils.ui_components import load_css, sidebar_brand, sidebar_footer, section_header, empty_state
from utils.model import DEVICE
from utils.firebase import fetch_history, delete_all

st.set_page_config(page_title="History · Steel Defect Pro", page_icon="📋", layout="wide")
load_css()

with st.sidebar:
    sidebar_brand()
    st.markdown("---")
    st.markdown(f"""
    <div class='sidebar-meta'>Device <code>{DEVICE.upper()}</code></div>
    <div class='sidebar-meta'>Session scans &nbsp;
        <code style='color:#58a6ff'>{st.session_state.get('detection_count', 0)}</code>
    </div>""", unsafe_allow_html=True)
    sidebar_footer()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<span style='font-size:1.8rem;font-weight:800;color:#e6edf3'>📋 Detection History</span>
<p style='color:#8b949e;margin:4px 0 0'>All past detections stored in Firebase Firestore</p>
""", unsafe_allow_html=True)
st.markdown("---")

# ── Toolbar ───────────────────────────────────────────────────────────────────
tb_l, tb_r = st.columns([7, 1])
with tb_l:
    if st.button("🔄 Refresh"):
        st.toast("Refreshing…", icon="🔄")
        st.rerun()
with tb_r:
    if st.button("🗑️ Clear All", type="secondary"):
        with st.spinner("Deleting records…"):
            ok = delete_all()
        if ok:
            st.success("History cleared.")
            st.toast("History cleared", icon="🗑️")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("Clear failed.")

# ── Load data ─────────────────────────────────────────────────────────────────
load_ph  = st.empty()
load_bar = load_ph.progress(0, text="Fetching records…")
with st.spinner("📡 Loading history…"):
    for i in range(1, 50):
        load_bar.progress(i, text="Fetching records…")
        time.sleep(0.006)
    records = fetch_history(limit=300)
    for i in range(50, 101):
        load_bar.progress(i, text="Processing…")
        time.sleep(0.004)
load_ph.empty()

if not records:
    empty_state("📭", "No detection records yet — run a detection first.")
    st.stop()

df = pd.DataFrame(records)

if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df["date"]      = df["timestamp"].dt.date
else:
    df["date"] = None

# ── Filters ───────────────────────────────────────────────────────────────────
section_header("Filters")
f1, f2, f3 = st.columns(3)

with f1:
    sev_opts = ["All"] + sorted(df["severity"].dropna().unique().tolist())
    sel_sev  = st.selectbox("Severity", sev_opts)

with f2:
    if df["date"].notna().any():
        date_range = st.date_input("Date range", value=(df["date"].min(), df["date"].max()))
    else:
        date_range = None

with f3:
    sel_defect = st.selectbox("Defect status", ["All", "Defect Only", "Clean Only"])

# Apply
filtered = df.copy()
if sel_sev != "All":
    filtered = filtered[filtered["severity"] == sel_sev]
if date_range and len(date_range) == 2:
    filtered = filtered[(filtered["date"] >= date_range[0]) & (filtered["date"] <= date_range[1])]
if sel_defect == "Defect Only":
    filtered = filtered[filtered["defect_detected"] == True]
elif sel_defect == "Clean Only":
    filtered = filtered[filtered["defect_detected"] == False]

st.markdown(
    f"<p style='color:#8b949e'>Showing <b style='color:#e6edf3'>{len(filtered)}</b> "
    f"of <b style='color:#e6edf3'>{len(df)}</b> records</p>",
    unsafe_allow_html=True,
)

# ── Column mapping ────────────────────────────────────────────────────────────
COL_MAP = {
    "timestamp":       "Timestamp",
    "steel_prob":      "Steel Prob (%)",
    "defect_detected": "Defect",
    "severity":        "Severity",
    "defect_ratio":    "Area (%)",
}
cols = [c for c in COL_MAP if c in filtered.columns]

# ── Last 10 ───────────────────────────────────────────────────────────────────
section_header("Last 10 Detections")
st.dataframe(
    filtered[cols].head(10).rename(columns=COL_MAP),
    use_container_width=True, hide_index=True,
)

# ── Full table ────────────────────────────────────────────────────────────────
with st.expander(f"📄 Full table — {len(filtered)} rows"):
    st.dataframe(
        filtered[cols].rename(columns=COL_MAP),
        use_container_width=True, hide_index=True,
    )

# ── Search ────────────────────────────────────────────────────────────────────
section_header("Search")
query = st.text_input("Search by severity or defect status", placeholder="e.g. High, True, False…")
if query:
    mask = filtered.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)
    st.dataframe(filtered[mask][cols].rename(columns=COL_MAP), use_container_width=True, hide_index=True)
