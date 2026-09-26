"""
plot_lon_vs_slip_ratio.py — graph whole-car longitudinal G against slip ratio.

Plots the fitted curve from car_lon_g_curve.py (carG.m model, fitted so
slip ratio 0 -> 0 g and 0.4 -> 1.4 g). Negative slip ratio is braking on all
four wheels; positive is driving on the driven wheels only.

Usage (from the repo root):
    uv run corner-model/Forces/plot_lon_vs_slip_ratio.py
    uv run corner-model/Forces/plot_lon_vs_slip_ratio.py --kappa-max 0.6 --no-show
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kinematics.plots import apply_style, ACCENT, GREY

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from car_lon_g_curve import DRIVEN, FIT_LON_G, FIT_SLIP_RATIO, LonGCurve

RESULTS_DIR = _ROOT / "results"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--kappa-max", type=float, default=0.5, help="Plot slip ratio from -this to +this")
    parser.add_argument("--no-show", action="store_true", help="Save the plot without opening a window")
    args = parser.parse_args()

    curve = LonGCurve()
    kappa = np.linspace(-args.kappa_max, args.kappa_max, 801)
    lon_g = curve.lon_g_from_slip_ratio(kappa)

    apply_style()
    fig, ax = plt.subplots(figsize=(8, 6))
    brk, drv = kappa < 0, kappa >= 0
    ax.plot(kappa[brk], lon_g[brk], color=GREY, linewidth=1.6, label="Braking (4 wheels)")
    ax.plot(kappa[drv], lon_g[drv], color=ACCENT, linewidth=1.6, label=f"Driving ({DRIVEN})")
    ax.plot([0, FIT_SLIP_RATIO], [0, FIT_LON_G], "o", color=ACCENT, markersize=5)
    ax.annotate(f"fit: κ = {FIT_SLIP_RATIO:g} → {FIT_LON_G:g} g", (FIT_SLIP_RATIO, FIT_LON_G),
                textcoords="offset points", xytext=(0, -16), ha="center", color=ACCENT)
    for mask in (brk, drv):
        i = np.argmax(np.abs(lon_g[mask]))
        k, g = kappa[mask][i], lon_g[mask][i]
        ax.plot(k, g, "o", color=GREY, markersize=4)
        ax.annotate(f"peak {g:.2f} g @ κ = {k:.3f}", (k, g), textcoords="offset points",
                    xytext=(0, 8 if g > 0 else -16), ha="center", color=GREY)
    ax.axhline(0, linewidth=0.8, color=GREY)
    ax.axvline(0, linewidth=0.8, color=GREY)
    ax.set_xlabel("Slip ratio κ (-)")
    ax.set_ylabel("Longitudinal acceleration (g)")
    ax.set_title(f"Longitudinal G vs slip ratio (carG.m, scale {curve.scale:.3f})")
    ax.legend(loc="upper left")

    RESULTS_DIR.mkdir(exist_ok=True)
    out_png = RESULTS_DIR / "lon_g_vs_slip_ratio.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"Scale {curve.scale:.4f}; saved {out_png}")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
