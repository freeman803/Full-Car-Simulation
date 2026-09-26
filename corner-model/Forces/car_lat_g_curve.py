"""
car_lat_g_curve.py — whole-car lateral G vs slip angle, from carG.m.

Python port of the "car lateral g vs slip angle" curve in carG.m:
MF6.1 pure lateral force (zero camber, nominal pressure, no aero), the same
slip angle on all four tyres, and load transfer solved at every point.

The raw curve is then fitted to the two anchor points
    slip angle = 0 deg  -> lat = 0 g
    slip angle = 10 deg -> lat = 1.8 g
by taking its odd part (so 0 -> 0 and the curve is symmetric) and scaling
it so 10 deg gives exactly 1.8 g.

slip_angle_from_lat_g() inverts that curve on its rising branch (0 deg to
peak). Lateral G beyond the curve's peak has no slip angle and returns NaN,
or the peak's slip angle with saturate=True.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from tire_model import PacejkaTireModel

TIR_PATH = Path(__file__).resolve().parent / "R20 7.5x10_NEW.TIR"

# Car settings, as in carG.m
MASS_KG = 295.0
CG_HEIGHT_M = 0.313
TRACK_M = 1.219
FRONT_FRAC = 0.50
LLTD_FRONT = 0.50
G = 9.81

# Fit anchor: slip angle (deg) -> lateral G
FIT_SLIP_DEG = 10.0
FIT_LAT_G = 1.8


def _flat_params(tir_path: Path) -> dict[str, float]:
    tyre = PacejkaTireModel.from_tir(tir_path)
    return {k: v for section in tyre.coefficients.values() for k, v in section.items() if isinstance(v, float)}


def mf61_fy(p: dict[str, float], fz: float, alpha_rad: float) -> float:
    """MF6.1 pure lateral force (N), zero camber, nominal pressure (lateral() in carG.m)."""
    q = p.get
    eps = 1e-6
    fz0 = q("LFZO", 1.0) * q("FNOMIN", 1000.0)
    dfz = (fz - fz0) / fz0
    lmuy = q("LMUY", 1.0)
    lmuy_p = 10 * lmuy / (1 + 9 * lmuy)

    kya = (q("PKY1", -20.0) * fz0
           * math.sin(q("PKY4", 2.0) * math.atan((fz / fz0) / q("PKY2", 1.0)))
           * q("LKY", 1.0))
    svy = fz * (q("PVY1", 0.0) + q("PVY2", 0.0) * dfz) * q("LVY", 1.0) * lmuy_p
    shy = (q("PHY1", 0.0) + q("PHY2", 0.0) * dfz) * q("LHY", 1.0)
    ay = math.tan(alpha_rad) + shy
    cy = q("PCY1", 1.3) * q("LCY", 1.0)
    dy = (q("PDY1", 1.0) + q("PDY2", 0.0) * dfz) * lmuy * fz
    ey = min((q("PEY1", 0.0) + q("PEY2", 0.0) * dfz) * (1 - q("PEY3", 0.0) * np.sign(ay)) * q("LEY", 1.0), 1.0)
    by = kya / (cy * dy + eps)
    return dy * math.sin(cy * math.atan(by * ay - ey * (by * ay - math.atan(by * ay)))) + svy


def corner_loads_lat(ay_g: float) -> list[float]:
    """[front outer, front inner, rear outer, rear inner] vertical loads (N)."""
    w = MASS_KG * G
    wf = w * FRONT_FRAC
    wr = w - wf
    df = w * ay_g * CG_HEIGHT_M / TRACK_M
    dff = min(df * LLTD_FRONT, wf / 2)
    dfr = min(df - dff, wr / 2)
    dff = min(df - dfr, wf / 2)
    return [wf / 2 + dff, wf / 2 - dff, wr / 2 + dfr, wr / 2 - dfr]


def raw_car_lat_g(p: dict[str, float], alpha_deg: float) -> float:
    """Car lateral G at one slip angle (all four tyres), load transfer iterated."""
    w = MASS_KG * G
    alpha = math.radians(alpha_deg)
    ay = 0.0
    for _ in range(40):
        fy = sum(mf61_fy(p, fz, alpha) for fz in corner_loads_lat(abs(ay)) if fz > 0)
        ay_new = fy / w
        if abs(ay_new - ay) < 1e-6:
            return ay_new
        ay = ay_new
    return ay


def _odd_lat_g(p: dict[str, float], alpha_deg: float) -> float:
    # .tir axis system gives negative Fy for positive slip; flip so +slip -> +g
    return (raw_car_lat_g(p, -alpha_deg) - raw_car_lat_g(p, alpha_deg)) / 2


class LatGCurve:
    """Fitted lateral G vs slip angle curve, with its inverse."""

    def __init__(self, tir_path: Path = TIR_PATH, max_deg: float = 20.0, step_deg: float = 0.05):
        p = _flat_params(tir_path)
        self.scale = FIT_LAT_G / _odd_lat_g(p, FIT_SLIP_DEG)
        self.slip_deg = np.arange(0.0, max_deg + step_deg, step_deg)
        self.lat_g = np.array([self.scale * _odd_lat_g(p, a) for a in self.slip_deg])
        peak = int(np.argmax(self.lat_g))
        self.peak_slip_deg = float(self.slip_deg[peak])
        self.peak_lat_g = float(self.lat_g[peak])
        self._rise_slip = self.slip_deg[: peak + 1]
        self._rise_lat = self.lat_g[: peak + 1]

    def lat_g_from_slip(self, slip_deg):
        s = np.asarray(slip_deg, dtype=float)
        return np.sign(s) * np.interp(np.abs(s), self.slip_deg, self.lat_g)

    def slip_from_lat_g(self, lat_g, saturate: bool = False):
        """Slip angle (deg) for each lateral G; beyond the curve's peak, NaN (or the peak slip if saturate)."""
        g = np.asarray(lat_g, dtype=float)
        mag = np.abs(g)
        slip = np.interp(mag, self._rise_lat, self._rise_slip)
        if saturate:
            return np.sign(g) * slip          # np.interp holds the end value past the peak
        return np.where(mag <= self.peak_lat_g, np.sign(g) * slip, np.nan)
