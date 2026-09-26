"""
plot_percent_error.py — graph the model vs strain gauge comparison.

Reads the CSV made by run_linkage_from_slip_csv.py and plots, against time:
    top:    measured strain gauge force and the model force in the gauged linkage
    bottom: percent error of the model, with a ±10% band

Usage (from the repo root):
    uv run corner-model/Forces/plot_percent_error.py
    uv run corner-model/Forces/plot_percent_error.py --sample-rate 100 --error-limit 150
    uv run corner-model/Forces/plot_percent_error.py path/to/results.csv --flip-sign
    uv run corner-model/Forces/plot_percent_error.py path/to/results.csv --flip-sign --align-measured
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kinematics.plots import apply_style, ACCENT, GREY

RESULTS_DIR = _ROOT / "results"
DEFAULT_CSV = RESULTS_DIR / "axial_force_1_slip_angle_front_linkage_forces.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", nargs="?", type=Path, default=DEFAULT_CSV, help="Output of run_linkage_from_slip_csv.py")
    parser.add_argument("--linkage", default="pushrod", help="Model linkage column to plot against the gauge")
    parser.add_argument("--sample-rate", type=float, default=100.0, help="Log sample rate (Hz) for the time axis, if the CSV has no time column")
    parser.add_argument("--error-limit", type=float, default=100.0, help="Percent error axis limit (±); spikes beyond it are cut off")
    parser.add_argument("--flip-sign", action="store_true",
                        help="Negate the model force before comparing (gauge reads compression as +)")
    parser.add_argument("--align-measured", action="store_true",
                        help="Shift the gauge by the median (model - measured) so the two line up (zero-offset correction)")
    parser.add_argument("--no-show", action="store_true", help="Save the plot without opening a window")
    args = parser.parse_args()

    df = pd.read_csv(args.csv).dropna(subset=["measured_N", "percent_error"])
    if "time" in df:  # Influx runs carry real timestamps (rows may have been filtered out)
        time = pd.to_datetime(df["time"])
        t = (time - time.iloc[0]).dt.total_seconds()
    else:
        t = df["row"] / args.sample_rate
    measured = df["measured_N"]
    model = df[f"{args.linkage}_N"]
    err = df["percent_error"]
    if args.flip_sign:
        model = -model
        err = (model - measured) / measured.abs() * 100.0
    offset = 0.0
    if args.align_measured:
        offset = float((model - measured).median())
        measured = measured + offset
        err = (model - measured) / measured.abs() * 100.0
        print(f"Shifted measured by {offset:+.1f} N")
    name = args.linkage.replace("_", " ")

    apply_style()
    fig, (ax_f, ax_e) = plt.subplots(2, 1, figsize=(13, 8), sharex=True, gridspec_kw={"height_ratios": [1.2, 1]})

    # Force: both series on one axis (same units). Clip the view to the bulk of
    # the data so the accelerometer spikes don't flatten everything else.
    ax_f.plot(t, model, color=ACCENT, lw=0.8, label=f"Model {name}" + (" (sign flipped)" if args.flip_sign else ""))
    ax_f.plot(t, measured, color=GREY, lw=1.2, label="Measured (strain gauge)" + (f" {offset:+.0f} N" if args.align_measured else ""))
    both = pd.concat([measured, model])
    lo, hi = both.quantile(0.002), both.quantile(0.998)
    pad = 0.1 * (hi - lo)
    ax_f.set_ylim(lo - pad, hi + pad)
    ax_f.set_ylabel("Axial force (N)  [+ compression]" if args.flip_sign else "Axial force (N)  [− compression]")
    ax_f.set_title(f"Front {name}: model vs strain gauge")
    ax_f.legend(loc="lower right")

    # Percent error with the ±10% band.
    ax_e.axhspan(-10, 10, color=GREY, alpha=0.15, lw=0, label="±10%")
    ax_e.axhline(0, color=GREY, lw=0.8)
    ax_e.plot(t, err, color=ACCENT, lw=0.8, label="Percent error")
    ax_e.set_ylim(-args.error_limit, args.error_limit)
    ax_e.set_ylabel("Percent error (%)")
    ax_e.set_xlabel("Time (s)")
    n_cut = int((err.abs() > args.error_limit).sum())
    cut_note = f", {n_cut} points beyond ±{args.error_limit:.0f}% cut off" if n_cut else ""
    ax_e.set_title(
        f"(model − measured) / |measured|:  mean {err.mean():+.1f}%, "
        f"mean |error| {err.abs().mean():.1f}%, {(err.abs() <= 10).mean() * 100:.0f}% of points within ±10%{cut_note}",
        fontsize=10,
    )
    ax_e.legend(loc="lower right")

    plt.tight_layout()
    flip_suffix = "_flipped" if args.flip_sign else ""
    align_suffix = "_aligned" if args.align_measured else ""
    out_png = RESULTS_DIR / f"{args.csv.stem}_{args.linkage}{flip_suffix}{align_suffix}_percent_error.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"Saved -> {out_png}")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
