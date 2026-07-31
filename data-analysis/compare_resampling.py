# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy"]
# ///
"""
compare_resampling.py — what changes if we filter on a true 100 Hz grid
instead of the InfluxDB union grid.

THIS DECIDES NOTHING. It measures, so the decision can be made with the
delta visible rather than from an argument about which is more correct.

The case is that the union grid is not a sample rate: on endurance_full its
median spacing is 0.39ms while individual gaps run 0.019-19.3ms, a 1030x
range inside one file. lowpass() designs its Butterworth from a single
scalar dt, so on that grid the assumed dt is locally wrong and the filter
is effectively position-dependent. Resampling to the true 100 Hz first
removes that.

The case against changing anything is that every published roll, pitch and
travel number shifts, and existing figures go stale. Hence this script.

Run it:
    uv run compare_resampling.py --dir comp2026_data
"""

import os
import glob
import argparse

import numpy as np

from parse_influx import parse_influx
from case_common import (
    G, lowpass, elapsed_seconds, fill_gaps,
    uniform_resample, uniform_resample_corners, UNIFORM_RATE_HZ,
    to_wheel_travel, mm_to_deg, CORNERS, CORNER_SIGNAL_NAMES,
    FRONT_TRACK_MM, REAR_TRACK_MM, AVG_TRACK_MM, WHEELBASE_MM,
    SKIDPAD_CUTOFF_HZ, AUTOX_END_CUTOFF_HZ, detect_event_type,
    find_step_glitches,
)

EDGE_EXCLUDE_FRACTION = 0.02


def interior_peak(values, t, edge_fraction=EDGE_EXCLUDE_FRACTION):
    """Largest |value| ignoring filtfilt's boundary overshoot.

    Excludes by ELAPSED TIME, not sample count. That distinction is the
    whole point of this script: the union grid is non-uniform, so dropping
    2% of its samples drops a different physical span than dropping 2% of a
    uniform grid's — which would put a bias into the very comparison being
    made.
    """
    t = np.asarray(t, dtype=float)
    span = t[-1] - t[0]
    lo = t[0] + span * edge_fraction
    hi = t[-1] - span * edge_fraction

    keep = (t >= lo) & (t <= hi)
    trimmed = np.asarray(values)[keep] if keep.any() else np.asarray(values)

    return float(np.nanmax(np.abs(trimmed)))


def measure(path):
    signals = parse_influx(path, verbose=False)

    if not all(CORNER_SIGNAL_NAMES[c] in signals for c in CORNERS):
        return None

    event = detect_event_type(path)
    cutoff = SKIDPAD_CUTOFF_HZ if event == "skidpad" else AUTOX_END_CUTOFF_HZ

    # ── on the union grid, exactly as the case scripts do it ──
    t_union = elapsed_seconds(signals[CORNER_SIGNAL_NAMES["FL"]].time)
    dt_union = float(np.median(np.diff(t_union)))

    raw_union = {
        c: fill_gaps(np.asarray(signals[CORNER_SIGNAL_NAMES[c]].value, dtype=float))
        for c in CORNERS
    }

    # Glitches would dominate any peak comparison — mask them on both sides
    # so this measures the resampling and nothing else.
    gmask_u, _ = find_step_glitches(raw_union, t_union)

    wheel_u = to_wheel_travel(raw_union)
    roll_u = lowpass(wheel_u["FR"] - wheel_u["FL"], dt_union, cutoff)
    pitch_u = lowpass(
        (wheel_u["FL"] + wheel_u["FR"]) / 2.0 - (wheel_u["RL"] + wheel_u["RR"]) / 2.0,
        dt_union, cutoff)

    roll_u = np.where(gmask_u, 0.0, roll_u)
    pitch_u = np.where(gmask_u, 0.0, pitch_u)

    # ── on a true 100 Hz grid, from the RAW samples ──
    t_uni, raw_uni = uniform_resample_corners(signals)
    dt_uni = 1.0 / UNIFORM_RATE_HZ

    gmask_r, _ = find_step_glitches(raw_uni, t_uni)

    wheel_r = to_wheel_travel(raw_uni)
    roll_r = lowpass(wheel_r["FR"] - wheel_r["FL"], dt_uni, cutoff)
    pitch_r = lowpass(
        (wheel_r["FL"] + wheel_r["FR"]) / 2.0 - (wheel_r["RL"] + wheel_r["RR"]) / 2.0,
        dt_uni, cutoff)

    roll_r = np.where(gmask_r, 0.0, roll_r)
    pitch_r = np.where(gmask_r, 0.0, pitch_r)

    out = {
        "file": os.path.basename(path),
        "event": event,
        "cutoff": cutoff,
        "n_union": len(t_union),
        "n_uniform": len(t_uni),
        "roll_mm": (interior_peak(roll_u, t_union), interior_peak(roll_r, t_uni)),
        "pitch_mm": (interior_peak(pitch_u, t_union), interior_peak(pitch_r, t_uni)),
    }

    # Lateral G too — case1's headline.
    if "VCPDU_lat" in signals:
        lat_u = lowpass(
            fill_gaps(np.asarray(signals["VCPDU_lat"].value, dtype=float) / G),
            dt_union, cutoff)
        t_lat, lat_raw_r = uniform_resample(signals["VCPDU_lat"], name="VCPDU_lat")
        lat_r = lowpass(lat_raw_r / G, dt_uni, cutoff)
        out["lat_g"] = (interior_peak(lat_u, t_union), interior_peak(lat_r, t_lat))

    return out


def report_sample_rates(path):
    """Measured true rate of every signal, from its RAW timestamps.

    Kept as running code rather than a note, because it is the evidence for
    two claims the analysis leans on: that 100 Hz is the real rate (so
    resampling to it loses nothing), and that VCFRONT_brakePressure is the
    one exception at 10 Hz — which caps its useful cutoff at a 5 Hz Nyquist.
    If a future log changes a task rate, this says so instead of the README
    quietly going stale.
    """
    signals = parse_influx(path, verbose=False)

    names = (list(CORNER_SIGNAL_NAMES.values())
             + ["VCPDU_lat", "VCPDU_lon", "VCFRONT_vehicleSpeed",
                "VCFRONT_brakePressure", "VCREAR_brakePressure"])

    print(f"\n  Measured source rates ({os.path.basename(path)})")
    print(f"    {'signal':<28}{'median dt':>12}{'rate':>10}{'jitter p99':>13}")

    for name in names:
        if name not in signals:
            continue

        t = elapsed_seconds(signals[name].time_raw)
        dt = np.diff(t)
        median = float(np.median(dt))

        flag = ""
        if abs(1.0 / median - UNIFORM_RATE_HZ) > 1.0:
            flag = f"   <-- NOT {UNIFORM_RATE_HZ:.0f} Hz; Nyquist {1 / median / 2:.1f} Hz"

        print(f"    {name:<28}{median * 1000:>10.3f}ms{1 / median:>9.0f}Hz"
              f"{np.percentile(np.abs(dt - median), 99) * 1000:>11.2f}ms{flag}")


def report_residual_inflation(paths, cutoff=5.0):
    """How much of the union grid's 'discarded content' is a ZOH artefact.

    The residual view in filter_compare is what settles a borderline cutoff
    — "structure here means real signal is being deleted". On the union grid
    a large share of that structure is the zero-order-hold staircase, not
    signal, so this quantifies the error the resampling removed.
    """
    print(f"\n  Residual (raw - filtered) RMS at {cutoff} Hz — roll")
    print(f"    {'file':<26}{'union':>10}{'100 Hz':>10}{'inflation':>12}")

    for path in paths:
        signals = parse_influx(path, verbose=False)
        if not all(CORNER_SIGNAL_NAMES[c] in signals for c in CORNERS):
            continue

        t = elapsed_seconds(signals[CORNER_SIGNAL_NAMES["FL"]].time)
        dt = float(np.median(np.diff(t)))

        wu = to_wheel_travel({
            c: fill_gaps(np.asarray(signals[CORNER_SIGNAL_NAMES[c]].value, dtype=float))
            for c in CORNERS
        })
        roll_u = wu["FR"] - wu["FL"]

        _, raw_r = uniform_resample_corners(signals)
        wr = to_wheel_travel(raw_r)
        roll_r = wr["FR"] - wr["FL"]

        a = float(np.sqrt(np.nanmean((roll_u - lowpass(roll_u, dt, cutoff)) ** 2)))
        b = float(np.sqrt(np.nanmean(
            (roll_r - lowpass(roll_r, 1.0 / UNIFORM_RATE_HZ, cutoff)) ** 2)))

        print(f"    {os.path.basename(path)[:25]:<26}{a:>10.4f}{b:>10.4f}"
              f"{100 * (a - b) / b:>11.0f}%")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="comp2026_data")
    args = parser.parse_args()

    paths = sorted(glob.glob(os.path.join(args.dir, "*.csv")))

    report_sample_rates(paths[0])
    report_residual_inflation(paths)

    rows = [r for p in paths if (r := measure(p)) is not None]

    print(f"\nFiltering on the UNION grid vs a true {UNIFORM_RATE_HZ:.0f} Hz grid")
    print("(peaks, glitch-masked, outer 2% excluded; + means resampling reports MORE)\n")

    for key, unit in (("roll_mm", "mm"), ("pitch_mm", "mm"), ("lat_g", "g")):
        print(f"  {key} ({unit})")
        print(f"    {'file':<26}{'cutoff':>8}{'union':>12}{'100 Hz':>12}{'change':>10}")

        deltas = []
        for r in rows:
            if key not in r:
                continue
            u, v = r[key]
            pct = 100.0 * (v - u) / u if u else 0.0
            deltas.append(pct)
            print(f"    {r['file'][:25]:<26}{r['cutoff']:>8.1f}"
                  f"{u:>12.3f}{v:>12.3f}{pct:>9.2f}%")

        if deltas:
            print(f"    {'':<26}{'':>8}{'':>12}{'mean':>12}{np.mean(deltas):>9.2f}%")
            print(f"    {'':<26}{'':>8}{'':>12}{'worst':>12}"
                  f"{max(deltas, key=abs):>9.2f}%")
        print()

    print("  grid size (samples per file)")
    print(f"    {'file':<26}{'union':>12}{'100 Hz':>12}{'ratio':>10}")
    for r in rows:
        print(f"    {r['file'][:25]:<26}{r['n_union']:>12,}{r['n_uniform']:>12,}"
              f"{r['n_union'] / r['n_uniform']:>9.1f}x")


if __name__ == "__main__":
    main()
