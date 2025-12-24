import streamlit as st
import plotly.graph_objects as go

from utils.base_model import run_for_ui

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Solar Ninja", page_icon="☀️", layout="wide")

# -------------------------
# CSS (Lovable-like) - v2
# -------------------------
st.markdown("""
<style>
/* Constrain width like Lovable (a bit wider than before) */
.block-container{
  max-width: 1240px;
  margin: 0 auto;
  padding-top: 1.2rem;
  padding-bottom: 2.2rem;
}

/* Hide Streamlit header space */
header {visibility: hidden; height: 0px;}

/* Reduce top padding caused by Streamlit */
section.main > div {padding-top: 0.2rem;}

/* Brand */
.brand { margin-top: 6px; }
.brand b { font-size: 1.05rem; }
.brand small {color: rgba(2,6,23,.6);}

/* Centered hero */
.hero-wrap{ text-align:center; margin: 14px 0 26px; }
.hero-kicker{
  display:inline-flex; align-items:center; gap:8px;
  padding:7px 14px; border-radius:999px;
  background: rgba(245,158,11,0.12);
  color:#b45309; font-weight:800; font-size:0.9rem;
}
.hero-title{
  font-size:3.7rem;
  font-weight:950;
  color:#0f172a;
  margin:12px 0 8px;
  letter-spacing: -0.02em;
}
.hero-title span{ color:#f59e0b; }
.hero-sub{
  color:rgba(2,6,23,.65);
  font-size:1.08rem;
  margin:0 auto;
  max-width: 820px;
  line-height: 1.45;
}

/* Panels and cards */
.panel{
  background:#fff;
  border:1px solid rgba(15,23,42,.08);
  border-radius:18px;
  padding:18px;
  box-shadow:0 10px 28px rgba(15,23,42,.06);
}
.card{
  background:#fff;
  border:1px solid rgba(15,23,42,.08);
  border-radius:16px;
  padding:14px 16px;
  box-shadow:0 10px 28px rgba(15,23,42,.06);
}
.section-title{
  font-size:1.02rem;
  font-weight:900;
  color:#0f172a;
  margin-bottom:12px;
}

/* KPI */
.kpi-card{
  min-height: 120px;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
}
.card-title{ font-size:.88rem; color:rgba(2,6,23,.6); margin-bottom:6px; }
.card-value{ font-size:1.75rem; font-weight:950; color:#0f172a; line-height:1.05; }
.card-sub{ font-size:.82rem; color:rgba(2,6,23,.55); margin-top:6px; }

/* Tiles (Lovable grey) */
.tile{
  background:#f1f5f9;
  border:1px solid rgba(15,23,42,.08);
  border-radius:16px;
  padding:14px 10px;
  text-align:center;
}
.tile .m{ font-size:.82rem; color:rgba(2,6,23,.62); }
.tile .v{ font-size:1.18rem; font-weight:950; color:#0f172a; margin-top:4px; }

/* Buttons orange (submit / normal / download) */
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

/* Slider: force orange as much as Streamlit allows */
div[data-baseweb="slider"] div[role="slider"]{
  background-color:#f59e0b !important;
  border-color:#f59e0b !important;
}
div[data-baseweb="slider"] div{
  border-color:#f59e0b !important;
}

/* Remove weird empty "bars"/spacers some themes create */
div[data-testid="stVerticalBlock"] > div:empty { display:none !important; }

/* Nice spacing helper */
.spacer-14{ height:14px; }
.spacer-18{ height:18px; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Top brand (left)
# -------------------------
st.markdown(
    "<div class='brand'><b>☀️ Solar Ninja</b><br/><small>Solar Energy Optimization</small></div>",
    unsafe_allow_html=True
)

# -------------------------
# Hero (center)
# -------------------------
st.markdown("""
<div class="hero-wrap">
  <div class="hero-kicker">☀️ Optimize your solar system</div>
  <div class="hero-title">Maximize <span>generation</span></div>
  <div class="hero-sub">Calculate the Optimal Panel Tilt Angle and Get the Accurate Forecast of Annual Generation for Your Location.</div>
</div>
""", unsafe_allow_html=True)

# -------------------------
# Main layout
# -------------------------
left, right = st.columns([0.38, 0.62], gap="large")

# -------------------------
# LEFT: Inputs (Calculator)
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

    # KPI + PDF button
    k1, k2, k3, k4 = st.columns([1, 1, 1, 0.92], gap="medium")

    with k1:
        st.markdown(f"""
        <div class="card kpi-card">
          <div>
            <div class="card-title">Optimal angle</div>
            <div class="card-value">{out.optimal_angle}°</div>
          </div>
          <div class="card-sub">Annual optimum</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="card kpi-card">
          <div>
            <div class="card-title">Your generation</div>
            <div class="card-value">{out.annual_kwh_user:,.0f}</div>
          </div>
          <div class="card-sub">kWh / year</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="card kpi-card">
          <div>
            <div class="card-title">Potential</div>
            <div class="card-value">+{out.potential_pct:.1f}%</div>
          </div>
          <div class="card-sub">vs current tilt</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        # Make this look like a "card" button area
        st.markdown("<div class='card kpi-card' style='display:flex; align-items:center; justify-content:center;'>", unsafe_allow_html=True)
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

    st.markdown("<div class='spacer-18'></div>", unsafe_allow_html=True)

    # Monthly generation chart
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

    st.markdown("<div class='spacer-18'></div>", unsafe_allow_html=True)

    # Optimal tilt by month
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

    st.markdown("<div class='spacer-18'></div>", unsafe_allow_html=True)

    # Recommendations
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Recommendations</div>", unsafe_allow_html=True)
    for r in out.recommendations:
        st.markdown(f"- {r}")
    st.markdown("</div>", unsafe_allow_html=True)
