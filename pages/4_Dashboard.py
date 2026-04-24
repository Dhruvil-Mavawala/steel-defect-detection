import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

from utils.ui_components import (
    load_css, sidebar_brand, sidebar_footer,
    kpi_card, section_header, empty_state,
    SEV_COLORS, CHART_LAYOUT, GRID,
)
from utils.model import DEVICE
from utils.firebase import fetch_history

st.set_page_config(page_title="Dashboard · Steel Defect Pro", page_icon="📊", layout="wide")
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
<div class='anim-1'>
    <span style='font-size:1.8rem;font-weight:800;color:#e6edf3'>📊 Analytics Dashboard</span>
    <p style='color:#8b949e;margin:4px 0 0'>Real-time insights from your detection history</p>
</div>""", unsafe_allow_html=True)
st.markdown("---")

# ── Load with progress ────────────────────────────────────────────────────────
load_ph  = st.empty()
load_bar = load_ph.progress(0, text="Connecting to Firebase…")

with st.spinner("📡 Loading analytics…"):
    for i in range(1, 40):
        load_bar.progress(i, text="Connecting to Firebase…")
        time.sleep(0.008)
    records = fetch_history(limit=500)
    for i in range(40, 101):
        load_bar.progress(i, text="Processing data…")
        time.sleep(0.005)

load_ph.empty()

if not records:
    empty_state("📊", "No data yet — run some detections first, then come back here.")
    st.stop()

st.success(f"✅ Loaded {len(records)} records successfully!")
time.sleep(0.4)
# clear the success so it doesn't persist
st.empty()

df = pd.DataFrame(records)
if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df["date"]      = df["timestamp"].dt.date

total        = len(df)
defect_count = int(df["defect_detected"].sum()) if "defect_detected" in df.columns else 0
clean_count  = total - defect_count
defect_rate  = defect_count / total * 100 if total else 0
avg_conf     = df["steel_prob"].mean() if "steel_prob" in df.columns else 0

# ── KPIs ──────────────────────────────────────────────────────────────────────
section_header("Key Metrics")
st.markdown("<div class='result-reveal'>", unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card(total, "Total Scans", "#58a6ff"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card(defect_count, "Defects Found", "#f85149"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card(f"{defect_rate:.1f}%", "Defect Rate", "#d29922"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card(f"{avg_conf:.1f}%", "Avg Confidence", "#3fb950"), unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Pie + Bar ──────────────────────────────────────────────────────────
section_header("Defect Overview")
with st.spinner("📊 Rendering charts…"):
    time.sleep(0.3)

ch1, ch2 = st.columns(2)

with ch1:
    fig_pie = px.pie(
        values=[defect_count, clean_count],
        names=["Defect", "No Defect"],
        title="Defect vs No Defect",
        color_discrete_sequence=["#f85149", "#3fb950"],
        hole=0.45,
    )
    fig_pie.update_traces(textfont_color="#e6edf3", textinfo="percent+label")
    fig_pie.update_layout(**CHART_LAYOUT, legend=dict(font=dict(color="#8b949e")))
    st.plotly_chart(fig_pie, use_container_width=True)

with ch2:
    if "severity" in df.columns:
        sev_df = df["severity"].value_counts().reset_index()
        sev_df.columns = ["Severity", "Count"]
        fig_bar = px.bar(
            sev_df, x="Severity", y="Count",
            title="Severity Distribution",
            color="Severity",
            color_discrete_map=SEV_COLORS,
            text="Count",
        )
        fig_bar.update_traces(textfont_color="#e6edf3", textposition="outside")
        fig_bar.update_layout(**CHART_LAYOUT, showlegend=False, xaxis=GRID, yaxis=GRID)
        st.plotly_chart(fig_bar, use_container_width=True)

# ── Row 2: Line chart ─────────────────────────────────────────────────────────
if "date" in df.columns and df["date"].notna().any():
    section_header("Detections Over Time")
    with st.spinner("📈 Building trend chart…"):
        time.sleep(0.2)

    daily     = df.groupby("date").size().reset_index(name="Scans")
    daily_def = (df[df["defect_detected"] == True]
                 .groupby("date").size().reset_index(name="Defects"))
    daily = daily.merge(daily_def, on="date", how="left").fillna(0)

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=daily["date"], y=daily["Scans"], name="Total Scans",
        line=dict(color="#58a6ff", width=2.5), mode="lines+markers",
        marker=dict(size=6),
    ))
    fig_line.add_trace(go.Scatter(
        x=daily["date"], y=daily["Defects"], name="Defects",
        line=dict(color="#f85149", width=2.5), mode="lines+markers",
        marker=dict(size=6),
    ))
    fig_line.update_layout(
        title="Daily Scan Volume", **CHART_LAYOUT,
        xaxis=GRID, yaxis=GRID,
        legend=dict(font=dict(color="#8b949e")),
    )
    st.plotly_chart(fig_line, use_container_width=True)

# ── Row 3: Histogram + daily bar ─────────────────────────────────────────────
section_header("Confidence & Daily Breakdown")
h1, h2 = st.columns(2)

with h1:
    if "steel_prob" in df.columns:
        fig_hist = px.histogram(
            df, x="steel_prob", nbins=20,
            title="Steel Confidence Distribution",
            color_discrete_sequence=["#58a6ff"],
            labels={"steel_prob": "Confidence (%)"},
        )
        fig_hist.update_layout(**CHART_LAYOUT, xaxis=GRID, yaxis=GRID)
        st.plotly_chart(fig_hist, use_container_width=True)

with h2:
    if "date" in df.columns and df["date"].notna().any():
        daily_bar = df.groupby("date").size().reset_index(name="Scans")
        fig_daily = px.bar(
            daily_bar, x="date", y="Scans",
            title="Daily Detection Count",
            color_discrete_sequence=["#1f6feb"],
            text="Scans",
        )
        fig_daily.update_traces(textfont_color="#e6edf3", textposition="outside")
        fig_daily.update_layout(**CHART_LAYOUT, xaxis=GRID, yaxis=GRID)
        st.plotly_chart(fig_daily, use_container_width=True)
