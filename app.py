# app.py

import streamlit as st
import pandas as pd

from utils.base_model import run_for_ui

st.set_page_config(page_title="Solar Ninja — Baseline Model", layout="wide")

st.title("Solar Ninja — Baseline Solar Output Model")
st.caption("Baseline model (verified logic): clear-sky GHI + AOI cosine; supports both hemispheres + user azimuth + system ideal azimuth.")

# -----------------------------
# Location selection (map click)
# -----------------------------
st.subheader("1) Pick location on the map")

# Defaults (Kyiv as a start point)
DEFAULT_LAT = 50.4501
DEFAULT_LON = 30.5234

if "lat" not in st.session_state:
    st.session_state["lat"] = DEFAULT_LAT
if "lon" not in st.session_state:
    st.session_state["lon"] = DEFAULT_LON

map_ok = True
try:
    import folium
    from folium.plugins import LatLngPopup
    from streamlit_folium import st_folium
except Exception:
    map_ok = False

if map_ok:
    col_map, col_loc = st.columns([2, 1])

    with col_map:
        m = folium.Map(location=[st.session_state["lat"], st.session_state["lon"]], zoom_start=6)
        LatLngPopup().add_to(m)
        folium.Marker(
            [st.session_state["lat"], st.session_state["lon"]],
            tooltip="Selected location",
        ).add_to(m)

        map_data = st_folium(m, height=450, use_container_width=True)

        # streamlit-folium returns dict with last_clicked
        if map_data and map_data.get("last_clicked"):
            st.session_state["lat"] = float(map_data["last_clicked"]["lat"])
            st.session_state["lon"] = float(map_data["last_clicked"]["lng"])

    with col_loc:
        st.markdown("**Selected coordinates**")
        st.write(f"Latitude:  {st.session_state['lat']:.6f}")
        st.write(f"Longitude: {st.session_state['lon']:.6f}")
        st.info("Tip: click anywhere on the map to update the point.")
else:
    st.warning("Map component not available. Install `folium` + `streamlit-folium` to enable click-on-map location.")
    st.session_state["lat"] = st.number_input("Latitude", value=float(st.session_state["lat"]), format="%.6f")
    st.session_state["lon"] = st.number_input("Longitude", value=float(st.session_state["lon"]), format="%.6f")

latitude = float(st.session_state["lat"])
longitude = float(st.session_state["lon"])

st.divider()

# -----------------------------
# Inputs
# -----------------------------
st.subheader("2) System parameters")

with st.sidebar:
    st.header("Inputs")

    system_power_kw = st.number_input("System power (kW)", value=10.0, min_value=0.1, step=0.1)
    user_tilt = st.slider("User tilt (deg)", min_value=0.0, max_value=90.0, value=30.0, step=0.5)

    # Default/ideal azimuth (equator-facing)
    recommended_az = 180.0 if float(latitude) >= 0.0 else 0.0

    st.subheader("Azimuth")
    az_mode = st.radio(
        "User azimuth input",
        options=["Auto (use default/ideal)", "Manual (user-defined)"],
        index=0,
        help="Auto uses 180° in Northern hemisphere or 0° in Southern hemisphere.",
    )

    if az_mode == "Auto (use default/ideal)":
        user_azimuth = None
        _ = st.slider(
            "User azimuth (deg)",
            min_value=0.0,
            max_value=360.0,
            value=float(recommended_az),
            step=1.0,
            disabled=True,
            help="0=N, 90=E, 180=S, 270=W",
        )
    else:
        user_azimuth = st.slider(
            "User azimuth (deg)",
            min_value=0.0,
            max_value=360.0,
            value=float(recommended_az),
            step=1.0,
            help="0=N, 90=E, 180=S, 270=W",
        )

# -----------------------------
# Run model
# -----------------------------
out = run_for_ui(
    latitude=latitude,
    longitude=longitude,
    system_power_kw=system_power_kw,
    user_tilt=user_tilt,
    user_azimuth=user_azimuth,
)

# -----------------------------
# Results
# -----------------------------
st.subheader("3) Results")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Optimal angle (system)", f"{out.optimal_angle}°")
c2.metric("Your generation", f"{out.annual_kwh_user:,.0f} kWh")
c3.metric("Optimal generation", f"{out.annual_kwh_optimal:,.0f} kWh")
c4.metric("Potential", f"{out.potential_pct:+.1f}%")

st.caption(f"User azimuth used: {out.user_azimuth_used:.0f}° | System optimal azimuth: {out.optimal_azimuth:.0f}°")

st.divider()

left, right = st.columns([2, 1])

with left:
    st.subheader("Monthly generation: Your vs Optimal")
    chart_df = out.monthly_chart_df.set_index("month")[["kwh_user", "kwh_optimal"]]
    chart_df = chart_df.rename(columns={"kwh_user": "Your (user tilt + user az)", "kwh_optimal": "Optimal (system az + optimal tilt)"})
    st.bar_chart(chart_df)

with right:
    st.subheader("Optimal tilt by month (system azimuth)")
    st.dataframe(out.tilt_by_month_df, use_container_width=True)

st.divider()

st.subheader("4) Recommendations / Notes")
for r in out.recommendations:
    st.write(f"- {r}")

st.divider()

st.subheader("5) PDF report")
if out.pdf_bytes:
    st.download_button(
        label="Download PDF report",
        data=out.pdf_bytes,
        file_name="solar_ninja_report.pdf",
        mime="application/pdf",
    )
else:
    st.warning("PDF generation failed (see logs).")
