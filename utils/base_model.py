import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Optional
from io import BytesIO

from pvlib.location import Location
from pvlib import irradiance

import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage


MONTH_NAMES = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]
MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


@dataclass
class UIOutput:
    optimal_angle: int
    annual_kwh_user: float
    annual_kwh_optimal: float
    potential_pct: float
    monthly_chart_df: pd.DataFrame      # month, kwh_user, kwh_optimal_yearly
    tilt_by_month_df: pd.DataFrame      # Month, BestTiltDeg
    recommendations: List[str]
    pdf_bytes: Optional[bytes]


def _month_index_series(values_by_month: dict) -> pd.Series:
    """values_by_month: {1..12 -> value}"""
    return pd.Series([values_by_month[m] for m in range(1, 13)], index=pd.Index(range(1, 13), name="month"))


def calculate_solar_output(
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth: float,
) -> dict:
    # Assumptions
    system_losses = 0.18
    timezone = "UTC"

    # Hourly times for the year
    times = pd.date_range("2025-01-01 00:00", "2025-12-31 23:00", freq="1h", tz=timezone)

    location = Location(latitude=latitude, longitude=longitude, tz=timezone)
    solar_position = location.get_solarposition(times)

    clearsky = location.get_clearsky(times, model="ineichen")
    ghi = clearsky["ghi"].clip(lower=0)         # W/m2
    ghi_kw = (ghi / 1000.0).astype(float)       # kW/m2

    # Compute hourly energy for tilts 0..90
    tilts = range(0, 91)
    hourly_energy = {}

    for t in tilts:
        aoi = irradiance.aoi(
            surface_tilt=t,
            surface_azimuth=user_azimuth,
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"],
        )
        cos_aoi = np.cos(np.radians(aoi)).astype(float)
        cos_aoi = np.where(cos_aoi < 0, 0, cos_aoi)
        poa = ghi_kw.values * cos_aoi * (1 - system_losses)   # kW/m2 (simplified)
        hourly_energy[f"tilt_{t}"] = poa * system_power_kw    # kWh per hour (approx)

    df_energy = pd.DataFrame(hourly_energy, index=times)

    # Monthly sums per tilt (rows: month 1..12)
    monthly_sum = df_energy.groupby(df_energy.index.month).sum()

    # Best tilt per month
    best_cols = monthly_sum.idxmax(axis=1)
    best_tilts = best_cols.str.replace("tilt_", "", regex=False).astype(int)

    monthly_best = pd.DataFrame({
        "Month": [MONTH_NAMES[m - 1] for m in monthly_sum.index],
        "BestTiltDeg": best_tilts.values
    })

    # Annual optimal tilt
    annual_sum = df_energy.sum()
    annual_opt_col = annual_sum.idxmax()
    annual_optimal_tilt = int(str(annual_opt_col).replace("tilt_", ""))
    annual_energy_optimal = float(annual_sum.max())

    # User tilt hourly energy
    aoi_user = irradiance.aoi(
        surface_tilt=user_tilt,
        surface_azimuth=user_azimuth,
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
    )
    cos_user = np.cos(np.radians(aoi_user)).astype(float)
    cos_user = np.where(cos_user < 0, 0, cos_user)
    poa_user = ghi_kw.values * cos_user * (1 - system_losses)
    hourly_user = pd.Series(poa_user * system_power_kw, index=times)

    monthly_user = hourly_user.groupby(hourly_user.index.month).sum()
    annual_energy_user = float(hourly_user.sum())

    # Optimal yearly tilt monthly generation
    monthly_opt_yearly = df_energy[f"tilt_{annual_optimal_tilt}"].groupby(df_energy.index.month).sum()

    # Optimal monthly-changing tilt generation
    monthly_opt_monthly_vals = {}
    for m in range(1, 13):
        best_tilt_m = int(monthly_best.loc[m - 1, "BestTiltDeg"])
        monthly_opt_monthly_vals[m] = float(df_energy.loc[df_energy.index.month == m, f"tilt_{best_tilt_m}"].sum())

    monthly_opt_monthly = _month_index_series(monthly_opt_monthly_vals)

    # Potential
    potential_pct = 0.0
    if annual_energy_user > 0:
        potential_pct = (annual_energy_optimal - annual_energy_user) / annual_energy_user * 100.0

    # Recommendations
    recs = [
        f"Your current tilt angle of {user_tilt:.0f}° is compared against the annual optimal tilt of {annual_optimal_tilt}° for the same azimuth ({user_azimuth:.0f}°).",
        f"Potential uplift compared to your current setup is approximately {potential_pct:+.1f}% (clearsky model, {int(system_losses*100)}% system losses assumed).",
        "Seasonal tilt adjustment can further improve generation (see monthly optimal tilt values).",
        "Regularly clean panels and avoid shading to maintain maximum efficiency.",
    ]

    # Monthly table for PDF (unique column keys internally)
    monthly_table_df = pd.DataFrame({
        "Month": MONTH_NAMES,
        "Your Generation kWh": [float(monthly_user.get(m, 0.0)) for m in range(1, 13)],
        "Optimal Tilt, yearly": [annual_optimal_tilt] * 12,
        "Optimal Generation kWh (yearly)": [float(monthly_opt_yearly.get(m, 0.0)) for m in range(1, 13)],
        "Optimal Tilt, monthly": [int(best_tilts.loc[m]) for m in range(1, 13)],
        "Optimal Generation kWh (monthly)": [float(monthly_opt_monthly.loc[m]) for m in range(1, 13)],
    })

    # Chart for PDF
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=160)
    ax.plot(MONTH_ABBR, monthly_table_df["Your Generation kWh"].values, label="Your tilt", color="#f59e0b", linewidth=2.6)
    ax.plot(MONTH_ABBR, monthly_table_df["Optimal Generation kWh (yearly)"].values, label="Optimal tilt", color="#22c55e", linewidth=2.6)
    ax.set_title("Monthly Generation Chart")
    ax.set_ylabel("kWh")
    ax.grid(True, alpha=0.25)
    ax.legend()
    plt.tight_layout()

    img_buf = BytesIO()
    fig.savefig(img_buf, format="png", dpi=160)
    img_buf.seek(0)
    plt.close(fig)

    # PDF
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
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18, spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceBefore=10, spaceAfter=6)
    sub = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=9)

    # As requested in spec
    report_date = pd.Timestamp("2025-12-22").strftime("%m/%d/%Y")

    story = []
    story.append(Paragraph("Solar Ninja - Generation Report", h1))
    story.append(Paragraph(f"Date: {report_date}", sub))
    story.append(Spacer(1, 12))

    story.append(Paragraph("System Parameters", h2))
    params_table = Table(
        [
            ["Parameter", "Value"],
            ["Location (lat, lon)", f"{latitude:.4f}, {longitude:.4f}"],
            ["System Power", f"{system_power_kw:.2f} kW"],
            ["Your Tilt Angle", f"{user_tilt:.1f}°"],
            ["Azimuth", f"{user_azimuth:.0f}°"],
            ["Optimal Annual Tilt", f"{annual_optimal_tilt}°"],
            ["Annual Generation (your tilt)", f"{annual_energy_user:,.0f} kWh"],
            ["Annual Generation (optimal)", f"{annual_energy_optimal:,.0f} kWh"],
        ],
        colWidths=[210, 270],
    )
    params_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(params_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Monthly Generation Chart", h2))
    story.append(PDFImage(img_buf, width=500, height=250))
    story.append(Spacer(1, 10))

    # Monthly Data table (as requested)
    story.append(Paragraph("Monthly Data", h2))

    header = [
        Paragraph("Month", small),
        Paragraph("Your Generation kWh", small),
        Paragraph("Optimal Tilt, yearly", small),
        Paragraph("Optimal Generation kWh", small),
        Paragraph("Optimal Tilt, monthly", small),
        Paragraph("Optimal Generation kWh", small),
    ]

    rows = []
    for _, r in monthly_table_df.iterrows():
        rows.append([
            r["Month"],
            f"{r['Your Generation kWh']:.0f}",
            f"{int(r['Optimal Tilt, yearly'])}",
            f"{r['Optimal Generation kWh (yearly)']:.0f}",
            f"{int(r['Optimal Tilt, monthly'])}",
            f"{r['Optimal Generation kWh (monthly)']:.0f}",
        ])

    monthly_table = Table([header] + rows, colWidths=[88, 86, 78, 92, 78, 92])
    monthly_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbfdff")]),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(monthly_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Recommendations", h2))
    for r in recs:
        story.append(Paragraph(f"• {r}", styles["Normal"]))

    doc.build(story)
    pdf_buf.seek(0)

    return {
        "monthly_best": monthly_best,
        "annual_optimal_tilt": annual_optimal_tilt,
        "annual_energy_user": annual_energy_user,
        "annual_energy_optimal": annual_energy_optimal,
        "monthly_user": monthly_user,
        "monthly_opt_yearly": monthly_opt_yearly,
        "monthly_opt_monthly": monthly_opt_monthly,
        "potential_pct": potential_pct,
        "recommendations": recs,
        "monthly_table_df": monthly_table_df,
        "pdf_bytes": pdf_buf.getvalue(),
    }


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

    monthly_chart_df = pd.DataFrame({
        "month": MONTH_ABBR,
        "kwh_user": [float(res["monthly_user"].get(m, 0.0)) for m in range(1, 13)],
        "kwh_optimal_yearly": [float(res["monthly_opt_yearly"].get(m, 0.0)) for m in range(1, 13)],
    })

    return UIOutput(
        optimal_angle=int(res["annual_optimal_tilt"]),
        annual_kwh_user=float(res["annual_energy_user"]),
        annual_kwh_optimal=float(res["annual_energy_optimal"]),
        potential_pct=float(res["potential_pct"]),
        monthly_chart_df=monthly_chart_df,
        tilt_by_month_df=res["monthly_best"][["Month", "BestTiltDeg"]].copy(),
        recommendations=list(res["recommendations"]),
        pdf_bytes=res["pdf_bytes"],
    )
