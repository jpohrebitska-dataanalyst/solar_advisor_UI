# app.py
import streamlit as st
import plotly.graph_objects as go

from utils.base_model import run_for_ui

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Solar Ninja", page_icon="☀️", layout="wide")

# -------------------------
# CSS (Lovable-like v2)
# -------------------------
st.markdown(
    """
<style>
:root{
  --sn-bg:#f6f7fb;
  --sn-white:#ffffff;
  --sn-text:#0f172a;
  --sn-muted:rgba(2,6,23,.62);
  --sn-border:rgba(15,23,42,.08);
  --sn-shadow:0 16px 40px rgba(15,23,42,.08);
  --sn-orange:#f59e0b;
  --sn-green:#22c55e;
}

/* App background */
.stApp{ background: var(--sn-bg) !important; }

/* Width like Lovable */
.block-container{
  max-width: 1120px;
  margin: 0 auto;
  padding-top: 1.6rem;
  padding-bottom: 3rem;
}

/* Hide Streamlit chrome */
header {visibility: hidden; height: 0px;}
footer {visibility: hidden; height: 0px;}
#MainMenu {visibility: hidden;}

/* Brand */
.sn-brand{ margin: 4px 0 10px; }
.sn-brand .t{ font-size: 1.45rem; font-weight: 950; color: var(--sn-text); }
.sn-brand .s{ font-size: 1.02rem; color: var(--sn-muted); margin-top: 2px; }

/* Hero */
.sn-hero{ text-align:center; margin: 22px 0 18px; }
.sn-kicker{
  display:inline-flex; align-items:center; gap:10px;
  padding:10px 16px; border-radius:999px;
  background: rgba(245,158,11,0.14);
  color:#b45309; font-weight:900; font-size:0.95rem;
}
.sn-title{
  font-size:4.1rem; font-weight:1000; letter-spacing:-0.04em;
  color:var(--sn-text); margin:12px 0 8px;
}
.sn-title span{ color: var(--sn-orange); }
.sn-sub{
  color: rgba(2,6,23,.62);
  font-size: 1.08rem;
  margin: 0 auto;
  max-width: 760px;
}

/* Big white sections (ONLY what we wrap) */
.sn-section{
  background: var(--sn-white) !important;
  border: 1px solid rgba(15,23,42,.06);
  border-radius: 28px;
  box-shadow: var(--sn-shadow);
  padding: 22px 22px;
}
.sn-section-title{
  font-size: 1.08rem;
  font-weight: 950;
  color: var(--sn-text);
  margin-bottom: 10px;
}

/* KPI cards */
.sn-kpi{
  background: var(--sn-white);
  border: 1px solid rgba(15,23,42,.06);
  border-radius: 24px;
  box-shadow: 0 12px 28px rgba(15,23,42,.07);
  padding: 16px 18px;
  min-height: 92px;
}
.sn-kpi .k{ font-size:.92rem; font-weight:850; color: rgba(2,6,23,.62); }
.sn-kpi .v{
  margin-top: 8px;
  font-size: 1.95rem;
  font-weight: 1000;
  color: var(--sn-text);
  letter-spacing: -0.02em;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.sn-kpi .sub{
  margin-top: 6px;
  font-size: .88rem;
  color: rgba(2,6,23,.55);
}

/* Download button: no extra frame (we won't wrap it in a card) */
.stDownloadButton button{
  background: var(--sn-orange) !important;
  color: #0b1220 !important;
  border: 1px solid rgba(15,23,42,.10) !important;
  border-radius: 16px !important;
  font-weight: 950 !important;
  padding: 0.75rem 1.05rem !important;
  box-shadow: 0 10px 24px rgba(245,158,11,.22) !important;
}
.stDownloadButton button:hover{ filter: brightness(0.98); }

/* Calculate + all buttons */
.stFormSubmitButton button, .stButton button{
  background: var(--sn-orange) !important;
  color: #0b1220 !important;
  border: 1px solid rgba(15,23,42,.10) !important;
  border-radius: 16px !important;
  font-weight: 950 !important;
  padding: 0.75rem 1.05rem !important;
  box-shadow: 0 10px 24px rgba(245,158,11,.18) !important;
}
.stFormSubmitButton button:hover, .stButton button:hover{ filter: brightness(0.98); }

/* Inputs a bit cleaner on white */
div[data-testid="stNumberInput"] input{
  background: rgba(15,23,42,.03) !important;
  border: 1px solid rgba(15,23,42,.06) !important;
  border-radius: 14px !important;
}

/* Slider styling (orange filled / green rest) */
div[data-baseweb="slider"] div[aria-hidden="true"]{
  background: var(--sn-green) !important;     /* unfilled (to the right) */
  border-radius: 999px !important;
}
div[data-baseweb="slider"] div[aria-hidden="true"] > div{
  background: var(--sn-orange) !important;    /* filled (to the left) */
  border-radius: 999px !important;
}
div[data-baseweb="slider"] div[role="slider"]{
  background: var(--sn-orange) !important;
  border-color: var(--sn-orange) !important;
}
div[data-baseweb="slider"] span{
  color: var(--sn-orange) !important;
  font-weight: 900 !important;
}

/* Month tiles grid (equal size + stable gaps) */
.sn-tiles{
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
  margin-top: 12px;
}
@media (max-width: 980px){
  .sn-tiles{ grid-template-columns: repeat(3, 1fr); }
}
.sn-tile{
  background: #f1f5f9;
  border: 1px solid rgba(15,23,42,.06);
  border-radius: 20px;
  padding: 14px 10px;
  text-align: center;
  min-height: 74px;
}
.sn-tile .m{
  font-size: .80rem;
  font-weight: 800;
  color: rgba(2,6,23,.60);
  line-height: 1.1;
  margin-bottom: 6px;
}
.sn-tile .d{
  font-size: 1.22rem;
  font-weight: 1000;
  color: var(--sn-text);
  line-height: 1.0;
  white-space: nowrap;
}

/* Plotly background inside white card */
.js-plotly-plot, .plot-container{
  background: transparent !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------
# Brand (top-left)
# -------------------------
st.markdown(
    """
<div class="sn-brand">
  <div class="t">☀️ Solar Ninja</div>
  <div class="s">Solar Energy Optimization</div>
</div>
""",
    unsafe_allow_html=True,
)

# -------------------------
# Hero (center)
# -------------------------
st.markdown(
    """
<div class="sn-hero">
  <div class="sn-kicker">☀️ Optimize your solar system</div>
  <div class="sn-title">Maximize <span>generation</span></div>
  <div class="sn-sub">Calculate the optimal panel tilt angle and get the accurate forecast of annual generation for your location.</div>
</div>
""",
    unsafe_allow_html=True,
)

# -------------------------
# Main layout
# -------------------------
left, right = st.columns([0.40, 0.60], gap="large")

# Avoid unbound variable on first run
submitted = False

# -------------------------
# LEFT: System Parameters (white container)
# -------------------------
with left:
    st.markdown('<div class="sn-section">', unsafe_allow_html=True)
    st.markdown('<div class="sn-section-title">System Parameters</div>', unsafe_allow_html=True)

    with st.form("calc_form", border=False):
        st.markdown("**📍 Location**")
        latitude = st.number_input("Latitude (°)", value=50.45, format="%.4f")
        longitude = st.number_input("Longitude (°)", value=30.52, format="%.4f")

        st.divider()

        st.markdown("**⚡ System power**")
        system_power_kw = st.number_input("System power (kW)", value=10.0, step=0.5)

        st.divider()

        st.markdown("**📐 Panel tilt**")
        user_tilt = st.slider("Tilt angle (°)", 0, 90, 45)

        st.divider()

        st.markdown("**🧭 Orientation (azimuth)**")
        user_azimuth = st.slider("Azimuth (°)", 0, 360, 180)

        submitted = st.form_submit_button("⚡ Calculate", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# RIGHT: Results
# -------------------------
with right:
    # Run calc only when submitted, or on very first load
    if submitted or "ui_result" not in st.session_state:
        with st.spinner("Running Solar Ninja calculations…"):
            st.session_state.ui_result = run_for_ui(
                latitude=latitude,
                longitude=longitude,
                system_power_kw=system_power_kw,
                user_tilt=user_tilt,
                user_azimuth=user_azimuth,
            )

    out = st.session_state.ui_result

    # Top row: Download PDF (no container/frame)
    top_l, top_r = st.columns([0.62, 0.38], gap="small")
    with top_r:
        if out.pdf_bytes:
            st.download_button(
                "⬇️ Download PDF",
                data=out.pdf_bytes,
                file_name="solar_ninja_generation_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button("⬇️ Download PDF", disabled=True, use_container_width=True)

    st.write("")

    # KPI row (4 cards)
    k1, k2, k3, k4 = st.columns(4, gap="medium")

    with k1:
        st.markdown(
            f"""
<div class="sn-kpi">
  <div class="k">Optimal angle</div>
  <div class="v">{int(out.optimal_angle)}°</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with k2:
        st.markdown(
            f"""
<div class="sn-kpi">
  <div class="k">Your generation</div>
  <div class="v">{out.annual_kwh_user:,.0f}</div>
  <div class="sub">kWh / year</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with k3:
        st.markdown(
            f"""
<div class="sn-kpi">
  <div class="k">Optimal generation</div>
  <div class="v">{out.annual_kwh_optimal:,.0f}</div>
  <div class="sub">kWh / year</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with k4:
        sign = "+" if out.potential_pct >= 0 else ""
        st.markdown(
            f"""
<div class="sn-kpi">
  <div class="k">Potential</div>
  <div class="v">{sign}{out.potential_pct:.1f}%</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.write("")

    # Monthly generation (white container)
    st.markdown('<div class="sn-section">', unsafe_allow_html=True)
    st.markdown('<div class="sn-section-title">Monthly generation (kWh)</div>', unsafe_allow_html=True)

    df = out.monthly_chart_df

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=df["kwh_user"],
            name="Your tilt",
            mode="lines",
            line=dict(color="#f59e0b", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=df["kwh_optimal_yearly"],
            name="Optimal tilt",
            mode="lines",
            line=dict(color="#22c55e", width=3),
        )
    )

    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="rgba(15,23,42,0.08)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    # Optimal tilt by month (white container + equal tiles)
    st.markdown('<div class="sn-section">', unsafe_allow_html=True)
    st.markdown('<div class="sn-section-title">Optimal tilt by month</div>', unsafe_allow_html=True)

    m_df = out.tilt_by_month_df  # columns: Month, BestTiltDeg
    months = m_df["Month"].tolist()
    tilts = m_df["BestTiltDeg"].astype(int).tolist()

    tiles_html = '<div class="sn-tiles">'
    for m, t in zip(months, tilts):
        tiles_html += f'<div class="sn-tile"><div class="m">{m}</div><div class="d">{t}°</div></div>'
    tiles_html += "</div>"

    st.markdown(tiles_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    # Recommendations (white container)
    st.markdown('<div class="sn-section">', unsafe_allow_html=True)
    st.markdown('<div class="sn-section-title">Recommendations</div>', unsafe_allow_html=True)
    for r in out.recommendations:
        st.markdown(f"- {r}")
    st.markdown("</div>", unsafe_allow_html=True)
