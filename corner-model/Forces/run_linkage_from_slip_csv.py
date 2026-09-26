"""
run_linkage_from_slip_csv.py — run the linkage force calculator over a slip-angle CSV.

Takes the lat G and slip angle columns from the CSV made by lat_to_slip_angle.py
(results/axial_force_1_slip_angle.csv by default), plus the Lon G column from
the original log (Forces/axial_force_1.csv, same rows in the same order), and
feeds every row through the same calculation as run_linkage_calculation.py,
for the front corner.

The log can also be an InfluxDB export (e.g. "influx.data (9).csv"). Then Lon G
(VCPDU_lon) is matched to each row by timestamp, and the measured force is the
pushrod load from the strain gauge (VCFRONT_shockpotVoltFR, calibrated as in
read_influx_csv.py) at the nearest timestamp.

The other calculator inputs aren't logged, so they're fixed for every row
(change them with the options below):
    slip ratio = 0, tire pressure = 11 psi
With --lon-g-per-slip-ratio K, slip ratio is instead worked out per row from
the linear relation Lon G = K * slip ratio (e.g. K = 3.3425).
With --lon-curve, slip ratio is instead read off the fitted carG.m curve in
car_lon_g_curve.py (0 -> 0 g, 0.4 -> 1.4 g). Positive Lon G is braking, as
in wheel_loads.py, so it maps to negative slip ratio (--lon-positive driving
flips that). Rows with Lon G beyond the curve's peaks are dropped, or with
--saturate get the peak's slip ratio (flagged in the lon_beyond_peak column).
--max-slip none turns off the slip angle filter.

The measured force rises at the start of the log, so rows before the top of
that rise are dropped (--start-row to override).

Only rows with |slip angle| <= 10 deg are used (--max-slip); the rest are
accelerometer spikes. --max-lon does the same for |Lon G| (off by default).

Each row also gets percent_error = (model - measured) / |measured| * 100, comparing
the strain gauge force (force_2p5Hz_N) to the model force in the gauged linkage
(pushrod by default, --linkage to change).

Usage (from the repo root):
    uv run corner-model/Forces/run_linkage_from_slip_csv.py
    uv run corner-model/Forces/run_linkage_from_slip_csv.py --slip-ratio 0.05 --pressure 12
    uv run corner-model/Forces/run_linkage_from_slip_csv.py "corner-model/results/influx.data (9)_slip_angle_max10deg.csv" --log-csv "corner-model/Forces/influx.data (9).csv"
    uv run corner-model/Forces/run_linkage_from_slip_csv.py "corner-model/results/influx.data (9)_slip_angle_max10deg.csv" --log-csv "corner-model/Forces/influx.data (9).csv" --lon-curve
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Forces.linkage_forces import LINKAGE_NAMES, calculate_linkage_forces
from Forces.read_influx_csv import N_OFFSET, N_PER_V, VOLTAGE_FIELD, read_column_g

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from car_lon_g_curve import LonGCurve

PSI_TO_PA = 6894.757293168
RESULTS_DIR = _ROOT / "results"
DEFAULT_CSV = RESULTS_DIR / "axial_force_1_slip_angle.csv"
DEFAULT_LOG_CSV = Path(__file__).resolve().parent / "axial_force_1.csv"
START_SEARCH_ROWS = 2000
# Max time gap when matching a strain gauge sample to an IMU sample
INFLUX_MATCH_TOLERANCE = pd.Timedelta("20ms")


def is_influx_export(csv_path: Path) -> bool:
    with open(csv_path) as f:
        return f.readline().startswith("#group")


def load_influx_log(csv_path: Path, slip: pd.DataFrame) -> pd.DataFrame:
    """Add Lon_g (same timestamp) and measured_N (nearest strain gauge sample) to slip-angle rows."""
    log = read_column_g(csv_path)
    lon = log[log["_field"] == "VCPDU_lon"][["_time", "_value"]].rename(columns={"_time": "time", "_value": "Lon_g"})
    gauge = log[log["_field"] == VOLTAGE_FIELD][["_time", "_value"]].rename(columns={"_time": "time"})
    gauge["measured_N"] = N_PER_V * gauge.pop("_value") + N_OFFSET

    slip = slip.copy()
    slip["time"] = pd.to_datetime(slip["time"], utc=True)
    df = slip.merge(lon, on="time", how="left")
    if df["Lon_g"].isna().any():
        raise ValueError(f"{df['Lon_g'].isna().sum()} rows have no VCPDU_lon sample at the same timestamp")
    df = pd.merge_asof(df.sort_values("time"), gauge.sort_values("time"), on="time",
                       direction="nearest", tolerance=INFLUX_MATCH_TOLERANCE)
    return df[["time", "Lon_g", "Lat_g", "slip_angle_deg", "measured_N"]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", nargs="?", type=Path, default=DEFAULT_CSV, help="CSV with Lat_g and slip_angle_deg columns")
    parser.add_argument("--log-csv", type=Path, default=DEFAULT_LOG_CSV, help="Original log with the Lon (G) column")
    parser.add_argument("--measured-column", default="force_2p5Hz_N", help="Strain gauge force column in the log (N)")
    parser.add_argument("--linkage", choices=LINKAGE_NAMES, default="pushrod", help="Linkage the strain gauge is on")
    parser.add_argument("--start-row", type=int, default=None, help="First row to use (default: top of the initial rise in the measured force)")
    parser.add_argument("--max-slip", type=lambda v: None if v.lower() == "none" else float(v), default=10.0,
                        help="Only use rows with |slip angle| <= this (deg); 'none' keeps every row")
    parser.add_argument("--max-lon", type=float, default=None, help="Only use rows with |Lon G| <= this (g)")
    parser.add_argument("--slip-ratio", type=float, default=0.0, help="Slip ratio for every row")
    parser.add_argument("--lon-g-per-slip-ratio", type=float, default=None,
                        help="Per-row slip ratio = Lon G / this (overrides --slip-ratio)")
    parser.add_argument("--lon-curve", action="store_true",
                        help="Per-row slip ratio from the fitted carG.m Lon G curve (overrides the other slip ratio options)")
    parser.add_argument("--lon-positive", choices=["braking", "driving"], default="braking",
                        help="What positive logged Lon G means, for --lon-curve (default braking, as in wheel_loads.py)")
    parser.add_argument("--saturate", action="store_true",
                        help="With --lon-curve, give Lon G beyond the curve's peaks the peak slip ratio instead of dropping the row")
    parser.add_argument("--pressure", type=float, default=11.0, help="Tire pressure (psi) for every row")
    args = parser.parse_args()

    influx = is_influx_export(args.log_csv)
    if influx:
        df = load_influx_log(args.log_csv, pd.read_csv(args.csv, usecols=["time", "Lat_g", "slip_angle_deg"]))
        measured_label = f"pushrod load from {VOLTAGE_FIELD}"
    else:
        df = pd.read_csv(args.csv, usecols=["Lat_g", "slip_angle_deg"])
        log = pd.read_csv(args.log_csv, usecols=["Lon", args.measured_column])
        if len(log) != len(df):
            raise ValueError(f"{args.log_csv.name} has {len(log)} rows but {args.csv.name} has {len(df)}; they must line up row for row")
        df.insert(0, "Lon_g", log["Lon"])
        df["measured_N"] = log[args.measured_column]
        measured_label = args.measured_column
    df.insert(0, "row", df.index)
    n_total = len(df)

    # The measured force in the plain log rises at the start (filter start-up);
    # start at the top of that rise, i.e. the peak within the first START_SEARCH_ROWS.
    start_row = args.start_row
    if start_row is None:
        start_row = 0 if influx else int(df["measured_N"].iloc[:START_SEARCH_ROWS].idxmax())
    df = df.iloc[start_row:]

    if args.max_slip is not None:
        df = df[df["slip_angle_deg"].abs() <= args.max_slip]
    if args.max_lon is not None:
        df = df[df["Lon_g"].abs() <= args.max_lon]
    df = df.reset_index(drop=True)
    if args.lon_curve:
        curve = LonGCurve()
        curve.build_inverse()
        sign = -1.0 if args.lon_positive == "braking" else 1.0   # curve: + = driving
        curve_g = sign * df["Lon_g"].to_numpy()
        df["slip_ratio"] = curve.slip_ratio_from_lon_g(curve_g, saturate=args.saturate)
        if args.saturate:
            df["lon_beyond_peak"] = (curve_g > curve.peak_drive[1]) | (curve_g < curve.peak_brake[1])
        n_before = len(df)
        df = df.dropna(subset=["slip_ratio"]).reset_index(drop=True)
        print(f"Lon G curve: braking peak {curve.peak_brake[1]:.2f} g @ {curve.peak_brake[0]:.3f}, "
              f"driving peak {curve.peak_drive[1]:.2f} g @ {curve.peak_drive[0]:.3f}; "
              + (f"{int(df['lon_beyond_peak'].sum())} rows beyond the peaks set to the peak slip ratio" if args.saturate
                 else f"dropped {n_before - len(df)} rows beyond the peaks"))
    elif args.lon_g_per_slip_ratio is not None:
        df["slip_ratio"] = df["Lon_g"] / args.lon_g_per_slip_ratio
    else:
        df["slip_ratio"] = args.slip_ratio

    # Many rows repeat the same (lon G, lat G, slip angle) set, so solve each once.
    keys = ["Lon_g", "Lat_g", "slip_angle_deg", "slip_ratio"]
    pairs = df[keys].drop_duplicates().reset_index(drop=True)
    rows = []
    for long_g, lat_g, slip_angle_deg, slip_ratio in zip(*(pairs[k] for k in keys)):
        forces = calculate_linkage_forces(
            lateral_g=lat_g,
            long_g=long_g,
            axle="front",
            slip_angle_rad=math.radians(slip_angle_deg),
            slip_ratio=slip_ratio,
            pressure_pa=args.pressure * PSI_TO_PA,
        )
        rows.append({f"{name}_N": forces[name]["force_N"] for name in LINKAGE_NAMES})
    pairs = pd.concat([pairs, pd.DataFrame(rows)], axis=1)

    out = df.merge(pairs, on=keys, how="left")
    # Percent error of the model vs the strain gauge, relative to the measured force.
    # Rows where the log has no force reading get NaN.
    out["percent_error"] = (out[f"{args.linkage}_N"] - out["measured_N"]) / out["measured_N"].abs() * 100.0
    lon_suffix = f"_maxlon{args.max_lon:g}g" if args.max_lon is not None else ""
    sr_suffix = "_sr_from_curve" if args.lon_curve else "_sr_from_lon" if args.lon_g_per_slip_ratio is not None else ""
    out_csv = RESULTS_DIR / f"{args.csv.stem}{lon_suffix}{sr_suffix}_front_linkage_forces.csv"
    out.to_csv(out_csv, index=False)

    print(f"Starting at row {start_row} (measured {df['measured_N'].iloc[0]:.2f} N)")
    print(f"{args.csv.name}: {len(out)} of {n_total} rows{f" with |slip angle| <= {args.max_slip} deg" if args.max_slip is not None else ""}{f" and |Lon G| <= {args.max_lon} g" if args.max_lon is not None else ""} ({len(pairs)} unique), front corner")
    slip_ratio_label = ("slip ratio from carG.m Lon G curve" if args.lon_curve
                        else f"slip ratio = Lon G / {args.lon_g_per_slip_ratio:g}" if args.lon_g_per_slip_ratio is not None
                        else f"slip ratio {args.slip_ratio}")
    print(f"Lon G from {args.log_csv.name}, {slip_ratio_label}, {args.pressure} psi\n")
    print(f"{'Linkage':<18}{'min (N)':>12}{'max (N)':>12}{'mean (N)':>12}")
    for name in LINKAGE_NAMES:
        col = out[f"{name}_N"]
        print(f"{name:<18}{col.min():>12.1f}{col.max():>12.1f}{col.mean():>12.1f}")

    err = out["percent_error"].dropna()
    print(f"\nPercent error, model {args.linkage} vs measured '{measured_label}' ({len(err)} rows with a force reading):")
    print(f"  mean {err.mean():+.1f}%, mean absolute {err.abs().mean():.1f}%, median absolute {err.abs().median():.1f}%")
    print(f"  range {err.min():+.1f}% to {err.max():+.1f}%")
    print(f"  within +/-10%: {(err.abs() <= 10).mean() * 100:.1f}% of rows, within +/-25%: {(err.abs() <= 25).mean() * 100:.1f}%")
    print(f"\nSaved -> {out_csv}")


if __name__ == "__main__":
    main()
