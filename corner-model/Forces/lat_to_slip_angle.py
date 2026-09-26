"""
lat_to_slip_angle.py — slip angle for each logged lateral G.

Reads lateral G from a logged CSV and converts each value to a slip angle.
Accepts either a CSV with a `Lat` column (e.g. axial_force_1.csv) or an
InfluxDB export (e.g. "influx.data (9).csv"), where `VCPDU_lat` is used.
Conversion inverts the whole-car lateral G vs slip angle curve from carG.m
(MF6.1 tyre + load transfer, see car_lat_g_curve.py), fitted so that
0 deg -> 0 g and 10 deg -> 1.8 g. Samples above the curve's peak lateral G
have no slip angle and are dropped, or with --saturate get the peak's slip
angle (flagged in the lat_beyond_peak column).

Usage (from the repo root):
    uv run corner-model/Forces/lat_to_slip_angle.py
    uv run corner-model/Forces/lat_to_slip_angle.py path/to/log.csv
    uv run corner-model/Forces/lat_to_slip_angle.py path/to/log.csv --max-slip 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from car_lat_g_curve import LatGCurve
from read_influx_csv import read_column_g

INFLUX_LAT_FIELD = "VCPDU_lat"

DEFAULT_CSV = Path(__file__).resolve().parent / "axial_force_1.csv"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def read_lat(csv_path: Path) -> pd.DataFrame:
    """Return lateral G (and time, if available) from a plain or Influx CSV."""
    header = pd.read_csv(csv_path, comment="#", nrows=0).columns
    if "Lat" in header:
        return pd.read_csv(csv_path, usecols=["Lat"]).rename(columns={"Lat": "Lat_g"})
    df = read_column_g(csv_path)
    df = df[df["_field"] == INFLUX_LAT_FIELD]
    return pd.DataFrame({"time": df["_time"].values, "Lat_g": df["_value"].values})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", nargs="?", type=Path, default=DEFAULT_CSV, help="Logged CSV file")
    parser.add_argument("--max-slip", type=float, default=None,
                        help="Keep only samples with |slip angle| <= this many degrees")
    parser.add_argument("--saturate", action="store_true",
                        help="Give samples above the curve's peak lateral G the peak slip angle instead of dropping them")
    args = parser.parse_args()

    out = read_lat(args.csv)
    curve = LatGCurve()
    print(f"Lat G curve: peak {curve.peak_lat_g:.3f} g at {curve.peak_slip_deg:.1f} deg (scale {curve.scale:.4f})")
    out["slip_angle_deg"] = curve.slip_from_lat_g(out["Lat_g"], saturate=args.saturate)
    if args.saturate:
        out["lat_beyond_peak"] = out["Lat_g"].abs() > curve.peak_lat_g
        print(f"{int(out['lat_beyond_peak'].sum())} samples above the curve's peak set to ±{curve.peak_slip_deg:.1f} deg")
    n_before = len(out)
    out = out.dropna(subset=["slip_angle_deg"]).reset_index(drop=True)
    if len(out) < n_before:
        print(f"Dropped {n_before - len(out)} samples above the curve's peak lateral G")

    suffix = "_saturated" if args.saturate else ""
    if args.max_slip is not None:
        n_before = len(out)
        out = out[out["slip_angle_deg"].abs() <= args.max_slip].reset_index(drop=True)
        print(f"Dropped {n_before - len(out)} samples with |slip angle| > {args.max_slip:g} deg")
        suffix += f"_max{args.max_slip:g}deg"

    RESULTS_DIR.mkdir(exist_ok=True)
    out_csv = RESULTS_DIR / f"{args.csv.stem}_slip_angle{suffix}.csv"
    out.to_csv(out_csv, index=False)

    print(f"{args.csv.name}: {len(out)} samples")
    print(f"Slip angle: {out['slip_angle_deg'].min():.2f} to {out['slip_angle_deg'].max():.2f} deg")
    print(f"Saved -> {out_csv}")


if __name__ == "__main__":
    main()
