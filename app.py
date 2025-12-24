import streamlit as st
import plotly.graph_objects as go
from contextlib import contextmanager

from utils.base_model import run_for_ui


@contextmanager
def white_card():
    # Works on newer Streamlit; safe fallback on older versions
    try:
        with st.container(border=True):
            yield
    except TypeError:
        with st.container():
            yield


def spacer(px: int = 18):
    st.markdown(f"<div style='height:{px}px'></div>", unsafe_allow_html=True)


st.set_page_config(page_title="Solar Ninja", page_icon="☀️", layout="wide")

st.markdown(
    """
<style>
.stApp{ background:#f6f7fb; }
.block-container{ max-width:1240px; margin:0 auto; padding-top:1.05rem; padding-bottom:2.2rem; }
header{ visibility:hidden; height:0px; }
section.main > div{ padding-top:0.10rem; }

/* Brand */
.brand{ margin-top:6px; }
.brand b{ font-size:1.38rem; font-weight:950; color:#0f172a; }
.brand small{ display:block; margin-top:2px; font-size:1.03rem; color:rgba(2,6,23,.62); }

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

/* Make border=True containers look like Lovable white cards */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:#fff !important;
  border:0 !important;
  border-radius:18px !important;
  box-shadow:0 10px 28px rgba(15,23,42,.08) !important;
  padding:16px 16px 14px 16px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div{
  background:#fff !important;
  border-radius:18px !important;
  padding:0 !important;
}

.section-title{
  font-size:1.02rem; font-weight:950; color:#0f172a; margin:0 0 12px 0;
}

/* KPI cards */
.kpi{
  background:#fff;
  border:0;
  border-radius:18px;
  box-shadow:0 10px 28px rgba(15,23,42,.08);
  padding:14px 16px;
  min-height:118px;
  display:flex; flex-direction:column; justify-content:center;
}
.kpi .t{ font-size:.92rem; color:rgba(2,6,23,.62); margin-bottom:10px; font-weight:850; }
.kpi .v{ font-size:1.88rem; font-weight:950; color:#0f172a; l
