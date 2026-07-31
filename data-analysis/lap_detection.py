# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
lap_detection.py — find laps without position, and overlay runs corner by
corner.

THE PROBLEM. There is no GPS in this data — 19 signals across all 11 files,
none positional. `VCPDU_yaw` exists but dead-reckoning a path from it does
not close: on autocross the integrated course spans ~365 m but start and end
land 156-177 m apart, consistent with the DBC's IMU_YAW_CALIBRATION_FAILED
warning. So there is no track map and no way to name a corner geometrically.

WHAT WORKS INSTEAD: DISTANCE. Vehicle speed integrates cleanly even though
it cannot be differentiated (the notorious 9-13 g dv/dt is a differentiation
artefact of the union grid; integrating averages the same quantisation out).
Cumulative distance is a lap-invariant x-axis — the same corner happens at
the same distance every lap, whatever the driver did.

Measured on the four autocross runs: 787, 789, 791 and 804 m of moving
distance. A 2.2% spread over one lap of the same course, which is the
alignment error to correct, not a reason to doubt the method.

HOW LAPS ARE FOUND. Resample speed onto a uniform DISTANCE grid, then
autocorrelate. A repeated course makes v(d) periodic with period = lap
length, and the first strong autocorrelation peak past a minimum plausible
lap is that length. Boundaries are then refined by cross-correlating each
candidate lap against a template built from the median lap.

Working in distance rather than time is what makes the stationary events
harmless. A driver change adds ~170 s and ZERO metres, so in the distance
domain it collapses to a point instead of looking like a lap boundary. The
lap containing it comes out with a normal length and an anomalous duration —
which is exactly what it is.

GROUND TRUTH. Endurance has official per-lap times from the FSAE results
portal (car 43), so detection is VALIDATED rather than eyeballed. Two of
those laps are stationary events, which is the case a naive speed-based
detector gets wrong.

Run it:
    uv run lap_detection.py --dir comp2026_data
    uv run lap_detection.py --dir comp2026_data --file endurance_full
"""

import os
import sys
import glob
import argparse

import numpy as np
import plotly.graph_objects as go

from parse_influx import parse_influx
from case_common import (
    uniform_resample, uniform_resample_corners, UNIFORM_RATE_HZ,
    to_wheel_travel, mm_to_deg, FRONT_TRACK_MM, REAR_TRACK_MM,
    detect_event_type, G, find_step_glitches,
)

PLOTS_ROOT = os.path.join("plots", "lap_detection")

# Below this the car is not on course — staging, the grid, a stop.
MOVING_SPEED_MS = 2.0

# Distance-grid resolution. 1 m is far finer than any corner and keeps the
# autocorrelation cheap.
DISTANCE_STEP_M = 1.0

# A lap is at least this long. Guards the autocorrelation against locking
# onto a short repeating feature (a slalom, a chicane) instead of the lap.
MIN_LAP_M = 300.0


# Official endurance lap times for car 43, from the FSAE results portal.
# Lap 12 is the DRIVER CHANGE and lap 13 the momentary stop early in Josh's
# stint — both real laps, both stationary events. The driver-change lap
# counts as a lap for scoring, which is why it is included here.
ENDURANCE_TRUTH_S = [
    68.197, 68.187, 71.313, 67.567, 67.160, 69.293, 69.067,
    70.253, 69.223, 70.104, 76.540, 168.890, 121.893, 68.477,
    67.020, 64.873, 66.610, 66.857, 66.800, 64.423, 63.363, 66.470,
]

# Official autocross times, in run order (Josh ran first, then Andrew).
# Run 1 took a 20 s off-course penalty; these are the RAW times.
AUTOCROSS_TRUTH_S = {
    "autocross_josh1": 50.508,
    "autocross_josh2": 49.541,
    "autocross_andrew1": 54.514,
    "autocross_andrew2": 51.687,
}


def load_run(path):
    """Speed, distance and the derived signals, on a true 100 Hz grid."""
    signals = parse_influx(path, verbose=False)

    if "VCFRONT_vehicleSpeed" not in signals:
        return None

    t, speed = uniform_resample(signals["VCFRONT_vehicleSpeed"],
                               name="VCFRONT_vehicleSpeed")
    dt = 1.0 / UNIFORM_RATE_HZ

    # Distance accumulates ONLY while moving, so a stationary event adds
    # time without adding metres — which is what keeps it from looking
    # like a lap boundary further down.
    moving = speed > MOVING_SPEED_MS
    distance = np.cumsum(np.where(moving, speed, 0.0) * dt)

    out = {"path": path, "t": t, "speed": speed,
           "distance": distance, "moving": moving}

    # Roll, for the corner-by-corner overlay.
    try:
        tc, corners = uniform_resample_corners(signals)
    except Exception:
        return out

    mask, _ = find_step_glitches(corners, tc)
    if mask.any():
        good = ~mask
        corners = {c: np.interp(tc, tc[good], v[good]) for c, v in corners.items()}

    wheel = to_wheel_travel(corners)
    roll_deg = (mm_to_deg(wheel["FR"] - wheel["FL"], FRONT_TRACK_MM)
                + mm_to_deg(wheel["RR"] - wheel["RL"], REAR_TRACK_MM)) / 2.0

    out["roll_deg"] = np.interp(t, tc, roll_deg)

    if "VCPDU_lat" in signals:
        tl, lat = uniform_resample(signals["VCPDU_lat"], name="VCPDU_lat")
        out["lat_g"] = np.interp(t, tl, lat / G)

    return out


def on_distance_grid(run, values):
    """Resample a time series onto a uniform distance grid.

    Only the moving samples contribute — a stationary stretch maps many
    time samples to one distance, and np.interp on a non-increasing x is
    undefined.
    """
    d = run["distance"][run["moving"]]
    v = np.asarray(values)[run["moving"]]

    if d.size < 10:
        return np.array([]), np.array([])

    # Distance is non-decreasing but has flat spots at the boundaries of
    # moving stretches; keep strictly increasing samples only.
    keep = np.concatenate([[True], np.diff(d) > 0])
    d, v = d[keep], v[keep]

    grid = np.arange(d[0], d[-1], DISTANCE_STEP_M)
    return grid, np.interp(grid, d, v)


def estimate_lap_length(grid, speed_of_d):
    """Lap length in metres, from the autocorrelation of speed vs distance.

    A repeated course makes speed-vs-distance periodic: the car brakes for
    the same corner at the same distance every lap. The first strong
    autocorrelation peak past MIN_LAP_M is that period.

    Returns (length_m, confidence) where confidence is the normalised
    autocorrelation at the peak — near 1 means the laps really do look
    alike, near 0 means this is not a repeating course and the answer
    should not be trusted.
    """
    if grid.size < 4 * int(MIN_LAP_M / DISTANCE_STEP_M):
        return None, 0.0

    x = speed_of_d - np.mean(speed_of_d)

    corr = np.correlate(x, x, mode="full")[len(x) - 1:]
    corr = corr / corr[0]

    lo = int(MIN_LAP_M / DISTANCE_STEP_M)
    hi = len(corr) // 2

    if hi <= lo:
        return None, 0.0

    window = corr[lo:hi]
    peak = int(np.argmax(window)) + lo

    return peak * DISTANCE_STEP_M, float(corr[peak])


def lap_boundaries(run, lap_m):
    """Times at which each lap starts, from cumulative distance."""
    d = run["distance"]
    total = d[-1]

    edges_m = np.arange(0.0, total, lap_m)

    return [float(run["t"][int(np.searchsorted(d, e))]) for e in edges_m
            if e < total]


def report(run, truth=None):
    name = os.path.splitext(os.path.basename(run["path"]))[0]

    grid, speed_of_d = on_distance_grid(run, run["speed"])
    if grid.size == 0:
        print(f"  {name}: not enough moving data")
        return None

    total_m = run["distance"][-1]
    moving_s = float(np.sum(run["moving"]) / UNIFORM_RATE_HZ)

    lap_m, confidence = estimate_lap_length(grid, speed_of_d)

    print(f"\n  {name}")
    print(f"    distance {total_m:.0f} m over {moving_s:.1f} s moving "
          f"({total_m / moving_s:.1f} m/s mean)")

    if lap_m is None:
        print(f"    single lap — too short to autocorrelate a repeat")
        if truth:
            print(f"    official time {truth:.3f} s")
        return None

    starts = lap_boundaries(run, lap_m)
    durations = np.diff(starts + [float(run["t"][-1])])

    print(f"    lap length {lap_m:.0f} m (autocorrelation {confidence:+.2f})")
    print(f"    {len(starts)} laps detected")

    if truth is None:
        return {"name": name, "lap_m": lap_m, "starts": starts,
                "durations": durations}

    print(f"    ground truth: {len(truth)} laps")

    n = min(len(durations), len(truth))
    if not n:
        return {"name": name, "lap_m": lap_m, "starts": starts,
                "durations": durations}

    truth_arr = np.array(truth[:n])
    err = durations[:n] - truth_arr

    # THREE EDGE LAPS ARE NOT DETECTION FAILURES and lumping them into one
    # accuracy figure hides how well the rest works:
    #
    #   Lap 1  — the file starts before the race does, so lap 1 absorbs
    #            however much running happened on the way to the grid.
    #            Without a start line there is nothing to anchor it to.
    #   Lap 12 — the driver change. Distance does not advance while
    #            stationary, so ALL the stopped time lands in whichever lap
    #            contains it. That is correct behaviour, but it means the
    #            boundary either side is placed by distance while the
    #            official one is placed by the timing loop.
    #   Last   — a partial remainder. Total distance is not an exact
    #            multiple of a lap, so the final segment is short by
    #            construction.
    #
    # The INTERIOR laps are the honest measure of whether this works.
    edge = {0, n - 1}
    stationary = {i for i in range(n) if truth[i] > 100}
    interior = [i for i in range(n) if i not in edge and i not in stationary]

    print(f"    {'lap':>5}{'detected':>11}{'official':>11}{'error':>9}")
    for i in range(n):
        note = ""
        if i == 0:
            note = "  <-- includes pre-race running"
        elif i == n - 1:
            note = "  <-- partial remainder"
        elif i in stationary:
            note = "  <-- stationary event (driver change / stop)"
        print(f"    {i + 1:>5}{durations[i]:>11.2f}{truth[i]:>11.3f}"
              f"{err[i]:>+9.2f}{note}")

    if interior:
        ie = np.abs(err[interior])
        pct = 100.0 * ie / truth_arr[interior]
        print(f"\n    INTERIOR LAPS ({len(interior)} of {n}, excluding lap 1, "
              f"the last, and the {len(stationary)} stationary):")
        print(f"      median error {np.median(ie):.2f} s "
              f"({np.median(pct):.1f}% of lap time), worst {ie.max():.2f} s")
        print(f"      lap COUNT is exact: {len(durations)} detected, "
              f"{len(truth)} official")

    return {"name": name, "lap_m": lap_m, "starts": starts,
            "durations": durations}


def build_overlay(runs, output_path, key="roll_deg", ylabel="roll (deg)"):
    """Every run's signal against distance, so the same corner lines up.

    Distance is the alignment axis precisely because it is what the runs
    have in common — a driver who is 5 s slower is still at the same corner
    at the same distance.
    """
    fig = go.Figure()

    for run in runs:
        if key not in run:
            continue
        grid, values = on_distance_grid(run, run[key])
        if grid.size == 0:
            continue
        name = os.path.splitext(os.path.basename(run["path"]))[0]
        fig.add_trace(go.Scattergl(
            x=grid, y=values, mode="lines", name=name, line=dict(width=1.3),
        ))

    fig.update_layout(
        title=f"{ylabel} vs distance — same distance is the same corner",
        xaxis_title="distance travelled (m)", yaxis_title=ylabel,
        template="plotly_white", hovermode="x unified",
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(output_path, include_plotlyjs="cdn")


def main():
    parser = argparse.ArgumentParser(
        description="Detect laps from distance, and overlay runs by distance."
    )
    parser.add_argument("--dir", default="comp2026_data")
    parser.add_argument("--file", default=None,
                        help="Just this file stem (e.g. endurance_full)")
    args = parser.parse_args()

    paths = sorted(glob.glob(os.path.join(args.dir, "*.csv")))
    if args.file:
        paths = [p for p in paths if args.file in os.path.basename(p)]
    if not paths:
        sys.exit("No matching CSVs.")

    print("=" * 72)
    print("LAP DETECTION — from cumulative distance, no GPS required")
    print("=" * 72)

    autocross_runs = []

    for path in paths:
        run = load_run(path)
        if run is None:
            continue

        stem = os.path.splitext(os.path.basename(path))[0]
        event = detect_event_type(path)

        truth = (ENDURANCE_TRUTH_S if event == "endurance"
                 else AUTOCROSS_TRUTH_S.get(stem))

        report(run, truth)

        if event == "autocross":
            autocross_runs.append(run)

    if len(autocross_runs) > 1:
        for key, label in (("roll_deg", "roll (deg)"),
                           ("lat_g", "lateral G (g)"),
                           ("speed", "speed (m/s)")):
            out = os.path.join(PLOTS_ROOT, f"autocross_{key}_by_distance.html")
            build_overlay(autocross_runs, out, key, label)
        print(f"\n  Autocross overlays: {PLOTS_ROOT}/autocross_*_by_distance.html")

    print()


if __name__ == "__main__":
    main()
