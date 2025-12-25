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
        winter = [mon]()
