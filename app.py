import streamlit as st

# ✅ FIX IMPORT
from utils.base_model import run_for_ui


def inject_css():
    st.markdown(
        """
        <style>
        :root{
          --sn-accent:#f59e0b;
          --sn-text:#0f172a;
          --sn-muted:#64748b;
          --sn-card:#ffffff;
          --sn-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
          --sn-radius: 26px;
        }

        /* Page width */
        div.block-container{
          max-width: 1440px;
          padding-top: 2.2rem;
          padding-bottom: 3rem;
        }

        /* Background similar to Lovable (left warm, right cool) */
        [data-testid="stAppViewContainer"]{
          background: linear-gradient(90deg, #f3eadf 0%, #f7f7fb 18%, #f7f7fb 82%, #e6f2ec 100%);
        }

        /* Center hero */
        .sn-hero{
          text-align:center;
          margin: 12px 0 18px 0;
        }
        .sn-badge{
          display:inline-flex;
          align-items:center;
          gap:10px;
          padding:10px 18px;
          border-radius:999px;
          background: rgba(245,158,11,0.14);
          color:#b45309;
          font-weight:600;
          font-size:15px;
          border: 1px solid rgba(245,158,11,0.20);
        }
        .sn-h1{
          margin: 18px 0 6px 0;
          font-size: 74px;
          line-height: 1.03;
          letter-spacing: -1.5px;
          color: var(--sn-text);
          font-weight: 800;
        }
        .sn-h1 span{ color: var(--sn-accent); }
        .sn-sub{
          color: var(--sn-muted);
          font-size: 18px;
          max-width: 880px;
          margin: 0 auto;
        }

        /* Hide marker rows (they were your “white pлашки” in some variants) */
        div[data-testid="stMarkdownContainer"]:has(.sn-card-marker){
          height:0 !important;
          margin:0 !important;
          padding:0 !important;
          overflow:hidden !important;
        }
        .sn-card-marker{ display:none; }

        /* 🎯 Style ONLY the block right after marker => no nested mega cards */
        div[data-testid="stMarkdownContainer"]:has(.sn-card-marker) + div{
          background: var(--sn-card);
          border-radius: var(--sn-radius);
          box-shadow: var(--sn-shadow);
          padding: 26px 26px 22px 26px;
        }

        /* KPI cards */
        .sn-kpi{
          background: #fff;
          border-radius: 22px;
          box-shadow: 0 14px 38px rgba(15, 23, 42, 0.06);
          padding: 18px 18px 14px 18px;
          height: 122px;
          display:flex;
          flex-direction:column;
          justify-content:space-between;
        }
        .sn-kpi-title{
          color: var(--sn-muted);
          font-weight: 600;
          font-size: 14px;
          white-space: nowrap;      /* ✅ no wrapping => same card height */
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .sn-kpi-value{
          font-size: 40px;
          line-height: 1;
          font-weight: 800;
          color: var(--sn-text);
          white-space: nowrap;      /* ✅ prevent breaking numbers */
        }
        .sn-kpi-unit{
          color: var(--sn-muted);
          font-size: 12.5px;
          margin-top: 6px;
        }

        /* Download button (make it look like Lovable) */
        div.stDownloadButton > button{
          background: var(--sn-accent) !important;
          color: #111827 !important;
          border-radius: 16px !important;
          border: none !important;
          padding: 12px 18px !important;
          font-weight: 700 !important;
          box-shadow: 0 14px 34px rgba(245, 158, 11, 0.22) !important;
        }

        /* Section titles */
        .sn-section-title{
          font-size: 28px;
          font-weight: 800;
          color: var(--sn-text);
          margin: 6px 0 8px 0;
        }

        /* Tilt month grid cards */
        .sn-month-card{
          background:#f8fafc;
          border:1px solid rgba(15,23,42,0.06);
          border-radius:18px;
          padding:14px 10px;
          text-align:center;
          height: 92px;
          display:flex;
          flex-direction:column;
          justify-content:center;
        }
        .sn-month-name{ color: var(--sn-muted); font-weight:700; font-size: 12px; }
        .sn-month-val{ color: var(--sn-text); font-weight:900; font-size: 26px; margin-top: 4px; }

        </style>
        """,
        unsafe_allow_html=True,
    )


def card():
    """Creates a styled card section without nesting bugs."""
    st.markdown('<span class="sn-card-marker"></span>', unsafe_allow_html=True)
    return st.container()


def fmt_int(x):
    try:
        return f"{float(x):,.0f}".replace(",", " ")
    except Exception:
        return "—"


st.set_page_config(page_title="Solar Ninja", layout="wide")
inject_css()

# ===== HERO =====
st.markdown(
    """
    <div class="sn-hero">
      <div class="sn-badge">🌞 Optimize your solar system</div>
      <div class="sn-h1">Maximize <span>generation</span></div>
      <div class="sn-sub">Calculate the optimal panel tilt angle and get the accurate forecast of annual generation for your location.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ===== LAYOUT =====
left, right = st.columns([1.05, 1.55], gap="large")

# ---- LEFT: System Parameters (BIG CARD #1) ----
with left:
    with card():
        st.markdown('<div class="sn-section-title">System Parameters</div>', unsafe_allow_html=True)

        with st.form("params_form", border=False):
            c1, c2 = st.columns(2, gap="medium")
            with c1:
                lat = st.number_input("Latitude (°)", value=50.45, format="%.4f")
            with c2:
                lon = st.number_input("Longitude (°)", value=30.52, format="%.4f")

            power = st.number_input("System power (kW)", value=10.0, step=0.5)
            tilt = st.slider("Tilt angle (°)", 0, 90, 35)
            az  = st.slider("Orientation / Azimuth (°)", 0, 360, 180)

            submitted = st.form_submit_button("⚡  Calculate", use_container_width=True)

# ---- RIGHT TOP: Download + KPI row (NO big wrapper card here!) ----
with right:
    top = st.columns([1, 1], vertical_alignment="center")
    with top[1]:
        # if you have real PDF bytes -> set them here
        pdf_bytes = st.session_state.get("pdf_bytes", None)
        if pdf_bytes:
            st.download_button("⬇️  Download PDF", data=pdf_bytes, file_name="solar_ninja_report.pdf")
        else:
            st.download_button("⬇️  Download PDF", data=b"", file_name="solar_ninja_report.pdf", disabled=True)

    k1, k2, k3, k4 = st.columns(4, gap="medium")
    # placeholders before calc
    res = st.session_state.get("res")

    def kpi(col, title, value, unit=""):
        with col:
            st.markdown(
                f"""
                <div class="sn-kpi">
                  <div class="sn-kpi-title">{title}</div>
                  <div>
                    <div class="sn-kpi-value">{value}</div>
                    <div class="sn-kpi-unit">{unit}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if res:
        kpi(k1, "Optimal angle", f"{int(round(res['optimal_angle']))}°", f"Your current: {int(round(res['your_tilt']))}°")
        kpi(k2, "Your generation", fmt_int(res["your_generation"]), "kWh/year")
        kpi(k3, "Optimal generation", fmt_int(res["optimal_generation"]), "kWh/year")
        kpi(k4, "Potential", f"{res['potential_pct']:+.1f}%", "")
    else:
        kpi(k1, "Optimal angle", "—", "")
        kpi(k2, "Your generation", "—", "kWh/year")
        kpi(k3, "Optimal generation", "—", "kWh/year")
        kpi(k4, "Potential", "—", "")

# ===== CALC =====
if submitted:
    # Make it robust to your run_for_ui format (dict/tuple)
    out = run_for_ui(lat, lon, power, tilt, az)

    if isinstance(out, dict):
        res = out
    else:
        # if your run_for_ui returns a tuple – map it here as needed
        # (adapt once based on your actual return)
        res = {
            "optimal_angle": out[0],
            "your_generation": out[1],
            "optimal_generation": out[2],
            "potential_pct": out[3],
            "monthly_df": out[4],
            "monthly_opt_tilt": out[5],
            "recommendations": out[6],
            "pdf_bytes": out[7] if len(out) > 7 else None,
            "your_tilt": tilt,
        }

    st.session_state["res"] = res
    if res.get("pdf_bytes"):
        st.session_state["pdf_bytes"] = res["pdf_bytes"]

    st.rerun()

# ===== RIGHT: Monthly generation (BIG CARD #2) =====
with right:
    res = st.session_state.get("res")
    if res:
        with card():
            st.markdown('<div class="sn-section-title">Monthly Generation (kWh)</div>', unsafe_allow_html=True)

            # If you already have matplotlib fig in res -> show it with full width
            fig = res.get("monthly_fig")
            if fig is not None:
                st.pyplot(fig, use_container_width=True)
            else:
                # fallback: show dataframe if exists
                df = res.get("monthly_df")
                if df is not None:
                    st.line_chart(df.set_index("month")[["your", "optimal"]], height=320, use_container_width=True)

# ===== RIGHT: Optimal tilt by month (BIG CARD #3) =====
with right:
    res = st.session_state.get("res")
    if res:
        with card():
            st.markdown('<div class="sn-section-title">Optimal Tilt by Month</div>', unsafe_allow_html=True)

            months = ["January","February","March","April","May","June","July","August","September","October","November","December"]

            # Expect list/dict with 12 values
            mot = res.get("monthly_opt_tilt", {})
            vals = []
            if isinstance(mot, dict):
                for i, m in enumerate(months, start=1):
                    vals.append(mot.get(i) or mot.get(m) or None)
            else:
                vals = list(mot) if mot is not None else [None]*12
                if len(vals) < 12:
                    vals = vals + [None]*(12-len(vals))
                vals = vals[:12]

            # grid 6 + 6
            row1 = st.columns(6, gap="medium")
            row2 = st.columns(6, gap="medium")

            for i in range(6):
                v = vals[i]
                row1[i].markdown(
                    f"""<div class="sn-month-card"><div class="sn-month-name">{months[i]}</div><div class="sn-month-val">{'—' if v is None else int(round(float(v)))}°</div></div>""",
                    unsafe_allow_html=True,
                )
            for i in range(6, 12):
                v = vals[i]
                row2[i-6].markdown(
                    f"""<div class="sn-month-card"><div class="sn-month-name">{months[i]}</div><div class="sn-month-val">{'—' if v is None else int(round(float(v)))}°</div></div>""",
                    unsafe_allow_html=True,
                )

# ===== RIGHT: Recommendations (BIG CARD #4) =====
with right:
    res = st.session_state.get("res")
    if res:
        with card():
            st.markdown('<div class="sn-section-title">Recommendations</div>', unsafe_allow_html=True)

            recs = res.get("recommendations", [])
            if not recs:
                recs = [
                    f"Your tilt angle is {tilt}° and the annual optimal tilt for this location is {int(round(res['optimal_angle']))}° (azimuth {az}°).",
                    f"Estimated potential change vs your current tilt: {res['potential_pct']:+.1f}%.",
                    "If your mounting system allows it, seasonal tilt adjustment can improve generation (see monthly optimal tilt).",
                    "Keep panels clean and minimize shading to maintain efficiency.",
                ]
            for r in recs:
                st.write("• " + str(r))
