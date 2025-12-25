import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from utils.base_model import run_for_ui


# -----------------------------
# Page
# -----------------------------
st.set_page_config(
    page_title="Solar Ninja",
    page_icon="☀️",
    layout="wide",
)

# -----------------------------
# CSS (Lovable-like)
# -----------------------------
st.markdown(
    """
<style>
/* ---- App background ---- */
.stApp{
  background:
    radial-gradient(900px 520px at 10% 5%, rgba(245,158,11,0.14), transparent 55%),
    radial-gradient(900px 520px at 92% 20%, rgba(34,197,94,0.10), transparent 60%),
    #f5f6f8;
}
.block-container{
  padding-top: 2.0rem;
  padding-bottom: 3rem;
  max-width: 1180px;
}

/* ---- Hide anchor blocks ---- */
.sn-card-anchor{
  display:none !important;
  height:0 !important;
  margin:0 !important;
  padding:0 !important;
}

/* ---- Only our 4 white containers (NOT global) ---- */
/* Streamlit renders each st.container as stVerticalBlock. We "tag" it by placing an anchor inside and use :has() */
div[data-testid="stVerticalBlock"]:has(.sn-card-anchor.sn-system),
div[data-testid="stVerticalBlock"]:has(.sn-card-anchor.sn-chart),
div[data-testid="stVerticalBlock"]:has(.sn-card-anchor.sn-tilt),
div[data-testid="stVerticalBlock"]:has(.sn-card-anchor.sn-recs){
  background: #ffffff !important;
  border-radius: 28px !important;
  border: 1px solid rgba(15,23,42,0.06) !important;
  box-shadow: 0 16px 38px rgba(15,23,42,0.08) !important;
  padding: 26px 26px 20px 26px !important;
  margin-bottom: 20px !important;
}

/* Make the inner blocks not add extra top padding that looks like "white pucks" */
div[data-testid="stVerticalBlock"]:has(.sn-card-anchor.sn-system) > div,
div[data-testid="stVerticalBlock"]:has(.sn-card-anchor.sn-chart) > div,
div[data-testid="stVerticalBlock"]:has(.sn-card-anchor.sn-tilt) > div,
div[data-testid="stVerticalBlock"]:has(.sn-card-anchor.sn-recs) > div{
  padding-top: 0 !important;
}

/* ---- Hero ---- */
.sn-hero-pill{
  display:inline-flex;
  align-items:center;
  gap:10px;
  padding:10px 18px;
  border-radius:999px;
  background: rgba(245,158,11,0.14);
  border: 1px solid rgba(245,158,11,0.18);
  color:#b45309;
  font-weight:600;
  margin: 10px 0 16px 0;
}
.sn-hero-title{
  font-size: 74px;
  line-height: 1.02;
  font-weight: 850;
  letter-spacing:-0.02em;
  margin: 10px 0 10px 0;
  color:#0f172a;
}
.sn-hero-title span{
  color:#f59e0b;
}
.sn-hero-sub{
  font-size:18px;
  color:#475569;
  margin-bottom: 24px;
}

/* ---- Header brand ---- */
.sn-brand{
  display:flex;
  flex-direction:column;
  gap:6px;
}
.sn-brand-title{
  font-size: 26px;
  font-weight: 800;
  color:#0f172a;
}
.sn-brand-sub{
  font-size: 15px;
  color:#64748b;
}

/* ---- KPI cards ---- */
.sn-kpi{
  background:#ffffff;
  border-radius:24px;
  border:1px solid rgba(15,23,42,0.06);
  box-shadow: 0 12px 26px rgba(15,23,42,0.07);
  padding: 18px 18px 16px 18px;
  min-height: 98px;
}
.sn-kpi-label{
  font-size: 14px;
  color:#64748b;
  font-weight: 650;
  margin-bottom: 10px;
}
.sn-kpi-value{
  font-size: 34px;
  font-weight: 850;
  color:#0f172a;
  white-space: nowrap;   /* keep 10,392 on one line */
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.01em;
}
.sn-kpi-sub{
  margin-top: 6px;
  font-size: 12px;
  color:#94a3b8;
  white-space: nowrap;
}

/* ---- Titles inside cards ---- */
.sn-card-title{
  font-size: 22px;
  font-weight: 820;
  color:#0f172a;
  margin-bottom: 14px;
}

/* ---- Primary buttons (Download + Calculate) ---- */
button[kind="primary"]{
  background:#f59e0b !important;
  color:#0f172a !important;
  border:none !important;
  border-radius: 999px !important;
  padding: 0.85rem 1.15rem !important;
  box-shadow: 0 14px 26px rgba(245,158,11,0.22) !important;
  font-weight: 800 !important;
}
button[kind="primary"]:hover{
  filter: brightness(0.98);
}

/* Make st.download_button align nicer */
div[data-testid="stDownloadButton"]{
  display:flex;
  justify-content:flex-end;
}

/* ---- Inputs ---- */
div[data-testid="stNumberInput"] input{
  border-radius: 14px !important;
  padding-top: 10px !important;
  padding-bottom: 10px !important;
}

/* ---- Sliders: green rail + orange fill + orange thumb ---- */
div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"]{
  background-color: #f59e0b !important;
  border: 2px solid white !important;
  box-shadow: 0 6px 14px rgba(15,23,42,0.10) !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div[aria-hidden="true"]{
  background-color: #16a34a !important; /* rail */
}
/* this typically targets the filled part in many baseweb builds */
div[data-testid="stSlider"] [data-baseweb="slider"] div[aria-hidden="true"] > div{
  background-color: #f59e0b !important; /* fill */
}

/* Slider value labels we render manually */
.sn-row{
  display:flex;
  justify-content:space-between;
  align-items:baseline;
  gap: 14px;
  margin: 6px 0 6px 0;
}
.sn-row .l{
  font-size:14px;
  color:#475569;
  font-weight:650;
}
.sn-row .v-orange{
  font-size:26px;
  font-weight:850;
  color:#f59e0b;
  white-space:nowrap;
}
.sn-row .v-green{
  font-size:26px;
  font-weight:850;
  color:#16a34a;
  white-space:nowrap;
}
.sn-slider-hints{
  display:flex;
  justify-content:space-between;
  font-size:13px;
  color:#64748b;
  margin-top: -4px;
  margin-bottom: 8px;
}

/* ---- Month cards ---- */
.sn-month{
  background:#f3f4f6;
  border-radius:18px;
  border:1px solid rgba(15,23,42,0.06);
  padding: 14px 10px;
  text-align:center;
  height: 92px;          /* fixed size -> all equal */
  display:flex;
  flex-direction:column;
  justify-content:center;
  gap: 6px;
}
.sn-month .m{
  font-size: 12px;       /* smaller so it always fits */
  color:#64748b;
  font-weight: 700;
  line-height: 1.05;
}
.sn-month .d{
  font-size: 22px;
  color:#0f172a;
  font-weight: 900;
  line-height: 1.0;
}
</style>
""",
    unsafe_allow_html=True,
)


def kpi_card(label: str, value: str, sub: str = ""):
    sub_html = f'<div class="sn-kpi-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="sn-kpi">
      <div class="sn-kpi-label">{label}</div>
      <div class="sn-kpi-value">{value}</div>
      {sub_html}
    </div>
    """


def monthly_chart_matplotlib(df: pd.DataFrame):
    # df: month (Jan...), kwh_user, kwh_optimal_yearly
    fig, ax = plt.subplots(figsize=(9.2, 3.6), dpi=160)
    x = df["month"].tolist()
    y1 = df["kwh_user"].astype(float).tolist()
    y2 = df["kwh_optimal_yearly"].astype(float).tolist()

    ax.plot(x, y1, linewidth=2.8, label="Your Generation")
    ax.plot(x, y2, linewidth=2.8, label="Optimal Generation")

    # gentle fill (Lovable-ish)
    ax.fill_between(range(len(x)), y1, alpha=0.08)
    ax.fill_between(range(len(x)), y2, alpha=0.08)

    ax.set_xticks(range(len(x)))
    ax.set_xticklabels(x)
    ax.set_ylabel("kWh")
    ax.grid(True, alpha=0.18)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper center", ncols=2, frameon=False)
    fig.tight_layout()
    return fig


# -----------------------------
# State
# -----------------------------
if "ui" not in st.session_state:
    st.session_state.ui = None

# -----------------------------
# Header
# -----------------------------
hdr_left, hdr_right = st.columns([0.7, 0.3])
with hdr_left:
    st.markdown(
        """
        <div class="sn-brand">
          <div class="sn-brand-title">☀️ Solar Ninja</div>
          <div class="sn-brand-sub">Solar Energy Optimization</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hdr_right:
    # (Optional) you can add simple links / placeholders
    st.write("")

st.markdown('<div style="text-align:center;">', unsafe_allow_html=True)
st.markdown('<div class="sn-hero-pill">☀️ Optimize your solar system</div>', unsafe_allow_html=True)
st.markdown('<div class="sn-hero-title">Maximize <span>generation</span></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sn-hero-sub">Calculate the optimal panel tilt angle and get the accurate forecast of annual generation for your location.</div>',
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Layout
# -----------------------------
colL, colR = st.columns([0.42, 0.58], gap="large")


# -------- Left: System Parameters (white card) --------
with colL:
    with st.container():
        st.markdown('<div class="sn-card-anchor sn-system"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sn-card-title">System Parameters</div>', unsafe_allow_html=True)

        st.markdown("#### 📍 Location")
        lat_col, lon_col = st.columns(2, gap="medium")
        with lat_col:
            latitude = st.number_input("Latitude (°)", value=50.45, format="%.4f")
        with lon_col:
            longitude = st.number_input("Longitude (°)", value=30.52, format="%.4f")

        st.divider()

        st.markdown("#### ⚡ System power")
        system_power_kw = st.number_input("System power (kW)", value=10.00, min_value=0.1, step=0.1, format="%.2f")

        st.divider()

        st.markdown("#### 📐 Tilt Angle")
        tilt_value = st.slider(
            "Tilt angle (°)",
            min_value=0,
            max_value=90,
            value=35,
            label_visibility="collapsed",
            key="tilt",
        )
        st.markdown(
            f"""
            <div class="sn-row">
              <div class="l">Current Tilt Angle</div>
              <div class="v-orange">{tilt_value}°</div>
            </div>
            <div class="sn-slider-hints">
              <span>0° (horizontal)</span>
              <span>90° (vertical)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 🧭 Orientation (Azimuth)")
        az_value = st.slider(
            "Azimuth (°)",
            min_value=0,
            max_value=360,
            value=180,
            label_visibility="collapsed",
            key="az",
        )
        st.markdown(
            f"""
            <div class="sn-row">
              <div class="l">Panel Direction</div>
              <div class="v-green">{az_value}°</div>
            </div>
            <div class="sn-slider-hints">
              <span>0° (N)</span>
              <span>90° (E)</span>
              <span>180° (S)</span>
              <span>270° (W)</span>
              <span>360°</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        calc = st.button("⚡ Calculate", type="primary", use_container_width=True)

# -------- Right: Download + KPI + cards --------
with colR:
    # Download button row
    with st.container():
        dl_col1, dl_col2 = st.columns([0.62, 0.38])
        with dl_col2:
            if st.session_state.ui and st.session_state.ui.pdf_bytes:
                st.download_button(
                    "⬇️ Download PDF",
                    data=st.session_state.ui.pdf_bytes,
                    file_name="solar_ninja_report.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=False,
                    key="download_pdf",
                )

    # Calculate action
    if calc:
        st.session_state.ui = run_for_ui(
            latitude=float(latitude),
            longitude=float(longitude),
            system_power_kw=float(system_power_kw),
            user_tilt=float(tilt_value),
            user_azimuth=float(az_value),
        )

    ui = st.session_state.ui

    # KPI row
    if ui:
        k1, k2, k3, k4 = st.columns(4, gap="medium")
        with k1:
            st.markdown(kpi_card("Optimal angle", f"{ui.optimal_angle}°"), unsafe_allow_html=True)
        with k2:
            st.markdown(kpi_card("Your generation", f"{ui.annual_kwh_user:,.0f}", "kWh/year"), unsafe_allow_html=True)
        with k3:
            st.markdown(kpi_card("Optimal generation", f"{ui.annual_kwh_optimal:,.0f}", "kWh/year"), unsafe_allow_html=True)
        with k4:
            sign = "+" if ui.potential_pct >= 0 else ""
            st.markdown(kpi_card("Potential", f"{sign}{ui.potential_pct:.1f}%"), unsafe_allow_html=True)

    # Monthly chart card
    if ui:
        with st.container():
            st.markdown('<div class="sn-card-anchor sn-chart"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sn-card-title">Monthly Generation (kWh)</div>', unsafe_allow_html=True)
            fig = monthly_chart_matplotlib(ui.monthly_chart_df)
            st.pyplot(fig, clear_figure=True)

        # Optimal tilt by month card
        with st.container():
            st.markdown('<div class="sn-card-anchor sn-tilt"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sn-card-title">Optimal Tilt by Month</div>', unsafe_allow_html=True)

            # Order months
            month_order = ["January","February","March","April","May","June","July","August","September","October","November","December"]
            dfm = ui.tilt_by_month_df.copy()
            dfm["Month"] = pd.Categorical(dfm["Month"], categories=month_order, ordered=True)
            dfm = dfm.sort_values("Month")

            # 6 + 6 grid
            top = dfm.iloc[:6].reset_index(drop=True)
            bottom = dfm.iloc[6:].reset_index(drop=True)

            row1 = st.columns(6, gap="medium")
            for i, c in enumerate(row1):
                m = str(top.loc[i, "Month"])
                d = int(top.loc[i, "BestTiltDeg"])
                with c:
                    st.markdown(
                        f'<div class="sn-month"><div class="m">{m}</div><div class="d">{d}°</div></div>',
                        unsafe_allow_html=True,
                    )

            row2 = st.columns(6, gap="medium")
            for i, c in enumerate(row2):
                m = str(bottom.loc[i, "Month"])
                d = int(bottom.loc[i, "BestTiltDeg"])
                with c:
                    st.markdown(
                        f'<div class="sn-month"><div class="m">{m}</div><div class="d">{d}°</div></div>',
                        unsafe_allow_html=True,
                    )

        # Recommendations card
        with st.container():
            st.markdown('<div class="sn-card-anchor sn-recs"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sn-card-title">Recommendations</div>', unsafe_allow_html=True)
            for r in ui.recommendations:
                st.markdown(f"- {r}")

    else:
        # No results yet -> keep right side clean
        st.info("Set parameters and click **Calculate** to see results.")
