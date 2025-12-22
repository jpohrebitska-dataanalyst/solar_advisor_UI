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
st.markdown("""
<style>
/* Constrain width like Lovable */
.block-container{
  max-width: 1120px;
  margin: 0 auto;
  padding-top: 1.2rem;
  padding-bottom: 2rem;
}

/* Hide Streamlit header space */
header {visibility: hidden; height: 0px;}

/* Brand */
.brand small {color: rgba(2,6,23,.6);}

/* Centered hero */
.hero-wrap{ text-align:center; margin: 22px 0 22px; }
.hero-kicker{
  display:inline-flex; align-items:center; gap:8px;
  padding:6px 12px; border-radius:999px;
  background: rgba(245,158,11,0.12);
  color:#b45309; font-weight:700; font-size:0.85rem;
}
.hero-title{ font-size:3.05rem; font-weight:900; color:#0f172a; margin:10px 0 6px; }
.hero-title span{ color:#f59e0b; }
.hero-sub{ color:rgba(2,6,23,.65); font-size:1rem; margin:0 auto; max-width: 720px; }

/* Panels and cards */
.panel{
  background:#fff;
  border:1px solid rgba(15,23,42,.08);
  border-radius:16px;
  padding:16px;
  box-shadow:0 8px 24px rgba(15,23,42,.06);
}
.card{
  background:#fff;
  border:1px solid rgba(15,23,42,.08);
  border-radius:14px;
  padding:14px 16px;
  box-shadow:0 8px 24px rgba(15,23,42,.06);
}
.section-title{ font-size:1rem; font-weight:800; color:#0f172a; margin-bottom:10px; }

/* KPI */
.card-title{ font-size:.85rem; color:rgba(2,6,23,.6); margin-bottom:6px; }
.card-value{ font-size:1.6rem; font-weight:900; color:#0f172a; line-height:1.1; }
.card-sub{ font-size:.8rem; color:rgba(2,6,23,.55); margin-top:4px; }

/* Tiles (Lovable grey) */
.tile{
  background:#f1f5f9;
  border:1px solid rgba(15,23,42,.08);
  border-radius:14px;
  padding:12px 10px;
  text-align:center;
}
.tile .m{ font-size:.8rem; color:rgba(2,6,23,.6); }
.tile .v{ font-size:1.15rem; font-weight:900; color:#0f172a; margin-top:4px; }

/* Make form submit button orange */
.stFormSubmitButton button, .stButton button{
  background:#f59e0b !important;
  color:#0b1220 !important;
  border:1px solid rgba(15,23,42,.12) !important;
  border-radius:12px !important;
  font-weight:900 !important;
  padding:0.55rem 0.9rem !important;
}
.stFormSubmitButton button:hover, .stButton button:hover{
  filter: brightness(0.96);
}

/* Make download button orange as well */
.stDownloadButton button{
  background:#f59e0b !important;
  color:#0b1220 !important;
  border:1px solid rgba(15,23,42,.12) !important;
  border-radius:12px !important;
  font-weight:900 !important;
  padding:0.55rem 0.9rem !important;
}
.stDownloadButton button:hover{ filter: brightness(0.96); }

/* Slider: attempt to force orange */
div[data-baseweb="slider"] div[role="slider"]{
  background-color:#f59e0b !important;
  border-color:#f59e0b !important;
}
div[data-baseweb="slider"] div{
  border-color:#f59e0b !important;
}
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
    k1, k2, k3, k4 = st.columns([1, 1, 1, 0.9], gap="medium")

    with k1:
        st.markdown(f"""
        <div class="card">
          <div class="card-title">Optimal angle</div>
          <div class="card-value">{out.optimal_angle}°</div>
          <div class="card-sub">Annual optimum</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="card">
          <div class="card-title">Your generation</div>
          <div class="card-value">{out.annual_kwh_user:,.0f}</div>
          <div class="card-sub">kWh / year</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="card">
          <div class="card-title">Potential</div>
          <div class="card-value">+{out.potential_pct:.1f}%</div>
          <div class="card-sub">vs current tilt</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
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

    st.write("")

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
        line=dict(color="#f59e0b", width=3)  # orange
    ))
    fig.add_trace(go.Scatter(
        x=df["month"],
        y=df["kwh_optimal_yearly"],
        name="Optimal tilt",
        mode="lines",
        line=dict(color="#22c55e", width=3)  # green
    ))

    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="rgba(15,23,42,0.08)")
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    # Optimal tilt by month
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Optimal tilt by month</div>", unsafe_allow_html=True)

    items = list(out.tilt_by_month_df.itertuples(index=False))
    row1 = st.columns(6, gap="small")
    row2 = st.columns(6, gap="small")

    for i, r in enumerate(items[:6]):
        with row1[i]:
            st.markdown(
                f"<div class='tile'><div class='m'>{r.Month}</div><div class='v'>{getattr(r, 'Best Tilt (deg)')}°</div></div>",
                unsafe_allow_html=True
            )

    for i, r in enumerate(items[6:12]):
        with row2[i]:
            st.markdown(
                f"<div class='tile'><div class='m'>{r.Month}</div><div class='v'>{getattr(r, 'Best Tilt (deg)')}°</div></div>",
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    # Recommendations
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Recommendations</div>", unsafe_allow_html=True)
    for r in out.recommendations:
        st.markdown(f"- {r}")
    st.markdown("</div>", unsafe_allow_html=True)
