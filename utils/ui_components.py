"""
utils/ui_components.py — Reusable HTML/CSS UI building blocks + animation helpers.
"""
import streamlit as st
from pathlib import Path
import base64
import time

SEV_COLORS = {
    "High":   "#f85149",
    "Medium": "#d29922",
    "Low":    "#3fb950",
    "None":   "#58a6ff",
}

CHART_LAYOUT = dict(
    paper_bgcolor="#161b22", plot_bgcolor="#161b22",
    font_color="#c9d1d9",    title_font_color="#e6edf3",
    margin=dict(t=44, b=20, l=10, r=10),
)
GRID = dict(gridcolor="#21262d", zerolinecolor="#21262d")

_ASSETS = Path(__file__).parent.parent / "assets"


# ── Logo helpers ──────────────────────────────────────────────────────────────
def _logo_b64() -> str:
    if "_logo_b64" not in st.session_state:
        logo_path = _ASSETS / "Steelmark_logo.svg"
        if logo_path.exists():
            raw = logo_path.read_bytes()
            st.session_state["_logo_b64"] = base64.b64encode(raw).decode()
        else:
            st.session_state["_logo_b64"] = ""
    return st.session_state["_logo_b64"]


def logo_img_tag(size: int = 40) -> str:
    b64 = _logo_b64()
    if not b64:
        return "<span style='font-size:1.6rem'>🔩</span>"
    return (
        f"<img src='data:image/svg+xml;base64,{b64}' "
        f"width='{size}' height='{size}' style='vertical-align:middle;' />"
    )


# ── CSS ───────────────────────────────────────────────────────────────────────
def load_css():
    css_path = _ASSETS / "styles.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


# ── Loading helpers ───────────────────────────────────────────────────────────
def show_loading_screen(title: str = "Loading…", subtitle: str = "Please wait"):
    placeholder = st.empty()
    placeholder.markdown(f"""
    <div class='loading-screen'>
        <div class='loading-logo'>{logo_img_tag(64)}</div>
        <div class='loading-title'>{title}</div>
        <div class='loading-sub'>{subtitle}</div>
        <div class='dot-spinner'>
            <span></span><span></span><span></span>
        </div>
    </div>""", unsafe_allow_html=True)
    return placeholder


def skeleton_card(lines: int = 3):
    inner = "<div class='skeleton skeleton-title'></div>"
    inner += "".join(
        f"<div class='skeleton skeleton-text' style='width:{w}%'></div>"
        for w in ([90, 75, 60, 80, 70][:lines])
    )
    st.markdown(f"<div class='glass-card'>{inner}</div>", unsafe_allow_html=True)


def skeleton_kpis():
    cols = st.columns(4)
    for col in cols:
        with col:
            st.markdown(
                "<div class='skeleton skeleton-card'></div>",
                unsafe_allow_html=True,
            )


def detection_progress(label: str = "Analysing…"):
    ph  = st.empty()
    bar = ph.progress(0, text=label)
    return ph, bar


def animate_progress(bar, steps: int = 18, delay: float = 0.04):
    for i in range(1, steps + 1):
        bar.progress(int(i / steps * 100))
        time.sleep(delay)


# ── Result summary card ───────────────────────────────────────────────────────
def result_summary_card(result: dict) -> None:
    """
    Renders the full result section using native Streamlit widgets only.
    No raw HTML passed through columns — avoids Streamlit escaping bug.
    """
    is_steel = result.get("is_steel", False)
    detected = result.get("defect_detected", False)
    severity = result.get("severity", "None")
    prob_pct = result.get("steel_prob", 0) * 100
    area_pct = result.get("defect_area", 0)

    sev_color  = SEV_COLORS.get(severity, "#58a6ff")
    bar_color  = "#3fb950" if prob_pct >= 80 else ("#d29922" if prob_pct >= 50 else "#f85149")
    bar_width  = f"{prob_pct:.1f}%"

    # ── Status banner (self-contained single st.markdown call) ───────────────
    if not is_steel:
        banner_cls   = "notsteel"
        banner_icon  = "&#x1F527;"   # 🔩 as HTML entity — avoids emoji encoding issues
        banner_title = "Not a Steel Surface"
        banner_sub   = "Material classification failed &mdash; detection skipped"
        banner_color = "#8b949e"
    elif detected:
        banner_cls   = "defect"
        banner_icon  = "&#x26A0;&#xFE0F;"  # ⚠️
        banner_title = "Defect Detected &mdash; " + severity + " Severity"
        banner_sub   = str(area_pct) + "% of surface area affected"
        banner_color = SEV_COLORS.get(severity, "#f85149")
    else:
        banner_cls   = "clean"
        banner_icon  = "&#x2705;"   # ✅
        banner_title = "Surface is Clean"
        banner_sub   = "No defects detected on this steel surface"
        banner_color = "#3fb950"

    # Build the bar fill style without nested f-string braces
    bar_style = (
        "width:" + bar_width + ";"
        "background:linear-gradient(90deg," + bar_color + "88," + bar_color + ")"
    )

    html = (
        "<div class='result-summary'>"
        "<div class='result-summary-title'>Detection Report</div>"

        "<div class='status-banner " + banner_cls + "'>"
        "<div class='status-banner-icon'>" + banner_icon + "</div>"
        "<div>"
        "<div class='status-banner-title' style='color:" + banner_color + "'>"
        + banner_title +
        "</div>"
        "<div class='status-banner-sub'>" + banner_sub + "</div>"
        "</div>"
        "</div>"

        "<div class='stat-row'>"

        "<div class='stat-item'>"
        "<div class='stat-label'>Steel Probability</div>"
        "<div class='stat-value' style='color:" + bar_color + "'>" + f"{prob_pct:.1f}%" + "</div>"
        "<div class='prob-bar-track'>"
        "<div class='prob-bar-fill' style='" + bar_style + "'></div>"
        "</div>"
        "</div>"

        "<div class='stat-item'>"
        "<div class='stat-label'>Severity</div>"
        "<div class='stat-value' style='color:" + sev_color + "'>" + severity + "</div>"
        "</div>"

        "<div class='stat-item'>"
        "<div class='stat-label'>Defect Area</div>"
        "<div class='stat-value' style='color:#e6edf3'>" + str(area_pct) + "%</div>"
        "</div>"

        "</div>"  # stat-row
        "</div>"  # result-summary
    )

    st.markdown(html, unsafe_allow_html=True)


# ── Cards ─────────────────────────────────────────────────────────────────────
def kpi_card(value, label: str, color: str = "#58a6ff") -> str:
    return f"""
    <div class='kpi-card'>
        <div class='kpi-val' style='color:{color}'>{value}</div>
        <div class='kpi-label'>{label}</div>
    </div>"""


def badge(severity: str) -> str:
    cls = {"High": "badge-high", "Medium": "badge-medium",
           "Low": "badge-low", "None": "badge-none"}.get(severity, "badge-none")
    return f"<span class='badge {cls}'>{severity}</span>"


def feat_card(icon: str, title: str, desc: str) -> str:
    return f"""
    <div class='feat-card'>
        <div class='feat-icon'>{icon}</div>
        <div class='feat-title'>{title}</div>
        <div class='feat-desc'>{desc}</div>
    </div>"""


def result_card(html: str) -> str:
    return f"<div class='result-reveal'>{html}</div>"


# ── Layout helpers ────────────────────────────────────────────────────────────
def section_header(text: str):
    st.markdown(f"<div class='section-header'>{text}</div>", unsafe_allow_html=True)


def empty_state(icon: str, text: str):
    st.markdown(f"""
    <div class='empty-state'>
        <div class='empty-state-icon'>{icon}</div>
        <div class='empty-state-text'>{text}</div>
    </div>""", unsafe_allow_html=True)


def sidebar_brand():
    st.markdown(f"""
    <div class='sidebar-brand'>
        {logo_img_tag(36)}
        <span class='sidebar-brand-text'>Steel Defect Pro</span>
    </div>""", unsafe_allow_html=True)


def sidebar_footer():
    st.markdown(
        "<div class='sidebar-footer'>Built by Dhruvil 🚀</div>",
        unsafe_allow_html=True,
    )
