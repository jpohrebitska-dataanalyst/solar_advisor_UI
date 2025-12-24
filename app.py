import streamlit as st
import plotly.graph_objects as go

from utils.base_model import run_for_ui

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Solar Ninja", page_icon="☀️", layout="wide")

# -------------------------
# CSS (Lovable-like, NO decorative empty bars)
# -------------------------
st.markdown(
    """
<style>
/* Wider canvas (~+4cm total vs before) */
.block-container{
  max-width: 1270px;  /* wider */
  margin: 0 auto;
  padding-top: 1.2rem;
  padding-bottom: 2rem;
}

/* Grey page background */
.stApp{
  background: #f1f5f9;
}

/* Hide Streamlit header space */
header {visibility: hidden; height: 0px;}

/* Brand (top-left) */
.brand{
  display:flex;
  flex-direction:column;
  gap:2px;
  margin-bottom: 10px;
}
.brand-title{
  font-size: 1.35rem;
  font-weight: 950;
  color: #0f172a;
}
.brand-sub{
  font-size: 1.05rem;
  color: rgba(2,6,23,.65);
  font-weight: 650;
}

/* Centered hero */
.hero-wrap{
  text-align:center;
  margin: 18px 0 18px;
}
.hero-kicker{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:7px 14px;
  border-radius:999px;
  background: rgba(245,158,11,0.12);
  color:#b45309;
  font-weight:850;
  font-size:0.9rem;
}
.hero-title{
  font-size: 3.65rem;    /* bigger */
  font-weight: 980;
  color:#0f172a;
  margin: 12px 0 8px;
  line-height: 1.05;
}
.hero-title span{ color:#f59e0b; }
.hero-sub{
  color: rgba(2,6,23,.65);
  font-size: 1.08rem;
  margin: 0 auto;
  max-width: 820px;
  line-height: 1.5;
}

/* White blocks (big panels) */
.panel, .card{
  background:#ffffff;
  border:1px solid rgba(15,23,42,.08);
  border-radius:16px;
  box-shadow:0 8px 24px rgba(15,23,42,.06);
}

.panel{ padding:16px; }
.card{ padding:14px 16px; }

/* Titles */
.section-title{
  font-size: 1.03rem;
  font-weight: 950;
  color:#0f172a;
  margin: 0 0 10px 0;
}

/* KPI cards */
.kpi{
  padding:14px 16px;
  border-radius:16px;
  background:#ffffff;
  border:1px solid rgba(15,23,42,.08);
  box-shadow:0 8px 24px rgba(15,23,42,.06);
  min-height: 98px;
}
.kpi-title{
  font-size: .88rem;
  color: rgba(2,6,23,.62);
  font-weight: 800;
  margin-bottom: 8px;
}
.kpi-value{
  font-size: 1.85rem;
  font-weight: 980;
  color:#0f172a;
  line-height: 1.06;
}
.kpi-unit{
  font-size: .95rem;
  font-weight: 900;
  color: rgba(2,6,23,.70);
  margin-left: 6px;
}

/* Tiles (Lovable grey) */
.tile{
  background:#f1f5f9;
  border:1px solid rgba(15,23,42,.08);
  border-radius:14px;
  padding:12px 10px;
  text-align:center;
}
.tile .m{ font-size:.82rem; color:rgba(2,6,23,.62); font-weight:800; }
.tile .v{ font-size:1.18rem; font-weight:980; color:#0f172a; margin-top:4px; }

/* Orange buttons (including download) */
.stFormSubmitButton button, .stButton button, .stDownloadButton button{
  background:#f59e0b !important;
  color:#0b1220 !important;
  border:1px solid rgba(15,23,42,.12) !important;
  border-radius:12px !important;
  font-weight:980 !important;
  padding:0.58rem 1.00rem !important;
}
.stFormSubmitButton button:hover, .stButton button:hover, .stDownloadButton button:hover{
  filter: brightness(0.96);
}

/* ---- Slider styling (orange filled / green remaining) ----
   Goal:
   - from 0 to thumb: orange
   - from thumb to max: green
   - thumb/label number: orange (no red)
*/
div[data-baseweb="slider"] > div{
  /* track remaining color (thumb -> max) */
  background: rgba(34,197,94,0.35) !important;  /* green tint for remaining */
  border-radius: 999px !important;
}
div[data-baseweb="slider"] div[role="slider"]{
  background-color:#f59e0b !important;   /* thumb */
  border-color:#f59e0b !important;
}
div[data-baseweb="slider"] div > div{
  /* filled track (0 -> thumb) */
  background-color: rgba(245,158,11,0.55) !important;  /* orange fill */
}

/* Try to make the thumb label number orange (Streamlit versions vary) */
div[data-baseweb="slider"] div[role="slider"] *{
  color:#f59e0b !important;
}

/* Orange inline helpers */
.orange{ color:#f59e0b; font-weight: 950; }

/* Spacing blocks (instead of st.divider) */
.spacer-10{ height:10px; }
.spacer-14{ height:14px; }
</style>
""",
    unsafe_allow_html=True
)

# -------------------------
# Brand (top-left)
# -------------------------
st.markdown(
    """
<div class="brand">
  <div class="brand-title">☀️ Solar Ninja</div>
  <div class="brand-sub">Solar Energy Optimization</div>
</div>
""",
    unsafe_allow_html=True
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
    unsafe_allow_html=True
)

# -------------------------
# Main layout
# -------------------------
left, right = st.columns([0.38, 0.62], gap="large")

# -------------------------
# LEFT: Inputs (one long white card)
# -------------------------
with left:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>System Parameters</div>", unsafe_allow_html=True)

    with st.form("calc_form", border=False):
        st.markdown("**<span class='orange'>📍</span> Location**", unsafe_allow_html=True)
        latitude = st.number_input("Latitude (°)", value=50.45, format="%.4f")
        longitude = st.number_input("Longitude (°)", value=30.52, format="%.4f")

        st.markdown("<div class='spacer-14'></div>", unsafe_allow_html=True)

        st.markdown("**<span class='orange'>⚡</span> System power**", unsafe_allow_html=True)
        system_power_kw = st.number_input("System power (kW)", value=10.0, step=0.5)

        st.markdown("<div class='spacer-14'></div>", unsafe_allow_html=True)

        st.markdown("**<span class='orange'>📐</span> Panel tilt**", unsafe_allow_html=True)
        user_tilt = st.slider("Tilt angle (°)", 0, 90, 45)
        st.markdown(
            f"<div style='margin-top:-6px; margin-bottom:10px;'>Current tilt: <span class='orange'>{user_tilt}°</span></div>",
            unsafe_allow_html=True
        )

        st.markdown("<div class='spacer-14'></div>", unsafe_allow_html=True)

        st.markdown("**<span class='orange'>🧭</span> Orientation (azimuth)**", unsafe_allow_html=True)
        user_azimuth = st.slider("Azimuth (°)", 0, 360, 180)
        st.markdown(
            f"<div style='margin-top:-6px; margin-bottom:10px;'>Current azimuth: <span class='orange'>{user_azimuth}°</span></div>",
            unsafe_allow_html=True
        )

        submitted = st.form_submit_button("⚡ Calculate", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# RIGHT: Results (white blocks)
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

    # Download button ABOVE KPI row
    dl_col = st.columns([0.78, 0.22], gap="medium")
    with dl_col[1]:
        if out.pdf_bytes:
            st.download_button(
                "⬇️ Download",
                data=out.pdf_bytes,
                file_name="solar_ninja_generation_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.button("⬇️ Download", disabled=True, use_container_width=True)

    st.markdown("<div class='spacer-10'></div>", unsafe_allow_html=True)

    # KPI row (4 cards)
    potential_kwh = float(out.annual_kwh_optimal - out.annual_kwh_user)

    k1, k2, k3, k4 = st.columns([1, 1, 1, 1], gap="medium")

    with k1:
        st.markdown(
            f"""
<div class="kpi">
  <div class="kpi-title">Optimal angle</div>
  <div class="kpi-value">{out.optimal_angle}°</div>
</div>
""",
            unsafe_allow_html=True
        )

    with k2:
        st.markdown(
            f"""
<div class="kpi">
  <div class="kpi-title">Your generation</div>
  <div class="kpi-value">{out.annual_kwh_user:,.0f}<span class="kpi-unit">kWh/year</span></div>
</div>
""",
            unsafe_allow_html=True
        )

    with k3:
        st.markdown(
            f"""
<div class="kpi">
  <div class="kpi-title">Optimal generation</div>
  <div class="kpi-value">{out.annual_kwh_optimal:,.0f}<span class="kpi-unit">kWh/year</span></div>
</div>
""",
            unsafe_allow_html=True
        )

    with k4:
        sign = "+" if out.potential_pct >= 0 else ""
        st.markdown(
            f"""
<div class="kpi">
  <div class="kpi-title">Potential</div>
  <div class="kpi-value">{sign}{out.potential_pct:.1f}%</div>
</div>
""",
            unsafe_allow_html=True
        )

    st.markdown("<div class='spacer-14'></div>", unsafe_allow_html=True)

    # Monthly generation chart (white card)
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
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="rgba(15,23,42,0.10)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='spacer-14'></div>", unsafe_allow_html=True)

    # Optimal tilt by month (paired rows: Jan-Jul, Feb-Aug, ...)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Optimal tilt by month</div>", unsafe_allow_html=True)

    m_df = out.tilt_by_month_df
    months = m_df["Month"].tolist()
    tilts = m_df["Best Tilt (deg)"].astype(int).tolist()
    month_to_tilt = {months[i]: tilts[i] for i in range(min(len(months), len(tilts)))}

    pair_order = [
        ("January", "July"),
        ("February", "August"),
        ("March", "September"),
        ("April", "October"),
        ("May", "November"),
        ("June", "December"),
    ]

    for left_m, right_m in pair_order:
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if left_m in month_to_tilt:
                st.markdown(
                    f"<div class='tile'><div class='m'>{left_m}</div><div class='v'>{month_to_tilt[left_m]}°</div></div>",
                    unsafe_allow_html=True
                )
        with c2:
            if right_m in month_to_tilt:
                st.markdown(
                    f"<div class='tile'><div class='m'>{right_m}</div><div class='v'>{month_to_tilt[right_m]}°</div></div>",
                    unsafe_allow_html=True
                )
        st.markdown("<div class='spacer-10'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='spacer-14'></div>", unsafe_allow_html=True)

    # Recommendations (white card)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Recommendations</div>", unsafe_allow_html=True)
    for r in out.recommendations:
        st.markdown(f"- {r}")
    st.markdown("</div>", unsafe_allow_html=True)
