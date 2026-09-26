"""
plot_slip_vs_lat.py — graph lateral G against slip angle.

Reads the CSV made by lat_to_slip_angle.py (columns Lat_g, slip_angle_deg)
and scatters every logged sample, lateral G vs slip angle, over the fitted
model curve from car_lat_g_curve.py extended out to --curve-max degrees.

Usage (from the repo root):
    uv run corner-model/Forces/plot_slip_vs_lat.py
    uv run corner-model/Forces/plot_slip_vs_lat.py path/to/slip.csv --no-show
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kinematics.plots import apply_style, ACCENT, GREY

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from car_lat_g_curve import LatGCurve

RESULTS_DIR = _ROOT / "results"
DEFAULT_CSV = RESULTS_DIR / "influx.data (9)_slip_angle_max10deg.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", nargs="?", type=Path, default=DEFAULT_CSV, help="Output of lat_to_slip_angle.py")
    parser.add_argument("--curve-max", type=float, default=20.0, help="Extend the model curve to ± this slip angle (deg)")
    parser.add_argument("--no-show", action="store_true", help="Save the plot without opening a window")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)

    apply_style()
    fig, ax = plt.subplots(figsize=(8, 6))
    curve = LatGCurve(max_deg=args.curve_max)
    slip = np.linspace(-args.curve_max, args.curve_max, 801)
    ax.plot(slip, curve.lat_g_from_slip(slip), color=GREY, linewidth=1.4, label="Model curve (carG.m, fitted 10° → 1.8 g)")
    ax.scatter(df["slip_angle_deg"], df["Lat_g"], s=2, color=ACCENT, alpha=0.4, linewidths=0, label="Logged samples")
    ax.plot([curve.peak_slip_deg, -curve.peak_slip_deg], [curve.peak_lat_g, -curve.peak_lat_g], "o", color=GREY, markersize=4)
    ax.annotate(f"peak {curve.peak_lat_g:.3f} g @ {curve.peak_slip_deg:.1f}°", (curve.peak_slip_deg, curve.peak_lat_g),
                textcoords="offset points", xytext=(0, 8), ha="center", color=GREY)
    ax.legend(loc="upper left", markerscale=5)
    ax.set_xlabel("Slip angle (deg)")
    ax.set_ylabel("Lateral acceleration (g)")
    ax.set_title(f"Lateral G vs slip angle — {args.csv.stem}")
    ax.axhline(0, linewidth=0.8, color="#888888")
    ax.axvline(0, linewidth=0.8, color="#888888")

    out_png = args.csv.with_name(f"{args.csv.stem}_slip_vs_lat.png")
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"Saved {out_png}")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
