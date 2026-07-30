"""
case_common.py — shared constants and helpers for the case*_*.py analysis
scripts (max G's, max roll, and whatever comes after).

Why this exists: case1_max_gs.py and filter_compare.py had drifted onto two
different values of G (9.81 vs 9.80665) despite both supposedly using "the
same filtering." Anything that must stay identical across case scripts
(the gravity constant, filter order, locked-in cutoff frequencies, event
detection, steady-segment/peak-detection logic) lives here instead of being
redefined per-script. A new case script should import from here rather than
copy-pasting these definitions.

IMPORTANT — real elapsed time, not sample count * dt: the InfluxDB union
time grid (see parse_influx.py) is NOT uniformly sampled — its density
depends on how many CAN messages happen to be active at any given moment,
which varies within a single file (e.g. a stopped car generating fewer
signal updates than one accelerating out of a corner). Multiplying a
sample count by one global `dt = median(diff(t))` to get a duration is
therefore wrong, sometimes by 3-5x. Confirmed on real data: a stopped
window in autocross_andrew2.csv measured as 1.32s / 1.01s that way was
actually 6.42s / 4.90s of real elapsed time, wrongly failing the >=2.0s
static-baseline gate; skidpad turn segments were similarly under-reported
by ~3 seconds each. Every function here that gates or reports a duration
takes the actual elapsed-time array `t` (seconds, from elapsed_seconds())
and measures real `t[e] - t[s]` spans — never sample-count * dt. `dt`
itself is still fine for filter design (lowpass()'s Butterworth needs an
approximate sample rate, not exact spacing) — just not for anything
duration-based.

Run it:
    (not runnable directly — imported by case1_max_gs.py, case2_max_roll.py, etc.)
"""

import os
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, find_peaks

# ── Physical / filter constants ──────────────────────────────────────────
G = 9.80665                  # standard gravity (m/s^2) — matches filter_compare.py
FILTER_ORDER = 4              # Butterworth order, every case script
SKIDPAD_CUTOFF_HZ = 2.0       # locked-in cutoff for skidpad (steady-state cornering)
AUTOX_END_CUTOFF_HZ = 5.0     # locked-in cutoff for autocross/endurance (transient)

# ── Event detection ───────────────────────────────────────────────────────
EVENT_KEYWORDS = ["skidpad", "autocross", "endurance", "brake", "accel"]
CASE_EVENTS = ["skidpad", "autocross", "endurance"]   # events every case*_*.py covers


def detect_event_type(filename):
    lower = os.path.basename(filename).lower()
    for keyword in EVENT_KEYWORDS:
        if keyword in lower:
            return keyword
    return "unknown"


def group_by_event(csv_paths):
    groups = {kw: [] for kw in EVENT_KEYWORDS}
    groups["unknown"] = []
    for path in csv_paths:
        groups[detect_event_type(path)].append(path)
    return groups


# ── Filtering / time helpers ──────────────────────────────────────────────
def fill_gaps(values):
    """Linearly interpolate NaN gaps — filtfilt can't handle NaNs."""
    return pd.Series(values).interpolate(limit_direction="both").to_numpy()


def lowpass(values, dt, cutoff_hz, order=FILTER_ORDER):
    """Zero-phase Butterworth low-pass filter. `dt` here is an approximate
    sample interval for filter design only (Butterworth just needs a
    representative sample rate, not exact uniform spacing) — this is the
    one place a scalar dt is still the right tool. Falls back to the
    (gap-filled) raw signal if the sample rate is too low for the
    requested cutoff."""
    fs = 1.0 / dt
    nyq = fs / 2.0
    filled = fill_gaps(values)
    if cutoff_hz >= nyq:
        print(f"  [!] Sample rate too low for {cutoff_hz} Hz cutoff — skipping filter.")
        return filled
    b, a = butter(order, cutoff_hz / nyq, btype="low")
    return filtfilt(b, a, filled)


def elapsed_seconds(time_array):
    idx = pd.DatetimeIndex(time_array)
    return (idx - idx[0]).total_seconds().to_numpy()


def trim_window(t, s, e, trim_s):
    """Return (ts, te) trimming `trim_s` seconds of REAL elapsed time off
    each end of window [s, e], using the actual elapsed-time array `t`
    (not an assumed uniform dt). Falls back to the untrimmed window if
    trimming would invert it (window shorter than 2*trim_s)."""
    ts = int(np.searchsorted(t, t[s] + trim_s, side="left"))
    te = int(np.searchsorted(t, t[e] - trim_s, side="right")) - 1
    ts = max(ts, s)
    te = min(te, e)
    if te <= ts:
        return s, e
    return ts, te


# ── Skidpad: steady-state segmentation (by sign + magnitude of a signal) ──

# Tuned against real lateral-G data (see case1_max_gs.py history) — a
# steady skidpad circle shows up as a ~7-8s run of one sign (real elapsed
# time is actually more like ~10-11s — see module docstring), with a few
# short noise/transition fragments in between that these thresholds are
# meant to exclude.
MIN_LAT_G_FOR_TURN = 0.3     # g — below this, not really "turning"
MIN_RUN_SECONDS = 2.0         # minimum REAL elapsed duration to count as a real circling segment
TRIM_SECONDS = 0.5            # trim this much off each end (entry/exit transition)

# How segments are separated from transitions, WITHOUT assuming how many runs
# a file contains.
#
# This replaced a hard `RUNS_PER_DIRECTION = 2` cap, which encoded "the file
# has 2 back-to-back runs, one each way". That held for
# skidpad_austin_both.csv but silently discarded data as soon as the session
# format changed: three runs per direction reported two, and four runs
# combined into one CSV reported two. Anything past the second-longest
# vanished with no warning.
#
# The cap could not simply be removed, because it was doing real work. On
# skidpad_austin_both sign -1, FIVE segments clear the 2.0s min_run_s gate:
# 11.2, 10.8, 5.7, 3.5 and 2.0s. Only the first two are steady circles; the
# rest are entry/exit arcs and transitions, and averaging them in would
# corrupt the result.
#
# So the two jobs are now separated: min_run_s rejects noise, and this
# RELATIVE criterion rejects transitions — keep every segment at least this
# fraction as long as the longest one of the same sign. That adapts to any
# run count while still discriminating properly, because real runs of the
# same manoeuvre have similar durations and transitions are much shorter.
#
# 0.7 verified against every real file: it reproduces the previous cap-of-2
# results exactly, with a wide margin either side — the genuine second run
# is 0.96 of the longest, while the longest spurious segment is 0.51.
MIN_FRACTION_OF_LONGEST = 0.7


def find_steady_segments(signal_f, t, threshold=MIN_LAT_G_FOR_TURN,
                          min_run_s=MIN_RUN_SECONDS, runs_per_direction=None,
                          min_fraction_of_longest=MIN_FRACTION_OF_LONGEST):
    """Return {sign: [(start_idx, end_idx, duration_s), ...]} — the
    qualifying steady segments of each sign of `signal_f`, in time order.
    `duration_s` and the `min_run_s` gate are real elapsed time (t[e]-t[s]),
    not sample-count * dt — see module docstring.

    Segment selection adapts to however many runs the file contains: a
    segment is kept if it lasts at least `min_fraction_of_longest` of the
    longest segment of the same sign (see the comment above). So one run,
    two runs, five runs, or a single-direction mock skidpad all work without
    changing anything.

    `runs_per_direction` is an optional HARD cap on the number kept per
    sign, applied after the relative filter, for callers that genuinely know
    the structure (case3's brake fallback does). Leave it None otherwise —
    setting it is how the original assumption got baked in.

    Written against lateral G specifically (see case1_max_gs.py's docstring
    for why steering-rate gating was tried and abandoned) — pass the
    filtered lateral-G array here even when the quantity you actually want
    to report (e.g. roll) is something else. Lateral G is what reliably
    identifies "the car is mid-corner, holding a steady line."
    """
    turning = np.abs(signal_f) > threshold
    sign = np.sign(signal_f)

    runs = []
    start = None
    cur_sign = None
    for i in range(len(turning)):
        if turning[i] and (start is None or sign[i] != cur_sign):
            if start is not None:
                runs.append((start, i - 1, cur_sign))
            start, cur_sign = i, sign[i]
        elif not turning[i] and start is not None:
            runs.append((start, i - 1, cur_sign))
            start, cur_sign = None, None
    if start is not None:
        runs.append((start, len(turning) - 1, cur_sign))

    good_runs = [(s, e, sg) for (s, e, sg) in runs if (t[e] - t[s]) >= min_run_s]

    by_sign = {}
    for s, e, sg in good_runs:
        dur = float(t[e] - t[s])
        by_sign.setdefault(sg, []).append((s, e, dur))

    top_by_sign = {}
    for sg, run_list in by_sign.items():
        run_list.sort(key=lambda r: r[2], reverse=True)
        longest = run_list[0][2]
        kept = [r for r in run_list if r[2] >= min_fraction_of_longest * longest]
        if runs_per_direction is not None:
            kept = kept[:runs_per_direction]
        kept.sort(key=lambda r: r[0])              # back to time order for reporting
        top_by_sign[sg] = kept
    return top_by_sign


# ── Autocross/Endurance: peak detection ──────────────────────────────────

TOP_K_PEAKS = 5
PEAK_MIN_DISTANCE_S = 1.0     # minimum REAL elapsed spacing between counted peaks,
                              # so one corner/bump isn't double-counted


def top_k_peaks(signal, t, k=TOP_K_PEAKS, prominence=None, min_distance_s=PEAK_MIN_DISTANCE_S):
    """Top-k peaks of `signal` by height, at least `min_distance_s` REAL
    elapsed seconds apart. `prominence` is metric-specific (g for G's, mm
    for roll) — always pass it explicitly rather than relying on a shared
    default.

    Peaks are found by prominence only, with NO index-based `distance`
    argument to scipy — the time grid isn't uniformly sampled, so a fixed
    sample-count distance means different amounts of real time in
    different parts of the same file (see module docstring). Temporal
    spacing is enforced afterward directly against elapsed time: tallest
    candidate first, reject any peak within `min_distance_s` real seconds
    of an already-accepted one (greedy non-max suppression in time)."""
    idxs, _ = find_peaks(signal, prominence=prominence)
    if len(idxs) == 0:
        return np.array([], dtype=int), np.array([])

    heights = signal[idxs]
    order = np.argsort(heights)[::-1]
    idxs_sorted = idxs[order]
    heights_sorted = heights[order]

    accepted_idx, accepted_h, accepted_t = [], [], []
    for idx, h in zip(idxs_sorted, heights_sorted):
        ti = t[idx]
        if all(abs(ti - at) >= min_distance_s for at in accepted_t):
            accepted_idx.append(idx)
            accepted_h.append(h)
            accepted_t.append(ti)
            if len(accepted_idx) >= k:
                break
    return np.array(accepted_idx), np.array(accepted_h)


# ── Static baseline: find a stopped-car window for zeroing a sensor ─────

STATIC_SPEED_THRESHOLD_MS = 0.5   # m/s — below this, treat the car as stopped
STATIC_MIN_DURATION_S = 2.0        # minimum REAL elapsed length of a stop to trust as a baseline reference
STATIC_TRIM_S = 0.5                # trim this much off each end of the chosen window (settling transition)
STATIC_EDGE_FRACTION = 0.15        # "near the start/end" = within this fraction of total elapsed duration


def _low_speed_runs(speed, t, threshold=STATIC_SPEED_THRESHOLD_MS, min_duration_s=STATIC_MIN_DURATION_S):
    low = np.abs(speed) < threshold
    runs = []
    start = None
    for i in range(len(low)):
        if low[i] and start is None:
            start = i
        elif not low[i] and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(low) - 1))
    return [(s, e) for s, e in runs if (t[e] - t[s]) >= min_duration_s]


def find_static_window(speed, t, edge_fraction=STATIC_EDGE_FRACTION):
    """Return (start_idx, end_idx) of a stopped-car window to use as a
    sensor baseline reference, or None if no qualifying stop exists.

    Preference order: a stop within the first `edge_fraction` of the
    file's REAL elapsed duration (car sitting still before the run
    starts) — else within the last `edge_fraction` (sitting still after)
    — else the single longest stop anywhere in the file (by real elapsed
    time), which catches a mid-session stop (e.g. an endurance driver
    change) when there's no clean stop at either edge.
    """
    runs = _low_speed_runs(speed, t)
    if not runs:
        return None

    total_span = t[-1] - t[0]
    edge_span = total_span * edge_fraction
    start_cutoff = t[0] + edge_span
    end_cutoff = t[-1] - edge_span

    def real_dur(run):
        s, e = run
        return t[e] - t[s]

    start_runs = [(s, e) for s, e in runs if t[s] <= start_cutoff]
    if start_runs:
        return max(start_runs, key=real_dur)

    end_runs = [(s, e) for s, e in runs if t[e] >= end_cutoff]
    if end_runs:
        return max(end_runs, key=real_dur)

    return max(runs, key=real_dur)   # longest stop anywhere, by real elapsed time


def static_baseline(values, t, window, trim_s=STATIC_TRIM_S):
    """Median of `values` over `window` (start_idx, end_idx), trimmed by
    `trim_s` real seconds off each end (via trim_window()) to skip the
    settling transition into/out of the stop. Returns None if `window` is
    None."""
    if window is None:
        return None
    s, e = window
    ts, te = trim_window(t, s, e, trim_s)
    return float(np.median(values[ts:te + 1]))


# ── The four shock pots: naming + per-corner baselining ──────────────────

CORNERS = ["FL", "FR", "RL", "RR"]

CORNER_SIGNAL_NAMES = {
    "FL": "VCFRONT_shockpotdispFL",
    "FR": "VCFRONT_shockpotdispFR",
    "RL": "VCREAR_shockpotdispRL",
    "RR": "VCREAR_shockpotdispRR",
}


# ── Motion ratio: shock/spring travel -> wheel travel ────────────────────
#
# Measured values (from the team's suspension loads sheet), defined as
# WHEEL displacement / SPRING displacement — so both are > 1 and you
# MULTIPLY shock-pot mm by these to get wheel mm.
#
# FRONT AND REAR DIFFER, which dictates where the conversion has to happen:
# every corner must be converted to wheel travel FIRST, before any roll,
# pitch or modal arithmetic. Computing (front_avg - rear_avg) on raw
# shock-pot mm and then applying one ratio afterwards is only valid when
# the two ratios are equal, and they are not — it would misreport pitch by
# roughly the 11% spread between them. Use to_wheel_travel() and do all
# subsequent maths on its output.
#
# These replace the earlier MOTION_RATIO = 1.0 placeholder that every case
# script carried, so all previously reported angles were understated:
# front by 15%, rear by ~4%.
MOTION_RATIO_FRONT = 1.15
MOTION_RATIO_REAR = 1.038

CORNER_MOTION_RATIO = {
    "FL": MOTION_RATIO_FRONT,
    "FR": MOTION_RATIO_FRONT,
    "RL": MOTION_RATIO_REAR,
    "RR": MOTION_RATIO_REAR,
}


# ── Brake pressure: detecting when the car is actually braking ───────────
#
# Preferred over thresholding longitudinal G for brake events, because it
# measures driver input directly rather than inferring it from the result
# (lon G also responds to drivetrain drag, downshifts and gradient).
#
# Threshold picked from real data: front pressure sits below ~50 psi as
# residual/drag noise, so 100 psi is comfortably "on the brakes" while
# still catching light applications. Measured front maxima: braketest1
# 1830 psi, braketest2 1112, autocross 580-1262, skidpad 456, accel
# 224-792 (accel runs end with a stop, which is why they show up at all).
#
# CAUTION — endurance_full.csv SATURATES: its front pressure p99 is exactly
# 2000 psi, the top of the DBC range [0|2000]. Peak brake pressure in
# endurance is therefore a floor, not a true maximum.
BRAKE_PRESSURE_SIGNALS = {
    "front": "VCFRONT_brakePressure",
    "rear": "VCREAR_brakePressure",
}

BRAKING_PRESSURE_PSI = 100.0     # above the ~50 psi residual-drag floor
BRAKE_PRESSURE_MAX_PSI = 2000.0  # DBC ceiling — at/above this, treat as saturated
BRAKE_MIN_DURATION_S = 0.3       # ignore pressure blips shorter than this


BRAKING_MIN_SPEED_MS = 3.0       # must be rolling this fast to count as braking


def find_braking_windows(bp_front, t, speed=None, threshold=BRAKING_PRESSURE_PSI,
                          min_duration_s=BRAKE_MIN_DURATION_S,
                          min_speed_ms=BRAKING_MIN_SPEED_MS):
    """Return [(start_idx, end_idx, duration_s), ...] where front brake
    pressure exceeds `threshold` AND the car is rolling faster than
    `min_speed_ms`, for at least `min_duration_s` of REAL elapsed time
    (never sample-count * dt — see module docstring).

    Uses front pressure only: front and rear track each other closely
    (they share the same master-cylinder input via the balance bar), and
    front is the larger of the two on every file measured.

    The SPEED GATE IS NOT OPTIONAL in practice — pressure alone is not a
    braking event. Without it, braketest1 produced a single 30.33-second
    "braking window" (the driver simply holding the pedal at a standstill)
    and several windows whose pitch was POSITIVE, i.e. squat rather than
    dive, which is physically impossible under braking. Passing `speed`
    removes those. It defaults to None only so callers whose files lack the
    speed channel still work.
    """
    on = np.asarray(bp_front, dtype=float) > threshold
    if speed is not None:
        on = on & (np.abs(np.asarray(speed, dtype=float)) > min_speed_ms)
    runs = []
    start = None
    for i in range(len(on)):
        if on[i] and start is None:
            start = i
        elif not on[i] and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(on) - 1))
    return [(s, e, float(t[e] - t[s])) for s, e in runs
            if (t[e] - t[s]) >= min_duration_s]


# NOTE on detecting ACCELERATION: use the longitudinal accelerometer
# (VCPDU_lon), not a derivative of VCFRONT_vehicleSpeed. Speed cannot be
# differentiated on this time grid — measured dv/dt reaches 89-127 m/s^2
# (9-13 g) and stays there at the 99th percentile, and low-passing all the
# way down to 0.2 Hz still leaves 5-6 g. The cause is the grid, not the
# sensor: speed is quantised at 0.01 m/s and the union grid's intervals are
# sub-millisecond, so one quantisation step is already ~12 m/s^2. Vehicle
# speed is reliable for coarse gating only (moving vs stopped, as
# find_static_window uses it). VCPDU_lon peaks at a sensible 0.99 g on the
# accel runs by comparison.


# ── Shock-pot step glitches ──────────────────────────────────────────────
#
# Four of the eleven comp2026_data files contain instantaneous step
# discontinuities in the front shock pots — FL and FR jumping together, by
# ~13mm and ~22mm respectively, then holding at the new level. Suspension
# cannot step and then sit still, so these are sensor/electrical faults:
#   accel_corinne1  @118.84s    autocross_andrew1 @76.99s
#   autocross_josh1 @84.56s     braketest2        @147.95s  (+5 smaller)
#
# They matter because they are LARGER than any real event, so an
# unprotected peak search reports them as the worst case. Before this
# filter, glitches held the top spot in three of case4's five events —
# including its overall "design-driving case".
#
# THRESHOLD IS NOT A JUDGEMENT CALL — the two populations are cleanly
# bimodal. Measured over 7.6 million real sensor updates: legitimate
# per-update jumps have p99.9 = 1.19mm, p99.99 = 1.78mm, and the largest
# in any clean file is 4.38mm. The glitches are 20.35 / 22.24 / 22.26 /
# 23.32mm. NOTHING falls between 4.4mm and 20.3mm, and exactly 12 events
# exceed 5mm — the same 12 that exceed 10mm. 8mm sits mid-gap.
#
# Detection runs on RAW pre-filter values, because low-passing smears the
# step across neighbouring samples.
GLITCH_STEP_MM = 8.0    # per-sensor-update jump above this is not real motion
GLITCH_PAD_S = 1.0      # also exclude this much either side (filtfilt rings
                        # around a step; observed false peaks landed
                        # 0.16-0.19s after the glitch itself)


def find_step_glitches(corners_raw, t, threshold_mm=GLITCH_STEP_MM,
                        pad_s=GLITCH_PAD_S):
    """Return (bad_mask, events) for a {corner: raw displacement} dict.

    `bad_mask` is a boolean array over the full time grid, True where a step
    glitch (or its filter ringing) makes the data untrustworthy. `events` is
    a list of (corner, time_s, jump_mm) for reporting.

    Pass RAW displacements — unfiltered, and it does not matter whether they
    are baselined or motion-ratio-converted, since a step is a step under
    any affine transform (though the mm threshold assumes shock-pot scale,
    so convert AFTER detecting).
    """
    t = np.asarray(t, dtype=float)
    bad = np.zeros(len(t), dtype=bool)
    events = []
    for corner, values in corners_raw.items():
        v = np.asarray(values, dtype=float)
        finite_idx = np.flatnonzero(np.isfinite(v))
        if len(finite_idx) < 2:
            continue
        jumps = np.abs(np.diff(v[finite_idx]))
        for pos in np.flatnonzero(jumps > threshold_mm):
            hit = int(finite_idx[pos + 1])
            events.append((corner, float(t[hit]), float(jumps[pos])))
            lo = int(np.searchsorted(t, t[hit] - pad_s, side="left"))
            hi = int(np.searchsorted(t, t[hit] + pad_s, side="right"))
            bad[lo:hi] = True
    events.sort(key=lambda e: e[1])
    return bad, events


def to_wheel_travel(corners):
    """Convert a {corner: shock-pot mm} dict to {corner: wheel mm}, applying
    the front/rear motion ratio per corner. Do this before computing roll,
    pitch, heave or warp — see the comment above."""
    return {c: np.asarray(v, dtype=float) * CORNER_MOTION_RATIO[c]
            for c, v in corners.items()}


def baseline_corner_displacements(signals, t, speed):
    """Pull the four shock-pot displacement channels out of a parsed
    SignalSet and zero each one against its OWN stopped-car reading.

    Returns (corners, baselines, baselines_found) where `corners` maps
    "FL"/"FR"/"RL"/"RR" -> baselined displacement array (unfiltered).

    Why per-corner baselining is mandatory, not optional: each shock pot
    carries its own sensor/calibration zero offset. Differencing two
    corners (roll = FR - FL) or two axles (pitch = front_avg - rear_avg)
    without removing those offsets first counts the offset as real
    suspension movement. This was a genuine bug found and fixed while
    building case2 — results were visibly skewed until every corner was
    baselined against the same stopped-car window.

    If no qualifying stopped window exists, returns the raw channels with
    baselines of 0.0 and baselines_found=False, so the caller can warn
    rather than silently reporting un-baselined numbers.
    """
    static_window = find_static_window(speed, t)
    corners, baselines = {}, {}
    for corner in CORNERS:
        raw = np.asarray(signals[CORNER_SIGNAL_NAMES[corner]].value, dtype=float)
        baseline = static_baseline(raw, t, static_window)
        baselines[corner] = baseline
        corners[corner] = raw

    baselines_found = all(b is not None for b in baselines.values())
    if not baselines_found:
        baselines = {c: 0.0 for c in CORNERS}
    else:
        corners = {c: corners[c] - baselines[c] for c in CORNERS}
    return corners, baselines, baselines_found
