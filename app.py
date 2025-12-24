import streamlit as st
import plotly.graph_objects as go
from contextlib import contextmanager

from utils.base_model import run_for_ui


# -------------------------
# Helpers
# -------------------------
@contextmanager
def white_card():
    """
    Real Streamlit container that keeps content inside.
    We restyle it via CSS to look like a Lovable white card.
    """
    try:
        with st.container(border=True):
            yield
    except TypeError:
        with st.container():
            yield


def spacer(px: int = 18):
    st.markdown(f"<div style='height:{px}px'></div>", unsafe_allow_html=True)


# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Solar Ninja", page_icon="☀️", layout="wide")


# -------------------------
# CSS (Lovable-like) — fix: true white cards, no grey frames, no PDF frame
# -------------------------
st.markdown(
    """
<style>
/* Page background */
.stApp{
  background: #f6f7fb;
}

/* Constrain width */
.block-container{
  max-width: 1240px;
  margin: 0 auto;
  padding-top: 1.05rem;
  padding-bottom: 2.2rem;
}

/* Hide Streamlit header */
header {visibility: hidden; height: 0px;}
section.main > div {padding-top: 0.10rem;}

/* ---------- Brand ---------- */
.brand { margin-top: 6px; }
.brand b { font-size: 1.38rem; font-weight: 950; color:#0f172a; }
.brand small { display:block; margin-top:2px; font-size: 1.03rem; color: rgba(2,6,23,.62); }

/* ---------- Hero ---------- */
.hero-wrap{ text-align:center; margin: 10px 0 26px; }
.hero-kicker{
  display:inline-flex; align-items:center; gap:8px;
  padding:9px 16px; border-radius:999px;
  background: rgba(245,158,11,0.14);
  color:#b45309; font-weight:900; font-size:1.08rem;
}
.hero-title{
  font-size:4.15rem;
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

/* ---------- Streamlit bordered containers → convert to WHITE cards ---------- */
/* This wrapper is what Streamlit renders for container(border=True) */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background: #ffffff !important;
  border: 0 !important;                /* remove grey frame */
  border-radius: 18px !important;
  box-shadow: 0 10px 28px rgba(15,23,42,.08) !important;
  padding: 16px 16px 14px 16px !important;
}

/* Ensure inside stays white (Streamlit sometimes sets transparent) */
div[data-testid="stVerticalBlockBorderWrapper"] > div{
  background: #ffffff !important;
  border-radius: 18px !important;
  padding: 0 !important;
}

/* Section title */
.section-title{
  font-size:1.02rem;
  font-weight:950;
  color:#0f172a;
  margin: 0 0 12px 0;
}

/* ---------- KPI cards (HTML) ---------- */
.kpi{
  background:#fff;
  border:0;
  border-radius:18px;
  box-shadow:0 10px 28px rgba(15,23,42,.08);
  padding:14px 16px;
  min-height: 118px;
  display:flex;
  flex-direction:column;
  justify-content:center;
}
.kpi .t{
  font-size:.92rem;
  color:rgba(2,6,23,.62);
  margin-bottom:10px;
  font-weight:850;
}
.kpi .v{
  font-size:1.88rem;
  font-weight:950;
  color:#0f172a;
  line-height:1.05;
}

/* ---------- Month tiles ---------- */
.tile{
  background:#f1f5f9;
  border:1px solid rgba(15,23,42,.08);
  border-radius:16px;
  padding:14px 10px;
  text-align:center;
}
.tile .m{ font-size:.84rem; color:rgba(2,6,23,.62); font-weight:700; }
.tile .v{ font-size:1.18rem; font-weight:950; color:#0f172a; margin-top:4px; }

/* ---------- Buttons ---------- */
.stFormSubmitButton button, .stButton button, .stDownloadButton button{
  background:#f59e0b !important;
  color:#0b1220 !important;
  border:0 !important;
  border-radius:14px !important;
  font-weight:950 !important;
  padding:0.62rem 0.95rem !important;
  box-shadow:0 10px 24px rgba(245,158,11,.18) !important;
}
.stFormSubmitButton button:hover, .stButton button:hover, .stDownloadButton button:hover{
  filter: brightness(0.96);
}

/* ---------- Sliders: ORANGE filled + GREEN unfilled ---------- */
/* BaseWeb structure varies across versions; this set is safer */
div[data-baseweb="slider"] [role="presentation"]{
  background-color:#22c55e !important; /* unfilled rail */
}
div[data-baseweb="slider"] [role="presentation"] > div{
  background-color:#f59e0b !important; /* filled part */
}
div[data-baseweb="slider"] div[role="slider"]{
  background-color:#f59e0b !important;
  border-color:#f59e0b !important;
}

/* Slider value label */
div[data-baseweb="slider"] span{
  color:#f59e0b !important;
  font-weight:900 !important;
}

/* Remove empty weird spacers */
div[data-testid="stVerticalBlock"] > div:empty { display:none !important; }
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------
# Brand
# -------------------------
st.markdown(
    "<div class='brand'><b>☀️ Solar Ninja</b><small>Solar Energy Optimization</small></div>",
    unsafe_allow_html=True
)

# -------------------------
# Hero
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
# Layout
# -----
