import streamlit as st
import plotly.graph_objects as go

from utils.base_model import run_for_ui

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Solar Ninja", page_icon="☀️", layout="wide")

# -------------------------
# CSS (Lovable-like) - v2.1
# -------------------------
st.markdown("""
<style>
/* App background (grey) */
.stApp{
  background: #f6f7fb;
}

/* Constrain width like Lovable */
.block-container{
  max-width: 1240px;
  margin: 0 auto;
  padding-top: 1.1rem;
  padding-bottom: 2.2rem;
}

/* Hide Streamlit header space */
header {visibility: hidden; height: 0px;}
section.main > div {padding-top: 0.15rem;}

/* Brand (bigger) */
.brand { margin-top: 6px; }
.brand b { font-size: 1.35rem; font-weight: 950; color:#0f172a; }
.brand small { display:block; margin-top:2px; font-size: 1.0rem; color: rgba(2,6,23,.62); }

/* Hero */
.hero-wrap{ text-align:center; margin: 10px 0 26px; }
.hero-kicker{
  display:inline-flex; align-items:center; gap:8px;
  padding:9px 16px; border-radius:999px;
  background: rgba(245,158,11,0.14);
  color:#b45309; font-weight:900; font-size:1.02rem;
}
.hero-title{
  font-size:4.05rem;
  font-weight:950;
  color:#0f172a;
  margin:12px 0 8px;
  letter-spacing: -0.02em;
}
.hero-title span{ color:#f59e0b; }
.hero-sub{
  color:rgba(2,6,23,.65);
  font-size:1.10rem;
  margin:0 auto;
  max-width: 900px;
  line-height: 1.45;
}

/* Panels / Cards (white on grey background) */
.panel, .card{
  background:#fff;
  border:1px solid rgba(15,23,42,.08);
  border-radius:18px;
  box-shadow:0 10px 28px rgba(15,23,42,.06);
}
.panel{ padding:18px; }
.card{ padding:14px 16px; }

.section-title{
  font-size:1.02rem;
  font-weight:950;
  color:#0f172a;
  margin-bottom:12px;
}

/* KPI cards */
.kpi-card{
  min-height: 118px;
  display:flex;
  flex-direction:column;
  justify-content:center;
}
.card-title{ font-size:.92rem; color:rgba(2,6,23,.62); margin-bottom:8px; font-weight:800; }
.card-value{ font-size:1.85rem; font-weight:950; color:#0f172a; line-height:1.05; }

/* PDF card */
.pdf-card{
  min-height: 86px;
  display:flex;
  align-items:center;
  justify-content:center;
}

/* Month tiles (grey inside white card) */
.tile{
  background:#f1f5f9;
  border:1px solid rgba(15,23,42,.08);
  border-radius:16px;
  padding:14px 10px;
  text-align:center;
}
.tile .m{ font-size:.84rem; color:rgba(2,6,23,.62); font-weight:700; }
.tile .v{ font-size:1.18rem; font-weight:950; color:#0f172a; margin-top:4px; }

/* Buttons orange */
.stFormSubmitButton button, .stButton button, .stDownloadButton button{
  background:#f59e0b !important;
  color:#0b1220 !important;
  border:1px solid rgba(15,23,42,.12) !important;
  border-radius:14px !important;
  font-weight:950 !important;
  padding:0.62rem 0.95rem !important;
  box-shadow:0 10px 24px rgba(245,158,11,.18);
}
.stFormSubmitButton button:hover, .stButton button:hover, .stDownloadButton button:hover{
  filter: brightness(0.96);
}

/* Sliders: left part orange, right part green (BaseWeb) */
div[data-baseweb="slider"] > div{
  /* rail (unfilled) */
  background-color: #22c55e !important;
}
div[data-baseweb="slider"] div[data-testid="stTickBar"]{
  background: transparent !important;
}
div[data-baseweb="slider"] div[role="slider"]{
  background-color:#f59e0b !important;
  border-color:#f59e0b !important;
}
div[data-baseweb="slider"] div[aria-hidden="true"]{
  /* often the filled portion */
  background-color:#f59e0b !important;
}

/* Fallback selector for filled track (varies by Streamlit versions) */
div[data-baseweb="slider"] div > div{
  border-color:#f59e0b !important;
}

/* Remove weird empty spacers */
div[data-testid="stVerticalBlock"] > div:empty { display:none !important; }

/* Controlled spacers */
.sp18{ height:18px; }
.sp22{ height:22px; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Brand (left)
# -------------------------
st.markdown(
    "<div class='brand'><b>☀️ Solar Ninja</b><small>Solar Energy Optimization</small></div>",
    unsafe_allow_html=True
)

# -------------------------
# Hero (center)
# -------------------------
st.markdown("""
<div class="hero-wrap">
  <div class="hero-kicker">☀️ Optimize your solar system</div>
  <div class="hero-title">Maximize <span>generation</span></div>
  <div class="hero-sub">Calculate the optimal panel tilt angle and get the accurate forecast of annual generation for your location.</div>
</div>
""", unsafe_allow_html=True)

# -------------------------
# Main layout
# -------------------------
left, right = st.columns([0.38, 0.62], gap="large")

# -------------------------
# LEFT: Inputs (single white card)
# -------------------------
with left:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>System Parameters</div>", unsafe_allow_html=True)

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
    if submitted or "ui_result" not in st.session_state:
        with st.spinner("Running Solar Ninja calculations…"):
            st.session_state.ui_result = run_for_ui(
                latitude=latitude,
                longitude=longitude,
                system_power_kw=system_power_kw,
                user_tilt=user_tilt,
                user_azimuth=user_azimuth
            )

    out = st.session_state.ui_result

    # --- PDF card ABOVE KPI row ---
    pdf_sp, pdf_col = st.columns([0.70, 0.30], gap="medium")
    with pdf_sp:
        st.markdown("<div></div>", unsafe_allow_html=True)

    with pdf_col:
        st.markdown("<div class='card pdf-card'>", unsafe_allow_html=True)
        if out.pdf_bytes:
            st.download_button(
                "⬇️ Download PDF",
                data=out.pdf_bytes,
                file_name="solar_ninja_generation_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.button("⬇️ Download PDF", disabled=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sp18'></div>", unsafe_allow_html=True)

    # --- KPI row: 4 cards (Optimal angle / Your / Optimal / Potential) ---
    k1, k2, k3, k4 = st.columns([1, 1, 1, 1], gap="medium")

    with k1:
        st.markdown(f"""
        <div class="card kpi-card">
          <div class="card-title">Optimal angle</div>
          <div class="card-value">{out.optimal_angle}°</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="card kpi-card">
          <div class="card-title">Your generation</div>
          <div class="card-value">{out.annual_kwh_user:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="card kpi-card">
          <div class="card-title">Optimal generation</div>
          <div class="card-value">{out.annual_kwh_optimal:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="card kpi-card">
          <div class="card-title">Potential</div>
          <div class="card-value">{out.potential_pct:+.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='sp22'></div>", unsafe_allow_html=True)

    # --- Card: Monthly generation chart ---
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Monthly generation (kWh)</div>", unsafe_allow_html=True)

    df = out.monthly_chart_df

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["month"],
        y=df["kwh_user"],
        name="Your tilt",
        mode="lines",
        line=dict(color="#f59e0b", width=3)
    ))
    fig.add_trace(go.Scatter(
        x=df["month"],
        y=df["kwh_optimal_yearly"],
        name="Optimal tilt",
        mode="lines",
        line=dict(color="#22c55e", width=3)
    ))

    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="rgba(15,23,42,0.08)"),
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sp22'></div>", unsafe_allow_html=True)

    # --- Card: Optimal tilt by month (white) + grey month tiles ---
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Optimal tilt by month</div>", unsafe_allow_html=True)

    m_df = out.tilt_by_month_df
    months = m_df["Month"].tolist()
    tilts = m_df["BestTiltDeg"].astype(int).tolist()

    row1 = st.columns(6, gap="small")
    row2 = st.columns(6, gap="small")

    for i in range(min(6, len(months))):
        with row1[i]:
            st.markdown(
                f"<div class='tile'><div class='m'>{months[i]}</div><div class='v'>{tilts[i]}°</div></div>",
                unsafe_allow_html=True
            )

    for i in range(6, min(12, len(months))):
        with row2[i - 6]:
            st.markdown(
                f"<div class='tile'><div class='m'>{months[i]}</div><div class='v'>{tilts[i]}°</div></div>",
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sp22'></div>", unsafe_allow_html=True)

    # --- Card: Recommendations ---
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Recommendations</div>", unsafe_allow_html=True)
    for r in out.recommendations:
        st.markdown(f"- {r}")
    st.markdown("</div>", unsafe_allow_html=True)
