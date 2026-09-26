"""
car_lon_g_curve.py — whole-car longitudinal G vs slip ratio, from carG.m.

Python port of the "car longitudinal g vs slip ratio" curve in carG.m:
MF6.1 pure longitudinal force (zero camber, nominal pressure, no aero),
longitudinal load transfer solved at every point. Braking (kappa < 0) uses
all four wheels at that slip ratio; driving (kappa > 0) the driven wheels only.

The raw curve is then fitted to the two anchor points
    slip ratio = 0   -> lon = 0 g
    slip ratio = 0.4 -> lon = 1.4 g
by removing each branch's value at kappa = 0 (braking and driving use a
different number of wheels, so each has its own small offset) and scaling
the whole curve so kappa = 0.4 gives exactly 1.4 g.
"""

from __future__ import annotations

import numpy as np

from car_lat_g_curve import CG_HEIGHT_M, FRONT_FRAC, G, MASS_KG, TIR_PATH, _flat_params
from car_data import CarData

WHEELBASE_M = CarData.WHEELBASE_MM / 1000.0
DRIVEN = "RWD"          # 'RWD' or 'AWD', as in carG.m

# Fit anchor: slip ratio -> longitudinal G
FIT_SLIP_RATIO = 0.4
FIT_LON_G = 1.4


def mf61_fx(p: dict[str, float], fz: float, kappa: float) -> float:
    """MF6.1 pure longitudinal force (N), zero camber, nominal pressure (mf61 'Fx' in carG.m)."""
    q = p.get
    eps = 1e-6
    fz0 = q("LFZO", 1.0) * q("FNOMIN", 1000.0)
    dfz = (fz - fz0) / fz0
    lmux = q("LMUX", 1.0)
    lmux_p = 10 * lmux / (1 + 9 * lmux)

    shx = (q("PHX1", 0.0) + q("PHX2", 0.0) * dfz) * q("LHX", 1.0)
    kx = kappa + shx
    cx = q("PCX1", 1.6) * q("LCX", 1.0)
    dx = (q("PDX1", 1.0) + q("PDX2", 0.0) * dfz) * lmux * fz
    kxk = fz * (q("PKX1", 20.0) + q("PKX2", 0.0) * dfz) * np.exp(q("PKX3", 0.0) * dfz) * q("LKX", 1.0)
    ex = min((q("PEX1", 0.0) + q("PEX2", 0.0) * dfz + q("PEX3", 0.0) * dfz**2)
             * (1 - q("PEX4", 0.0) * np.sign(kx)) * q("LEX", 1.0), 1.0)
    bx = kxk / (cx * dx + eps)
    svx = fz * (q("PVX1", 0.0) + q("PVX2", 0.0) * dfz) * q("LVX", 1.0) * lmux_p
    return float(dx * np.sin(cx * np.arctan(bx * kx - ex * (bx * kx - np.arctan(bx * kx)))) + svx)


def raw_car_lon_g(p: dict[str, float], kappa: float, braking: bool | None = None) -> float:
    """Car longitudinal G at one slip ratio, load transfer iterated (+ax loads the rear)."""
    w = MASS_KG * G
    wf = w * FRONT_FRAC
    wr = w - wf
    if braking is None:
        braking = kappa < 0
    front_driven = braking or DRIVEN.upper() == "AWD"
    ax = 0.0
    for _ in range(40):
        df = w * ax * CG_HEIGHT_M / WHEELBASE_M
        ff = max((wf - df) / 2, 0.0)
        fr = max((wr + df) / 2, 0.0)
        fx = 2 * mf61_fx(p, fr, kappa) if fr > 0 else 0.0
        if front_driven and ff > 0:
            fx += 2 * mf61_fx(p, ff, kappa)
        ax_new = fx / w
        if abs(ax_new - ax) < 1e-6:
            return ax_new
        ax = ax_new
    return ax


class LonGCurve:
    """Fitted longitudinal G vs slip ratio curve."""

    def __init__(self, tir_path=TIR_PATH):
        self._p = _flat_params(tir_path)
        self._off_brake = raw_car_lon_g(self._p, 0.0, braking=True)
        self._off_drive = raw_car_lon_g(self._p, 0.0, braking=False)
        self.scale = FIT_LON_G / self._shifted(FIT_SLIP_RATIO)

    def _shifted(self, kappa: float) -> float:
        braking = kappa < 0
        offset = self._off_brake if braking else self._off_drive
        return raw_car_lon_g(self._p, kappa, braking) - offset

    def lon_g_from_slip_ratio(self, kappa):
        k = np.atleast_1d(np.asarray(kappa, dtype=float))
        return np.array([self.scale * self._shifted(x) for x in k])

    def build_inverse(self, kappa_max: float = 0.5, step: float = 0.001) -> None:
        """Tabulate the curve so slip_ratio_from_lon_g() can invert it."""
        k = np.arange(-kappa_max, kappa_max + step / 2, step)
        g = self.lon_g_from_slip_ratio(k)
        i_brk = int(np.argmin(g))          # braking peak (most negative g)
        i_drv = int(np.argmax(g))          # driving peak
        self.peak_brake = (float(k[i_brk]), float(g[i_brk]))
        self.peak_drive = (float(k[i_drv]), float(g[i_drv]))
        # rising branches between the two peaks, split at kappa = 0
        zero = int(np.argmin(np.abs(k)))
        self._brk_k, self._brk_g = k[i_brk:zero + 1], g[i_brk:zero + 1]
        self._drv_k, self._drv_g = k[zero:i_drv + 1], g[zero:i_drv + 1]

    def slip_ratio_from_lon_g(self, lon_g, saturate: bool = False):
        """Slip ratio for each curve G (+ = driving); beyond either peak, NaN (or the peak slip ratio if saturate)."""
        if not hasattr(self, "_drv_k"):
            self.build_inverse()
        g = np.asarray(lon_g, dtype=float)
        drv = np.interp(g, self._drv_g, self._drv_k)
        brk = np.interp(g, self._brk_g, self._brk_k)
        out = np.where(g >= 0, drv, brk)
        if saturate:
            return out                        # np.interp holds the end value past the peak
        in_range = (g <= self.peak_drive[1]) & (g >= self.peak_brake[1])
        return np.where(in_range, out, np.nan)
