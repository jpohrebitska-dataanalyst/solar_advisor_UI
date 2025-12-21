import streamlit as st
import plotly.graph_objects as go

from utils.base_model import run_for_ui  # <-- ВАЖЛИВО: новий UI-адаптер

# =========================
# Page config
# =========================
st.set_page_config(
    page_title="Solar Ninja",
    page_icon="☀️",
    layout="wide"
)

# =========================
# CSS (Lovable-style)
# =========================
st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
header {visibility: hidden; height: 0px;}

.hero-kicker {
  display:inline-flex; gap:8px; align-items:center;
  padding:6px 12px; border-radius:999px;
  background:rgba(245,158,11,0.12);
  color:#b45309; font-weight:600; font-size:0.85rem;
}

.hero-title {font-size:3rem; font-weight:800; color:#0f172a; margin:10px 0 6px;}
.hero-title span {color:#f59e0b;}
.hero-sub {color:rgba(2,6,23,.65); font-size:1rem; margin-bottom:20px;}

.panel {
  background:#fff;
  border:1px solid rgba(15,23,42,.08);
  border-radius:16px;
  padding:16px;
  box-shadow:0 8px 24px rgba(15,23,42,.06);
}

.card {
  background:#fff;
  border:1px solid rgba(15,23,42,.08);
  border-radius:14px;
  padding:14px 16px;
  box-shadow:0 8px 24px rgba(15,23,42,.06);
}

.card-title {font-size:.85rem; color:rgba(2,6,23,.6);}
.card-value {font-size:1.55rem; font-weight:800; color:#0f172a;}
.card-sub {font-size:.8rem; color:rgba(2,6,23,.55);}

.section-title {font-size:1rem; font-weight:700; color:#0f172a; margin-bottom:10px;}

.tile {
  background:#fff;
  border:1px solid rgba(15,23,42,.08);
  border-radius:12px;
  padding:10px;
  text-align:center;
}
.tile .m {font-size:.8rem; color:rgba(2,6,23,.6);}
.tile .v {font-size:1.15rem; font-weight:800; color:#0f172a;}
</style>
""", unsafe_allow_html=True)

# =========================
# Header
# =========================
st.markdown("**☀️ Solar Ninja**  \n<small style='color:rgba(2,6,23,.6)'>Solar Energy Optimization</small>", unsafe_allow_html=True)

st.markdown("<div class='hero-kicker'>⚔️ Solar calculator</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-title'>Maximize <span>generation</span></div>", unsafe_allow_html=True)
st.markdown(
    "<div class='hero-sub'>Calculate optimal tilt angle and accurate annual solar generation for your location.</div>",
    unsafe_allow_html=True
)

# =========================
# Layout
# =========================
left, right = st.columns([0.36, 0.64], gap="large")

# =========================
# LEFT — Inputs
# =========================
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

        submitted = st.form_submit_button("⚡ Calculate", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# RIGHT — Results
# =========================
with right:
    if submitted or "ui_result" not in st.session_state:
        with st.spinner("Running Solar Ninja calculations…"):
            st.session_state.ui_result = run_for_ui(
                latitude=latitude,
                longitude=longitude,
                system_power_kw=system_power_kw,
                user_tilt=user_tilt
            )

    out = st.session_state.ui_result

    # KPI cards
    c1, c2, c3, c4 = st.columns([1, 1, 1, 0.9])

    with c1:
        st.markdown(f"""
        <div class="card">
          <div class="card-title">Optimal angle</div>
          <div class="card-value">{out.optimal_angle}°</div>
          <div class="card-sub">Annual optimum</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card">
          <div class="card-title">Your generation</div>
          <div class="card-value">{out.annual_kwh:,.0f}</div>
          <div class="card-sub">kWh / year</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card">
          <div class="card-title">Potential</div>
          <div class="card-value">+{out.potential_pct:.1f}%</div>
          <div class="card-sub">vs current tilt</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        if out.pdf_bytes:
            st.download_button(
                "⬇️ PDF",
                data=out.pdf_bytes,
                file_name="solar_ninja_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    st.write("")

    # Monthly chart
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Monthly generation (kWh)</div>", unsafe_allow_html=True)

    df = out.monthly_chart_df
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["month"], y=df["kwh_current"],
                             name="Your tilt", mode="lines"))
    fig.add_trace(go.Scatter(x=df["month"], y=df["kwh_optimal"],
                             name="Optimal tilt", mode="lines"))

    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    # Optimal tilt by month
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Optimal tilt by month</div>", unsafe_allow_html=True)

    items = list(out.tilt_by_month_df.itertuples(index=False))
    row1 = st.columns(6)
    row2 = st.columns(6)

    for i, r in enumerate(items[:6]):
        with row1[i]:
            st.markdown(f"<div class='tile'><div class='m'>{r.Month}</div><div class='v'>{r._1}°</div></div>",
                        unsafe_allow_html=True)

    for i, r in enumerate(items[6:]):
        with row2[i]:
            st.markdown(f"<div class='tile'><div class='m'>{r.Month}</div><div class='v'>{r._1}°</div></div>",
                        unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    # Recommendations
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Recommendations</div>", unsafe_allow_html=True)
    for r in out.recommendations:
        st.markdown(f"- {r}")
    st.markdown("</div>", unsafe_allow_html=True)
