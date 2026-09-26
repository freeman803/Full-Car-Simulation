"""
read_influx_csv.py — read column G (_value) of an InfluxDB CSV export.

An Influx export stacks every logged channel into one `_value` column
(column G), with the channel name in `_field` (column H). This splits it back
into one column per channel, lined up by sample number:

    VCFRONT_shockpotVoltFR -> strain gauge voltage (V), also converted to pushrod
                              load with the calibration line
                              load_N = 1691.4 * V - 932.6
                              (from 0.969 V = 72 kg and 0.94 V = 67 kg)
    VCPDU_lon              -> longitudinal G
    VCPDU_lat              -> lateral G

Usage (from the repo root):
    uv run corner-model/Forces/read_influx_csv.py
    uv run corner-model/Forces/read_influx_csv.py "path/to/influx.data.csv"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

G = 9.81

# Calibration line, Load (N) = 1691.4 * V - 932.6
# (two points: 0.969 V = 72 kg, 0.94 V = 67 kg)
N_PER_V = 1691.4
N_OFFSET = -932.6

VOLTAGE_FIELD = "VCFRONT_shockpotVoltFR"
COLUMN_NAMES = {
    VOLTAGE_FIELD: "gauge_V",
    "VCPDU_lon": "Lon",
    "VCPDU_lat": "Lat",
}

DEFAULT_CSV = Path(__file__).resolve().parent / "influx.data (9).csv"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def read_column_g(csv_path: Path) -> pd.DataFrame:
    """Return the export's rows as time, field, value (column G), skipping Influx's # annotation lines."""
    df = pd.read_csv(csv_path, comment="#", usecols=["_time", "_value", "_field"])
    df = df.dropna(subset=["_value"])
    df = df[df["_field"] != "_field"]  # repeated header rows between tables
    df["_value"] = df["_value"].astype(float)
    df["_time"] = pd.to_datetime(df["_time"])
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", nargs="?", type=Path, default=DEFAULT_CSV, help="Influx CSV export")
    args = parser.parse_args()

    df = read_column_g(args.csv)
    t0 = df["_time"].min()

    columns = {}
    print(f"{args.csv.name}: column G (_value), {len(df)} values\n")
    print(f"{'Field':<26}{'samples':>9}{'min':>10}{'max':>10}{'mean':>10}{'rate (Hz)':>11}")
    for field, group in df.groupby("_field", sort=False):
        name = COLUMN_NAMES.get(field, field)
        values = group["_value"].reset_index(drop=True)
        t = (group["_time"] - t0).dt.total_seconds().reset_index(drop=True)
        rate = (len(t) - 1) / (t.iloc[-1] - t.iloc[0]) if len(t) > 1 else float("nan")
        print(f"{field:<26}{len(values):>9}{values.min():>10.3f}{values.max():>10.3f}{values.mean():>10.3f}{rate:>11.1f}")

        columns[f"{name}_time_s"] = t
        columns[name] = values
        if field == VOLTAGE_FIELD:
            columns["pushrod_load_N"] = N_PER_V * values + N_OFFSET
            columns["pushrod_load_kg"] = columns["pushrod_load_N"] / G

    out = pd.DataFrame(columns)

    if "pushrod_load_N" in out:
        load = out["pushrod_load_N"].dropna()
        print(f"\nPushrod load (N) = {N_PER_V} * V {N_OFFSET:+}: "
              f"{load.min():.1f} to {load.max():.1f} N, mean {load.mean():.1f} N ({load.mean() / G:.1f} kg)")

    RESULTS_DIR.mkdir(exist_ok=True)
    out_csv = RESULTS_DIR / f"{args.csv.stem.replace(' ', '_')}_columns.csv"
    out.to_csv(out_csv, index=False)
    print(f"Saved -> {out_csv}")


if __name__ == "__main__":
    main()
