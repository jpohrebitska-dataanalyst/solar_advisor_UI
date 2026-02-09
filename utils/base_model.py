# utils/base_model.py

import pandas as pd
import numpy as np
from pvlib.location import Location
from pvlib import irradiance
import matplotlib.pyplot as plt
from io import BytesIO
from dataclasses import dataclass
from typing import List, Optional, Any, Dict

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
    monthly_chart_df: pd.DataFrame
    tilt_by_month_df: pd.DataFrame
    recommendations: List[str]
    pdf_bytes: Optional[bytes]


def _clamp_lat(lat: float) -> float:
    return max(-90.0, min(90.0, float(lat)))


def _wrap_lon(lon: float) -> float:
    return ((float(lon) + 180.0) % 360.0) - 180.0


def _parse_optional_float(x: Any) -> Optional[float]:
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
    ideal_azimuth = 180.0 if float(latitude) >= 0.0 else 0.0
    user_az = _parse_optional_float(user_azimuth)
    if user_az is None:
        return {
            "ideal_azimuth": ideal_azimuth,
            "user_azimuth_effective": ideal_azimuth,
            "user_azimuth_provided": False,
        }
    user_az = user_az % 360.0
    return {
        "ideal_azimuth": ideal_azimuth,
        "user_azimuth_effective": user_az,
        "user_azimuth_provided": True,
    }


def _potential_pct(opt_kwh: float, user_kwh: float) -> float:
    u = float(user_kwh)
    o = float(opt_kwh)
    if u == 0.0 and o > 0.0:
        return 100.0
    if u == 0.0 and o == 0.0:
        return 0.0
    return (o - u) / u * 100.0


def calculate_solar_output(
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth: Optional[float] = None,
):
    latitude = _clamp_lat(latitude)
    longitude = _wrap_lon(longitude)

    system_losses = 0.18

    az = _resolve_azimuths(latitude=float(latitude), user_azimuth=user_azimuth)
    ideal_azimuth = float(az["ideal_azimuth"])
    user_azimuth_effective = float(az["user_azimuth_effective"])
    user_azimuth_provided = bool(az["user_azimuth_provided"])

    timezone = "UTC"
    times = pd.date_range("2025-01-01", "2025-12-31 23:00", freq="1h", tz=timezone)

    location = Location(latitude=float(latitude), longitude=float(longitude), tz=timezone)
    solar_position = location.get_solarposition(times)

    clearsky = location.get_clearsky(times, model="ineichen")
    ghi = clearsky["ghi"].clip(lower=0)
    ghi_kw = ghi / 1000.0

    tilts = list(range(0, 91))
    hourly_energy_df = {}

    for t in tilts:
        aoi = irradiance.aoi(
            surface_tilt=t,
            surface_azimuth=ideal_azimuth,
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"],
        )
        cos_aoi = np.cos(np.radians(aoi))
        cos_aoi[cos_aoi < 0] = 0
        poa = ghi_kw * cos_aoi * (1 - system_losses)
        hourly_energy_df[f"tilt_{t}"] = poa * float(system_power_kw)

    df_energy = pd.DataFrame(hourly_energy_df, index=times)
    monthly_sum = df_energy.resample("M").sum()

    monthly_best = monthly_sum.idxmax(axis=1).str.extract(r"(\d+)").astype(int)
    monthly_best.columns = ["Best Tilt (deg)"]
    monthly_best["Month"] = monthly_best.index.strftime("%B")

    best_tilt = None
    best_energy = -1.0
    for t in tilts:
        aoi = irradiance.aoi(
            surface_tilt=t,
            surface_azimuth=ideal_azimuth,
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"],
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

    aoi_user = irradiance.aoi(
        surface_tilt=float(user_tilt),
        surface_azimuth=user_azimuth_effective,
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
    )
    cos_user = np.cos(np.radians(aoi_user))
    cos_user[cos_user < 0] = 0
    poa_user = ghi_kw * cos_user * (1 - system_losses)
    hourly_user = poa_user * float(system_power_kw)

    monthly_user = hourly_user.resample("M").sum()
    annual_energy = float(hourly_user.sum())

    monthly_opt = df_energy[f"tilt_{annual_optimal_tilt}"].resample("M").sum()

    monthly_df = pd.DataFrame({
        "Month": monthly_user.index.strftime("%B"),
        "Energy (kWh)": monthly_user.values.round(0),
    })
    monthly_opt_df = pd.DataFrame({
        "Month": monthly_opt.index.strftime("%B"),
        "Energy (kWh)": monthly_opt.values.round(0),
    })

    # -------- PDF content --------
    annual_potential = _potential_pct(annual_optimal_energy, annual_energy)

    months_dt = pd.date_range("2025-01-01", periods=12, freq="MS")
    month_short = months_dt.strftime("%b").tolist()

    user_vals = monthly_user.values.astype(float)
    opt_vals = monthly_opt.values.astype(float)

    # Chart (smaller height to fit 1 page), only orange+green, Y from 0
    fig, ax = plt.subplots(figsize=(7, 3.0), dpi=150)
    ax.plot(month_short, user_vals, color="#f59e0b", linewidth=3, label="Your tilt")
    ax.plot(month_short, opt_vals, color="#22c55e", linewidth=3, label="Optimal tilt")
    ax.set_ylim(bottom=0)
    ax.set_title("Monthly generation (kWh)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Month", fontsize=9)
    ax.set_ylabel("Energy (kWh)", fontsize=9)
    ax.tick_params(axis="both", labelsize=8)
    ax.grid(True, axis="y", alpha=0.18)
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    plt.tight_layout()

    img_buffer = BytesIO()
    fig.savefig(img_buffer, format="png", dpi=150)
    img_buffer.seek(0)

    monthly_breakdown = []
    for m, u, o in zip(month_short, user_vals, opt_vals):
        pot = _potential_pct(o, u)

        u_disp = int(round(u))
        o_disp = int(round(o))

        if u == 0.0 and o > 0.0:
            pot_str = "100.0%"
        elif u == 0.0 and o == 0.0:
            pot_str = "0.0%"
        else:
            pot_str = f"{pot:+.1f}%"

        monthly_breakdown.append([m, f"{u_disp}", f"{o_disp}", pot_str])

    pdf_buffer = BytesIO()

    # ✅ Smaller margins to fit 1 page
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=28, leftMargin=28,
        topMargin=22, bottomMargin=22,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        alignment=1,
        spaceAfter=4,   # минимально
        fontSize=14,    # меньше
        leading=16,
    )

    h_style = ParagraphStyle(
        "H2Tight",
        parent=styles["Heading2"],
        fontSize=11,
        leading=13,
        spaceBefore=0,
        spaceAfter=2,
    )

    story = []
    # мінімальний відступ зверху — забезпечує topMargin
    story.append(Paragraph("Solar Ninja — Energy Generation Report", title_style))
    story.append(Spacer(1, 4))  # мінімальна

    if annual_energy == 0.0 and annual_optimal_energy > 0.0:
        annual_potential_str = "100.0%"
    elif annual_energy == 0.0 and annual_optimal_energy == 0.0:
        annual_potential_str = "0.0%"
    else:
        annual_potential_str = f"{annual_potential:+.1f}%"

    summary_data = [
        ["Parameter", "Value"],
        ["Location (Lat, Lon)", f"{float(latitude):.4f}, {float(longitude):.4f}"],
        ["System Power", f"{float(system_power_kw):.2f} kW"],
        ["User Tilt", f"{float(user_tilt):.1f}°"],
        ["Optimal Annual Tilt", f"{annual_optimal_tilt}°"],
        ["User Generation (yearly)", f"{annual_energy:,.0f} kWh"],
        ["Optimal Generation (yearly)", f"{annual_optimal_energy:,.0f} kWh"],
        ["Potential", annual_potential_str],
    ]

    summary_table = Table(summary_data, colWidths=[230, 170])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 8))  # мінімальна між title/table

    # середня відстань між блоками
    story.append(Paragraph("Monthly Energy Production Chart:", h_style))
    story.append(Spacer(1, 4))  # мінімальна між заголовком і графіком

    rl_image = PDFImage(img_buffer, width=470, height=200)  # нижче, щоб влазило
    story.append(rl_image)

    story.append(Spacer(1, 8))  # середня між чартом і breakdown

    story.append(Paragraph("Monthly Breakdown:", h_style))
    story.append(Spacer(1, 4))  # мінімальна

    table_data = [["Month", "Energy (User Tilt), kWh", "Energy (Optimal Tilt), kWh", "Potential, %"]]
    table_data.extend(monthly_breakdown)

    main_table = Table(table_data, colWidths=[55, 150, 160, 85])
    main_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
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
    latitude = _clamp_lat(latitude)
    longitude = _wrap_lon(longitude)

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
    potential_pct = _potential_pct(annual_kwh_optimal, annual_kwh_user)

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
        f"Azimuth specified by user: {user_az_eff:.0f}°."
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
