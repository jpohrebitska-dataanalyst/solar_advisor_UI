# utils/base_model.py

import pandas as pd
import numpy as np
from pvlib.location import Location
from pvlib import irradiance
import matplotlib.pyplot as plt
from io import BytesIO
import tempfile
import os
from dataclasses import dataclass
from typing import List, Optional

# --- PDF imports (as in your verified version) ---
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage


@dataclass
class UIOutput:
    optimal_angle: int
    annual_kwh_user: float
    annual_kwh_optimal: float
    potential_pct: float
    monthly_chart_df: pd.DataFrame      # columns: month, kwh_user, kwh_optimal_yearly
    tilt_by_month_df: pd.DataFrame      # columns: Month, BestTiltDeg
    recommendations: List[str]
    pdf_bytes: Optional[bytes]


def calculate_solar_output(latitude, longitude, system_power_kw, user_tilt):
    """
    Solar Ninja — Basic Model (Fixed PDF Formatting)
    ✅ This function is kept as your verified baseline logic.
    """
    # losses
    system_losses = 0.18

    # ------------------------------------------------------------
    # 1. Time index
    # ------------------------------------------------------------
    timezone = "UTC"
    times = pd.date_range(
        "2025-01-01", "2025-12-31 23:00",
        freq="1h",
        tz=timezone
    )

    # ------------------------------------------------------------
    # 2. Location & sun positions
    # ------------------------------------------------------------
    location = Location(latitude=latitude, longitude=longitude, tz=timezone)
    solar_position = location.get_solarposition(times)

    # ------------------------------------------------------------
    # 3. Clearsky GHI
    # ------------------------------------------------------------
    clearsky = location.get_clearsky(times, model="ineichen")
    ghi = clearsky["ghi"].clip(lower=0)
    ghi_kw = ghi / 1000.0

    # ------------------------------------------------------------
    # 4. Monthly optimal tilt (maximize kWh per month)
    # ------------------------------------------------------------
    tilts = list(range(0, 91))
    hourly_energy_df = {}

    for t in tilts:
        aoi = irradiance.aoi(
            surface_tilt=t,
            surface_azimuth=180,  # ✅ baseline: fixed azimuth
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"]
        )
        cos_aoi = np.cos(np.radians(aoi))
        cos_aoi[cos_aoi < 0] = 0

        poa = ghi_kw * cos_aoi * (1 - system_losses)
        hourly_energy = poa * system_power_kw

        hourly_energy_df[f"tilt_{t}"] = hourly_energy

    df_energy = pd.DataFrame(hourly_energy_df, index=times)

    monthly_sum = df_energy.resample("M").sum()

    monthly_best = monthly_sum.idxmax(axis=1).str.extract(r"(\d+)").astype(int)
    monthly_best.columns = ["Best Tilt (deg)"]
    monthly_best["Month"] = monthly_best.index.strftime("%B")

    # ------------------------------------------------------------
    # 5. Annual optimal tilt
    # ------------------------------------------------------------
    best_tilt = None
    best_energy = -1.0

    for t in tilts:
        aoi = irradiance.aoi(
            surface_tilt=t,
            surface_azimuth=180,  # ✅ baseline: fixed azimuth
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"]
        )
        cos_aoi = np.cos(np.radians(aoi))
        cos_aoi[cos_aoi < 0] = 0

        poa = ghi_kw * cos_aoi * (1 - system_losses)
        energy = float((poa * system_power_kw).sum())

        if energy > best_energy:
            best_energy = energy
            best_tilt = t

    annual_optimal_tilt = best_tilt
    annual_optimal_energy = float(best_energy)  # ✅ already computed in your baseline loop

    # ------------------------------------------------------------
    # 6. User tilt energy
    # ------------------------------------------------------------
    aoi_user = irradiance.aoi(
        surface_tilt=user_tilt,
        surface_azimuth=180,  # ✅ baseline: fixed azimuth
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"]
    )

    cos_user = np.cos(np.radians(aoi_user))
    cos_user[cos_user < 0] = 0

    poa_user = ghi_kw * cos_user * (1 - system_losses)
    hourly = poa_user * system_power_kw

    monthly_energy = hourly.resample("M").sum()
    annual_energy = float(hourly.sum())

    monthly_df = pd.DataFrame({
        "Month": monthly_energy.index.strftime("%B"),
        "Energy (kWh)": monthly_energy.values.round(0)  # ✅ keep your rounding
    })

    # monthly generation for ANNUAL optimal tilt (from already computed df_energy)
    monthly_opt_yearly = df_energy[f"tilt_{annual_optimal_tilt}"].resample("M").sum()
    monthly_opt_df = pd.DataFrame({
        "Month": monthly_opt_yearly.index.strftime("%B"),
        "Energy (kWh)": monthly_opt_yearly.values.round(0)  # ✅ keep same rounding style
    })

    # ------------------------------------------------------------
    # 7. Generate Charts (Matplotlib) (your baseline bar chart for PDF)
    # ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    ax.bar(monthly_df["Month"], monthly_df["Energy (kWh)"], color="orange")
    ax.set_title(f"Monthly Energy Output (Tilt = {user_tilt:.1f}°)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Energy (kWh)")
    plt.xticks(rotation=45)
    plt.tight_layout()

    img_buffer = BytesIO()
    fig.savefig(img_buffer, format="png", dpi=150)
    img_buffer.seek(0)

    # ------------------------------------------------------------
    # 8. Generate Professional PDF using PLATYPUS (your baseline)
    # ------------------------------------------------------------
    pdf_buffer = BytesIO()

    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=50, leftMargin=50,
        topMargin=50, bottomMargin=50
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        alignment=1,  # center
        spaceAfter=20,
        fontSize=18
    )

    story = []
    story.append(Paragraph("Solar Ninja — Energy Generation Report", title_style))
    story.append(Spacer(1, 12))

    summary_data = [
        ["Parameter", "Value"],
        ["Location (Lat, Lon)", f"{latitude:.4f}, {longitude:.4f}"],
        ["System Power", f"{system_power_kw:.2f} kW"],
        ["User Tilt", f"{user_tilt:.1f}°"],
        ["Optimal Annual Tilt", f"{annual_optimal_tilt}°"],
        ["Total Annual Energy", f"{annual_energy:,.0f} kWh"],
    ]

    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 24))

    rl_image = PDFImage(img_buffer, width=450, height=250)
    story.append(Paragraph("Monthly Energy Production Chart:", styles["Heading2"]))
    story.append(Spacer(1, 10))
    story.append(rl_image)
    story.append(Spacer(1, 24))

    story.append(Paragraph("Monthly Breakdown:", styles["Heading2"]))
    story.append(Spacer(1, 10))

    table_data = [["Month", "Energy (kWh)"]]
    for _, row in monthly_df.iterrows():
        table_data.append([row["Month"], f"{int(row['Energy (kWh)'])}"])

    main_table = Table(table_data, colWidths=[150, 150])
    main_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))

    story.append(main_table)

    doc.build(story)
    pdf_buffer.seek(0)

    return {
        "monthly_df": monthly_df,
        "monthly_opt_df": monthly_opt_df,
        "monthly_best": monthly_best.reset_index(drop=True),
        "annual_energy": annual_energy,
        "annual_optimal_energy": annual_optimal_energy,
        "annual_optimal_tilt": annual_optimal_tilt,
        "fig": fig,
        "pdf": pdf_buffer,
    }


def run_for_ui(
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth: float,
) -> UIOutput:
    """
    Adapter for the provided app.py.

    NOTE:
    - Baseline model uses fixed azimuth=180° in ALL calculations.
    - user_azimuth is accepted for UI compatibility but NOT applied, to keep the verified baseline unchanged.
    """
    res = calculate_solar_output(
        latitude=float(latitude),
        longitude=float(longitude),
        system_power_kw=float(system_power_kw),
        user_tilt=float(user_tilt),
    )

    annual_kwh_user = float(res["annual_energy"])
    annual_kwh_optimal = float(res["annual_optimal_energy"])
    optimal_angle = int(res["annual_optimal_tilt"])

    potential_pct = 0.0
    if annual_kwh_user != 0:
        potential_pct = (annual_kwh_optimal - annual_kwh_user) / annual_kwh_user * 100.0

    # Build monthly chart df for Plotly (as app.py expects)
    # Use Jan..Dec short labels
    months_dt = pd.date_range("2025-01-01", periods=12, freq="MS")
    month_short = months_dt.strftime("%b").tolist()

    # user monthly
    user_monthly = res["monthly_df"]["Energy (kWh)"].astype(float).tolist()

    # optimal yearly tilt monthly
    opt_monthly = res["monthly_opt_df"]["Energy (kWh)"].astype(float).tolist()

    monthly_chart_df = pd.DataFrame({
        "month": month_short,
        "kwh_user": user_monthly,
        "kwh_optimal_yearly": opt_monthly,
    })

    # Tilt by month tiles
    tilt_by_month_df = res["monthly_best"][["Month", "Best Tilt (deg)"]].copy()
    tilt_by_month_df = tilt_by_month_df.rename(columns={"Best Tilt (deg)": "BestTiltDeg"})

    # Recommendations (UI text only, does not affect calculations)
    recommendations = [
        f"Your tilt angle is {float(user_tilt):.1f}° and the annual optimal tilt for this location is {optimal_angle}°.",
        f"Estimated potential change vs your current tilt: {potential_pct:+.1f}%.",
        "Monthly optimal tilt may further improve generation if your mounting system allows seasonal adjustment.",
        "Note: this baseline model assumes south-facing azimuth (180°) for calculations.",
    ]

    # Convert PDF buffer -> bytes for Streamlit download button
    pdf_bytes = None
    try:
        pdf_bytes = res["pdf"].getvalue()
    except Exception:
        pdf_bytes = None

    # Close figure to avoid memory leaks in Streamlit reruns
    try:
        plt.close(res["fig"])
    except Exception:
        pass

    return UIOutput(
        optimal_angle=optimal_angle,
        annual_kwh_user=annual_kwh_user,
        annual_kwh_optimal=annual_kwh_optimal,
        potential_pct=float(potential_pct),
        monthly_chart_df=monthly_chart_df,
        tilt_by_month_df=tilt_by_month_df,
        recommendations=recommendations,
        pdf_bytes=pdf_bytes,
    )
