# utils/base_model.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict

import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from io import BytesIO

from pvlib.location import Location
from pvlib import irradiance

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
    monthly_chart_df: pd.DataFrame     # month, kwh_user, kwh_optimal_yearly
    tilt_by_month_df: pd.DataFrame     # Month, BestTiltDeg (Month should be short to fit)
    recommendations: List[str]
    pdf_bytes: Optional[bytes]


def _format_kwh(x: float) -> str:
    try:
        return f"{float(x):,.0f}"
    except Exception:
        return str(x)


def calculate_solar_output(
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth: float,
    year: int = 2025,
    system_losses: float = 0.18,
    timezone: str = "UTC",
) -> Dict[str, object]:
    """
    Simplified PV estimate (clearsky GHI + AOI cosine).
    Returns monthly series for:
      - user tilt
      - annual optimal tilt (single tilt for whole year)
      - monthly optimal tilt (tilt changes each month)
    """

    times = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="1h", tz=timezone)

    location = Location(latitude=latitude, longitude=longitude, tz=timezone)
    solar_position = location.get_solarposition(times)

    clearsky = location.get_clearsky(times, model="ineichen")
    ghi = clearsky["ghi"].clip(lower=0) / 1000.0  # kW/m2 proxy

    # Compute hourly energy for all tilts 0..90 (integer)
    tilts = range(0, 91)
    hourly_energy = {}

    for t in tilts:
        aoi = irradiance.aoi(
            surface_tilt=t,
            surface_azimuth=user_azimuth,
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"],
        )
        cos_aoi = np.cos(np.radians(aoi))
        cos_aoi = np.where(cos_aoi < 0, 0, cos_aoi)

        # Simple POA proxy + system losses
        poa = ghi * cos_aoi * (1 - system_losses)

        # kWh per hour (since timestep is 1 hour)
        hourly_energy[f"tilt_{t}"] = poa * system_power_kw

    df_energy = pd.DataFrame(hourly_energy, index=times)

    # Monthly best tilt
    monthly_sum = df_energy.resample("M").sum()
    best_cols = monthly_sum.idxmax(axis=1)
    best_tilts = best_cols.str.replace("tilt_", "", regex=False).astype(int)

    # Use short months for UI tiles (prevents wrapping)
    month_short = monthly_sum.index.strftime("%b")  # Jan, Feb...
    month_full = monthly_sum.index.strftime("%B")

    monthly_best = pd.DataFrame(
        {
            "Month": month_short,
            "MonthFull": month_full,
            "BestTiltDeg": best_tilts.values,
        }
    )

    # Annual optimal tilt
    annual_sum = df_energy.sum()
    annual_opt_col = annual_sum.idxmax()
    annual_optimal_tilt = int(str(annual_opt_col).replace("tilt_", ""))
    annual_energy_optimal = float(annual_sum.max())

    # User tilt energy (allow non-integer tilt)
    aoi_user = irradiance.aoi(
        surface_tilt=user_tilt,
        surface_azimuth=user_azimuth,
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
    )
    cos_user = np.cos(np.radians(aoi_user))
    cos_user = np.where(cos_user < 0, 0, cos_user)
    poa_user = ghi * cos_user * (1 - system_losses)
    hourly_user = poa_user * system_power_kw

    monthly_user = hourly_user.resample("M").sum()
    annual_energy_user = float(hourly_user.sum())

    # Annual-optimal tilt monthly generation
    monthly_opt_yearly = df_energy[f"tilt_{annual_optimal_tilt}"].resample("M").sum()

    # Monthly-changing tilt generation
    monthly_opt_monthly_vals = []
    for i, dt in enumerate(monthly_opt_yearly.index):
        best_tilt_m = int(monthly_best.loc[i, "BestTiltDeg"])
        mask = df_energy.index.month == dt.month
        monthly_opt_monthly_vals.append(float(df_energy.loc[mask, f"tilt_{best_tilt_m}"].sum()))
    monthly_opt_monthly = pd.Series(monthly_opt_monthly_vals, index=monthly_opt_yearly.index)

    potential_pct = 0.0
    if annual_energy_user > 0:
        potential_pct = (annual_energy_optimal - annual_energy_user) / annual_energy_user * 100.0

    recs = [
        f"Your tilt angle is {user_tilt:.0f}° and the annual optimal tilt for this location is {annual_optimal_tilt}° (azimuth {user_azimuth:.0f}°).",
        f"Estimated potential change vs your current tilt: {potential_pct:+.1f}% (clearsky model, {int(system_losses*100)}% system losses).",
        "If your mounting system allows it, seasonal tilt adjustment can improve generation (see monthly optimal tilt).",
        "Keep panels clean and minimize shading to maintain efficiency.",
    ]

    # Monthly Data table for PDF
    monthly_data_df = pd.DataFrame(
        {
            "Month": monthly_user.index.strftime("%b"),
            "Your Generation (kWh)": monthly_user.values.astype(float),
            "Optimal Tilt, yearly (°)": [annual_optimal_tilt] * len(monthly_user),
            "Optimal Gen, yearly (kWh)": monthly_opt_yearly.values.astype(float),
            "Optimal Tilt, monthly (°)": monthly_best["BestTiltDeg"].values.astype(int),
            "Optimal Gen, monthly (kWh)": monthly_opt_monthly.values.astype(float),
        }
    )

    # Chart image for PDF (user vs annual optimal)
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=160)
    ax.plot(month_short, monthly_user.values, label="Your tilt", color="#f59e0b", linewidth=2.6)
    ax.plot(month_short, monthly_opt_yearly.values, label="Optimal tilt", color="#22c55e", linewidth=2.6)
    ax.set_title("Monthly Generation Chart")
    ax.set_ylabel("kWh")
    ax.grid(True, alpha=0.25)
    ax.legend()
    plt.tight_layout()

    img_buf = BytesIO()
    fig.savefig(img_buf, format="png", dpi=160)
    img_buf.seek(0)
    plt.close(fig)

    # Build PDF
    pdf_bytes = _build_pdf_report(
        img_buf=img_buf,
        latitude=latitude,
        longitude=longitude,
        system_power_kw=system_power_kw,
        user_tilt=user_tilt,
        user_azimuth=user_azimuth,
        annual_optimal_tilt=annual_optimal_tilt,
        annual_energy_user=annual_energy_user,
        annual_energy_optimal=annual_energy_optimal,
        monthly_data_df=monthly_data_df,
        recommendations=recs,
    )

    return {
        "monthly_best": monthly_best,
        "annual_optimal_tilt": annual_optimal_tilt,
        "annual_energy_user": annual_energy_user,
        "annual_energy_optimal": annual_energy_optimal,
        "monthly_user": monthly_user,
        "monthly_opt_yearly": monthly_opt_yearly,
        "monthly_opt_monthly": monthly_opt_monthly,
        "monthly_data_df": monthly_data_df,
        "potential_pct": potential_pct,
        "recommendations": recs,
        "pdf_bytes": pdf_bytes,
    }


def _build_pdf_report(
    img_buf: BytesIO,
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth: float,
    annual_optimal_tilt: int,
    annual_energy_user: float,
    annual_energy_optimal: float,
    monthly_data_df: pd.DataFrame,
    recommendations: List[str],
) -> bytes:
    pdf_buf = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buf,
        pagesize=A4,
        rightMargin=44,
        leftMargin=44,
        topMargin=44,
        bottomMargin=44,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18, spaceAfter=6)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceBefore=10, spaceAfter=6)
    sub = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
    normal = ParagraphStyle("N", parent=styles["Normal"], fontSize=10, leading=13)

    story = []
    story.append(Paragraph("Solar Ninja - Generation Report", h1))
    story.append(Paragraph(f"Date: {pd.Timestamp.now().strftime('%m/%d/%Y')}", sub))
    story.append(Spacer(1, 12))

    # System Parameters
    story.append(Paragraph("System Parameters", h2))
    params_rows = [
        ["Location (lat, lon)", f"{latitude:.4f}, {longitude:.4f}"],
        ["System Power", f"{system_power_kw:.2f} kW"],
        ["Your Tilt Angle", f"{user_tilt:.1f}°"],
        ["Azimuth", f"{user_azimuth:.0f}°"],
        ["Optimal Annual Tilt", f"{annual_optimal_tilt}°"],
        ["Annual Generation (your tilt)", f"{_format_kwh(annual_energy_user)} kWh"],
        ["Annual Generation (optimal)", f"{_format_kwh(annual_energy_optimal)} kWh"],
    ]

    params_table = Table(
        [["Parameter", "Value"]] + params_rows,
        colWidths=[220, 260],
    )
    params_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (1, -1), "LEFT"),
            ]
        )
    )
    story.append(params_table)
    story.append(Spacer(1, 12))

    # Chart
    story.append(Paragraph("Monthly Generation Chart", h2))
    story.append(PDFImage(img_buf, width=500, height=250))
    story.append(Spacer(1, 12))

    # Monthly Data table
    story.append(Paragraph("Monthly Data", h2))

    header = [
        "Month",
        "Your Generation (kWh)",
        "Optimal Tilt, yearly (°)",
        "Optimal Gen, yearly (kWh)",
        "Optimal Tilt, monthly (°)",
        "Optimal Gen, monthly (kWh)",
    ]

    rows = []
    for _, r in monthly_data_df.iterrows():
        rows.append(
            [
                str(r["Month"]),
                _format_kwh(r["Your Generation (kWh)"]),
                str(int(r["Optimal Tilt, yearly (°)"])),
                _format_kwh(r["Optimal Gen, yearly (kWh)"]),
                str(int(r["Optimal Tilt, monthly (°)"])),
                _format_kwh(r["Optimal Gen, monthly (kWh)"]),
            ]
        )

    # A4 usable width ~ 507pt; keep table compact
    col_widths = [44, 92, 78, 104, 78, 104]  # total 500
    data_table = Table([header] + rows, colWidths=col_widths, repeatRows=1)

    data_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f59e0b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0b1220")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.8),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ]
        )
    )

    story.append(data_table)
    story.append(Spacer(1, 12))

    # Recommendations
    story.append(Paragraph("Recommendations", h2))
    for r in recommendations:
        story.append(Paragraph(f"• {r}", normal))

    doc.build(story)
    pdf_buf.seek(0)
    return pdf_buf.getvalue()


# ✅ This is what app.py imports
def run_for_ui(
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth: float,
) -> UIOutput:
    res = calculate_solar_output(
        latitude=latitude,
        longitude=longitude,
        system_power_kw=system_power_kw,
        user_tilt=user_tilt,
        user_azimuth=user_azimuth,
    )

    monthly_chart_df = pd.DataFrame(
        {
            "month": res["monthly_user"].index.strftime("%b"),
            "kwh_user": res["monthly_user"].values.astype(float),
            "kwh_optimal_yearly": res["monthly_opt_yearly"].values.astype(float),
        }
    )

    tilt_by_month_df = res["monthly_best"][["Month", "BestTiltDeg"]].copy()

    return UIOutput(
        optimal_angle=int(res["annual_optimal_tilt"]),
        annual_kwh_user=float(res["annual_energy_user"]),
        annual_kwh_optimal=float(res["annual_energy_optimal"]),
        potential_pct=float(res["potential_pct"]),
        monthly_chart_df=monthly_chart_df,
        tilt_by_month_df=tilt_by_month_df,
        recommendations=list(res["recommendations"]),
        pdf_bytes=res["pdf_bytes"],
    )
