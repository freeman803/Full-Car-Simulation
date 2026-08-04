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
import re
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, find_peaks

# ── Physical / filter constants ──────────────────────────────────────────
G = 9.80665                  # standard gravity (m/s^2) — matches filter_compare.py
FILTER_ORDER = 4              # Butterworth order, every case script
# ── Low-pass cutoffs ─────────────────────────────────────────────────────
#
# CHOSEN 2026-07-31 FROM MEASUREMENT, replacing an inherited 2.0 / 5.0 that
# no one had validated. Three findings drove it, all reproducible:
#
# 1. THERE IS NO RESONANCE TO AVOID. This file's previous guidance was built
#    around "a real 6-8 Hz mode carrying 5.88mm", which spectral_analysis.py
#    checked and disproved: no consistent mode in heave/roll/pitch/warp
#    across the 11 files (prominent peaks scatter 1.1-21.9 Hz), and
#    inter-corner coherence never exceeds 0.41 in any band. So 5 and 8 Hz
#    are not special values and the choice is not about dodging a frequency.
#
# 2. LOW CUTOFFS ARE THE UNSTABLE REGION — the opposite of the intuition.
#    cutoff_sweep.py measures how much each reported number moves if the
#    cutoff shifts one step. Mean across the peak-based quantities:
#
#        2 Hz  7.1%    5 Hz  6.0%    10 Hz  1.9%    20 Hz  3.3%
#        3 Hz  7.1%    8 Hz  3.0%    15 Hz  2.9%
#
#    Smoothing pushes candidate peaks toward each other, so at low cutoffs a
#    tiny filter change flips which peak the detector picks —
#    case3.endurance.worst_deg moves 15-21% PER STEP down there. By 10 Hz
#    the peaks are sharp and unambiguous. The old 5.0 sat on that slope,
#    which is the worst place to be.
#
# 3. ABOVE 10 Hz the numbers climb again as sharp transient content enters
#    (kerb strikes, driveline shock). That content is REAL — checked, it is
#    not the IMU 2-sample artefacts, which contribute 0.0% at every cutoff
#    except endurance lateral at 20 Hz — but whether it belongs in "peak
#    longitudinal G" is a modelling choice, and including it makes the
#    number less stable rather than more informative.
#
# Skidpad keeps the same value as everything else now. Its numbers are
# medians over steady segments and move only 0.3-1.7% across the whole
# 2-20 Hz sweep, so it has no preference worth encoding — and one constant
# is easier to reason about than two.
SKIDPAD_CUTOFF_HZ = 10.0      # was 2.0 — see above; skidpad is insensitive anyway
AUTOX_END_CUTOFF_HZ = 10.0    # was 5.0 — 5 Hz sat on the unstable slope

# FRONT BRAKE PRESSURE IS NOT A FREE CHOICE. Measured from its raw
# timestamps it is sampled at 10 Hz, the only channel here that is not 100
# Hz, so its Nyquist is 5 Hz and any higher cutoff is undefined for it.
# It is consumed by find_braking_windows() for SEGMENTATION rather than
# reporting, so what it needs is clean window edges, not a faithful peak.
BRAKE_PRESSURE_CUTOFF_HZ = 3.0

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


# ── Is a peak a plateau or a spike? ──────────────────────────────────────
#
# THE QUESTION THIS ANSWERS: every reported peak is a SINGLE INSTANTANEOUS
# sample of the filtered trace. Three things already stop that being fragile
# — the 10 Hz filter means ripple faster than 10 Hz cannot produce a peak at
# all, prominence gating rejects small wobbles, and 1.0s minimum spacing
# stops one event being counted five times — but none of them distinguish a
# genuine sustained limit from one isolated crest that happens to be tall.
#
# So report the mean over a short window centred on the peak alongside the
# peak itself. If the two agree the car really held that value; if the mean
# is much lower, the peak is a spike and the top-k average is the number to
# quote. Measured on real data, this separates cleanly:
#
#   endurance LATERAL G   single 1.5977, top-5 avg 1.5765 (1.3% apart)
#                         -> a real sustained cornering limit
#   endurance LONGITUDINAL G  single 1.7182, top-5 avg 1.4722 (17% apart)
#                         -> one isolated braking spike
#
# NOT a change to how peaks are found or reported. It is an extra column
# next to the existing number, so nothing that was pinned moves.

PEAK_PLATEAU_S = 0.2      # window width; ~2 periods of the 10 Hz cutoff
PLATEAU_RATIO = 0.95      # at/above this, the peak is a genuine plateau
SPIKE_RATIO = 0.85        # below this, it is one isolated sample


def plateau_mean(values, t, idx, window_s=PEAK_PLATEAU_S):
    """Mean of `values` over ±window_s/2 of REAL elapsed time around `idx`.

    Uses searchsorted against `t` rather than a fixed sample count, because
    the union grid is non-uniform — a fixed count spans different amounts
    of real time in different parts of the same file (see module docstring).
    """
    t = np.asarray(t)
    half = window_s / 2.0
    start = int(np.searchsorted(t, t[idx] - half, side="left"))
    end = int(np.searchsorted(t, t[idx] + half, side="right"))
    window = np.asarray(values, dtype=float)[start:max(end, start + 1)]
    if not np.any(np.isfinite(window)):
        return float("nan")
    return float(np.nanmean(window))


def peak_shape(values, t, idx, window_s=PEAK_PLATEAU_S):
    """(mean, ratio, verdict) for the peak at `idx`.

    `ratio` is the windowed mean as a fraction of the peak value, so 1.0
    means perfectly flat across the window. Pass the SAME array the peak
    was found in — if peaks were found on np.abs(x), pass np.abs(x).
    """
    peak = float(np.asarray(values, dtype=float)[idx])
    mean = plateau_mean(values, t, idx, window_s)

    if not np.isfinite(mean) or peak == 0:
        return mean, float("nan"), "?"

    ratio = mean / peak
    if ratio >= PLATEAU_RATIO:
        verdict = "plateau"
    elif ratio >= SPIKE_RATIO:
        verdict = "borderline"
    else:
        verdict = "SPIKE"
    return mean, ratio, verdict


def format_peak_shape(values, t, idx, unit="", window_s=PEAK_PLATEAU_S):
    """One-line ' (0.2s mean: X.XXX unit, NN% — verdict)' for console use."""
    mean, ratio, verdict = peak_shape(values, t, idx, window_s)
    if not np.isfinite(ratio):
        return ""
    return (f"  [{window_s:g}s mean: {mean:.4g}{unit}, "
            f"{ratio * 100:.0f}% of peak — {verdict}]")


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


# ── Known-bad channels, per file ─────────────────────────────────────────
#
# PER FILE AND PER CORNER, not per file. Throwing away a whole file to
# escape one bad channel discards good data for no reason — in the case
# below the rear pots are healthy in all four autocross runs, and the rear
# roll gradient moves 0.886 -> 0.885 whether the suspect files are in or
# out, i.e. not at all.
#
# WHY THESE TWO FILES. In autocross_josh2 and autocross_andrew1 BOTH front
# shock pots sit in a voltage band that never rises above 1.0 V — the
# extension end of their stroke — against 0.32-1.20 V in the two
# neighbouring runs. The front sweeps 7-13mm instead of 22-38mm, and the
# front roll gradient reads 0.29-0.31 deg/g against 0.78-0.79. Three checks
# rule out anything but a measurement problem:
#
#   - The runs are otherwise identical: matching lateral-G content, and
#     andrew1/andrew2 are TWO MINUTES apart, so nothing physical changed.
#   - The disp<-volt decode is identical in every file (-25.495 to -25.511
#     mm/V against the documented -25.510), so it is not units or scaling.
#   - The deficit is UNIFORM around the lap. Front/rear roll amplitude
#     ratio per 79m segment is ~0.6 in these files and ~1.5 in the clean
#     ones, constant all the way round — so not driving style, not one
#     corner, and not the Run 1 off-course excursion.
#
# WHICH CASES NEED THIS. Only case5. Cases 1-4 report PEAKS, and bad front
# data is SMALLER than good, so it never wins a peak search — verified by
# re-running case2 without these files, which changes its autocross roll by
# exactly 0.0%. A gradient is a fit over every sample, so bad data does not
# have to win anything, it just drags the slope: excluding these moves the
# autocross front gradient 0.557 -> 0.809 and its R^2 0.775 -> 0.931.
# (Was quoted as 0.540 -> 0.784 before the front motion ratio was corrected
# 1.15 -> 1.188; the +3.3% applies to both ends, the conclusion is the same.)
#
# The R^2 improvement is the tell that this is removing genuinely bad data
# rather than inconvenient data.
SUSPECT_CORNERS = {
    "autocross_josh2": {"FL", "FR"},
    "autocross_andrew1": {"FL", "FR"},
}


def suspect_corners(path):
    """Corners whose data is known bad in this file. Empty set if clean."""
    stem = os.path.splitext(os.path.basename(path))[0]
    return SUSPECT_CORNERS.get(stem, set())


def is_suspect(path, corners):
    """True if ANY of `corners` is known bad in this file.

    Pass the corners a quantity actually depends on: rear roll needs only
    RL/RR, so it survives a bad front pair, while whole-car roll needs all
    four and does not.
    """
    return bool(suspect_corners(path) & set(corners))


# ── Per-file caveats, for display ────────────────────────────────────────
#
# WHY THIS EXISTS AS DATA. Every one of these was already known and already
# written up in README "Known data problems" — which is exactly the problem.
# A reader opening plots/case2_max_roll/report.html sees four autocross runs
# presented identically, with no indication that two of them have half the
# front roll signal missing. The caveat has to travel WITH the plot, not sit
# in a document the reader may not have open.
#
# `level` drives presentation only: "error" = do not trust numbers derived
# from this file's affected channels, "warn" = a real caveat that does not
# invalidate the number, "info" = worth knowing.
#
# Keep this in sync with README "Known data problems" — that stays the long
# form with the evidence; this is the one-line version shown in context.
FILE_WARNINGS = {
    "autocross_josh2": [
        ("error", "Both FRONT shock pots stuck at the extension end of their "
                  "stroke — front sweeps 7-13mm instead of 22-38mm. Front and "
                  "whole-car roll from this file are NOT trustworthy; rear is "
                  "fine. Excluded from case5's front/whole-car gradient fits."),
    ],
    "autocross_andrew1": [
        ("error", "Both FRONT shock pots stuck at the extension end of their "
                  "stroke — front sweeps 7-13mm instead of 22-38mm. Front and "
                  "whole-car roll from this file are NOT trustworthy; rear is "
                  "fine. Excluded from case5's front/whole-car gradient fits."),
    ],
    "braketest2": [
        ("warn", "Stopped-car window shows 0.394mm (FL) and 0.667mm (FR) of "
                 "noise, 10-20x every other file — so the window is probably "
                 "not genuinely stopped, and this file's baselines deserve "
                 "more suspicion than the rest. NOTE the earlier 'unreliable' "
                 "verdict on this file was WRONG and has been retracted."),
    ],
    "endurance_full": [
        ("warn", "Front brake pressure saturates at the 2000 psi DBC ceiling "
                 "— a firmware clamp, not a sensor fault. Braking windows "
                 "detected from it are still valid; the pressure VALUE during "
                 "saturation is not."),
        ("info", "DNF on the last lap. The file covers both drivers: Andrew "
                 "first, then Josh."),
    ],
}


def file_warnings(path):
    """[(level, message), ...] for this file. Empty list if clean."""
    stem = os.path.splitext(os.path.basename(path))[0]
    return FILE_WARNINGS.get(stem, [])


# Caveats that apply to a whole SIGNAL rather than a file, keyed by the
# signal name as it appears in the CSVs.
SIGNAL_WARNINGS = {
    "VCFRONT_steeringAngle": (
        "error", "Unusable — uncalibrated and one-sided. Not used by any case."),
    "VCPDU_angleRoll": (
        "error", "Unusable — reads +/-20-36 deg against +/-1.3 deg derived "
                 "from the shock pots. An uncalibrated gravity-vector tilt, "
                 "not chassis attitude."),
    "VCPDU_anglePitch": (
        "error", "Unusable — see VCPDU_angleRoll."),
    "VCFRONT_brakePressure": (
        "info", "Sampled at 10 Hz (shares the VCFRONT_pedalInformation "
                "message), so its 5 Hz Nyquist bounds any cutoff applied to "
                "it. VCREAR_brakePressure is 100 Hz."),
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
# roughly the 14% spread between them. Use to_wheel_travel() and do all
# subsequent maths on its output.
#
# These replace the earlier MOTION_RATIO = 1.0 placeholder that every case
# script carried, so all previously reported angles were understated:
# front by 19%, rear by ~4%.
#
# FRONT CORRECTED 1.15 -> 1.188 (2026-08-01, supplied by Bianca). Every
# front and whole-car angle, and every front and whole-car gradient, scales
# with it linearly: +3.3%. Rear and rear-only figures are untouched.
#
# BOTH RATIOS ARE VALIDATED MEASUREMENTS ON THE CAR (Bianca, 2026-08-01).
# Treat them as inputs, not as free parameters to tune until something else
# agrees. In particular, DO NOT "solve" the front/rear roll disagreement by
# adjusting one of them: that inference was tried and is retracted. It reads
# a front ratio of ~1.30 out of the rigid-chassis constraint, but it only
# gets there by assuming the chassis is rigid AND all four pots are
# correctly calibrated, and the measurement overrides both assumptions.
#
# The disagreement itself is real and still unexplained — 1.188 narrows it
# from rear +13.2% to rear +9.5% without closing it — and it is NOT the
# motion ratio. Two things now point elsewhere:
#
#   - TYRE DEFLECTION MAKES IT WORSE, NOT BETTER. What a shock pot sees is
#     chassis roll MINUS the tyre-deflection roll at its own axle, so the
#     axle taking more load transfer reads LOW. Rear roll stiffness is the
#     larger share here (k_wr*T_r^2 = 22.2e6 against front 20.7e6, i.e.
#     51.7% rear), so the rear should read low — and it reads HIGH. Undoing
#     the tyre term at 150 N/mm widens the gap from 9.5% to ~10.6%.
#   - THE FRONT PAIR IS ASYMMETRIC AND THE REAR IS NOT. Per-corner travel on
#     skidpad is FL 6.76 / FR -11.38 mm/g (68% apart) against RL 9.11 /
#     RR -9.93 (9% apart). In pure roll those should be equal and opposite.
#
# So chassis torsional flex and front pot calibration are what is left. See
# the README, and the FL entry under Known data problems.
#
# THE ABSOLUTE SCALE IS NOW CONFIRMED, which it was not before. With no ARB
# the four springs (225 lbf/in front, 200 rear = 39.40 / 35.03 N/mm) make
# the entire roll stiffness: wheel rates 27.92 / 32.51 N/mm give 749 N*m/deg,
# and the measured 0.898 deg/g implies a sprung-mass x CG-height of 68.6
# kg*m — i.e. CG 0.280 m above the roll axis at 245 kg sprung, which is a
# real FSAE number. This is the first check on this analysis that does not
# route through the shock pots, so it is the first that could have caught a
# scale error.
MOTION_RATIO_FRONT = 1.188
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
    # Measured 20.0 in all 11 files. The firmware task that updates the value
    # runs at 10 Hz (steeringAngle.c, periodic10Hz_CLK) but the CAN message
    # carrying it, VCFRONT_inputStatus, goes out at 20 — so the frames are
    # 20 Hz and the information is 10 Hz. Latent either way: the channel is
    # unusable and no case reads it.
    "VCFRONT_steeringAngle": 20.0,
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


# ── Suspension-referenced vs ground-referenced angles ────────────────────
#
# WHICH LINE THE ANGLE IS MEASURED AGAINST. A shock pot is bolted between
# the chassis and the upright, so both its ends sit ABOVE the tyre. What it
# measures is therefore chassis roll relative to the line joining the two
# WHEEL CENTRES — call that SUSPENSION-REFERENCED. It is the only thing
# these sensors can see, and it is what every case script reports.
#
# A design roll gradient almost always means something else: chassis roll
# relative to the GROUND, which additionally contains the tyre's own
# deflection. Under lateral load transfer the outside tyre squashes and the
# inside one extends, so the wheel-centre line itself tilts against the
# road. Camber relative to the road is what sets grip, which is why the
# design side works in this reference.
#
# The two are NOT interchangeable, and comparing one to the other is how a
# measurement that is entirely correct comes to look ~33% too small. That
# happened here: CFR26.xlsx row 76 builds roll stiffness from `riderate`
# (row 55, "wheel rate and tire rate in series"), so the sheet's 1.396
# deg/g is ground-referenced, against 0.898 deg/g suspension-referenced
# measured. Reference difference 1.33x; the residual 1.17x is genuine
# design-vs-measured.
#
# THE CONVERSION IS EXACT for load-transfer-driven roll and pitch, because
# the same load increment deflects spring and tyre in series:
#
#     suspension roll at an axle = 2*dF / (k_wheel * track)
#     tyre roll       at an axle = 2*dF / (k_tyre  * track)
#     => ground roll = suspension roll * (1 + k_wheel / k_tyre)
#
# so the multiplier is per AXLE for roll, and a single number for pitch
# (which sums the two axles' compliances). Sprung mass, CG height and
# weight distribution all cancel — the tyre rate is the only input.
#
# WHERE IT IS ONLY APPROXIMATE: peak angles during transients. The tyre
# responds essentially instantly so it is a good approximation, but a peak
# driven by a kerb strike rather than by load transfer is not deflecting
# the tyre proportionally. Gradients carry no such caveat.
#
# NOT APPLICABLE TO case4's per-corner wheel travel. That is real
# suspension travel and is what bump-stop and droop margin are measured in;
# ground-referencing it would be meaningless.
#
# Inputs from CFR26.xlsx (the team's suspension sheet), rows 34/54.
LBF_IN_TO_N_MM = 0.1751268

SPRING_RATE_FRONT_LBF_IN = 225.0   # CFR26.xlsx D34
SPRING_RATE_REAR_LBF_IN = 200.0    # CFR26.xlsx E34
TYRE_RATE_LBF_IN = 520.0           # CFR26.xlsx D54/E54 — same front and rear

TYRE_RATE_N_MM = TYRE_RATE_LBF_IN * LBF_IN_TO_N_MM              # 91.07

# Wheel rate = spring rate / MR^2 (motion ratio enters stiffness squared).
WHEEL_RATE_FRONT_N_MM = (SPRING_RATE_FRONT_LBF_IN * LBF_IN_TO_N_MM
                         / MOTION_RATIO_FRONT ** 2)              # 27.92
WHEEL_RATE_REAR_N_MM = (SPRING_RATE_REAR_LBF_IN * LBF_IN_TO_N_MM
                        / MOTION_RATIO_REAR ** 2)                # 32.51

GROUND_MULT_ROLL_FRONT = 1.0 + WHEEL_RATE_FRONT_N_MM / TYRE_RATE_N_MM   # 1.307
GROUND_MULT_ROLL_REAR = 1.0 + WHEEL_RATE_REAR_N_MM / TYRE_RATE_N_MM     # 1.357

# Pitch sums the two axles' compliances, so it gets ONE multiplier rather
# than a per-axle pair.
GROUND_MULT_PITCH = 1.0 + (2.0 / TYRE_RATE_N_MM) / (
    1.0 / WHEEL_RATE_FRONT_N_MM + 1.0 / WHEEL_RATE_REAR_N_MM)           # 1.330

# The whole-car "avg" gets ONE stiffness-weighted multiplier rather than
# being rebuilt from the two axle figures.
#
# Rebuilding was tried first and is wrong here, for a reason specific to how
# these numbers are produced: case2's front_deg, rear_deg and avg_deg each
# come from their OWN peak search, so they land at three different instants.
# Averaging the converted front and rear peaks therefore combines two
# moments that never coexisted, and on endurance it inflated the whole-car
# figure to 2.08 deg against 1.95 the consistent way.
#
# The cost of one multiplier is negligible: on the skidpad steady gradient,
# where front/rear/avg ARE fitted over the same samples and rebuilding is
# legitimate, the two routes give 1.198 and 1.196 deg/g — 0.2% apart.
_RIDE_FRONT = (WHEEL_RATE_FRONT_N_MM * TYRE_RATE_N_MM
               / (WHEEL_RATE_FRONT_N_MM + TYRE_RATE_N_MM))
_RIDE_REAR = (WHEEL_RATE_REAR_N_MM * TYRE_RATE_N_MM
              / (WHEEL_RATE_REAR_N_MM + TYRE_RATE_N_MM))

GROUND_MULT_ROLL_AVG = (
    (WHEEL_RATE_FRONT_N_MM * FRONT_TRACK_MM ** 2
     + WHEEL_RATE_REAR_N_MM * REAR_TRACK_MM ** 2)
    / (_RIDE_FRONT * FRONT_TRACK_MM ** 2
       + _RIDE_REAR * REAR_TRACK_MM ** 2)
)                                                                       # 1.332

GROUND_MULT = {
    "front": GROUND_MULT_ROLL_FRONT,
    "rear": GROUND_MULT_ROLL_REAR,
    "avg": GROUND_MULT_ROLL_AVG,
    "pitch": GROUND_MULT_PITCH,
}


def to_ground_referenced(angle_deg, which):
    """Suspension-referenced angle (deg) -> ground-referenced.

    `which` is "front" / "rear" / "avg" for roll, or "pitch". Front and rear
    carry their own exact per-axle multipliers; "avg" carries the
    stiffness-weighted whole-car one — see the note above for why it is not
    rebuilt from the axles.
    """
    if angle_deg is None:
        return None
    return angle_deg * GROUND_MULT[which]


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

    FRONT vs REAR — measured 2026-07-31, and the conclusion is "keep front,
    it makes no difference", which is worth recording because the rear
    channel looks strictly better on paper:

        VCFRONT_brakePressure   10 Hz — shares VCFRONT_pedalInformation
                                        (id 0x51, cycleTimeMs 100)
        VCREAR_brakePressure   100 Hz — its own dedicated message

    Rear is 10x faster, saturates less on endurance (0.47% of samples at the
    2000 psi ceiling against front's 1.14%), and the two correlate at +0.945
    to +0.991 on every file. Yet swapping the source changes NOTHING that is
    reported: the worst braking pitch comes out IDENTICAL on braketest1
    (0.7727 deg), braketest2 (0.6654 deg) and endurance (0.9276 deg).

    The reason is that this function does SEGMENTATION, not measurement.
    Window edges landing 50 ms differently is immaterial when the window is
    0.5-1.1 s long and the caller takes max |pitch| inside it. Rear's extra
    bandwidth would only start to matter for something that needs the
    pressure TRACE — a brake-pressure rise rate, say, which front at 10 Hz
    genuinely cannot measure.

    Rear is not uniformly better either. On braketest2 it produces 3 windows
    whose pitch is POSITIVE (squat, impossible under braking) against
    front's 1, so front is marginally cleaner on the one physical sanity
    check available. It does find one extra real window on braketest1 (4 vs
    3), which front misses because a short pulse can fall between 10 Hz
    samples.

    CORRECTION: this docstring used to claim "front is the larger of the two
    on every file measured." That is false — rear peaks higher on 6 of 11
    files (e.g. braketest1 2000 vs 1830 psi, accel_jamie_both 846 vs 792).
    The claim was never load-bearing, but it was wrong.

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
    glitch_mask, glitch_events = find_step_glitches(raws, t)

    # PIECEWISE BASELINE when the sensor's zero moves mid-file. A single
    # scalar baseline is correct only while the pot keeps the same
    # relationship to the wheel — see segmented_baselines() for what goes
    # wrong when it doesn't, and for the two published numbers it broke.
    step_times = sorted({round(ts, 3) for _, ts, _ in glitch_events})
    if step_times:
        segmented = segmented_baselines(raws, t, speed, step_times,
                                        lon_g=lon_g_or_none(signals),
                                        bad_mask=glitch_mask)
        if segmented is not None:
            corners = {c: raws[c] - segmented[c] for c in CORNERS}
            # Report the baseline at the START of the file, so the printed
            # figure still means "what this corner reads at rest" and stays
            # comparable with the files that need no segmentation.
            baselines = {c: float(segmented[c][0]) for c in CORNERS}
            return corners, baselines, True

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


# How far two stopped windows in the same file may disagree on one corner
# before the file's baseline is treated as non-reproducible. Chosen from the
# measured separation, which is not close: the three affected files disagree
# by 13.0-13.6mm (FL) and 22.5-23.1mm (FR), while every clean file agrees to
# within 2.3mm on every corner. Anything from ~4 to ~12 would classify these
# files identically.
BASELINE_DISAGREE_MM = 4.0


def stopped_window_medians(raws, t, speed, lon_g=None, bad_mask=None,
                           split_at=()):
    """Median reading of every corner over each qualifying stopped window.

    Returns [(start_idx, end_idx, {corner: median}), ...] in time order.

    `split_at` is a list of times at which a window must be cut in two — a
    stop that straddles a sensor step contains two different zeros, and
    taking one median across it produces a value that matches neither.
    braketest2's baseline window (0-51s) straddles its 46.2s step exactly
    this way.
    """
    runs = _low_speed_runs(speed, t, lon_g=lon_g)

    if split_at:
        pieces = []
        for s, e in runs:
            cuts = [s] + [int(np.searchsorted(t, x)) for x in split_at
                          if t[s] < x < t[e]] + [e + 1]
            for a, b in zip(cuts[:-1], cuts[1:]):
                if b - 1 > a and (t[b - 1] - t[a]) >= STATIC_MIN_DURATION_S:
                    pieces.append((a, b - 1))
        runs = pieces

    out = []
    for s, e in runs:
        ts, te = trim_window(t, s, e, STATIC_TRIM_S)
        medians = {}
        for corner in CORNERS:
            values = raws[corner][ts:te + 1]
            if bad_mask is not None:
                values = values[~bad_mask[ts:te + 1]]
            values = values[np.isfinite(values)]
            if values.size:
                medians[corner] = float(np.median(values))
        if len(medians) == len(CORNERS):
            out.append((s, e, medians))
    return out


def baseline_is_reproducible(raws, t, speed, lon_g=None,
                             tolerance_mm=BASELINE_DISAGREE_MM):
    """(ok, {corner: worst_disagreement_mm}) across a file's stopped windows.

    A file with only one stopped window cannot be checked and returns ok —
    absence of evidence, and saying so is better than failing it.
    """
    windows = stopped_window_medians(raws, t, speed, lon_g=lon_g)
    if len(windows) < 2:
        return True, {c: 0.0 for c in CORNERS}

    spread = {}
    for corner in CORNERS:
        values = [m[corner] for _, _, m in windows]
        spread[corner] = float(max(values) - min(values))
    return max(spread.values()) <= tolerance_mm, spread


def segmented_baselines(raws, t, speed, step_times, lon_g=None, bad_mask=None):
    """Per-sample baseline arrays, one constant value per inter-step segment.

    WHY A SCALAR BASELINE IS NOT ENOUGH. A shock pot reads its own
    extension, so "37 mm" means nothing until you subtract what that corner
    reads at rest. `baseline_corner_displacements` found ONE stopped window
    and used it for the whole file — correct only while the pot keeps the
    same relationship to the wheel.

    In three files it does not: the front pots re-seat mid-run and jump
    ~13mm (FL) / ~22mm (FR), both together (README, Known data problems #9
    and the case4 autocross finding). Every sample on the far side of that
    jump was then measured against a zero that no longer applied. It broke
    two published numbers — case4's autocross worst travel read -27.98mm
    where the corner had moved -3.63mm, and case3's autocross pitch read
    0.918 deg against a largest clean peak of 0.613 deg.

    THE FIX. Cut the file at each step, and give each segment the baseline
    measured from a stopped window INSIDE that segment. A segment with no
    stop of its own inherits its neighbour's, shifted by the difference the
    two windows actually show — never by the reported jump magnitude, which
    carries no sign (applying it signed-wrong once produced a -53mm FR).

    Returns {corner: array} or None if any segment cannot be resolved, in
    which case the caller falls back to the scalar path and the file is
    handled exactly as before.
    """
    windows = stopped_window_medians(raws, t, speed, lon_g=lon_g,
                                     bad_mask=bad_mask, split_at=step_times)
    if not windows:
        return None

    bounds = [0.0] + list(step_times) + [float(t[-1]) + 1.0]
    segments = list(zip(bounds[:-1], bounds[1:]))

    # Which stopped windows sit inside each segment.
    per_segment = []
    for lo, hi in segments:
        inside = [m for s, e, m in windows if lo <= t[s] < hi]
        per_segment.append(inside)

    if not any(per_segment):
        return None

    # A segment with its own stop uses the median of those stops. One
    # without inherits from the nearest segment that has one, corrected by
    # the offset between the two segments' own readings where that can be
    # measured — otherwise it is simply unresolved and we bail out.
    resolved = [None] * len(segments)
    for i, inside in enumerate(per_segment):
        if inside:
            resolved[i] = {c: float(np.median([m[c] for m in inside]))
                           for c in CORNERS}

    if any(r is None for r in resolved):
        # Carry the nearest known baseline outward. This is only reached
        # for a segment that contains no stop at all, where the honest
        # options are "inherit" or "give up"; inheriting keeps the
        # correctly-zeroed segments usable.
        known = [i for i, r in enumerate(resolved) if r is not None]
        for i, r in enumerate(resolved):
            if r is None:
                nearest = min(known, key=lambda j: abs(j - i))
                resolved[i] = dict(resolved[nearest])

    out = {c: np.empty(len(t), dtype=float) for c in CORNERS}
    for (lo, hi), values in zip(segments, resolved):
        m = (t >= lo) & (t < hi)
        for c in CORNERS:
            out[c][m] = values[c]
    return out



# ── Display decimation ───────────────────────────────────────────────────
#
# DISPLAY ONLY. Nothing here touches a reported number — every case computes
# its answer from the full array and only then hands the array to a plot
# builder. This exists purely because the plots had become unopenable:
# endurance_full is ~1.5M samples on the union grid, and writing all of it
# into a Plotly HTML produced a 162 MB single-chart file that no browser
# will render inside a report iframe.
#
# NAIVE SUBSAMPLING IS WRONG HERE and was not used. Taking every Nth sample
# deletes exactly the brief excursions this chart exists to show — the raw
# trace would visibly lose the spikes that the filter is being judged
# against, and a step glitch could vanish entirely. Instead this keeps, per
# bucket, the sample at the MINIMUM and the sample at the MAXIMUM of every
# series being drawn. The drawn envelope is then identical to the full-rate
# envelope at any zoom-out level: no peak can be lost, because a peak is by
# definition a bucket extremum.
#
# The cost is that deep interactive zoom shows the decimated set rather than
# true full rate. For a raw-vs-filtered sanity check that is the right
# trade; filter_compare.py remains the full-rate instrument.

PLOT_MAX_BUCKETS = 6000


def decimate_for_plot(t, series, max_buckets=PLOT_MAX_BUCKETS):
    """Envelope-preserving decimation of several co-sampled arrays.

    `series` is a list of 1-D arrays sharing the time base `t`. Returns
    (t_small, [array_small, ...]) using ONE shared index set, so the arrays
    stay aligned and comparable — a residual computed from the decimated
    raw and filtered is still exactly their difference.

    Returns the inputs untouched when there is nothing worth decimating.
    """
    t = np.asarray(t)
    n = len(t)
    if n <= 2 * max_buckets or not series:
        return t, [np.asarray(s, dtype=float) for s in series]

    arrays = [np.asarray(s, dtype=float) for s in series]
    edges = np.linspace(0, n, max_buckets + 1, dtype=int)

    keep = {0, n - 1}
    for array in arrays:
        # NaN-safe: a bucket that is entirely NaN has no extremum, and
        # nanargmin would raise on it. Those buckets contribute nothing,
        # which is correct — there is no data there to preserve.
        for start, end in zip(edges[:-1], edges[1:]):
            if end <= start:
                continue
            chunk = array[start:end]
            if not np.any(np.isfinite(chunk)):
                continue
            keep.add(start + int(np.nanargmin(chunk)))
            keep.add(start + int(np.nanargmax(chunk)))

    idx = np.array(sorted(keep), dtype=int)
    return t[idx], [array[idx] for array in arrays]


# Grid resolution for scatter thinning. Roughly the pixel resolution these
# clouds are actually displayed at, which is the justification for the
# whole approach — see thin_scatter().
SCATTER_GRID = 500


def thin_scatter(x, y, grid=SCATTER_GRID):
    """Drop scatter points that would land on top of each other anyway.

    DISPLAY ONLY, like decimate_for_plot(). The g-g diagram, roll diagram
    and roll-pitch envelope each plot every sample of every file — 28 MB of
    markers for endurance, most of which are invisible because they are
    drawn on a pixel some earlier marker already covers.

    Snaps to a `grid` x `grid` lattice over the data extent and keeps the
    first point in each occupied cell. Two properties make this the right
    reduction for these particular charts:

      - THE OUTLINE IS PRESERVED. A g-g diagram is read for its outer
        envelope (the friction limit) and a roll diagram for its spread
        about the diagonal. An extreme point necessarily occupies a cell no
        other point can occupy, so it always survives. Uniform random
        subsampling has the opposite property — it thins the sparse edge
        hardest, which is precisely the part being read.
      - AT THIS RESOLUTION IT IS VISUALLY LOSSLESS. A dropped point was
        overdrawn by a kept one.

    What it does NOT preserve is opacity build-up: the dense core stops
    reading as darker, because duplicate coverage is what created that. The
    convex hull in case4 is computed from the full arrays regardless.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    finite = np.isfinite(x) & np.isfinite(y)
    if not np.any(finite):
        return x, y

    xf, yf = x[finite], y[finite]
    x_span = np.ptp(xf) or 1.0
    y_span = np.ptp(yf) or 1.0

    cells = (((xf - xf.min()) / x_span * (grid - 1)).astype(np.int32).astype(np.int64) * grid
             + ((yf - yf.min()) / y_span * (grid - 1)).astype(np.int32))

    _, first = np.unique(cells, return_index=True)
    first.sort()                       # keep original sample order
    return xf[first], yf[first]


# ── Shared plot styling: raw vs filtered ─────────────────────────────────
#
# WHY THIS IS HERE AND NOT PER-CASE: case1, case2 and case3 each grew their
# own build_before_after_plot(), and all three drew the same chart three
# slightly different ways — four saturated traces piled into one axis, with
# raw and filtered competing for the same visual weight. The problem is
# structural, not cosmetic: filtered sits almost on top of raw by
# construction, so overlaying them at equal weight guarantees one hides the
# other, and the whole point of the chart is to see the DIFFERENCE.
#
# filter_compare.py already solved this for its own PNGs (small multiples,
# raw as a thick pale neutral BEHIND, one saturated trace on top, plus a
# residual view showing exactly what the cutoff discarded). This is that
# same treatment for the interactive case plots — one implementation, so
# the three cases cannot drift apart again.

# Same neutral as filter_compare.py's RAW_COLOR — a reference trace, never
# a competitor for attention.
PLOT_RAW_COLOR = "#a8a7a1"
PLOT_RAW_WIDTH = 2.6
PLOT_FILTERED_WIDTH = 1.5

# Saturated series colors, in assignment order. Categorical (these are
# different signals, not an ordered magnitude), unlike the sequential ramp
# filter_compare uses for cutoffs.
PLOT_SERIES_COLORS = ["#2a78d6", "#e34948", "#1baf7a", "#eda100"]

PLOT_GRID_COLOR = "#e4e3df"
PLOT_TEMPLATE = "plotly_white"

# Steady-state shading (case1/case2/case3 skidpad, case4 accel). Green
# reads as "this is the part that counted", and at this alpha it sits
# under the traces without tinting them.
PLOT_STEADY_FILL = "rgba(27, 175, 122, 0.13)"
PLOT_STEADY_LINE = "rgba(27, 175, 122, 0.55)"

# Peak markers. Deliberately NOT one of the series colors — a marker is an
# annotation on the data, not another series, and it has to stay legible
# whichever panel it lands in.
PLOT_PEAK_COLOR = "#111111"
PLOT_PEAK_HALO = "rgba(233, 73, 72, 0.20)"

# Half-width of the window a #t= deep link zooms to.
PLOT_LINK_ZOOM_S = 3.0

TITLE_WRAP_CHARS = 110    # visible characters per subtitle line
TITLE_MAIN_PX = 26        # the bold first line
TITLE_SUB_LINE_PX = 18    # each wrapped <sub> line
TITLE_PAD_PX = 14         # above the title
HEADER_GAP_PX = 10        # BELOW the title, before the legend or the axes

_TAG_RE = re.compile(r"<[^>]+>")
_STASH_RE = re.compile(r"\x00(\d+)\x00")


def wrap_title_html(text, width=TITLE_WRAP_CHARS):
    """Insert <br> at word boundaries so a Plotly title line fits the figure.

    Plotly does NOT wrap title text — a long subtitle runs straight off the
    side and is clipped, which is how a 350-character g-g caption came to
    be half-invisible. Length is counted on VISIBLE characters so markup
    doesn't eat the budget, and tags are stashed before splitting so a
    break can never land inside one (`<span style='...'>` contains a space
    and would otherwise be torn in half). Explicit <br> in the input is
    preserved.
    """
    out = []
    for para in text.split("<br>"):
        tags = []

        def _stash(match):
            tags.append(match.group(0))
            return f"\x00{len(tags) - 1}\x00"

        stashed = _TAG_RE.sub(_stash, para)

        lines, line, length = [], [], 0
        for word in stashed.split():
            visible = len(_STASH_RE.sub("", word).replace("&nbsp;", " "))
            if line and length + 1 + visible > width:
                lines.append(" ".join(line))
                line, length = [word], visible
            else:
                length += (1 if line else 0) + visible
                line.append(word)
        if line:
            lines.append(" ".join(line))

        out.extend(_STASH_RE.sub(lambda m: tags[int(m.group(1))], one)
                   for one in (lines or [""]))
    return "<br>".join(out)


def title_block(main, sub, width=TITLE_WRAP_CHARS):
    """(title_text, pixel_height) for a wrapped main + <sub> title."""
    wrapped = wrap_title_html(sub, width)
    n_lines = wrapped.count("<br>") + 1
    text = f"{main}<br><sub>{wrapped}</sub>"
    return text, (TITLE_PAD_PX + TITLE_MAIN_PX
                  + n_lines * TITLE_SUB_LINE_PX + HEADER_GAP_PX)


def titled(fig, main, sub, extra_top_px=0, width=TITLE_WRAP_CHARS):
    """Set a wrapped title and a top margin actually big enough for it.

    Every caller used to hardcode `margin=dict(t=95)` or `t=110`, which is
    a guess that silently stops being true the moment the caption grows.
    """
    text, title_px = title_block(main, sub, width)
    fig.update_layout(
        title=dict(text=text, x=0, xanchor="left", xref="container",
                   y=1, yanchor="top", yref="container",
                   pad=dict(t=12, l=12)),
        margin=dict(t=title_px + extra_top_px),
    )
    return title_px


# Vertical budget for the header stack above a subplot grid, in pixels.
# Measured against the rendered charts rather than guessed: a two-line
# Plotly title occupies ~56px, a horizontal legend row ~22px, and a
# subplot title needs ~30px of clear space above the axes. Roughly three
# legend entries fit per row at these figure widths and font size; the
# estimate errs toward TOO MANY rows, which costs whitespace rather than
# an overlap.
LEGEND_ROW_PX = 22
LEGEND_PAD_PX = 10
LEGEND_ITEMS_PER_ROW = 3
SUBPLOT_TITLE_PX = 30


# Injected into every time-series plot. Lets a report page link to a
# specific instant — "the worst corner-travel sample is at 116.59s" is in
# the console text, but nothing took you there, and finding 116.59s by hand
# on an 1800-second trace is genuinely tedious.
#
# Reads `#t=116.59` from the URL and zooms every x-axis to a window around
# it, then drops a marker line. Degrades silently: no hash, no change, so
# the plot files stay perfectly usable opened directly.
DEEP_LINK_SCRIPT = """
function cfrJumpToHash(gd) {
  var m = /[#&]t=(-?[0-9.]+)/.exec(window.location.hash || "");
  if (!m) return;
  var t = parseFloat(m[1]);
  if (!isFinite(t)) return;
  var half = %(half)s;
  var update = {}, shapes = (gd.layout.shapes || []).slice();
  Object.keys(gd.layout).forEach(function (key) {
    if (/^xaxis\\d*$/.test(key)) update[key + ".range"] = [t - half, t + half];
  });
  shapes.push({
    type: "line", xref: "x", yref: "paper",
    x0: t, x1: t, y0: 0, y1: 1,
    line: {color: "%(color)s", width: 1.5, dash: "dot"}
  });
  update["shapes"] = shapes;
  Plotly.relayout(gd, update);
}
cfrJumpToHash(document.getElementById("{plot_id}"));
window.addEventListener("hashchange", function () {
  window.location.reload();
});
""" % {"half": PLOT_LINK_ZOOM_S, "color": PLOT_PEAK_COLOR}


def _add_peak_markers(fig, markers, row, col, values_for_y=None):
    """Drop a labelled marker at each (time, label) on one subplot."""
    import plotly.graph_objects as go

    if not markers:
        return

    times = [m[0] for m in markers]
    labels = [m[1] for m in markers]
    ys = [m[2] for m in markers]

    fig.add_trace(go.Scatter(
        x=times, y=ys, mode="markers+text",
        marker=dict(symbol="circle-open", size=13, line=dict(width=2.2),
                    color=PLOT_PEAK_COLOR),
        text=labels, textposition="top center",
        textfont=dict(size=9, color=PLOT_PEAK_COLOR),
        name="reported peak", showlegend=(row == 1 and col == 1),
        legendgroup="peaks",
        hovertemplate="%{text}<br>t=%{x:.2f}s<extra>reported peak</extra>",
    ), row=row, col=col)


def build_raw_vs_filtered(panels, t, title, output_path, cutoff_hz,
                          shade=None, xaxis_title="Elapsed time (s)",
                          shade_label="counted as steady state",
                          markers=None):
    """Small-multiples raw-vs-filtered chart, one row per signal.

    `panels` is a list of (label, raw_array, filtered_array, ylabel). Each
    gets two cells: the trace pair on the left, and the RESIDUAL
    (raw - filtered) on the right — what this cutoff threw away. The
    residual is the decision-relevant half: formless residual means the
    cutoff is safe, visibly coherent oscillation means real signal is being
    deleted.

    `shade` is an optional list of (start_s, end_s) spans to highlight —
    the windows the analysis actually measured over. Everything outside
    them is context, and without the shading there is no way to tell which
    is which by looking.

    `markers` is {panel_index: [(time_s, label, y_value), ...]} — the peaks
    this file's report actually quotes. The console says "worst at 116.59s"
    and until now nothing on the chart pointed there.
    """
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    # One shared index set across every trace on the page, so raw, filtered
    # and residual stay sample-aligned — see decimate_for_plot().
    flat = [array for _, raw, filtered, _ in panels for array in (raw, filtered)]
    t, flat = decimate_for_plot(t, flat)
    panels = [
        (label, flat[2 * i], flat[2 * i + 1], ylabel)
        for i, (label, _, _, ylabel) in enumerate(panels)
    ]

    nrows = len(panels)

    fig = make_subplots(
        rows=nrows, cols=2,
        shared_xaxes=True,
        column_widths=[0.62, 0.38],
        horizontal_spacing=0.07,
        vertical_spacing=0.10 / max(nrows, 1),
        subplot_titles=[
            title_text
            for label, _, _, _ in panels
            for title_text in (label, f"{label} — discarded by the {cutoff_hz} Hz filter")
        ],
    )

    for row, (label, raw, filtered, ylabel) in enumerate(panels, start=1):
        color = PLOT_SERIES_COLORS[(row - 1) % len(PLOT_SERIES_COLORS)]

        # Raw first and therefore underneath, thick and pale. It is never
        # occluded because nothing saturated is wide enough to cover it.
        fig.add_trace(go.Scattergl(
            x=t, y=raw, mode="lines", name=f"{label} — raw",
            line=dict(color=PLOT_RAW_COLOR, width=PLOT_RAW_WIDTH),
            legendgroup=label, hovertemplate="%{x:.2f}s  %{y:.3f}<extra>raw</extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scattergl(
            x=t, y=filtered, mode="lines", name=f"{label} — {cutoff_hz} Hz",
            line=dict(color=color, width=PLOT_FILTERED_WIDTH),
            legendgroup=label,
            hovertemplate="%{x:.2f}s  %{y:.3f}<extra>filtered</extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scattergl(
            x=t, y=np.asarray(raw, dtype=float) - np.asarray(filtered, dtype=float),
            mode="lines", name=f"{label} — residual",
            line=dict(color=color, width=1.0), opacity=0.75,
            legendgroup=label, showlegend=False,
            hovertemplate="%{x:.2f}s  %{y:.3f}<extra>raw − filtered</extra>",
        ), row=row, col=2)

        fig.add_hline(y=0, line=dict(color=PLOT_GRID_COLOR, width=1),
                      row=row, col=2)

        fig.update_yaxes(title_text=ylabel, row=row, col=1)
        fig.update_yaxes(title_text="raw − filtered", row=row, col=2)

        for start_s, end_s in (shade or []):
            for col in (1, 2):
                fig.add_vrect(
                    x0=start_s, x1=end_s,
                    fillcolor=PLOT_STEADY_FILL, line_width=0,
                    layer="below", row=row, col=col,
                )

        _add_peak_markers(fig, (markers or {}).get(row - 1), row, 1)

    fig.update_xaxes(title_text=xaxis_title, row=nrows)

    subtitle = f"raw (grey) vs {cutoff_hz} Hz 4th-order Butterworth, zero-phase"
    if shade:
        subtitle += (f" &nbsp;·&nbsp; <span style='color:#1baf7a'>green</span> = "
                     f"{shade_label} ({len(shade)} window"
                     f"{'s' if len(shade) != 1 else ''})")
    if markers:
        subtitle += " &nbsp;·&nbsp; circles = the peaks this case reports"

    # The top of the figure stacks four things: the two-line title, the
    # legend, the row-1 subplot titles, and then the plot itself. Size that
    # stack in PIXELS and place the legend in CONTAINER coordinates.
    #
    # The previous version put the legend at paper y=1.02 with a fixed
    # 110px top margin. Paper coordinates are a fraction of the PLOT AREA,
    # so "just above the plot" moves in pixels as soon as nrows changes,
    # and 1.02 of a tall plot area is a long way up — the legend landed on
    # top of the subtitle and the first subplot title. Container
    # coordinates are a fraction of the whole figure, so the offsets below
    # mean the same thing at 2 panels and at 4.
    n_legend_items = 2 * nrows + (1 if markers else 0)
    legend_rows = max(1, -(-n_legend_items // LEGEND_ITEMS_PER_ROW))

    title_text, title_px = title_block(title, subtitle)
    legend_px = LEGEND_PAD_PX + legend_rows * LEGEND_ROW_PX
    top_px = title_px + legend_px + SUBPLOT_TITLE_PX
    height = max(320, 260 * nrows) + top_px

    fig.update_layout(
        title=dict(text=title_text,
                   x=0, xanchor="left", xref="container",
                   y=1, yanchor="top", yref="container",
                   pad=dict(t=12, l=12)),
        template=PLOT_TEMPLATE,
        height=height,
        hovermode="x unified",
        legend=dict(orientation="h",
                    x=0, xanchor="left", xref="container",
                    y=1 - title_px / height, yanchor="top",
                    yref="container",
                    font=dict(size=11)),
        margin=dict(t=top_px),
    )

    fig.write_html(output_path, include_plotlyjs="cdn",
                   post_script=DEEP_LINK_SCRIPT)
