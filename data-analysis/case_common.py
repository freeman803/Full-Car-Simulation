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


# LOCKUP GUARD. VCFRONT_vehicleSpeed comes from wheel speed, so during a
# four-wheel lockup it reads ~zero while the car is still moving — and a
# locked, decelerating car is the worst possible baseline reference, since
# it is pitched hard forward under maximum load. Speed alone cannot tell
# the two apart.
#
# Longitudinal G can: a genuinely parked car reads ~0 g, a car under
# threshold braking reads ~1 g. Verified on braketest2, whose stopped
# window really is stopped (mean lon G +0.005 g) — this guard confirms it
# rather than changing it. That file matters: it is the brake test that
# PASSED at competition, with all four wheels locked, so it is exactly the
# data where a lockup could have been mistaken for a standstill.
#
# 0.15 g is well clear of a real stop's ~0.005 g and far below any braking
# worth the name.
STATIC_MAX_LON_G = 0.15


def _low_speed_runs(speed, t, threshold=STATIC_SPEED_THRESHOLD_MS,
                    min_duration_s=STATIC_MIN_DURATION_S,
                    lon_g=None, max_lon_g=STATIC_MAX_LON_G):
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
    runs = [(s, e) for s, e in runs if (t[e] - t[s]) >= min_duration_s]

    if lon_g is None:
        return runs

    # LOCKUP GUARD, applied PER RUN rather than per sample.
    #
    # Rejecting individual samples was the obvious implementation and it is
    # wrong: it fragments genuine stops on the brief lon-G transient of
    # rolling to a halt, and measurably so — it moved accel_jamie_both's
    # baseline window from 0.0-9.2s to an entirely different 17.2-25.3s,
    # and trimmed the tail off nine others.
    #
    # A lockup is a SUSTAINED deceleration of order 1 g, not a scattering
    # of samples, so the mean over the run is the right statistic. Every
    # genuine stop in comp2026_data averages 0.008-0.031 g — two orders of
    # magnitude of headroom under the threshold — while briefly touching
    # 0.26-0.94 g at the edges, which is exactly the transient that must
    # NOT disqualify it.
    lon_g = np.asarray(lon_g, dtype=float)

    kept = []
    for s, e in runs:
        segment = np.abs(lon_g[s:e + 1])
        segment = segment[np.isfinite(segment)]
        if segment.size == 0 or float(np.mean(segment)) < max_lon_g:
            kept.append((s, e))

    return kept


def lon_g_or_none(signals):
    """Longitudinal acceleration in g from a parsed SignalSet, or None if
    the channel is absent. Convenience for the lockup guard, so every
    caller of find_static_window() enables it the same way rather than
    each remembering to divide by G.

    VCPDU_lon is m/s^2 in the DBC (range [-32|32]), NOT g — that unit bug
    was a real one here once.
    """
    if "VCPDU_lon" not in signals:
        return None
    return np.asarray(signals["VCPDU_lon"].value, dtype=float) / G


def find_static_window(speed, t, edge_fraction=STATIC_EDGE_FRACTION, lon_g=None):
    """Return (start_idx, end_idx) of a stopped-car window to use as a
    sensor baseline reference, or None if no qualifying stop exists.

    Preference order: a stop within the first `edge_fraction` of the
    file's REAL elapsed duration (car sitting still before the run
    starts) — else within the last `edge_fraction` (sitting still after)
    — else the single longest stop anywhere in the file (by real elapsed
    time), which catches a mid-session stop (e.g. an endurance driver
    change) when there's no clean stop at either edge.

    Pass `lon_g` (longitudinal acceleration in g) to enable the lockup
    guard — see STATIC_MAX_LON_G. Optional so callers whose files lack the
    channel still work, but supply it whenever you have it: without it,
    a four-wheel lockup can be selected as "stopped".
    """
    runs = _low_speed_runs(speed, t, lon_g=lon_g)
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


def static_baseline(values, t, window, trim_s=STATIC_TRIM_S, bad_mask=None):
    """Median of `values` over `window` (start_idx, end_idx), trimmed by
    `trim_s` real seconds off each end (via trim_window()) to skip the
    settling transition into/out of the stop. Returns None if `window` is
    None.

    `bad_mask` excludes samples — pass find_step_glitches()'s mask. THE
    MEDIAN DOES NOT NEED IT: a step discontinuity inside the window shifts
    a median by nothing measurable, verified on braketest2, whose
    stopped-car window (0.5-50.2s) contains the 46.23s and 46.33s glitches
    and whose baselines are identical to three decimals either way
    (FL 53.330, FR 38.380).

    It is here because ANY STD-BASED measurement over such a window is
    inflated, and that is precisely how braketest2 was misdiagnosed as the
    noisiest file in the set: its "10-20x sensor noise" (0.394/0.667mm
    against a 0.031mm median) was std computed across a step, not noise.
    Masked, the same file measures 0.007-0.043mm — one of the CLEANEST.
    So anything reaching for a spread statistic over the baseline window
    gets the mask by default, and cannot repeat that mistake.
    """
    if window is None:
        return None
    s, e = window
    ts, te = trim_window(t, s, e, trim_s)

    segment = np.asarray(values[ts:te + 1], dtype=float)

    if bad_mask is not None:
        keep = ~np.asarray(bad_mask[ts:te + 1], dtype=bool)
        # Fall back to the unmasked segment rather than returning None if a
        # glitch happens to span the whole window — a slightly-suspect
        # baseline still beats no baseline at all, and the caller's
        # baselines_found flag would otherwise misreport the cause.
        if keep.any():
            segment = segment[keep]

    return float(np.median(segment))


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


# ── Uniform resampling ───────────────────────────────────────────────────
#
# The union grid is NOT a sample rate — it is the merged timestamps of every
# signal in the file, so its density reflects how many CAN messages happened
# to be active, not how fast anything was measured. On endurance_full its
# median spacing is 0.39ms (2577 Hz) while individual gaps run from 0.019ms
# to 19.3ms: a range of 1030x WITHIN ONE FILE.
#
# That breaks three things:
#
#   1. FILTERING. lowpass() designs a Butterworth from one scalar dt, so on
#      a grid this uneven the assumed dt is locally wrong and the filter is
#      effectively position-dependent — heavier where samples are dense.
#   2. ANY SPECTRUM. An FFT/PSD of a non-uniformly sampled signal is not
#      defined. Nothing in the frequency domain is possible without this.
#   3. ANY DERIVATIVE. Already documented above for dv/dt, which reaches
#      9-13 g on this grid.
#
# MEASURED TRUE RATES (median dt of the RAW per-signal samples, not the
# union grid), confirming the firmware's periodic task rates:
#
#   shock pots FL/FR/RL/RR   100 Hz     jitter p99 ~1.8ms
#   VCPDU_lat / VCPDU_lon    100 Hz     jitter p99 ~1.5ms
#   VCFRONT_vehicleSpeed     100 Hz     jitter p99 ~1.2ms
#   VCREAR_brakePressure     100 Hz     jitter p99 ~1.7ms
#   VCFRONT_brakePressure     10 Hz  <-- TEN, not a hundred
#
# The front brake pressure rate is the surprise and it has teeth: at 10 Hz
# its Nyquist is 5 Hz, so ANY CUTOFF AT OR ABOVE 5 Hz IS MEANINGLESS for
# that channel. It is the signal find_braking_windows() thresholds.
UNIFORM_RATE_HZ = 100.0

# Per-signal overrides for anything not sampled at UNIFORM_RATE_HZ.
SIGNAL_RATE_HZ = {
    "VCFRONT_brakePressure": 10.0,
}


def signal_rate_hz(name):
    """True source rate of a named signal, for resampling and for Nyquist
    checks. Defaults to UNIFORM_RATE_HZ."""
    return SIGNAL_RATE_HZ.get(name, UNIFORM_RATE_HZ)


def uniform_resample(signal, target_hz=None, name=None):
    """Put one signal on a genuinely uniform grid, returning (t, values).

    RESAMPLES FROM THE RAW PER-SIGNAL SAMPLES (`signal.time_raw` /
    `value_raw`), NEVER from the union-grid copy. This is not a detail.
    The union grid is built by zero-order hold (parse_influx._zoh_previous),
    and a zero-order hold is a staircase — it carries broadband
    high-frequency content that is an artefact of the resampling, not of
    the signal. Feeding that into a PSD would manufacture spectral energy
    across the whole band, which is precisely the measurement the spectral
    work exists to make.

    Linear interpolation is appropriate here because the raw samples are
    already near-uniform (100 Hz with <2ms jitter) — this corrects jitter
    and lands on an exact grid, it does not invent intermediate detail.
    """
    if target_hz is None:
        target_hz = signal_rate_hz(name if name is not None
                                   else getattr(signal, "name", None))

    t_raw = elapsed_seconds(signal.time_raw)
    v_raw = np.asarray(signal.value_raw, dtype=float)

    finite = np.isfinite(v_raw)
    if finite.sum() < 2:
        return np.asarray([]), np.asarray([])

    t_raw, v_raw = t_raw[finite], v_raw[finite]

    step = 1.0 / target_hz
    t_uniform = np.arange(t_raw[0], t_raw[-1] + step / 2.0, step)

    return t_uniform, np.interp(t_uniform, t_raw, v_raw)


def uniform_resample_corners(signals, target_hz=UNIFORM_RATE_HZ):
    """The four shock pots on ONE shared uniform grid, as (t, {corner: v}).

    A shared grid matters: roll and pitch are differences between corners,
    so the corners must be sampled at the same instants or the difference
    mixes in a time offset. The grid spans the overlap of all four, since
    they do not start and end at exactly the same timestamp.
    """
    per_corner = {
        corner: uniform_resample(signals[CORNER_SIGNAL_NAMES[corner]],
                                 target_hz=target_hz)
        for corner in CORNERS
    }

    start = max(t[0] for t, _ in per_corner.values())
    end = min(t[-1] for t, _ in per_corner.values())

    step = 1.0 / target_hz
    t = np.arange(start, end + step / 2.0, step)

    return t, {
        corner: np.interp(t, tc, vc)
        for corner, (tc, vc) in per_corner.items()
    }


# ── Vehicle geometry, and wheel travel -> angle ──────────────────────────
#
# These live here for the reason this module exists at all: they were
# previously defined THREE TIMES, in case2 (track widths), case3
# (wheelbase) and case4 (both). The values happened to agree, but nothing
# enforced that — and this file was created precisely because case1 and
# filter_compare had silently drifted onto two different values of G.
#
# The wheelbase disagrees with corner-model/Forces/car_data.py, which says
# 1545mm. 1543 is correct; 1545 is a known error on another branch.
FRONT_TRACK_MM = 1219.2   # centre-to-centre
REAR_TRACK_MM = 1168.4    # centre-to-centre
WHEELBASE_MM = 1543
AVG_TRACK_MM = (FRONT_TRACK_MM + REAR_TRACK_MM) / 2.0


def mm_to_deg(wheel_mm, span_mm):
    """Convert a WHEEL-travel difference (mm) to an angle (deg) about a
    span: track width for roll, wheelbase for pitch.

        angle = atan(wheel_mm / span_mm)

    NOT the small-angle approximation, despite what the case2/case3
    docstrings used to claim. `atan` is the EXACT relation for two vertical
    displacements separated by a horizontal span, so there is no
    approximation here to worry about. (For scale, had it been small-angle:
    the two agree to 0.002% at 10mm and 0.03% at 35mm, so the mislabel
    never changed a number — but it implied a limitation that does not
    exist.)

    Pass WHEEL travel, not raw shock-pot mm — see to_wheel_travel() and the
    motion-ratio comment above.
    """
    return np.degrees(np.arctan(np.asarray(wheel_mm, dtype=float) / span_mm))


# WHOLE-CAR "AVG ROLL" IS AN APPROXIMATION. Converting a mean-mm over a
# mean-track (mm_to_deg(avg_mm, AVG_TRACK_MM)) is not the same as averaging
# two separately-converted angles, because atan is non-linear and the two
# tracks differ by 50.8mm. Measured error is 0.17-0.19% — 1.6201 deg the
# approximate way against 1.6231 deg exact.
#
# Kept as-is deliberately, so published numbers stay comparable to what has
# already been shared. Documented rather than silently corrected. If you
# ever do want the exact figure, average mm_to_deg(front_mm, FRONT_TRACK_MM)
# and mm_to_deg(rear_mm, REAR_TRACK_MM) instead.


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
    static_window = find_static_window(speed, t, lon_g=lon_g_or_none(signals))
    corners, baselines = {}, {}

    raws = {
        corner: np.asarray(signals[CORNER_SIGNAL_NAMES[corner]].value, dtype=float)
        for corner in CORNERS
    }

    # Step glitches are excluded from the baseline window. This does not
    # move the numbers — the median is robust to a step — but it keeps the
    # window clean for anything that later measures spread over it. See
    # static_baseline() for why that distinction cost a whole file's
    # reputation once.
    glitch_mask, _ = find_step_glitches(raws, t)

    for corner in CORNERS:
        raw = raws[corner]
        baseline = static_baseline(raw, t, static_window, bad_mask=glitch_mask)
        baselines[corner] = baseline
        corners[corner] = raw

    baselines_found = all(b is not None for b in baselines.values())
    if not baselines_found:
        baselines = {c: 0.0 for c in CORNERS}
    else:
        corners = {c: corners[c] - baselines[c] for c in CORNERS}
    return corners, baselines, baselines_found
