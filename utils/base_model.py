import pandas as pd
import numpy as np
from pvlib.location import Location
from pvlib import irradiance
import matplotlib.pyplot as plt
from io import BytesIO
from dataclasses import dataclass
from typing import List, Optional

# ReportLab (PDF)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as PDFImage
)


# ======================================================
# UI OUTPUT STRUCTURE (expected by app.py)
# ======================================================
@dataclass
class UIOutput:
    optimal_angle: int
    annual_kwh_user: float
    annual_kwh_optimal: float
    potential_pct: float
    monthly_chart_df: pd.DataFrame     # columns: month, kwh_user, kwh_optimal_yearly
    tilt_by_month_df: pd.DataFrame     # columns: Month, BestTiltDeg
    recommendations: List[str]
    pdf_bytes: Optional[bytes]


# ======================================================
# CORE SOLAR CALCULATION MODEL
# ======================================================
def calculate_solar_output(
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth: float
) -> dict:
    """
    Solar Ninja — Generation Model (clearsky-based)

    Assumptions:
    - Clearsky irradiance (Ineichen)
    - Fixed system losses
    - Fixed azimuth
    """

    # --- System losses assumption
    system_losses = 0.18

    # --------------------------------------------------
    # 1. Time index (hourly, full year)
    # --------------------------------------------------
    timezone = "UTC"
    times = pd.date_range(
        "2025-01-01",
        "2025-12-31 23:00",
        freq="1h",
        tz=timezone
    )

    # --------------------------------------------------
    # 2. Location & solar position
    # --------------------------------------------------
    location = Location(latitude=latitude, longitude=longitude, tz=timezone)
    solar_position = location.get_solarposition(times)

    # --------------------------------------------------
    # 3. Clearsky GHI (kW/m²)
    # --------------------------------------------------
    clearsky = location.get_clearsky(times, model="ineichen")
    ghi = clearsky["ghi"].clip(lower=0)
    ghi_kw = ghi / 1000.0

    # --------------------------------------------------
    # 4. Hourly energy for all tilts (0–90°)
    # --------------------------------------------------
    tilts = range(0, 91)
    hourly_energy = {}

    for t in tilts:
        aoi = irradiance.aoi(
            surface_tilt=t,
            surface_azimuth=user_azimuth,
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"]
        )
        cos_aoi = np.cos(np.radians(aoi))
        cos_aoi[cos_aoi < 0] = 0

        poa = ghi_kw * cos_aoi * (1 - system_losses)
        hourly_energy[f"tilt_{t}"] = poa * system_power_kw

    df_energy = pd.DataFrame(hourly_energy, index=times)

    # --------------------------------------------------
    # 5. Monthly optimal tilt (per month)
    # --------------------------------------------------
    monthly_sum = df_energy.resample("M").sum()
    best_tilt_cols = monthly_sum.idxmax(axis=1)
    best_tilts = best_tilt_cols.str.replace("tilt_", "", regex=False).astype(int)

    monthly_best = pd.DataFrame({
        "Month": monthly_sum.index.strftime("%B"),
        "BestTiltDeg": best_tilts.values
    })

    # --------------------------------------------------
    # 6. Annual optimal tilt (single)
    # --------------------------------------------------
    annual_sum = df_energy.sum()
    annual_opt_col = annual_sum.idxmax()
    annual_optimal_tilt = int(annual_opt_col.replace("tilt_", ""))
    annual_energy_optimal = float(annual_sum.max())

    # --------------------------------------------------
    # 7. User tilt generation
    # --------------------------------------------------
    aoi_user = irradiance.aoi(
        surface_tilt=user_tilt,
        surface_azimuth=user_azimuth,
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"]
    )
    cos_user = np.cos(np.radians(aoi_user))
    cos_user[cos_user < 0] = 0

    poa_user = ghi_kw * cos_user * (1 - system_losses)
    hourly_user = poa_user * system_power_kw

    monthly_user = hourly_user.resample("M").sum()
    annual_energy_user = float(hourly_user.sum())

    # --------------------------------------------------
    # 8. Optimal yearly tilt – monthly generation
    # --------------------------------------------------
    monthly_opt_yearly = df_energy[f"tilt_{annual_optimal_tilt}"].resample("M").sum()

    # ---------------------------------
