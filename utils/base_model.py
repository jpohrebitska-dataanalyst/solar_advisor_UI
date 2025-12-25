# utils/base_model.py

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pvlib.location import Location
from pvlib import irradiance


# -----------------------------
# Config
# -----------------------------
@dataclass
class ModelConfig:
    tz: str = "Europe/Kyiv"
    losses: float = 0.18          # 18% system losses (inverter, wiring, soiling etc.)
    tilt_step: int = 1            # degrees
    min_tilt: int = 0
    max_tilt: int = 90
    year: int = 2023              # non-leap year (8760 hours)
    freq: str = "1h"


# -----------------------------
# Core PV helpers (simple PVWatts-like approach)
# -----------------------------
def _make_times(cfg: ModelConfig) -> pd.DatetimeIndex:
    start = f"{cfg.year}-01-01 00:00"
    end = f"{cfg.year}-12-31 23:00"
    return pd.date_range(start=start, end=end, freq=cfg.freq, tz=cfg.tz)


def _clearsky_inputs(lat: float, lon: float, cfg: ModelConfig) -> Tuple[Location, pd.DatetimeIndex, pd.DataFrame, pd.DataFrame]:
    loc = Location(latitude=lat, longitude=lon, tz=cfg.tz)
    times = _make_times(cfg)
    solpos = loc.get_solarposition(times)
    cs = loc.get_clearsky(times, model="ineichen")  # ghi,dni,dhi
    return loc, times, solpos, cs


def _poa_global(tilt: float, azimuth: float, solpos: pd.DataFrame, cs: pd.DataFrame) -> pd.Series:
    # POA irradiance (W/m2)
    poa = irradiance.get_total_irradiance(
        surface_tilt=float(tilt),
        surface_azimuth=float(azimuth),
        solar_zenith=solpos["apparent_zenith"],
        solar_azimuth=solpos["azimuth"],
        dni=cs["dni"],
        ghi=cs["ghi"],
        dhi=cs["dhi"],
        model="isotropic",
    )
    # clip negative or NaN
    poa_global = poa["poa_global"].fillna(0).clip(lower=0)
    return poa_global


def _energy_kwh_from_poa(poa_global: pd.Series, system_power_kw: float, losses: float) -> pd.Series:
    """
    Simple PVWatts-style:
    P(kW) ~ system_power_kw * (POA/1000) * (1 - losses)
    E(kWh) for hourly data ~ P(kW)*1h
    """
    p_kw = float(system_power_kw) * (poa_global / 1000.0) * (1.0 - float(losses))
    p_kw = p_kw.fillna(0).clip(lower=0)
    # hourly -> kWh
    e_kwh = p_kw  # 1 hour step
    return e_kwh


def _monthly_sum(e_kwh: pd.Series) -> pd.Series:
    return e_kwh.resample("MS").sum()  # month start frequency


def _annual_sum(e_kwh: pd.Series) -> float:
    return float(e_kwh.sum())


def _optimize_tilt_for_period(
    solpos: pd.DataFrame,
    cs: pd.DataFrame,
    system_power_kw: float,
    azimuth: float,
    cfg: ModelConfig,
    mask: Optional[pd.Series] = None,
) -> Tuple[int, float]:
    """
    Optimize tilt by scanning [min_tilt..max_tilt] with step cfg.tilt_step.
    If mask is provided, optimize only for that subset of hours.
    Returns: (best_tilt_deg, best_energy_kwh)
    """
    best_tilt = cfg.min_tilt
    best_energy = -1.0

    tilts = range(cfg.min_tilt, cfg.max_tilt + 1, cfg.tilt_step)

    for t in tilts:
        poa = _poa_global(t, azimuth, solpos, cs)
        e = _energy_kwh_from_poa(poa, system_power_kw, cfg.losses)
        if mask is not None:
            e = e[mask]
        total = _annual_sum(e)
        if total > best_energy:
            best_energy = total
            best_tilt = int(t)

    return best_tilt, float(best_energy)


def _build_monthly_optimal_tilts(
    times: pd.DatetimeIndex,
    solpos: pd.DataFrame,
    cs: pd.DataFrame,
    system_power_kw: float,
    azimuth: float,
    cfg: ModelConfig,
) -> List[Optional[float]]:
    """
    Returns 12 values (Jan..Dec) of optimal tilt for each month.
    """
    monthly_tilts: List[Optional[float]] = []
    for month in range(1, 13):
        mask = (times.month == month)
        best_tilt, _ = _optimize_tilt_for_period(solpos, cs, system_power_kw, azimuth, cfg, mask=mask)
        monthly_tilts.append(float(best_tilt))
    return monthly_tilts


def _make_monthly_plot(monthly_your: pd.Series, monthly_opt: pd.Series):
    """
    Matplotlib figure similar to Lovable.
    """
    fig = plt.figure(figsize=(10.5, 3.6), dpi=160)
    ax = fig.add_subplot(111)

    months = monthly_your.index.strftime("%b")
    ax.plot(months, monthly_your.values, label="Your Generation", linewidth=2.4)
    ax.plot(months, monthly_opt.values, label="Optimal Generation", linewidth=2.4)

    ax.set_ylabel("kWh")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)

    fig.tight_layout()
    return fig


def _build_recommendations(
    your_tilt: float,
    optimal_tilt: float,
    azimuth: float,
    potential_pct: float,
    monthly_opt_tilt: List[Optional[float]],
    losses: float,
) -> List[str]:
    recs: List[str] = []

    recs.append(
        f"Your tilt angle is {int(round(your_tilt))}° and the annual optimal tilt for this location is {int(round(optimal_tilt))}° (azimuth {int(round(azimuth))}°)."
    )
    recs.append(
        f"Estimated potential change vs your current tilt: {potential_pct:+.1f}% (clearsky model, {int(round(losses*100))}% system losses)."
    )

    # seasonal suggestion
    try:
        # Jun-Aug
        summer = [monthly_opt_tilt[i] for i in [5, 6, 7] if monthly_opt_tilt[i] is not None]
        # Dec-Feb
        winter = [monthly_opt_tilt[i] for i in [11, 0, 1] if monthly_opt_tilt[i] is not None]
        if summer and winter:
            recs.append(
                f"For maximum efficiency, consider seasonal adjustment: summer ~{int(round(float(np.mean(summer))))}°, winter ~{int(round(float(np.mean(winter))))}°."
            )
    except Exception:
        pass

    if 90 <= azimuth <= 270:
        recs.append(f"South-facing orientation (azimuth {int(round(azimuth))}°) is usually optimal for the Northern Hemisphere.")
    else:
        recs.append("Consider orienting panels toward the south for higher annual yield (Northern Hemisphere).")

    recs.append("Regularly clean panels from dust and snow to maintain maximum efficiency.")
    return recs


def _build_pdf_bytes(
    title: str,
    lat: float,
    lon: float,
    system_power_kw: float,
    your_tilt: float,
    azimuth: float,
    optimal_tilt: float,
    your_annual: float,
    opt_annual: float,
    potential_pct: float,
    fig,
    recommendations: List[str],
) -> Optional[bytes]:
    """
    Optional PDF generation. If reportlab is not available, returns None.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
    except Exception:
        return None

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 50, title)

    c.setFont("Helvetica", 10)
    c.drawString(40, height - 70, f"Location: {lat:.4f}, {lon:.4f} | Power: {system_power_kw:.2f} kW")
    c.drawString(40, height - 85, f"Your tilt: {your_tilt:.0f}° | Azimuth: {azimuth:.0f}° | Optimal tilt: {optimal_tilt:.0f}°")

    # KPIs
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, height - 115, "Key results")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 132, f"Your annual generation: {your_annual:,.0f} kWh/year".replace(",", " "))
    c.drawString(40, height - 147, f"Optimal annual generation: {opt_annual:,.0f} kWh/year".replace(",", " "))
    c.drawString(40, height - 162, f"Potential: {potential_pct:+.1f}%")

    # Plot image
    img_buf = BytesIO()
    fig.savefig(img_buf, format="png", bbox_inches="tight")
    img_buf.seek(0)
    img = ImageReader(img_buf)

    # place chart
    chart_w = width - 80
    chart_h = 260
    c.drawImage(img, 40, height - 460, width=chart_w, height=chart_h, preserveAspectRatio=True, mask='auto')

    # Recommendations
    y = height - 500
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Recommendations")
    y -= 18
    c.setFont("Helvetica", 10)
    for r in recommendations[:6]:
        # simple wrap
        text = r.strip()
        while len(text) > 95:
            c.drawString(55, y, u"\u2022 " + text[:95])
            text = text[95:]
            y -= 14
        c.drawString(55, y, u"\u2022 " + text)
        y -= 16
        if y < 60:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)

    c.showPage()
    c.save()

    buf.seek(0)
    return buf.getvalue()


# -----------------------------
# Public API for Streamlit UI
# -----------------------------
def run_for_ui(
    lat: float,
    lon: float,
    system_power_kw: float,
    tilt_deg: float,
    azimuth_deg: float,
    cfg: Optional[ModelConfig] = None,
) -> Dict[str, Any]:
    """
    Main function called from app.py.

    Returns dict:
      - optimal_angle
      - your_generation
      - optimal_generation
      - potential_pct
      - monthly_df   (month, your, optimal)
      - monthly_opt_tilt (12 values)
      - recommendations (list)
      - monthly_fig (matplotlib fig)
      - pdf_bytes (bytes or None)
      - your_tilt
    """
    cfg = cfg or ModelConfig()

    # inputs guard
    lat = float(lat)
    lon = float(lon)
    system_power_kw = max(0.1, float(system_power_kw))
    tilt_deg = float(tilt_deg)
    azimuth_deg = float(azimuth_deg)

    loc, times, solpos, cs = _clearsky_inputs(lat, lon, cfg)

    # your tilt energy
    poa_your = _poa_global(tilt_deg, azimuth_deg, solpos, cs)
    e_your = _energy_kwh_from_poa(poa_your, system_power_kw, cfg.losses)

    # optimal annual tilt
    best_tilt, best_energy = _optimize_tilt_for_period(solpos, cs, system_power_kw, azimuth_deg, cfg, mask=None)

    poa_opt = _poa_global(best_tilt, azimuth_deg, solpos, cs)
    e_opt = _energy_kwh_from_poa(poa_opt, system_power_kw, cfg.losses)

    your_annual = _annual_sum(e_your)
    opt_annual = _annual_sum(e_opt)

    potential_pct = 0.0
    if your_annual > 0:
        potential_pct = (opt_annual / your_annual - 1.0) * 100.0

    # monthly series
    m_your = _monthly_sum(e_your)
    m_opt = _monthly_sum(e_opt)

    # ensure 12 months
    m_your = m_your.reindex(pd.date_range(m_your.index.min(), periods=12, freq="MS", tz=cfg.tz)).fillna(0)
    m_opt = m_opt.reindex(pd.date_range(m_opt.index.min(), periods=12, freq="MS", tz=cfg.tz)).fillna(0)

    # monthly optimal tilts
    monthly_opt_tilt = _build_monthly_optimal_tilts(times, solpos, cs, system_power_kw, azimuth_deg, cfg)

    # recommendations
    recs = _build_recommendations(
        your_tilt=tilt_deg,
        optimal_tilt=float(best_tilt),
        azimuth=azimuth_deg,
        potential_pct=float(potential_pct),
        monthly_opt_tilt=monthly_opt_tilt,
        losses=cfg.losses,
    )

    # chart
    fig = _make_monthly_plot(m_your, m_opt)

    # monthly df for fallback
    monthly_df = pd.DataFrame(
        {
            "month": m_your.index.month,
            "your": m_your.values,
            "optimal": m_opt.values,
        }
    )

    # pdf bytes (optional)
    pdf_bytes = _build_pdf_bytes(
        title="Solar Ninja — Report",
        lat=lat,
        lon=lon,
        system_power_kw=system_power_kw,
        your_tilt=tilt_deg,
        azimuth=azimuth_deg,
        optimal_tilt=float(best_tilt),
        your_annual=your_annual,
        opt_annual=opt_annual,
        potential_pct=float(potential_pct),
        fig=fig,
        recommendations=recs,
    )

    return {
        "optimal_angle": float(best_tilt),
        "your_tilt": float(tilt_deg),
        "your_generation": float(your_annual),
        "optimal_generation": float(opt_annual),
        "potential_pct": float(potential_pct),
        "monthly_df": monthly_df,
        "monthly_opt_tilt": monthly_opt_tilt,
        "recommendations": recs,
        "monthly_fig": fig,
        "pdf_bytes": pdf_bytes,
    }
