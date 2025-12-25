import streamlit as st
import plotly.graph_objects as go

from utils.base_model import run_for_ui


def spacer(px: int = 18):
    st.markdown(f"<div style='height:{px}px'></div>", unsafe_allow_html=True)


# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Solar Ninja", page_icon="☀️", layout="wide")

# -------------------------
# CSS (Lovable-like, stable for Streamlit)
# -------------------------
st.markdown(
    """
<style>
/* Page background */
.stApp{ background:#f6f7fb; }

/* Constrain width */
.block-container{
  max-width:1240px;
  margin: 0 auto;
  padding-top: 1.05rem;
  padding-bottom: 2.2rem;
}

/* Hide header gap */
header {visibility: hidden; height: 0px;}

/* Brand */
.brand{ margin-top:6px; }
.brand b{ font-size:1.38rem; font-weight:950; color:#0f172a; }
.brand small{
  display:block; margin-top:2px;
  font-size:1.03rem; color:rgba(2,6,23,.62);
}

/* Hero */
.hero-wrap{ text-align:center; margin:10px 0 26px; }
.hero-kicker{
  display:inline-flex; align-items:center; gap:8px;
  padding:9px 16px; border-radius:999px;
  background:rgba(245,158,11,0.14);
  color:#b45309; font-weight:900; font-size:1.08rem;
}
.hero-title{
  font-size:4.15rem; font-weight:950; color:#0f172a;
  margin:12px 0 8px; letter-spacing:-0.02em;
}
.hero-title span{ color:#f59e0b; }
.hero-sub{
  color:rgba(2,6,23,.65);
  font-size:1.10rem;
  margin:0 auto; max-width:900px;
  line-height:1.45;
}

/* SECTION CONTAINERS: ONLY st.container(border=True) */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:#ffffff !important;
  border:0 !important;
  border-radius:22px !important;
  box-shadow:0 10px 28px rgba(15,23,42,.08) !important;
  padding:0 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div{
  padding:18px 18px 16px 18px !important;
}

/* Titles inside containers */
.sn-title{
  font-size:1.02rem;
  font-weight:950;
  color:#0f172a;
  margin:0 0 12px 0;
}

/* KPI cards */
.kpi{
  background:#fff;
  border-radius:22px;
  box-shadow:0 10px 28px rgba(15,23,42,.08);
  padding:14px 16px;
  min-height:118px;
  display:flex; flex-direction:column; justify-content:center;
}
.kpi .t{ font-size:.92rem; color:rgba(2,6,23,.62); margin-bottom:10px; font-weight:850; }
.kpi .v{ font-size:1.88rem; font-weight:950; color:#0f172a; line-height:1.05; }

/* Month tiles - equal size, content fits */
.tile{
  background:#f1f5f9 !important;
  border:1px solid rgba(15,23,42,.08) !important;
  border-radius:16px !important;
  padding:12px 10px !important;
  text-align:center !important;
  width:100% !important;
  min-height:92px !important;
  display:flex !important;
  flex-direction:column !important;
  justify-content:center !important;
  align-items:center !important;
}
.tile .m{
  font-size:.74rem;
  color:rgba(2,6,23,.62);
  font-weight:800;
  line-height:1.12;
  max-width:92px;
  white-space:normal;
  word-break:break-word;
}
.tile .v{ font-size:1.18rem; font-weight:950; color:#0f172a; margin-top:6px; }

/* Buttons: force orange (Download + Calculate) */
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stDownloadButton"] button,
div[data-testid="stButton"] button{
  background:#f59e0b !important;
  color:#0b1220 !important;
  border:0 !important;
  border-radius:14px !important;
  font-weight:950 !important;
  padding:0.62rem 0.95rem !important;
  box-shadow:0 10px 24px rgba(245,158,11,.18) !important;
}
div[data-testid="stFormSubmitButton"] button:hover,
div[data-testid="stDownloadButton"] button:hover,
div[data-testid="stButton"] button:hover{
  filter:brightness(0.96);
}

/* Inputs rounding */
div[data-testid="stNumberInput"] input{ border-radius:14px !important; }

/* Slider (best effort) */
div[data-baseweb="slider"] div[role="slider"]{
  background-color:#f59e0b !important;
  border-color:#f59e0b !important;
}
div[data-baseweb="slider"] span{
  color:#f59e0b !important;
  font-weight:900 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------
# Brand (left top)
# -------------------------
st.markdown(
    "<div class='brand'><b>☀️ Solar Ninja</b><small>Solar Energy Optimization</small></div>",
    unsafe_allow_html=True,
)

# -------------------------
# Hero (center)
# -------------------------
st.markdown(
    """
<div class="hero-wrap">
  <div class="hero-kicker">☀️ Optimize your solar system</div>
  <div class="hero-title">Maximize <span>generation</span></div>
  <div class="hero-sub">Calculate the optimal panel tilt angle and get the accurate forecast of annual generation for your location.</div>
</div>
""",
    unsafe_allow_html=True,
)

# -------------------------
# Main layout
# -------------------------
left, right = st.columns([0.38, 0.62], gap="large")

# -------------------------
# LEFT: System Parameters (ONE white container)
# -------------------------
with left:
    with st.container(border=True):
        st.markdown("<div class='sn-title'>System Parameters</div>", unsafe_allow_html=True)

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
                user_azimuth=user_azimuth,
            )

    out = st.session_state.ui_result

    # Download button (NO container, just right-aligned)
    a, b = st.columns([0.72, 0.28])
    with a:
        st.empty()
    with b:
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

    spacer(16)

    # KPI row
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        st.markdown(
            f"<div class='kpi'><div class='t'>Optimal angle</div><div class='v'>{out.optimal_angle}°</div></div>",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"<div class='kpi'><div class='t'>Your generation</div><div class='v'>{out.annual_kwh_user:,.0f}</div></div>",
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"<div class='kpi'><div class='t'>Optimal generation</div><div class='v'>{out.annual_kwh_optimal:,.0f}</div></div>",
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"<div class='kpi'><div class='t'>Potential</div><div class='v'>{out.potential_pct:+.1f}%</div></div>",
            unsafe_allow_html=True,
        )

    spacer(18)

    # Monthly chart container (white)
    with st.container(border=True):
        st.markdown("<div class='sn-title'>Monthly generation (kWh)</div>", unsafe_allow_html=True)

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
            height=370,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="rgba(15,23,42,0.08)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    spacer(18)

    # Optimal tilt by month container (white)
    with st.container(border=True):
        st.markdown("<div class='sn-title'>Optimal tilt by month</div>", unsafe_allow_html=True)

        m_df = out.tilt_by_month_df
        months = m_df["Month"].tolist()
        tilts = m_df["BestTiltDeg"].astype(int).tolist()

        # Use columns with consistent gaps
        row1 = st.columns(6, gap="small")
        row2 = st.columns(6, gap="small")

        for i in range(min(6, len(months))):
            with row1[i]:
                st.markdown(
                    f"<div class='tile'><div class='m'>{months[i]}</div><div class='v'>{tilts[i]}°</div></div>",
                    unsafe_allow_html=True,
                )

        for i in range(6, min(12, len(months))):
            with row2[i - 6]:
                st.markdown(
                    f"<div class='tile'><div class='m'>{months[i]}</div><div class='v'>{tilts[i]}°</div></div>",
                    unsafe_allow_html=True,
                )

    spacer(18)

    # Recommendations container (white)
    with st.container(border=True):
        st.markdown("<div class='sn-title'>Recommendations</div>", unsafe_allow_html=True)
        for r in out.recommendations:
            st.markdown(f"- {r}")
