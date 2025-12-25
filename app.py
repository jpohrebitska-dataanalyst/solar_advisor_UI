import streamlit as st
import plotly.graph_objects as go

from utils.base_model import run_for_ui

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Solar Ninja", page_icon="☀️", layout="wide")

# -------------------------
# CSS (Lovable-like)
# -------------------------
st.markdown(
    """
<style>
/* Page background */
html, body, [data-testid="stAppViewContainer"]{
  background: #f6f7fb !important;
}

/* Constrain width like Lovable */
.block-container{
  max-width: 1120px;
  margin: 0 auto;
  padding-top: 1.2rem;
  padding-bottom: 2.2rem;
}

/* Hide Streamlit header space */
header {visibility: hidden; height: 0px;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Brand */
.sn-brand{
  margin-top: 6px;
  margin-bottom: 6px;
}
.sn-brand .t{
  font-size: 1.35rem;
  font-weight: 900;
  color:#0f172a;
  display:flex;
  align-items:center;
  gap:10px;
}
.sn-brand .s{
  margin-top: 4px;
  font-size: 1.02rem;
  color: rgba(2,6,23,.62);
}

/* Hero */
.sn-hero{ text-align:center; margin: 18px 0 10px; }
.sn-kicker{
  display:inline-flex; align-items:center; gap:8px;
  padding:8px 16px; border-radius:999px;
  background: rgba(245,158,11,0.14);
  color:#b45309; font-weight:800; font-size:1rem;
}
.sn-title{
  margin: 14px 0 6px;
  font-size: 4.0rem;
  font-weight: 950;
  color:#0f172a;
  letter-spacing:-0.02em;
}
.sn-title span{ color:#f59e0b; }
.sn-sub{
  margin: 0 auto;
  max-width: 860px;
  color: rgba(2,6,23,.62);
  font-size: 1.1rem;
  line-height: 1.55;
}

/* ONLY the 4 required white containers (explicit wrappers) */
.sn-card{
  background:#ffffff;
  border: 1px solid rgba(15,23,42,.06);
  border-radius: 22px;
  box-shadow: 0 14px 40px rgba(15,23,42,.06);
  padding: 18px 18px;
}
.sn-card-title{
  font-size: 1.05rem;
  font-weight: 900;
  color:#0f172a;
  margin-bottom: 10px;
}

/* KPI cards */
.sn-kpi{
  background:#ffffff;
  border: 1px solid rgba(15,23,42,.06);
  border-radius: 20px;
  box-shadow: 0 10px 26px rgba(15,23,42,.06);
  padding: 16px 18px;
  height: 110px;
  display:flex;
  flex-direction:column;
  justify-content:center;
}
.sn-kpi .k{
  font-size: .9rem;
  color: rgba(2,6,23,.62);
  font-weight: 700;
  margin-bottom: 6px;
}
.sn-kpi .v{
  font-size: 2.0rem;
  font-weight: 950;
  color:#0f172a;
  line-height: 1.05;
  white-space: nowrap;
}
.sn-kpi .sub{
  font-size:.85rem;
  color: rgba(2,6,23,.55);
  margin-top: 6px;
}

/* Download button wrapper (NO container frame!) */
.sn-download-wrap{
  display:flex;
  justify-content:flex-end;
  align-items:flex-start;
  margin-top: 2px;
  margin-bottom: 10px;
}

/* Tiles grid */
.sn-tiles{
  display:grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px;
}
@media (max-width: 980px){
  .sn-tiles{ grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
.sn-tile{
  background:#f1f5f9;
  border: 1px solid rgba(15,23,42,.06);
  border-radius: 18px;
  height: 82px;
  display:flex;
  flex-direction:column;
  justify-content:center;
  align-items:center;
  text-align:center;
}
.sn-tile .m{
  font-size: .78rem;
  font-weight: 800;
  color: rgba(2,6,23,.62);
  line-height: 1.1;
}
.sn-tile .d{
  margin-top: 6px;
  font-size: 1.25rem;
  font-weight: 950;
  color:#0f172a;
  line-height: 1;
}

/* Orange buttons (Calculate + Download) */
.stFormSubmitButton button,
.stButton button,
.stDownloadButton button{
  background:#f59e0b !important;
  color:#0b1220 !important;
  border: 0px solid transparent !important;
  border-radius: 16px !important;
  font-weight: 950 !important;
  padding: 0.70rem 1.05rem !important;
  box-shadow: 0 10px 22px rgba(245,158,11,.20) !important;
}
.stFormSubmitButton button:hover,
.stButton button:hover,
.stDownloadButton button:hover{
  filter: brightness(0.97);
}

/* Slider thumb */
div[data-baseweb="slider"] div[role="slider"]{
  background-color:#f59e0b !important;
  border-color:#f59e0b !important;
  box-shadow: 0 0 0 3px rgba(245,158,11,.25) !important;
}

/* Slider track attempt: orange filled + green remaining (BaseWeb). 
   Streamlit/BaseWeb markup varies, so we apply multiple selectors. */
div[data-baseweb="slider"] div[aria-hidden="true"]{
  background: #22c55e !important;            /* remaining */
}
div[data-baseweb="slider"] div[aria-hidden="true"] > div{
  background: #f59e0b !important;            /* filled */
}

/* Remove weird "empty bars" from Streamlit */
hr { border-top: 1px solid rgba(15,23,42,.08); }

/* Tighter markdown spacing inside cards */
[data-testid="stMarkdownContainer"] p { margin-bottom: 0.35rem; }
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
# Layout
# -------------------------
left, right = st.columns([0.40, 0.60], gap="large")

# -------------------------
# LEFT: System Parameters (WHITE container #1)
# -------------------------
with left:
    st.markdown("<div class='sn-card'>", unsafe_allow_html=True)
    st.markdown("<div class='sn-card-title'>System Parameters</div>", unsafe_allow_html=True)

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
# RIGHT: Results + Cards
# -------------------------
with right:
    # Run calculations
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

    # Download (NO container frame)
    st.markdown("<div class='sn-download-wrap'>", unsafe_allow_html=True)
    if out.pdf_bytes:
        st.download_button(
            "⬇️ Download PDF",
            data=out.pdf_bytes,
            file_name="solar_ninja_generation_report.pdf",
            mime="application/pdf",
        )
    else:
        st.button("⬇️ Download PDF", disabled=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # KPI row
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

    # WHITE container #2: Monthly generation chart
    st.markdown("<div class='sn-card'>", unsafe_allow_html=True)
    st.markdown("<div class='sn-card-title'>Monthly generation (kWh)</div>", unsafe_allow_html=True)

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
        plot_bgcolor="#ffffff",
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    # WHITE container #3: Optimal tilt by month
    st.markdown("<div class='sn-card'>", unsafe_allow_html=True)
    st.markdown("<div class='sn-card-title'>Optimal tilt by month</div>", unsafe_allow_html=True)

    m_df = out.tilt_by_month_df.copy()  # Month, BestTiltDeg
    # Use abbreviations to guarantee equal tile sizes & no wrapping issues
    m_df["MonthShort"] = pd.to_datetime(m_df["Month"], format="%B").dt.strftime("%b")
    tiles_html = ["<div class='sn-tiles'>"]
    for _, r in m_df.iterrows():
        tiles_html.append(
            f"<div class='sn-tile'><div class='m'>{r['MonthShort']}</div><div class='d'>{int(r['BestTiltDeg'])}°</div></div>"
        )
    tiles_html.append("</div>")
    st.markdown("\n".join(tiles_html), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    # WHITE container #4: Recommendations
    st.markdown("<div class='sn-card'>", unsafe_allow_html=True)
    st.markdown("<div class='sn-card-title'>Recommendations</div>", unsafe_allow_html=True)
    for r in out.recommendations:
        st.markdown(f"- {r}")
    st.markdown("</div>", unsafe_allow_html=True)
