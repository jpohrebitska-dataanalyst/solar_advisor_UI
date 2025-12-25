import math
import streamlit as st

# ✅ Correct import (your file is utils/base_model.py)
from utils.base_model import run_for_ui


# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Solar Ninja",
    page_icon="☀️",
    layout="wide",
)

# -----------------------------
# Styling (Lovable-like)
# -----------------------------
st.markdown(
    """
<style>
:root{
  --sn-bg:#F6F7FB;
  --sn-card:#FFFFFF;
  --sn-text:#0F172A;
  --sn-muted:#64748B;
  --sn-border: rgba(15,23,42,.08);
  --sn-orange:#F59E0B;
  --sn-orange2:#F97316;
  --sn-radius:26px;
  --sn-radius-sm:18px;
  --sn-shadow:0 18px 50px rgba(15,23,42,.08);
  --sn-shadow-soft:0 10px 28px rgba(15,23,42,.06);
}

.stApp{
  background:
    radial-gradient(circle at 6% 48%, rgba(245,158,11,.20), transparent 55%),
    radial-gradient(circle at 96% 30%, rgba(56,189,248,.16), transparent 52%),
    radial-gradient(circle at 96% 80%, rgba(34,197,94,.10), transparent 55%),
    var(--sn-bg);
}

.block-container{
  max-width: 1250px;
  padding-top: 2.2rem;
}

.sn-brand{
  display:flex;
  gap:12px;
  align-items:center;
}
.sn-brand b{
  font-size: 22px;
  color: var(--sn-text);
}
.sn-brand span{
  display:block;
  margin-top:2px;
  font-size: 14px;
  color: var(--sn-muted);
}

.sn-hero{
  text-align:center;
  margin: 14px 0 26px 0;
}
.sn-pill{
  display:inline-flex;
  align-items:center;
  gap:10px;
  padding: 10px 18px;
  border-radius: 999px;
  background: rgba(245,158,11,.14);
  color: #B45309;
  font-weight: 700;
  border: 1px solid rgba(245,158,11,.18);
}
.sn-title{
  margin: 16px 0 8px 0;
  font-size: 68px;
  line-height: 1.05;
  font-weight: 900;
  letter-spacing: -1px;
  color: var(--sn-text);
}
.sn-title .accent{ color: var(--sn-orange); }
.sn-sub{
  margin: 0 auto;
  max-width: 760px;
  font-size: 18px;
  color: var(--sn-muted);
}

.sn-card{
  background: var(--sn-card);
  border-radius: var(--sn-radius);
  padding: 26px;
  box-shadow: var(--sn-shadow-soft);
  border: 1px solid rgba(15,23,42,.06);
}

.sn-card h3{
  margin: 0 0 10px 0;
  color: var(--sn-text);
}

.sn-section-title{
  display:flex;
  align-items:center;
  gap:10px;
  font-size: 22px;
  font-weight: 900;
  margin: 0 0 10px 0;
  color: var(--sn-text);
}

.sn-divider{
  height:1px;
  background: rgba(15,23,42,.10);
  margin: 18px 0;
}

.sn-kpi-grid{
  display:grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-top: 10px;
}
.sn-kpi{
  background: rgba(255,255,255,.95);
  border: 1px solid rgba(15,23,42,.06);
  border-radius: 22px;
  padding: 18px 18px 16px 18px;
  box-shadow: 0 10px 24px rgba(15,23,42,.05);
}
.sn-kpi .label{
  font-weight: 700;
  color: #475569;
  font-size: 14px;
  margin-bottom: 6px;
}
.sn-kpi .value{
  font-weight: 900;
  color: var(--sn-text);
  font-size: 34px;
  line-height: 1.0;
  white-space: nowrap;   /* ✅ prevent number splitting */
}
.sn-kpi .hint{
  margin-top: 6px;
  color: var(--sn-muted);
  font-size: 13px;
}

.sn-month-grid{
  display:grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px;
  margin-top: 10px;
}
.sn-month{
  background: #F3F4F6;
  border: 1px solid rgba(15,23,42,.06);
  border-radius: 18px;
  padding: 12px 10px;
  text-align:center;
  height: 92px;
  display:flex;
  flex-direction:column;
  justify-content:center;
}
.sn-month .m{
  font-size: 12px;       /* ✅ smaller month name so it fits */
  font-weight: 800;
  color: #64748B;
  margin-bottom: 6px;
}
.sn-month .t{
  font-size: 22px;
  font-weight: 900;
  color: var(--sn-text);
  line-height: 1.0;
}

.sn-btn-row{
  display:flex;
  justify-content:flex-end;
  margin-bottom: 12px;
}

/* Buttons: Calculate + Download PDF (orange) */
div[data-testid="stButton"] button,
div[data-testid="stDownloadButton"] button{
  background: var(--sn-orange) !important;
  color: #111827 !important;
  border: 0 !important;
  border-radius: 16px !important;
  padding: 0.85rem 1.1rem !important;
  font-weight: 900 !important;
  box-shadow: 0 14px 34px rgba(245,158,11,.25) !important;
}
div[data-testid="stButton"] button:hover,
div[data-testid="stDownloadButton"] button:hover{
  background: var(--sn-orange2) !important;
}

/* Inputs */
div[data-testid="stNumberInput"] input{
  border-radius: 14px !important;
  background: #F8FAFC !important;
  border: 1px solid rgba(15,23,42,.08) !important;
}
div[data-testid="stSlider"]{
  padding-top: 6px;
}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Helpers
# -----------------------------
MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]

def fmt_int(x):
    try:
        if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
            return "—"
        return f"{int(round(float(x))):,}".replace(",", " ")
    except Exception:
        return "—"

def fmt_pct(x):
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return "—"
        return f"{float(x):+.1f}%"
    except Exception:
        return "—"

def normalize_month_tilts(month_tilts):
    """
    Accepts:
      - dict {"January": 73, ...} or {"Jan": 73, ...}
      - list/tuple length 12
      - None
    Returns dict with full month names.
    """
    out = {m: None for m in MONTHS}
    if month_tilts is None:
        return out

    if isinstance(month_tilts, (list, tuple)) and len(month_tilts) == 12:
        for m, v in zip(MONTHS, month_tilts):
            out[m] = v
        return out

    if isinstance(month_tilts, dict):
        # map short to full
        short_map = {m[:3].lower(): m for m in MONTHS}
        for k, v in month_tilts.items():
            if not isinstance(k, str):
                continue
            kk = k.strip().lower()
            if kk in out:
                out[k] = v
            else:
                kk3 = kk[:3]
                if kk3 in short_map:
                    out[short_map[kk3]] = v
        return out

    return out


# -----------------------------
# Header
# -----------------------------
top_left, top_right = st.columns([3, 1])

with top_left:
    st.markdown(
        """
<div class="sn-brand">
  <div style="font-size:34px;">☀️</div>
  <div>
    <b>Solar<span style="color:var(--sn-orange)">Ninja</span></b>
    <span>Solar Energy Optimization</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

with top_right:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align:right; color: #64748B; font-weight:700;'>Calculator&nbsp;&nbsp;&nbsp;&nbsp;Map</div>",
        unsafe_allow_html=True,
    )

# Hero
st.markdown(
    """
<div class="sn-hero">
  <div class="sn-pill">☀️&nbsp;&nbsp;Optimize your solar system</div>
  <div class="sn-title">Maximize <span class="accent">generation</span></div>
  <div class="sn-sub">
    Calculate the optimal panel tilt angle and get an accurate forecast of annual generation for your location.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# State
# -----------------------------
if "results" not in st.session_state:
    st.session_state.results = None

# -----------------------------
# Main layout
# -----------------------------
left_col, right_col = st.columns([1, 1.35], gap="large")

# ---- Left: System Parameters card ----
with left_col:
    st.markdown("<div class='sn-card'>", unsafe_allow_html=True)
    st.markdown("<div class='sn-section-title'>System Parameters</div>", unsafe_allow_html=True)

    st.markdown("<div style='font-weight:900; font-size:18px; margin-top:6px;'>📍&nbsp;Location</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        lat = st.number_input("Latitude (°)", value=50.45, format="%.4f")
    with c2:
        lon = st.number_input("Longitude (°)", value=30.52, format="%.4f")

    st.markdown("<div class='sn-divider'></div>", unsafe_allow_html=True)

    st.markdown("<div style='font-weight:900; font-size:18px;'>⚡&nbsp;System Power</div>", unsafe_allow_html=True)
    power_kw = st.number_input("Total Power (kW)", value=10.0, min_value=0.1, step=0.5)

    st.markdown("<div class='sn-divider'></div>", unsafe_allow_html=True)

    st.markdown("<div style='font-weight:900; font-size:18px;'>📐&nbsp;Tilt Angle</div>", unsafe_allow_html=True)
    tilt = st.slider("Current Tilt Angle (°)", min_value=0, max_value=90, value=35)

    st.markdown("<div class='sn-divider'></div>", unsafe_allow_html=True)

    st.markdown("<div style='font-weight:900; font-size:18px;'>🧭&nbsp;Orientation (Azimuth)</div>", unsafe_allow_html=True)
    azimuth = st.slider("Panel Direction (°)", min_value=0, max_value=360, value=180)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    calc = st.button("⚡  Calculate", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ---- Right: Results ----
with right_col:
    # Calculate action
    if calc:
        with st.spinner("Calculating..."):
            st.session_state.results = run_for_ui(
                latitude=lat,
                longitude=lon,
                system_power_kw=power_kw,
                tilt_angle=tilt,
                azimuth=azimuth,
            )

    res = st.session_state.results or {}

    # Download button (top-right)
    pdf_bytes = res.get("pdf_bytes") or res.get("pdf") or None
    st.markdown("<div class='sn-btn-row'>", unsafe_allow_html=True)
    st.download_button(
        "⬇️  Download PDF",
        data=pdf_bytes if pdf_bytes else b"",
        file_name="solar_ninja_report.pdf",
        mime="application/pdf",
        disabled=pdf_bytes is None,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # KPI cards
    best_tilt = res.get("best_tilt") or res.get("optimal_angle") or res.get("optimal_tilt")
    your_gen = res.get("annual_your_kwh") or res.get("your_generation_kwh")
    opt_gen = res.get("annual_optimal_kwh") or res.get("optimal_generation_kwh")
    potential = res.get("potential_pct") or res.get("potential")

    st.markdown(
        f"""
<div class="sn-kpi-grid">
  <div class="sn-kpi">
    <div class="label">Optimal Angle</div>
    <div class="value">{fmt_int(best_tilt)}°</div>
  </div>
  <div class="sn-kpi">
    <div class="label">Your Generation</div>
    <div class="value">{fmt_int(your_gen)}</div>
    <div class="hint">kWh/year</div>
  </div>
  <div class="sn-kpi">
    <div class="label">Optimal Generation</div>
    <div class="value">{fmt_int(opt_gen)}</div>
    <div class="hint">kWh/year</div>
  </div>
  <div class="sn-kpi">
    <div class="label">Potential</div>
    <div class="value">{fmt_pct(potential)}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Monthly Generation card
    st.markdown("<div class='sn-card'>", unsafe_allow_html=True)
    st.markdown("<div class='sn-section-title'>☀️  Monthly Generation (kWh)</div>", unsafe_allow_html=True)

    fig = res.get("fig_monthly") or res.get("fig") or None
    if fig is not None:
        st.pyplot(fig, clear_figure=False, use_container_width=True)
    else:
        st.info("Run calculation to see the chart.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Optimal Tilt by Month card
    st.markdown("<div class='sn-card'>", unsafe_allow_html=True)
    st.markdown("<div class='sn-section-title'>🎯  Optimal Tilt by Month</div>", unsafe_allow_html=True)

    month_tilts = normalize_month_tilts(res.get("tilt_by_month") or res.get("monthly_opt_tilt") or res.get("optimal_tilt_by_month"))
    month_cards_html = "<div class='sn-month-grid'>"
    for m in MONTHS:
        v = month_tilts.get(m)
        val = "—" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{int(round(float(v)))}°"
        month_cards_html += f"""
  <div class="sn-month">
    <div class="m">{m}</div>
    <div class="t">{val}</div>
  </div>
"""
    month_cards_html += "</div>"
    st.markdown(month_cards_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Recommendations card
    st.markdown("<div class='sn-card'>", unsafe_allow_html=True)
    st.markdown("<div class='sn-section-title'>💡  Recommendations</div>", unsafe_allow_html=True)

    recs = res.get("recommendations")
    if not recs:
        # sensible default if model doesn't return recommendations
        recs = [
            f"Your current tilt angle is {tilt}° and the annual optimal tilt is {fmt_int(best_tilt)}° (azimuth {azimuth}°).",
            f"Estimated potential change vs your current tilt: {fmt_pct(potential)} (clearsky model, 18% system losses assumed).",
            "If your mounting system allows it, seasonal tilt adjustment can improve generation (see monthly optimal tilt).",
            "Keep panels clean and minimize shading to maintain efficiency.",
        ]

    for r in recs:
        st.markdown(f"- {r}")

    st.markdown("</div>", unsafe_allow_html=True)
