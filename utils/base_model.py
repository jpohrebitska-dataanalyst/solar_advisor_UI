import pandas as pd
import numpy as np
from pvlib.location import Location
from pvlib import irradiance
import matplotlib.pyplot as plt
from io import BytesIO
import tempfile
import os

# --- Оновлені імпорти для красивого PDF ---
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage

def calculate_solar_output(latitude, longitude, system_power_kw, user_tilt):
    """
    Solar Ninja — Basic Model (Fixed PDF Formatting + Updated Plot Styling)
    """
    # ВИЗНАЧЕННЯ: Втрати системи
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
    # 4. Monthly optimal tilt
    # ------------------------------------------------------------
    tilts = list(range(0, 91))
    hourly_energy_df = {}

    for t in tilts:
        aoi = irradiance.aoi(
            surface_tilt=t,
            surface_azimuth=180,
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
            surface_azimuth=180,
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

    # ------------------------------------------------------------
    # 6. User tilt energy
    # ------------------------------------------------------------
    aoi_user = irradiance.aoi(
        surface_tilt=user_tilt,
        surface_azimuth=180,
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
        "Energy (kWh)": monthly_energy.values.round(0)
    })

    # ------------------------------------------------------------
    # 7. Generate Charts (Matplotlib) - UPDATED STYLING
    # ------------------------------------------------------------
    # Використовуємо стиль, який добре виглядає і в темній, і в світлій темі
    # Але робимо його більш "пласким" і сучасним
    
    plt.rcParams.update({'font.size': 10})
    
    # Створюємо фігуру з прозорим фоном
    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    fig.patch.set_alpha(0.0) # Прозорий фон фігури
    ax.patch.set_alpha(0.0)  # Прозорий фон осей

    # Бар-чарт кольору "Solar Ninja Orange" (#FF4B4B - стандартний Streamlit червоний, або помаранчевий #FFA500)
    bars = ax.bar(monthly_df["Month"], monthly_df["Energy (kWh)"], color="#FF8C00", zorder=3)
    
    # Налаштування осей
    ax.set_title(f"Monthly Energy Output (Tilt = {user_tilt:.1f}°)", color="gray", pad=15, fontweight='bold')
    ax.set_xlabel("")
    ax.set_ylabel("Energy (kWh)", color="gray")
    
    # Кольори тексту осей
    ax.tick_params(axis='x', colors='gray', rotation=45)
    ax.tick_params(axis='y', colors='gray')
    
    # Сітка тільки по Y
    ax.grid(axis='y', linestyle='--', alpha=0.3, zorder=0, color='gray')
    
    # Прибираємо рамки зверху і справа (clean aesthetic)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('gray')
    ax.spines['bottom'].set_color('gray')

    plt.tight_layout()

    # Зберігаємо графік у буфер
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='png', dpi=150, transparent=False) # transparent=False для PDF, щоб не було чорним
    img_buffer.seek(0)

    # ------------------------------------------------------------
    # 8. Generate Professional PDF using PLATYPUS
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
        'CustomTitle', 
        parent=styles['Heading1'], 
        alignment=1, # Center
        spaceAfter=20,
        fontSize=18
    )
    normal_style = styles['Normal']

    story = []

    story.append(Paragraph("Solar Ninja — Energy Generation Report", title_style))
    story.append(Spacer(1, 12))

    summary_data = [
        ["Parameter", "Value"],
        ["Location (Lat, Lon)", f"{latitude:.4f}, {longitude:.4f}"],
        ["System Power", f"{system_power_kw:.2f} kW"],
        ["User Tilt", f"{user_tilt:.1f}°"],
        ["Optimal Annual Tilt", f"{annual_optimal_tilt}°"],
        ["Total Annual Energy", f"{annual_energy:,.0f} kWh"]
    ]

    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 24))

    rl_image = PDFImage(img_buffer, width=450, height=250) 
    story.append(Paragraph("Monthly Energy Production Chart:", styles['Heading2']))
    story.append(Spacer(1, 10))
    story.append(rl_image)
    story.append(Spacer(1, 24))

    story.append(Paragraph("Monthly Breakdown:", styles['Heading2']))
    story.append(Spacer(1, 10))

    table_data = [["Month", "Energy (kWh)"]]
    for idx, row in monthly_df.iterrows():
        table_data.append([row['Month'], f"{int(row['Energy (kWh)'])}"]) 

    main_table = Table(table_data, colWidths=[150, 150])
    main_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))

    story.append(main_table)

    doc.build(story)
    pdf_buffer.seek(0)

    return {
        "monthly_df": monthly_df,
        "monthly_best": monthly_best.reset_index(drop=True),
        "annual_energy": annual_energy,
        "annual_optimal_tilt": annual_optimal_tilt,
        "fig": fig,
        "pdf": pdf_buffer
    }
