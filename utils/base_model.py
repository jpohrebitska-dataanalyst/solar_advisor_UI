# utils/base_model.py

import pandas as pd
import numpy as np
from pvlib.location import Location
from pvlib import irradiance
import matplotlib.pyplot as plt
from io import BytesIO
from dataclasses import dataclass
from typing import List, Optional, Any, Dict

# --- PDF imports (as in your verified version) ---
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as PDFImage,
)


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


def _clamp_lat(lat: float) -> float:
    return max(-90.0, min(90.0, float(lat)))


def _wrap_lon(lon: float) -> float:
    # normalize to [-180, 180)
    return ((float(lon) + 180.0) % 360.0) - 180.0


def _parse_optional_float(x: Any) -> Optional[float]:
    """
    Robust parsing:
    - None, "", " ", NaN -> None
    - numeric / numeric strings -> float
    """
    if x is None:
        return None

    if isinstance(x, str):
        s = x.strip()
        if s == "":
            return None
        try:
            return float(s)
        except ValueError:
            return None

    try:
        val = float(x)
    except (TypeError, ValueError):
        return None

    if np.isnan(val):
        return None

    return val


def _resolve_azimuths(latitude: float, user_azimuth: Any) -> Dict[str, Any]:
    """
    Returns:
      - ideal_azimuth: 180° for Northern hemisphere (lat>=0), 0° for Southern (lat<0)
      - user_azimuth_effective: user azimuth if provided, else ideal_azimuth
      - user_azimuth_provided: bool
    """
    ideal_azimuth = 180.0 if float(latitude) >= 0.0 else 0.0

    user_az = _parse_optional_float(user_azimuth)
    if user_az is None:
        return {
            "ideal_azimuth": ideal_azimuth,
            "user_azimuth_effective": ideal_azimuth,
            "user_azimuth_provided": False,
        }

    # normalize into [0..360)
    user_az = user_az % 360.0
    return {
        "ideal_azimuth": ideal_azimuth,
        "user_azimuth_effective": user_az,
        "user_azimuth_provided": True,
    }


def calculate_solar_output(
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth: Optional[float] = None,
):
    """
    Solar Ninja — Basic Model (Fixed PDF Formatting)

    Azimuth rules:
      - Ideal azimuth: 180° (North hemi) or 0° (South hemi)
      - User/Yo uses user azimuth if provided; otherwise uses ideal azimuth
      - Optimal calculations always use ideal azimuth

    Safety:
      - Clamp/wrap coordinates to avoid pvlib altitude lookup index errors.
    """
    # --- normalize coordinates (NEW safety) ---
    latitude = _clamp_lat(latitude)
    longitude = _wrap_lon(longitude)

    # losses
    system_losses = 0.18

    # ------------------------------------------------------------
    # 0. Azimuth logic
    # ------------------------------------------------------------
    az = _resolve_azimuths(latitude=float(latitude), user_azimuth=user_azimuth)
    ideal_azimuth = float(az["ideal_azimuth"])
    user_azimuth_effective = float(az["user_azimuth_effective"])
    user_azimuth_provided = bool(az["user_azimuth_provided"])

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
    location = Location(latitude=float(latitude), longitude=float(longitude), tz=timezone)
    solar_position = location.get_solarposition(times)

    # ------------------------------------------------------------
    # 3. Clearsky GHI
    # ------------------------------------------------------------
    clearsky = location.get_clearsky(times, model="ineichen")
    ghi = clearsky["ghi"].clip(lower=0)
    ghi_kw = ghi / 1000.0

    # ------------------------------------------------------------
    # 4. Monthly optimal tilt — IDEAL azimuth
    # ------------------------------------------------------------
    tilts = list(range(0, 91))
    hourly_energy_df = {}

    for t in tilts:
        aoi = irradiance.aoi(
            surface_tilt=t,
            surface_azimuth=ideal_azimuth,
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"]
        )
        cos_aoi = np.cos(np.radians(aoi))
        cos_aoi[cos_aoi < 0] = 0

        poa = ghi_kw * cos_aoi * (1 - system_losses)
        hourly_energy = poa * float(system_power_kw)

        hourly_energy_df[f"tilt_{t}"] = hourly_energy

    df_energy = pd.DataFrame(hourly_energy_df, index=times)

    monthly_sum = df_energy.resample("M").sum()

    monthly_best = monthly_sum.idxmax(axis=1).str.extract(r"(\d+)").astype(int)
    monthly_best.columns = ["Best Tilt (deg)"]
    monthly_best["Month"] = monthly_best.index.strftime("%B")

    # ------------------------------------------------------------
    # 5. Annual optimal tilt — IDEAL azimuth
    # ------------------------------------------------------------
    best_tilt = None
    best_energy = -1.0

    for t in tilts:
        aoi = irradiance.aoi(
            surface_tilt=t,
            surface_azimuth=ideal_azimuth,
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"]
        )
        cos_aoi = np.cos(np.radians(aoi))
        cos_aoi[cos_aoi < 0] = 0

        poa = ghi_kw * cos_aoi * (1 - system_losses)
        energy = float((poa * float(system_power_kw)).sum())

        if energy > best_energy:
            best_energy = energy
            best_tilt = t

    annual_optimal_tilt = int(best_tilt)
    annual_optimal_energy = float(best_energy)

    # ------------------------------------------------------------
    # 6. User tilt energy — USER azimuth if provided, else IDEAL
    # ------------------------------------------------------------
    aoi_user = irradiance.aoi(
        surface_tilt=float(user_tilt),
        surface_azimuth=user_azimuth_effective,
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"]
    )

    cos_user = np.cos(np.radians(aoi_user))
    cos_user[cos_user < 0] = 0

    poa_user = ghi_kw * cos_user * (1 - system_losses)
    hourly = poa_user * float(system_power_kw)

    monthly_energy = hourly.resample("M").sum()
    annual_energy = float(hourly.sum())

    monthly_df = pd.DataFrame({
        "Month": monthly_energy.index.strftime("%B"),
        "Energy (kWh)": monthly_energy.values.round(0)
    })

    # monthly generation for ANNUAL optimal tilt (IDEAL azimuth)
    monthly_opt_yearly = df_energy[f"tilt_{annual_optimal_tilt}"].resample("M").sum()
    monthly_opt_df = pd.DataFrame({
        "Month": monthly_opt_yearly.index.strftime("%B"),
        "Energy (kWh)": monthly_opt_yearly.values.round(0)
    })

    # ------------------------------------------------------------
    # 7. Chart for PDF (baseline)
    # ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    ax.bar(monthly_df["Month"], monthly_df["Energy (kWh)"], color="orange")
    ax.set_title(f"Monthly Energy Output (Tilt = {float(user_tilt):.1f}°)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Energy (kWh)")
    plt.xticks(rotation=45)
    plt.tight_layout()

    img_buffer = BytesIO()
    fig.savefig(img_buffer, format="png", dpi=150)
    img_buffer.seek(0)

    # ------------------------------------------------------------
    # 8. PDF (baseline)
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
        alignment=1,
        spaceAfter=20,
        fontSize=18
    )

    story = []
    story.append(Paragraph("Solar Ninja — Energy Generation Report", title_style))
    story.append(Spacer(1, 12))

    summary_data = [
        ["Parameter", "Value"],
        ["Location (Lat, Lon)", f"{float(latitude):.4f}, {float(longitude):.4f}"],
        ["System Power", f"{float(system_power_kw):.2f} kW"],
        ["User Tilt", f"{float(user_tilt):.1f}°"],
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
        "ideal_azimuth": ideal_azimuth,
        "user_azimuth_effective": user_azimuth_effective,
        "user_azimuth_provided": user_azimuth_provided,
    }


def run_for_ui(
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth: Optional[float],
) -> UIOutput:
    """
    Adapter for the provided app.py.
    """
    res = calculate_solar_output(
        latitude=float(latitude),
        longitude=float(longitude),
        system_power_kw=float(system_power_kw),
        user_tilt=float(user_tilt),
        user_azimuth=user_azimuth,
    )

    annual_kwh_user = float(res["annual_energy"])
    annual_kwh_optimal = float(res["annual_optimal_energy"])
    optimal_angle = int(res["annual_optimal_tilt"])

    potential_pct = 0.0
    if annual_kwh_user != 0:
        potential_pct = (annual_kwh_optimal - annual_kwh_user) / annual_kwh_user * 100.0

    months_dt = pd.date_range("2025-01-01", periods=12, freq="MS")
    month_short = months_dt.strftime("%b").tolist()

    user_monthly = res["monthly_df"]["Energy (kWh)"].astype(float).tolist()
    opt_monthly = res["monthly_opt_df"]["Energy (kWh)"].astype(float).tolist()

    monthly_chart_df = pd.DataFrame({
        "month": month_short,
        "kwh_user": user_monthly,
        "kwh_optimal_yearly": opt_monthly,
    })

    tilt_by_month_df = res["monthly_best"][["Month", "Best Tilt (deg)"]].copy()
    tilt_by_month_df = tilt_by_month_df.rename(columns={"Best Tilt (deg)": "BestTiltDeg"})

    ideal_az = float(res.get("ideal_azimuth", 180.0))
    user_az_eff = float(res.get("user_azimuth_effective", ideal_az))
    user_az_provided = bool(res.get("user_azimuth_provided", False))

    az_line = (
        f"Azimuth used for Your/Yo: {user_az_eff:.0f}°."
        if user_az_provided
        else f"Azimuth not specified — using default (by hemisphere): {ideal_az:.0f}°."
    )

    recommendations = [
        f"Your tilt angle is {float(user_tilt):.1f}° and the annual optimal tilt for this location is {optimal_angle}°.",
        f"Estimated potential change vs your current setup: {potential_pct:+.1f}%.",
        "Monthly optimal tilt may further improve generation if your mounting system allows seasonal adjustment.",
        az_line,
    ]

    pdf_bytes = None
    try:
        pdf_bytes = res["pdf"].getvalue()
    except Exception:
        pdf_bytes = None

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
