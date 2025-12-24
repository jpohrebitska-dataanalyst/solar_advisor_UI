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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage


@dataclass
class UIOutput:
    optimal_angle: int
    annual_kwh_user: float
    annual_kwh_optimal: float
    potential_pct: float
    monthly_chart_df: pd.DataFrame          # columns: month, kwh_user, kwh_optimal_yearly
    tilt_by_month_df: pd.DataFrame          # columns: Month, Best Tilt (deg)
    recommendations: List[str]
    pdf_bytes: Optional[bytes]


def calculate_solar_output(latitude: float,
                          longitude: float,
                          system_power_kw: float,
                          user_tilt: float,
                          user_azimuth: float) -> dict:
    """
    Solar Ninja — Basic Model
    Clearsky-based estimate.
    """
    system_losses = 0.18

    timezone = "UTC"
    times = pd.date_range("2025-01-01", "2025-12-31 23:00", freq="1h", tz=timezone)

    location = Location(latitude=latitude, longitude=longitude, tz=timezone)
    solar_position = location.get_solarposition(times)

    clearsky = location.get_clearsky(times, model="ineichen")
    ghi = clearsky["ghi"].clip(lower=0)
    ghi_kw = ghi / 1000.0

    # hourly energy for tilts 0..90 at given azimuth
    tilts = list(range(0, 91))
    hourly_energy_df = {}

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
        hourly_energy = poa * system_power_kw
        hourly_energy_df[f"tilt_{t}"] = hourly_energy

    df_energy = pd.DataFrame(hourly_energy_df, index=times)

    # Monthly best tilt
    monthly_sum_by_tilt = df_energy.resample("M").sum()
    monthly_best = monthly_sum_by_tilt.idxmax(axis=1).str.extract(r"(\d+)").astype(int)
    monthly_best.columns = ["Best Tilt (deg)"]
    monthly_best["Month"] = monthly_best.index.strftime("%B")
    monthly_best = monthly_best.reset_index(drop=True)

    # Annual optimal tilt
    annual_sum_by_tilt = df_energy.sum(axis=0)
    annual_optimal_col = annual_sum_by_tilt.idxmax()
    annual_optimal_tilt = int(str(annual_optimal_col).replace("tilt_", ""))
    annual_energy_optimal = float(annual_sum_by_tilt.max())

    # User tilt energy
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

    # Optimal yearly tilt monthly generation
    hourly_opt_yearly = df_energy[f"tilt_{annual_optimal_tilt}"]
    monthly_opt_yearly = hourly_opt_yearly.resample("M").sum()

    # Optimal monthly changing tilt generation
    monthly_opt_monthly_values = []
    for dt, _ in monthly_opt_yearly.items():
        month_name = dt.strftime("%B")
        best_tilt_month = int(monthly_best.loc[monthly_best["Month"] == month_name, "Best Tilt (deg)"].iloc[0])
        monthly_value = float(df_energy[f"tilt_{best_tilt_month}"][df_energy.index.month == dt.month].sum())
        monthly_opt_monthly_values.append(monthly_value)

    monthly_opt_monthly = pd.Series(monthly_opt_monthly_values, index=monthly_opt_yearly.index)

    potential_pct = 0.0
    if annual_energy_user > 0:
        potential_pct = (annual_energy_optimal - annual_energy_user) / annual_energy_user * 100.0

    # Recommendations (English)
    seasonal_summer = int(monthly_best.loc[monthly_best["Month"] == "June", "Best Tilt (deg)"].iloc[0]) if (monthly_best["Month"] == "June").any() else None
    seasonal_winter = int(monthly_best.loc[monthly_best["Month"] == "December", "Best Tilt (deg)"].iloc[0]) if (monthly_best["Month"] == "December").any() else None

    recs = []
    recs.append(f"Your current tilt angle of {user_tilt:.0f}° is compared against the annual optimal tilt of {annual_optimal_tilt}° for the same azimuth ({user_azimuth:.0f}°).")
    recs.append(f"Potential uplift vs your current setup is approximately +{potential_pct:.1f}% (clearsky model, {int(system_losses*100)}% system losses assumed).")
    if seasonal_summer is not None and seasonal_winter is not None:
        recs.append(f"For seasonal adjustment, consider using ~{seasonal_summer}° in summer and ~{seasonal_winter}° in winter (see the monthly table).")
    recs.append("Regularly clean panels from dust and snow, and avoid shading to maintain maximum efficiency.")

    # Chart for PDF (user vs optimal yearly tilt)
    months_labels = monthly_user.index.strftime("%b")
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=160)
    ax.plot(months_labels, monthly_user.values, label="Your tilt", linewidth=2.6, color="#f59e0b")
    ax.plot(months_labels, monthly_opt_yearly.values, label="Optimal tilt (yearly)", linewidth=2.6, color="#22c55e")
    ax.set_title("Monthly Generation Chart")
    ax.set_xlabel("Month")
    ax.set_ylabel("kWh")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right")
    plt.tight_layout()

    img_buffer = BytesIO()
    fig.savefig(img_buffer, format="png", dpi=160
