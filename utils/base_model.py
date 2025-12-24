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
    Solar Ninja — Basic Model (Clearsky-based estimate)
    Outputs:
      - Annual optimal tilt (single tilt)
      - Monthly best tilt (tilt changes per month)
      - Annual generation for user tilt
      - Annual generation for optimal yearly tilt
      - Monthly generation series for:
          * user tilt
          * optimal yearly tilt
          * optimal monthly tilt (changing per month)
      - PDF bytes with requested structure
    """
    system_losses = 0.18
    timezone = "UTC"
    times = pd.date_range("2025-01-01", "2025-12-31 23:00", freq="1h", tz=timezone)

    # Location & sun position
    location = Location(latitude=latitude, longitude=longitude, tz=timezone)
    solar_position = location.get_solarposition(times)

    # Clearsky GHI (W/m2 -> kW/m2)
    clearsky = location.get_clearsky(times, model="ineichen")
    ghi = clearsky["ghi"].clip(lower=0)
    ghi_kw = ghi / 1000.0

    # Hourly energy for tilts 0..90 at fixed azimuth
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
        hourly_energy = poa * system_power_kw  # kWh per hour

        hourly_energy_df[f"tilt_{t}"] = hourly_energy

    df_energy = pd.DataFrame(hourly_energy_df, index=times)

    # Monthly best tilt (maximize each month)
    monthly_sum_by_tilt = df_energy.resample("M").sum()
    monthly_best = monthly_sum_by_tilt.idxmax(axis=1).str.extract(r"(\d+)").astype(int)
    monthly_best.columns = ["Best Tilt (deg)"]
    monthly_best["Month"] = monthly_best.index.strftime("%B")
    monthly_best = monthly_best.reset_index(drop=True)

    # Annual optimal tilt (single best tilt for whole year)
    annual_sum_by_tilt = df_energy.sum(axis=0)
    annual_optimal_col = annual_sum_by_tilt.idxmax()
    annual_optimal_tilt = int(str(annual_optimal_col).replace("tilt_", ""))
    annual_energy_optimal = float(annual_sum_by_tilt.max())

    # User tilt hourly -> monthly + annual
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

    # Optimal monthly-changing tilt generation
    monthly_opt_monthly_values = []
    for dt, _ in monthly_opt_yearly.items():
        month_name = dt.strftime("%B")
        best_tilt_month = int(monthly_best.loc[monthly_best["Month"] == month_name, "Best Tilt (deg)"].iloc[0])
        monthly_value = float(df_energy[f"tilt_{best_tilt_month}"][df_energy.index.month == dt.month].sum())
        monthly_opt_monthly_values.append(monthly_value)

    monthly_opt_monthly = pd.Series(monthly_opt_monthly_values, index=monthly_opt_yearly.index)

    # Potential %
    potential_pct = 0.0
    if annual_energy_user > 0:
        potential_pct = (annual_energy_optimal - annual_energy_user) / annual_energy_user * 100.0

    # Recommendations
    seasonal_summer = int(monthly_best.loc[monthly_best["Month"] == "June", "Best Tilt (deg)"].iloc[0]) if (monthly_best["Month"] == "June").any() else None
    seasonal_winter = int(monthly_best.loc[monthly_best["Month"] == "December", "Best Tilt (deg)"].iloc[0]) if (monthly_best["Month"] == "December").any() else None

    recs = []
    recs.append(
        f"Your current tilt angle of {user_tilt:.0f}° is compared against the annual optimal tilt of {annual_optimal_tilt}° for the same azimuth ({user_azimuth:.0f}°)."
    )
    recs.append(
        f"Potential uplift vs your current setup is approximately +{potential_pct:.1f}% (clearsky model, {int(system_losses*100)}% system losses assumed)."
    )
    if seasonal_summer is not None and seasonal_winter is not None:
        recs.append(
            f"For seasonal adjustment, consider using ~{seasonal_summer}° in summer and ~{seasonal_winter}° in winter (see the monthly table)."
        )
    recs.append("Regularly clean panels from dust and snow, and avoid shading to maintain maximum efficiency.")

    # ===== PDF chart (user vs optimal yearly tilt) =====
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
    fig.savefig(img_buffer, format="png", dpi=160)
    img_buffer.seek(0)
    plt.close(fig)

    # ===== Build PDF (requested structure, English) =====
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=44, leftMargin=44,
        topMargin=44, bottomMargin=44
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        alignment=0,
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        textColor=colors.HexColor("#475569"),
        fontSize=10,
        spaceAfter=14
    )
    h_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8
    )
    normal_style = styles["Normal"]

    report_date = pd.Timestamp.now().strftime("%m/%d/%Y")

    story = []
    story.append(Paragraph("Solar Ninja — Generation Report", title_style))
    story.append(Paragraph(f"Date: {report_date}", subtitle_style))

    # 1) System Parameters
    story.append(Paragraph("System Parameters", h_style))
    params_data = [
        ["Location (lat, lon)", f"{latitude:.4f}, {longitude:.4f}"],
        ["System Power", f"{system_power_kw:.2f} kW"],
        ["Your Tilt Angle", f"{user_tilt:.1f}°"],
        ["Azimuth", f"{user_azimuth:.0f}°"],
        ["Optimal Annual Tilt", f"{annual_optimal_tilt}°"],
        ["Annual Generation (your tilt)", f"{annual_energy_user:,.0f} kWh"],
        ["Annual Generation (optimal)", f"{annual_energy_optimal:,.0f} kWh"],
    ]

    params_table = Table([["Parameter", "Value"]] + params_data, colWidths=[220, 260])
    params_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f1f5f9"), colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(params_table)
    story.append(Spacer(1, 14))

    # 2) Monthly Generation Chart
    story.append(Paragraph("Monthly Generation Chart", h_style))
    story.append(Spacer(1, 6))
    story.append(PDFImage(img_buffer, width=500, height=250))
    story.append(Spacer(1, 14))

    # 3) Monthly Data table (requested columns)
    story.append(Paragraph("Monthly Data", h_style))
    story.append(Spacer(1, 6))

    months_full = monthly_user.index.strftime("%B").tolist()
    monthly_rows = []
    for i, m in enumerate(months_full):
        your_kwh = float(monthly_user.values[i])
        opt_yearly_kwh = float(monthly_opt_yearly.values[i])
        opt_monthly_kwh = float(monthly_opt_monthly.values[i])
        opt_tilt_month = int(monthly_best.loc[monthly_best["Month"] == m, "Best Tilt (deg)"].iloc[0])

        monthly_rows.append([
            m,
            f"{your_kwh:,.0f}",
            f"{annual_optimal_tilt}°",
            f"{opt_yearly_kwh:,.0f}",
            f"{opt_tilt_month}°",
            f"{opt_monthly_kwh:,.0f}",
        ])

    monthly_table = Table(
        [[
            "Month",
            "Your Generation (kWh)",
            "Optimal Tilt (yearly)",
            "Optimal Generation (kWh) — yearly tilt",
            "Optimal Tilt (monthly)",
            "Optimal Generation (kWh) — monthly tilt"
        ]] + monthly_rows,
        colWidths=[78, 92, 80, 120, 90, 120]
    )

    monthly_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f59e0b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0b1220")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))

    story.append(monthly_table)
    story.append(Spacer(1, 14))

    # 4) Recommendations
    story.append(Paragraph("Recommendations", h_style))
    bullets = "".join([f"<br/>• {r}" for r in recs])
    story.append(Paragraph(bullets, normal_style))

    doc.build(story)
    pdf_buffer.seek(0)

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
        "pdf": pdf_buffer,
    }


def run_for_ui(latitude: float,
               longitude: float,
               system_power_kw: float,
               user_tilt: float,
               user_azimuth: float) -> UIOutput:
    res = calculate_solar_output(
        latitude=latitude,
        longitude=longitude,
        system_power_kw=system_power_kw,
        user_tilt=user_tilt,
        user_azimuth=user_azimuth
    )

    months_short = res["monthly_user"].index.strftime("%b")
    monthly_chart_df = pd.DataFrame({
        "month": months_short,
        "kwh_user": res["monthly_user"].values.astype(float),
        "kwh_optimal_yearly": res["monthly_opt_yearly"].values.astype(float),
    })

    pdf_bytes = res["pdf"].getvalue() if res.get("pdf") is not None else None

    return UIOutput(
        optimal_angle=int(res["annual_optimal_tilt"]),
        annual_kwh_user=float(res["annual_energy_user"]),
        annual_kwh_optimal=float(res["annual_energy_optimal"]),
        potential_pct=float(res["potential_pct"]),
        monthly_chart_df=monthly_chart_df,
        tilt_by_month_df=res["monthly_best"][["Month", "Best Tilt (deg)"]].copy(),
        recommendations=list(res["recommendations"]),
        pdf_bytes=pdf_bytes
    )
