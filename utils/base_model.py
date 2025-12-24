import pandas as pd
import numpy as np
from pvlib.location import Location
from pvlib import irradiance
import matplotlib.pyplot as plt
from io import BytesIO
from dataclasses import dataclass
from typing import List, Optional

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
    monthly_chart_df: pd.DataFrame     # month, kwh_user, kwh_optimal_yearly
    tilt_by_month_df: pd.DataFrame     # Month, BestTiltDeg
    recommendations: List[str]
    pdf_bytes: Optional[bytes]


def calculate_solar_output(
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth: float
) -> dict:
    system_losses = 0.18

    timezone = "UTC"
    times = pd.date_range("2025-01-01", "2025-12-31 23:00", freq="1h", tz=timezone)

    location = Location(latitude=latitude, longitude=longitude, tz=timezone)
    solar_position = location.get_solarposition(times)

    clearsky = location.get_clearsky(times, model="ineichen")
    ghi = clearsky["ghi"].clip(lower=0)
    ghi_kw = ghi / 1000.0

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
        cos_aoi[cos_aoi < 0] = 0
        poa = ghi_kw * cos_aoi * (1 - system_losses)
        hourly_energy[f"tilt_{t}"] = poa * system_power_kw

    df_energy = pd.DataFrame(hourly_energy, index=times)

    # Monthly best tilt
    monthly_sum = df_energy.resample("M").sum()
    best_cols = monthly_sum.idxmax(axis=1)
    best_tilts = best_cols.str.replace("tilt_", "", regex=False).astype(int)

    monthly_best = pd.DataFrame({
        "Month": monthly_sum.index.strftime("%B"),
        "BestTiltDeg": best_tilts.values
    })

    # Annual optimal tilt
    annual_sum = df_energy.sum()
    annual_opt_col = annual_sum.idxmax()
    annual_optimal_tilt = int(str(annual_opt_col).replace("tilt_", ""))
    annual_energy_optimal = float(annual_sum.max())

    # User tilt energy
    aoi_user = irradiance.aoi(
        surface_tilt=user_tilt,
        surface_azimuth=user_azimuth,
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
    )
    cos_user = np.cos(np.radians(aoi_user))
    cos_user[cos_user < 0] = 0
    poa_user = ghi_kw * cos_user * (1 - system_losses)
    hourly_user = poa_user * system_power_kw

    monthly_user = hourly_user.resample("M").sum()
    annual_energy_user = float(hourly_user.sum())

    # Optimal yearly tilt monthly generation
    monthly_opt_yearly = df_energy[f"tilt_{annual_optimal_tilt}"].resample("M").sum()

    # Optimal monthly-changing tilt generation
    monthly_opt_monthly_vals = []
    for dt in monthly_opt_yearly.index:
        m = dt.strftime("%B")
        best_tilt_m = int(monthly_best.loc[monthly_best["Month"] == m, "BestTiltDeg"].iloc[0])
        mask = df_energy.index.month == dt.month
        monthly_opt_monthly_vals.append(float(df_energy.loc[mask, f"tilt_{best_tilt_m}"].sum()))
    monthly_opt_monthly = pd.Series(monthly_opt_monthly_vals, index=monthly_opt_yearly.index)

    potential_pct = 0.0
    if annual_energy_user > 0:
        potential_pct = (annual_energy_optimal - annual_energy_user) / annual_energy_user * 100.0

    recs = [
        f"Your current tilt angle of {user_tilt:.0f}° is compared against the annual optimal tilt of {annual_optimal_tilt}° for the same azimuth ({user_azimuth:.0f}°).",
        f"Potential uplift compared to your current setup is approximately +{potential_pct:.1f}% (clearsky model, {int(system_losses*100)}% system losses assumed).",
        "Seasonal tilt adjustment can further improve generation (see monthly optimal tilt values).",
        "Regularly clean panels and avoid shading to maintain maximum efficiency.",
    ]

    # Chart for PDF
    months_short = monthly_user.index.strftime("%b")
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=160)
    ax.plot(months_short, monthly_user.values, label="Your tilt", color="#f59e0b", linewidth=2.6)
    ax.plot(months_short, monthly_opt_yearly.values, label="Optimal tilt (yearly)", color="#22c55e", linewidth=2.6)
    ax.set_title("Monthly Generation Chart")
    ax.set_ylabel("kWh")
    ax.grid(True, alpha=0.25)
    ax.legend()
    plt.tight_layout()

    img_buf = BytesIO()
    fig.savefig(img_buf, format="png", dpi=160)
    img_buf.seek(0)
    plt.close(fig)

    # PDF (simple, aligned with UI; you can extend later)
    pdf_buf = BytesIO()
    doc = SimpleDocTemplate(pdf_buf, pagesize=A4, rightMargin=44, leftMargin=44, topMargin=44, bottomMargin=44)

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13)
    sub = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, textColor=colors.grey)

    story = []
    story.append(Paragraph("Solar Ninja — Generation Report", h1))
    story.append(Paragraph(f"Date: {pd.Timestamp.now().strftime('%m/%d/%Y')}", sub))
    story.append(Spacer(1, 14))

    story.append(Paragraph("System Parameters", h2))
    params_table = Table([
        ["Parameter", "Value"],
        ["Location (lat, lon)", f"{latitude:.4f}, {longitude:.4f}"],
        ["System Power", f"{system_power_kw:.2f} kW"],
        ["Your Tilt Angle", f"{user_tilt:.1f}°"],
        ["Azimuth", f"{user_azimuth:.0f}°"],
        ["Optimal Annual Tilt", f"{annual_optimal_tilt}°"],
        ["Annual Generation (your tilt)", f"{annual_energy_user:,.0f} kWh"],
        ["Annual Generation (optimal)", f"{annual_energy_optimal:,.0f} kWh"],
    ], colWidths=[220, 260])

    params_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    story.append(params_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Monthly Generation Chart", h2))
    story.append(PDFImage(img_buf, width=500, height=250))
    story.append(Spacer(1, 14))

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
        "pdf_bytes": pdf_buf.getvalue(),
    }


# ✅ This is what app.py imports
def run_for_ui(
    latitude: float,
    longitude: float,
    system_power_kw: float,
    user_tilt: float,
    user_azimuth: float
) -> UIOutput:
    res = calculate_solar_output(
        latitude=latitude,
        longitude=longitude,
        system_power_kw=system_power_kw,
        user_tilt=user_tilt,
        user_azimuth=user_azimuth
    )

    monthly_chart_df = pd.DataFrame({
        "month": res["monthly_user"].index.strftime("%b"),
        "kwh_user": res["monthly_user"].values.astype(float),
        "kwh_optimal_yearly": res["monthly_opt_yearly"].values.astype(float),
    })

    return UIOutput(
        optimal_angle=int(res["annual_optimal_tilt"]),
        annual_kwh_user=float(res["annual_energy_user"]),
        annual_kwh_optimal=float(res["annual_energy_optimal"]),
        potential_pct=float(res["potential_pct"]),
        monthly_chart_df=monthly_chart_df,
        tilt_by_month_df=res["monthly_best"][["Month", "BestTiltDeg"]].copy(),
        recommendations=list(res["recommendations"]),
        pdf_bytes=res["pdf_bytes"]
    )
