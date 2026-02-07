# utils/base_model.py

import pandas as pd
import numpy as np
from pvlib.location import Location
from pvlib import irradiance
import matplotlib.pyplot as plt
from io import BytesIO
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

# --- PDF imports (as in your verified version) ---
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage


# -----------------------------
# Helpers
# -----------------------------
def _normalize_azimuth_deg(az: float) -> float:
    """
    Normalize azimuth to [0, 360).
    pvlib convention: 0=N, 90=E, 180=S, 270=W
    """
    az = float(az)
    return az % 360.0


def _optimal_equator_facing_azimuth(latitude: float) -> float:
    """
    Baseline 'optimal azimuth' assumption (system ideal):
    - Northern hemisphere (lat >= 0): face South (180°)
    - Southern hemisphere (lat < 0): face North (0°)
    """
    return 180.0 if float(latitude) >= 0.0 else 0.0


def _hemisphere_label(latitude: float) -> str:
    return "Northern Hemisphere" if float(latitude) >= 0.0 else "Southern Hemisphere"


def _prepare_base(latitude: float, longitude: float, timezone: str = "UTC") -> Tuple[pd.DatetimeIndex, pd.DataFrame, pd.Series]:
    """
    Precompute time index, solar position, and clearsky GHI (kW/m^2), reused for any azimuth.
    Baseline year remains fixed to 2025, as in your verified model.
    """
    times = pd.date_range("2025-01-01", "2025-12-31 23:00", freq="1h", tz=timezone)

    location = Location(latitude=float(latitude), longitude=float(longitude), tz=timezone)
    solar_position = location.get_solarposition(times)

    clearsky = location.get_clearsky(times, model="ineichen")
    ghi = clearsky["ghi"].clip(lower=0)
    ghi_kw = ghi / 1000.0

    return times, solar_position, ghi_kw


def _compute_for_azimuth(
    *,
    times: pd.DatetimeIndex,
    solar_position: pd.DataFrame,
    ghi_kw: pd.Series,
    system_power_kw: float,
    user_tilt: float,
    surface_azimuth: float,
    system_losses: float = 0.18,
) -> Dict[str, Any]:
    """
    VERIFIED BASELINE LOGIC, parameterized by azimuth:
    - Same losses
    - Same clear-sky GHI
    - Same AOI cos() simplified POA
    - Same tilt grid 0..90
    - Same monthly best-tilt method
    - Same annual best-tilt loop
    """
    tilts = list(range(0, 91))
    hourly_energy_df = {}

    # ------------------------------------------------------------
    # Monthly optimal tilt (maximize kWh per month)
    # ------------------------------------------------------------
    for t in tilts:
        aoi = irradiance.aoi(
            surface_tilt=t,
            surface_azimuth=surface_azimuth,
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"],
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
    # Annual optimal tilt (verified baseline loop)
    # ------------------------------------------------------------
    best_tilt = None
    best_energy = -1.0

    for t in tilts:
        aoi = irradiance.aoi(
            surface_tilt=t,
            surface_azimuth=surface_azimuth,
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

    # ------------------------------------------------------------
    # User tilt energy (at this azimuth)
    # ------------------------------------------------------------
    aoi_user = irradiance.aoi(
        surface_tilt=float(user_tilt),
        surface_azimuth=surface_azimuth,
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
    )
    cos_user = np.cos(np.radians(aoi_user))
    cos_user[cos_user < 0] = 0

    poa_user = ghi_kw * cos_user * (1 - system_losses)
    hourly_user = poa_user * float(system_power_kw)

    monthly_energy = hourly_user.resample("M").sum()
    annual_energy = float(hourly_user.sum())

    monthly_df = pd.DataFrame(
        {
            "Month": monthly_energy.index.strftime("%B"),
            "Energy (kWh)": monthly_energy.values.round(0),
        }
    )

    # monthly generation for ANNUAL optimal tilt (from df_energy)
    monthly_opt_yearly = df_energy[f"tilt_{annual_optimal_tilt}"].resample("M").sum()
    monthly_opt_df = pd.DataFrame(
        {
            "Month": monthly_opt_yearly.index.strftime("%B"),
            "Energy (kWh)": monthly_opt_yearly.values.round(0),
        }
    )

    return {
        "monthly_df": monthly_df,
        "monthly_opt_df": monthly_opt_df,
        "monthly_best": monthly_best.reset_index(drop=True),
        "annual_energy": annual_energy,
        "annual_optimal_energy": annual_optimal_energy,
        "annual_optimal_tilt": annual_optimal_tilt,
        "surface_azimuth": float(surface_azimuth),
    }


def _make_user_monthly_chart_fig(monthly_df: pd.DataFrame, user_tilt: float, user_azimuth_used: float):
    """
    Keep your baseline Matplotlib bar chart style for PDF.
    """
    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    ax.bar(monthly_df["Month"], monthly_df["Energy (kWh)"], color="orange")
    ax.set_title(f"Monthly Energy Output (Tilt={float(user_tilt):.1f}°, Az={float(user_azimuth_used):.0f}°)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Energy (kWh)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig


def _build_pdf_bytes(
    *,
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth_used: float,
    optimal_azimuth: float,
    optimal_tilt: int,
    annual_kwh_user: float,
    annual_kwh_optimal: float,
    monthly_user_df: pd.DataFrame,
    monthly_optimal_df: pd.DataFrame,
) -> bytes:
    """
    PDF: baseline formatting preserved, but adds:
    - user azimuth used
    - system optimal azimuth
    - optimal tilt (system)
    - annual optimal generation
    - optional monthly optimal table
    """
    fig = _make_user_monthly_chart_fig(monthly_user_df, user_tilt, user_azimuth_used)
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format="png", dpi=150)
    img_buffer.seek(0)
    plt.close(fig)

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        alignment=1,
        spaceAfter=20,
        fontSize=18,
    )

    story = []
    story.append(Paragraph("Solar Ninja — Energy Generation Report", title_style))
    story.append(Spacer(1, 12))

    summary_data = [
        ["Parameter", "Value"],
        ["Location (Lat, Lon)", f"{float(latitude):.4f}, {float(longitude):.4f}"],
        ["System Power", f"{float(system_power_kw):.2f} kW"],
        ["User Tilt", f"{float(user_tilt):.1f}°"],
        ["User Azimuth (used)", f"{float(user_azimuth_used):.0f}°"],
        ["System Optimal Azimuth (baseline)", f"{float(optimal_azimuth):.0f}°"],
        ["System Optimal Tilt (baseline)", f"{int(optimal_tilt)}°"],
        ["Total Annual Energy (User)", f"{float(annual_kwh_user):,.0f} kWh"],
        ["Total Annual Energy (Optimal)", f"{float(annual_kwh_optimal):,.0f} kWh"],
    ]

    summary_table = Table(summary_data, colWidths=[230, 170])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 20))

    rl_image = PDFImage(img_buffer, width=450, height=250)
    story.append(Paragraph("Monthly Energy Production Chart (User Tilt+Azimuth):", styles["Heading2"]))
    story.append(Spacer(1, 10))
    story.append(rl_image)
    story.append(Spacer(1, 20))

    # User monthly table
    story.append(Paragraph("Monthly Breakdown (User Tilt+Azimuth):", styles["Heading2"]))
    story.append(Spacer(1, 10))

    user_table_data = [["Month", "Energy (kWh)"]]
    for _, row in monthly_user_df.iterrows():
        user_table_data.append([row["Month"], f"{int(row['Energy (kWh)'])}"])

    user_table = Table(user_table_data, colWidths=[180, 120])
    user_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]
        )
    )
    story.append(user_table)
    story.append(Spacer(1, 18))

    # Optimal monthly table (system optimal)
    story.append(Paragraph("Monthly Breakdown (System Optimal Tilt+Azimuth):", styles["Heading2"]))
    story.append(Spacer(1, 10))

    opt_table_data = [["Month", "Energy (kWh)"]]
    for _, row in monthly_optimal_df.iterrows():
        opt_table_data.append([row["Month"], f"{int(row['Energy (kWh)'])}"])

    opt_table = Table(opt_table_data, colWidths=[180, 120])
    opt_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]
        )
    )
    story.append(opt_table)

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


# -----------------------------
# UI Output schema (aligned to your updated requirements)
# -----------------------------
@dataclass
class UIOutput:
    optimal_angle: int                 # optimal tilt (system)
    optimal_azimuth: float             # ideal azimuth (system)
    annual_kwh_user: float             # your generation
    annual_kwh_optimal: float          # optimal generation (system ideal)
    potential_pct: float               # (optimal - your) / your
    monthly_chart_df: pd.DataFrame     # columns: month, kwh_user, kwh_optimal
    tilt_by_month_df: pd.DataFrame     # columns: Month, BestTiltDeg (system ideal azimuth)
    recommendations: List[str]
    pdf_bytes: Optional[bytes]
    user_azimuth_used: float           # for UI transparency


def run_for_ui(
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth: Optional[float],
) -> UIOutput:
    """
    Your updated logic:

    - User azimuth:
        If provided -> use it
        Else -> default = 180 (lat>=0) or 0 (lat<0)
    - System "optimal" azimuth:
        baseline equator-facing = 180 (lat>=0) or 0 (lat<0)
    - Your generation:
        user tilt + user azimuth used
    - Optimal generation:
        system optimal azimuth + system optimal tilt
    - Optimal tilt by month:
        computed under system optimal azimuth
    """
    latitude = float(latitude)
    longitude = float(longitude)
    system_power_kw = float(system_power_kw)
    user_tilt = float(user_tilt)

    # base precompute
    times, solar_position, ghi_kw = _prepare_base(latitude, longitude, timezone="UTC")

    # system ideal azimuth
    optimal_azimuth = _optimal_equator_facing_azimuth(latitude)

    # user azimuth used (user input OR default)
    if user_azimuth is None:
        user_azimuth_used = float(optimal_azimuth)
        user_az_note = "User azimuth not provided → defaulted to system optimal azimuth."
    else:
        user_azimuth_used = float(_normalize_azimuth_deg(user_azimuth))
        user_az_note = "User azimuth provided and used in 'Your generation'."

    # Compute user scenario (your generation)
    res_user = _compute_for_azimuth(
        times=times,
        solar_position=solar_position,
        ghi_kw=ghi_kw,
        system_power_kw=system_power_kw,
        user_tilt=user_tilt,
        surface_azimuth=user_azimuth_used,
        system_losses=0.18,
    )
    annual_kwh_user = float(res_user["annual_energy"])
    monthly_user_df = res_user["monthly_df"]

    # Compute system ideal scenario (optimal generation + optimal tilt)
    if float(user_azimuth_used) == float(optimal_azimuth):
        res_sys = res_user
    else:
        res_sys = _compute_for_azimuth(
            times=times,
            solar_position=solar_position,
            ghi_kw=ghi_kw,
            system_power_kw=system_power_kw,
            user_tilt=user_tilt,  # doesn't affect optimal tilt results; still needed for monthly_df in res, but we use monthly_opt_df
            surface_azimuth=float(optimal_azimuth),
            system_losses=0.18,
        )

    optimal_angle = int(res_sys["annual_optimal_tilt"])
    annual_kwh_optimal = float(res_sys["annual_optimal_energy"])
    monthly_optimal_df = res_sys["monthly_opt_df"]  # optimal tilt @ system azimuth
    monthly_best_sys = res_sys["monthly_best"]      # best tilt by month @ system azimuth

    # Potential
    potential_pct = 0.0
    if annual_kwh_user != 0:
        potential_pct = (annual_kwh_optimal - annual_kwh_user) / annual_kwh_user * 100.0

    # Monthly chart df for UI (Jan..Dec short labels)
    months_dt = pd.date_range("2025-01-01", periods=12, freq="MS")
    month_short = months_dt.strftime("%b").tolist()

    user_monthly = monthly_user_df["Energy (kWh)"].astype(float).tolist()
    opt_monthly = monthly_optimal_df["Energy (kWh)"].astype(float).tolist()

    monthly_chart_df = pd.DataFrame(
        {
            "month": month_short,
            "kwh_user": user_monthly,
            "kwh_optimal": opt_monthly,
        }
    )

    # Tilt by month (system ideal)
    tilt_by_month_df = monthly_best_sys[["Month", "Best Tilt (deg)"]].copy()
    tilt_by_month_df = tilt_by_month_df.rename(columns={"Best Tilt (deg)": "BestTiltDeg"})

    hemi = _hemisphere_label(latitude)
    recommendations = [
        f"Hemisphere detected: {hemi}. System optimal azimuth (baseline equator-facing) = {optimal_azimuth:.0f}°.",
        f"{user_az_note} User azimuth used = {user_azimuth_used:.0f}°.",
        f"Your generation: tilt {user_tilt:.1f}°, azimuth {user_azimuth_used:.0f}° → ~{annual_kwh_user:,.0f} kWh/year.",
        f"Optimal generation (system ideal): azimuth {optimal_azimuth:.0f}°, optimal tilt {optimal_angle}° → ~{annual_kwh_optimal:,.0f} kWh/year.",
        f"Estimated potential vs your current setup: {potential_pct:+.1f}%.",
        "Note: baseline model = clear-sky GHI + AOI cosine projection, kept intentionally consistent with your verified calculations.",
    ]

    # PDF bytes
    pdf_bytes = None
    try:
        pdf_bytes = _build_pdf_bytes(
            latitude=latitude,
            longitude=longitude,
            system_power_kw=system_power_kw,
            user_tilt=user_tilt,
            user_azimuth_used=user_azimuth_used,
            optimal_azimuth=float(optimal_azimuth),
            optimal_tilt=optimal_angle,
            annual_kwh_user=annual_kwh_user,
            annual_kwh_optimal=annual_kwh_optimal,
            monthly_user_df=monthly_user_df,
            monthly_optimal_df=monthly_optimal_df,
        )
    except Exception:
        pdf_bytes = None

    return UIOutput(
        optimal_angle=optimal_angle,
        optimal_azimuth=float(optimal_azimuth),
        annual_kwh_user=annual_kwh_user,
        annual_kwh_optimal=annual_kwh_optimal,
        potential_pct=float(potential_pct),
        monthly_chart_df=monthly_chart_df,
        tilt_by_month_df=tilt_by_month_df,
        recommendations=recommendations,
        pdf_bytes=pdf_bytes,
        user_azimuth_used=float(user_azimuth_used),
    )
