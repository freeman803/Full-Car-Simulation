"""
compare_strain_gauge.py — compare logged linkage strain gauge force against the model.

Reads a logged CSV (e.g. axial_force_1.csv) containing the measured axial force
plus longitudinal/lateral acceleration (G), runs every sample through the
linkage force balance, and compares the predicted force in each of the six
linkages against the measured one.

Usage (from the repo root):
    uv run corner-model/Forces/compare_strain_gauge.py
    uv run corner-model/Forces/compare_strain_gauge.py path/to/log.csv --axle front --linkage pushrod

Since the tire slip state isn't logged, the contact-patch forces are estimated
from the measured G's instead of the Pacejka model:
    Fz = load-transfer wheel load (wheel_loads.py)
    Fx = -long_g * Fz   (positive long G = braking, ground pushes the tire rearward)
    Fy = -lat_g  * Fz   (positive lat G = this is the outside wheel, ground pushes it inboard)
i.e. every tire is assumed to use the same fraction of its grip. Tire moments
are ignored.
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
from Forces.linkage_forces import LINKAGE_NAMES, build_equilibrium_matrix
from Forces.wheel_loads import calculate_total_wheel_load
from Forces.visualize_linkage_forces import DISPLAY_NAMES

RESULTS_DIR = _ROOT / "results"
DEFAULT_CSV = Path(__file__).resolve().parent / "axial_force_1.csv"


def load_log(
    csv_path: Path,
    force_column: str,
    max_g: float,
    median_window: int,
    sample_rate_hz: float | None,
    cutoff_hz: float,
) -> pd.DataFrame:
    """Load the log, drop rows with no force reading, and clean up the G channels."""
    df = pd.read_csv(csv_path)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df.dropna(subset=[force_column, "Lon", "Lat"]).reset_index(drop=True)

    for col in ("Lon", "Lat"):
        df[f"{col}_clean"] = clean_g(df[col], max_g, median_window, sample_rate_hz, cutoff_hz)

    return df


def clean_g(
    g: pd.Series,
    max_g: float,
    median_window: int,
    sample_rate_hz: float | None = None,
    cutoff_hz: float = 2.5,
) -> pd.Series:
    """
    The accelerometer channels have large single-sample spikes (±15 g): clip
    them, then median-filter to remove what's left.
    """
    g = g.clip(-max_g, max_g)
    if median_window > 1:
        g = g.rolling(median_window, center=True, min_periods=1).median()
    if sample_rate_hz is not None:
        # Match the low-pass already applied to the measured force channel.
        from scipy.signal import butter, filtfilt

        b, a = butter(2, cutoff_hz / (sample_rate_hz / 2.0))
        g = pd.Series(filtfilt(b, a, g.to_numpy()), index=g.index)
    return g


def predict_linkage_forces(long_g: np.ndarray, lat_g: np.ndarray, axle: str) -> np.ndarray:
    """Return an (n_samples, 6) array of linkage forces (N, +tension), columns in LINKAGE_NAMES order."""
    fz = np.array([
        calculate_total_wheel_load(lateral_g=lat, long_g=lon, axle=axle)
        for lon, lat in zip(long_g, lat_g)
    ])
    fz = np.clip(fz, 0.0, None)  # wheel lift: tire can't pull the car down

    tire_force = np.column_stack([-long_g * fz, -lat_g * fz, fz])
    tire_moment = np.zeros_like(tire_force)
    b = np.hstack([tire_force, tire_moment]).T  # (6, n)

    A = build_equilibrium_matrix(axle)
    return np.linalg.solve(A, b).T


def fit_stats(measured: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    corr = float(np.corrcoef(measured, predicted)[0, 1])
    return {
        "corr": corr,
        "mean_meas": float(measured.mean()),
        "mean_pred": float(predicted.mean()),
        "rms_err": float(np.sqrt(np.mean((measured - predicted) ** 2))),
        # RMS error after removing the mean offset (strain gauge zero is arbitrary)
        "rms_err_zeroed": float(np.std((measured - measured.mean()) - (predicted - predicted.mean()))),
    }


def plot_comparison(
    df: pd.DataFrame,
    measured: np.ndarray,
    predicted: np.ndarray,
    linkage: str,
    axle: str,
    stats: dict[str, float],
    sample_rate_hz: float | None,
) -> plt.Figure:
    if sample_rate_hz is not None:
        x = np.arange(len(df)) / sample_rate_hz
        x_label = "Time (s)"
    else:
        x = np.arange(len(df))
        x_label = "Sample"

    fig, (ax_ts, ax_sc) = plt.subplots(
        2, 1, figsize=(12, 9), gridspec_kw={"height_ratios": [1.3, 1]}
    )
    name = DISPLAY_NAMES[linkage]

    ax_ts.plot(x, measured, color=GREY, lw=0.8, label="Measured (strain gauge)")
    ax_ts.plot(x, predicted, color=ACCENT, lw=0.8, label=f"Model — {name}")
    ax_ts.axhline(0.0, color="black", lw=0.6)
    ax_ts.set_xlabel(x_label)
    ax_ts.set_ylabel("Axial force (N)  [+ tension / − compression]")
    ax_ts.set_title(f"{axle.capitalize()} {name}: measured vs model   (r = {stats['corr']:.2f})")
    ax_ts.legend(loc="upper right")

    ax_sc.scatter(predicted, measured, s=2, alpha=0.25, color=ACCENT, edgecolors="none")
    lo = min(predicted.min(), measured.min())
    hi = max(predicted.max(), measured.max())
    ax_sc.plot([lo, hi], [lo, hi], color=GREY, lw=1, ls="--", label="Perfect agreement")
    ax_sc.set_xlabel("Model force (N)")
    ax_sc.set_ylabel("Measured force (N)")
    ax_sc.legend(loc="upper left")

    plt.tight_layout()
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", nargs="?", type=Path, default=DEFAULT_CSV, help="Logged CSV file")
    parser.add_argument("--axle", choices=["front", "rear"], default="front")
    parser.add_argument(
        "--linkage", choices=["auto", *LINKAGE_NAMES], default="auto",
        help="Linkage the gauge is on (default: the best-correlated one)",
    )
    parser.add_argument("--force-column", default="force_2p5Hz_N", help="Measured force column (N)")
    parser.add_argument("--flip-lat", action="store_true", help="Flip Lat sign (use if the gauge is on the other side of the car)")
    parser.add_argument("--flip-lon", action="store_true", help="Flip Lon sign (if the logger reports braking as negative)")
    parser.add_argument("--max-g", type=float, default=3.0, help="Clip G channels to ±this (removes spikes)")
    parser.add_argument("--median-window", type=int, default=101, help="Median filter width (samples) on G channels")
    parser.add_argument("--sample-rate", type=float, default=None, help="Log sample rate (Hz); enables time axis and low-pass on G's")
    parser.add_argument("--cutoff", type=float, default=2.5, help="Low-pass cutoff (Hz) for G's, used with --sample-rate")
    parser.add_argument("--no-show", action="store_true", help="Save the plot without opening a window")
    args = parser.parse_args()

    df = load_log(args.csv, args.force_column, args.max_g, args.median_window, args.sample_rate, args.cutoff)
    long_g = df["Lon_clean"].to_numpy() * (-1.0 if args.flip_lon else 1.0)
    lat_g = df["Lat_clean"].to_numpy() * (-1.0 if args.flip_lat else 1.0)
    measured = df[args.force_column].to_numpy()

    predicted_all = predict_linkage_forces(long_g, lat_g, args.axle)
    all_stats = {name: fit_stats(measured, predicted_all[:, i]) for i, name in enumerate(LINKAGE_NAMES)}

    print(f"{args.csv.name}: {len(df)} samples, {args.axle} axle")
    print(f"Measured '{args.force_column}': mean {measured.mean():.1f} N, range {measured.min():.1f} to {measured.max():.1f} N\n")
    print(f"{'Linkage':<22}{'corr':>7}{'mean model (N)':>16}{'RMS err (N)':>13}{'RMS err, zeroed':>17}")
    for name, s in all_stats.items():
        print(f"{DISPLAY_NAMES[name]:<22}{s['corr']:>7.2f}{s['mean_pred']:>16.1f}{s['rms_err']:>13.1f}{s['rms_err_zeroed']:>17.1f}")

    linkage = args.linkage
    if linkage == "auto":
        linkage = max(all_stats, key=lambda n: all_stats[n]["corr"])
        print(f"\nBest-correlated linkage: {DISPLAY_NAMES[linkage]} (pass --linkage to choose)")

    idx = LINKAGE_NAMES.index(linkage)
    RESULTS_DIR.mkdir(exist_ok=True)

    out_csv = RESULTS_DIR / f"{args.csv.stem}_model_comparison.csv"
    out_df = pd.DataFrame({
        "measured_N": measured,
        "long_g_clean": long_g,
        "lat_g_clean": lat_g,
        **{f"model_{name}_N": predicted_all[:, i] for i, name in enumerate(LINKAGE_NAMES)},
    })
    out_df.to_csv(out_csv, index=False)
    print(f"Saved -> {out_csv}")

    apply_style()
    fig = plot_comparison(df, measured, predicted_all[:, idx], linkage, args.axle, all_stats[linkage], args.sample_rate)
    out_png = RESULTS_DIR / f"{args.csv.stem}_{args.axle}_{linkage}.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"Saved -> {out_png}")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
