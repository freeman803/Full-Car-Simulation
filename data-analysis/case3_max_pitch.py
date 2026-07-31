# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
case3_max_pitch.py — Case 3: max pitch angle, for ACCEL, BRAKE, SKIDPAD,
AUTOCROSS, and ENDURANCE (kept separate), derived from the same 4 shock-pot
linear-displacement signals case2_max_roll.py uses.

Pitch, per sample:
    pitch_mm = avg(shockpotdispFL, shockpotdispFR) - avg(shockpotdispRL, shockpotdispRR)

SIGN CONVENTION — verified empirically against vehicle speed, not assumed:
checking VCFRONT_vehicleSpeed during real accel/brake windows showed
negative VCPDU_lon <-> speeding up (accelerating), positive VCPDU_lon <->
slowing down (braking). Cross-referencing pitch_mm against those same
windows shows pitch_mm is POSITIVE during acceleration and NEGATIVE during
braking. That means, on this car's shockpot calibration, a HIGHER mm
reading is more EXTENSION (droop), not more compression — acceleration
squats the rear (rear compresses -> rear mm drops -> front-avg minus
rear-avg goes UP) and dives the front under braking (front compresses ->
front mm drops -> front-avg minus rear-avg goes DOWN). So:
    pitch_mm > 0  ~ the orientation seen under ACCELERATION (squat)
    pitch_mm < 0  ~ the orientation seen under BRAKING (dive)
This is the opposite of the "positive = nose-down" convention you might
guess at from the formula alone — called out here so it isn't silently
misread later.

mm -> degrees via atan (EXACT for this geometry — not the small-angle
approximation this line used to claim; same form as case2's roll conversion). NOTE the
motion ratio is applied PER CORNER first, because front and rear differ
(1.15 vs 1.038) — so the axle averages above are already WHEEL travel:
    pitch_mm  = avg(wheel FL, wheel FR) - avg(wheel RL, wheel RR)
    pitch_deg = atan(pitch_mm / WHEELBASE_MM) * 180/pi

Detecting WHEN the car is accelerating uses VCPDU_lon directly, never a
derivative of VCFRONT_vehicleSpeed: speed cannot be differentiated on this
time grid (measured dv/dt reaches 9-13 g and stays there at the 99th
percentile, and low-passing to 0.2 Hz still leaves 5-6 g, because speed is
quantised at 0.01 m/s while grid intervals are sub-millisecond). Speed is
used only as a coarse gate — stopped-car detection, and the braking speed
gate below.

Filtering is IDENTICAL to case1/case2 (imported from case_common, not
redefined here): 4th-order Butterworth, filtfilt, 10 Hz for every event
(3 Hz for front brake pressure, which is sampled at 10 Hz so its Nyquist is
5 Hz). Retuned 2026-07-31 from cutoff_sweep.py — see the README.

Methodology per event (verified against real data before picking each one
— see the session this was built in):
- SKIDPAD (10 Hz low-pass): reuses the exact same lateral-G steady-segment
  windows case1/case2 use. Reports MEDIAN pitch over each segment's
  trimmed middle. Expected to be near-zero (skidpad is constant-speed
  cornering, minimal longitudinal load transfer) — reported for
  completeness / as a sanity check, same "one steady number, no separate
  peak" treatment as case2 gives skidpad roll.

- ACCEL (10 Hz low-pass): "quasi-steady" per request — verified this is
  real: accel files contain one continuous ~4s accelerating pull (not a
  series of short spikes), found via longitudinal-G steady-segment
  detection (same segment-finder as skidpad, applied to lon G instead of
  lat G), restricted to the NEGATIVE-lon-G runs (accelerating — see sign
  convention above; accel files also contain a short braking phase at the
  end, which is deliberately excluded here since that's not the event
  being measured). Reports MEDIAN pitch over the trimmed window(s), same
  single-number treatment as skidpad.

- BRAKE (10 Hz low-pass, brake pressure at 3 Hz): braking windows come from FRONT BRAKE PRESSURE
  (>100 psi) AND vehicle speed (>3 m/s), via
  case_common.find_braking_windows() — not from thresholding longitudinal
  G. Pressure is the driver's actual input; lon G is only the result of it
  and also responds to drivetrain drag, downshifts and gradient.

  BOTH gates are needed. Pressure alone gave a single 30.3-second
  "braking window" in braketest1 (the driver holding the pedal at a
  standstill) and several windows whose pitch came out POSITIVE — squat,
  which cannot happen under braking. Adding the speed gate cut braketest1
  from 10 windows to 3 and braketest2 from 30 to 23, and every surviving
  window now has NEGATIVE pitch (dive), consistent with the sign
  convention above. That 100% sign agreement is independent evidence the
  detection is correct. Surviving pulse durations are 0.31-2.43s, matching
  the 0.7-3.0s originally measured for real braking pulses.

  Within each window the single worst |pitch| instant is taken (a
  window-local peak, not a blind whole-file peak search) — pooled across
  all braking windows in all brake files, top 5 averaged + single highest
  reported, matching case1/case2's transient-event reporting style.

  CAUTION: endurance_full.csv saturates its brake-pressure channel at the
  DBC ceiling of 2000 psi, so pressure-derived numbers there are floors.

- AUTOCROSS / ENDURANCE (10 Hz low-pass): continuous mixed driving, no
  single "the maneuver" to isolate — same blind whole-file peak detection
  on |pitch| as case1/case2 use for G's/roll (prominence + minimum
  spacing), top 5 pooled across files + single highest.

Outputs (all under plots/case3_max_pitch/):
- Console report per event.
- One before/after low-pass filter plot per file -> <event>/<file>_pitch_before_after.html
- ONE headline chart across all 5 events: pitch_angle_summary.html

Run it:
    uv run case3_max_pitch.py --dir comp2026_data

Uses parse_influx.py and case_common.py (must be in the same folder, or
importable). Vehicle geometry constants below are plain hardcoded values —
deliberately NOT imported from corner-model/ (kept independent of that or
any other simulation model, same as case2).
"""

import os
import sys
import glob
import argparse
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from parse_influx import parse_influx
from case_report import report_page, write_index
from case_common import (
    G,
    FILTER_ORDER, SKIDPAD_CUTOFF_HZ, AUTOX_END_CUTOFF_HZ,
    group_by_event,
    lowpass, elapsed_seconds, trim_window,
    find_steady_segments, top_k_peaks,
    find_static_window, static_baseline, to_wheel_travel,
    MOTION_RATIO_FRONT, MOTION_RATIO_REAR,
    find_braking_windows, BRAKE_PRESSURE_SIGNALS, BRAKE_PRESSURE_MAX_PSI,
    BRAKING_PRESSURE_PSI, BRAKE_PRESSURE_CUTOFF_HZ,
    TRIM_SECONDS, TOP_K_PEAKS,
    WHEELBASE_MM, mm_to_deg,
)

# Vehicle geometry and the mm -> degree conversion now come from
# case_common too. They used to be redefined here, in case2 and in case4;
# the values agreed, but nothing enforced it.

# Motion ratio comes from case_common (measured: 1.15 front, 1.038 rear,
# wheel/spring displacement), applied PER CORNER via to_wheel_travel()
# before front_avg - rear_avg is taken. This ordering matters here more than
# anywhere else: pitch IS the front-minus-rear difference, so applying a
# single blended ratio afterwards would be wrong by roughly the 11% spread
# between the two. Everything below works in WHEEL millimetres. Replaces an
# earlier 1:1 placeholder that understated pitch by ~9%.

# Longitudinal-G threshold for "accelerating hard" / "braking hard",
# mirroring case_common's MIN_LAT_G_FOR_TURN (same magnitude, same idea,
# just keyed on lon G instead of lat G).
MIN_LON_G_FOR_MANEUVER = 0.3   # g

# Real braking pulses are short (verified: 0.7-3.0s) — well under
# case_common's default 2.0s "steady" minimum, so BRAKE needs its own
# shorter minimum and a higher per-file cap (real files show 2-5 braking
# pulses each).
BRAKE_MIN_RUN_SECONDS = 0.5
BRAKE_RUNS_PER_FILE = 6

# Peak-detection prominence for pitch, in mm. Checked against real data
# the same way case2's roll prominence was: measuring the filtered pitch
# signal's own noise during each file's stopped-car window gave std
# 0.13-0.55mm across the files checked (accel, brake, autocross,
# endurance) — 3mm sits comfortably above that (~5-20x margin) while
# staying well below real event magnitudes (~7-11mm+ seen in accel/brake).
PEAK_PROMINENCE_MM = 3.0

CASE3_EVENTS = ["accel", "brake", "skidpad", "autocross", "endurance"]

PLOTS_ROOT = os.path.join("plots", "case3_max_pitch")


def pitch_mm_to_deg(wheel_mm):
    """Pitch angle (deg) from a front-minus-rear WHEEL-travel mm difference.
    Thin wrapper so callers don't repeat the wheelbase."""
    return mm_to_deg(wheel_mm, WHEELBASE_MM)


# ── Parsing / derived signals ────────────────────────────────────────────

REQUIRED_SIGNALS = [
    "VCFRONT_shockpotdispFL", "VCFRONT_shockpotdispFR",
    "VCREAR_shockpotdispRL", "VCREAR_shockpotdispRR",
    "VCPDU_lat", "VCPDU_lon", "VCFRONT_vehicleSpeed",
]


def load_pitch_signals(path, cutoff_hz):
    try:
        signals = parse_influx(path)
    except Exception as e:
        print(f"  [!] Failed to parse '{path}': {e}")
        return None
    if any(name not in signals for name in REQUIRED_SIGNALS):
        print(f"  [!] '{path}' missing required signals, skipping.")
        return None

    dfl = np.asarray(signals["VCFRONT_shockpotdispFL"].value, dtype=float)
    dfr = np.asarray(signals["VCFRONT_shockpotdispFR"].value, dtype=float)
    drl = np.asarray(signals["VCREAR_shockpotdispRL"].value, dtype=float)
    drr = np.asarray(signals["VCREAR_shockpotdispRR"].value, dtype=float)
    # VCPDU_lat/VCPDU_lon are m/s^2 in the DBC (range [-32|32]) — convert to
    # g, exactly as case1_max_gs.py does. Without this, the 0.3 thresholds
    # below (MIN_LON_G_FOR_MANEUVER, and find_steady_segments' lateral
    # default) were being applied to m/s^2, gating at an effective 0.031 g.
    # That let coasting into the "accelerating" windows and understated accel
    # pitch by up to 32% (accel_corinne1: 7.51mm measured vs 11.04mm correct).
    lat_raw = np.asarray(signals["VCPDU_lat"].value, dtype=float) / G
    lon_raw = np.asarray(signals["VCPDU_lon"].value, dtype=float) / G
    speed = np.asarray(signals["VCFRONT_vehicleSpeed"].value, dtype=float)

    t_raw = np.asarray(signals["VCFRONT_shockpotdispFL"].time)
    dt = float(np.median(np.diff(t_raw)) / np.timedelta64(1, "s"))
    t = elapsed_seconds(t_raw)

    # Same per-corner static baselining as case2_max_roll.py — zero each
    # shock pot against its own stopped-car reading before combining, so a
    # sensor/calibration offset doesn't get counted as pitch.
    static_window = find_static_window(speed, t, lon_g=lon_raw)
    baseline_fl = static_baseline(dfl, t, static_window)
    baseline_fr = static_baseline(dfr, t, static_window)
    baseline_rl = static_baseline(drl, t, static_window)
    baseline_rr = static_baseline(drr, t, static_window)
    baselines_found = all(b is not None for b in (baseline_fl, baseline_fr, baseline_rl, baseline_rr))
    if not baselines_found:
        print(f"  [!] {os.path.basename(path)}: no stopped-car window found — "
              f"pitch is NOT baselined for this file (raw values used as-is).")
        baseline_fl = baseline_fr = baseline_rl = baseline_rr = 0.0

    # Shock-pot mm -> WHEEL mm per corner (front 1.15, rear 1.038) BEFORE
    # averaging and differencing the axles — see the MOTION_RATIO comment.
    wheel = to_wheel_travel({
        "FL": dfl - baseline_fl, "FR": dfr - baseline_fr,
        "RL": drl - baseline_rl, "RR": drr - baseline_rr,
    })

    front_avg = (wheel["FL"] + wheel["FR"]) / 2.0
    rear_avg = (wheel["RL"] + wheel["RR"]) / 2.0
    pitch_raw = front_avg - rear_avg

    # Front brake pressure, for locating real braking windows. Optional —
    # not every file necessarily carries it.
    bp_name = BRAKE_PRESSURE_SIGNALS["front"]
    if bp_name in signals:
        bp_raw = np.asarray(signals[bp_name].value, dtype=float)
        # NOT the event cutoff. Front brake pressure is sampled at 10 Hz —
        # the only channel here that is not 100 Hz — so its Nyquist is 5 Hz
        # and filtering it at the event's 10 Hz would be meaningless. See
        # case_common.BRAKE_PRESSURE_CUTOFF_HZ.
        bp_front = lowpass(bp_raw, dt, BRAKE_PRESSURE_CUTOFF_HZ)
        bp_saturated = bool(np.nanmax(bp_raw) >= BRAKE_PRESSURE_MAX_PSI)
    else:
        bp_front, bp_saturated = None, False

    pitch_f = lowpass(pitch_raw, dt, cutoff_hz)
    lat_f = lowpass(lat_raw, dt, cutoff_hz)   # only used to find skidpad's turning windows
    lon_f = lowpass(lon_raw, dt, cutoff_hz)   # only used to find accel/brake windows

    return {
        "path": path, "t_raw": t_raw, "dt": dt, "t": t,
        "pitch_raw": pitch_raw, "pitch_f": pitch_f, "lat_f": lat_f, "lon_f": lon_f,
        "bp_front": bp_front, "bp_saturated": bp_saturated, "speed": speed,
        "baselines_found": baselines_found,
        "baseline_fl": baseline_fl, "baseline_fr": baseline_fr,
        "baseline_rl": baseline_rl, "baseline_rr": baseline_rr,
    }


# ── SKIDPAD / ACCEL: steady-state segmentation -> median pitch ───────────

def analyze_steady_file(path, cutoff_hz, segment_signal_key, sign_filter=None):
    """Shared implementation for SKIDPAD (segment on lat_f, no sign
    filter) and ACCEL (segment on lon_f, keep only the negative/
    accelerating runs). Reports median pitch per qualifying run."""
    d = load_pitch_signals(path, cutoff_hz)
    if d is None:
        return None

    t = d["t"]
    kwargs = {}
    if segment_signal_key == "lon_f":
        kwargs["threshold"] = MIN_LON_G_FOR_MANEUVER
    segments = find_steady_segments(d[segment_signal_key], t, **kwargs)
    if sign_filter is not None:
        segments = {sg: runs for sg, runs in segments.items() if np.sign(sg) == sign_filter}

    runs_out = []
    pooled_pitch = []
    for sg, run_list in segments.items():
        for s, e, dur in run_list:
            ts, te = trim_window(t, s, e, TRIM_SECONDS)
            seg_pitch = d["pitch_f"][ts:te + 1]
            runs_out.append({
                "median_pitch_mm": float(np.median(seg_pitch)),
                "duration_s": dur, "start_s": float(t[ts]), "end_s": float(t[te]),
            })
            pooled_pitch.append(seg_pitch)

    combined_median_mm = float(np.median(np.concatenate(pooled_pitch))) if pooled_pitch else None

    return {
        "path": path, "t": t, "dt": d["dt"],
        "pitch_raw": d["pitch_raw"], "pitch_f": d["pitch_f"],
        "runs": runs_out, "combined_median_mm": combined_median_mm,
        "baselines_found": d["baselines_found"],
        "baseline_fl": d["baseline_fl"], "baseline_fr": d["baseline_fr"],
        "baseline_rl": d["baseline_rl"], "baseline_rr": d["baseline_rr"],
    }


def analyze_skidpad_file(path):
    return analyze_steady_file(path, SKIDPAD_CUTOFF_HZ, "lat_f", sign_filter=None)


def analyze_accel_file(path):
    return analyze_steady_file(path, AUTOX_END_CUTOFF_HZ, "lon_f", sign_filter=-1)


# ── BRAKE: window-local peak within each real braking pulse ──────────────

def analyze_brake_file(path):
    d = load_pitch_signals(path, AUTOX_END_CUTOFF_HZ)
    if d is None:
        return None

    t = d["t"]
    # Braking windows come from FRONT BRAKE PRESSURE, not from thresholding
    # longitudinal G. Pressure is the driver's actual input; lon G is the
    # result, and also responds to drivetrain drag, downshifts and gradient.
    # Falls back to the old lon-G segmentation if the pressure channel is
    # missing from a file.
    if d.get("bp_front") is not None:
        brake_windows = find_braking_windows(d["bp_front"], t, speed=d.get("speed"))
        window_source = "front brake pressure"
    else:
        segments = find_steady_segments(
            d["lon_f"], t, threshold=MIN_LON_G_FOR_MANEUVER,
            min_run_s=BRAKE_MIN_RUN_SECONDS, runs_per_direction=BRAKE_RUNS_PER_FILE,
        )
        brake_windows = [(s, e, dur) for sg, runs in segments.items()
                          if np.sign(sg) > 0 for s, e, dur in runs]
        window_source = "longitudinal G (brake pressure unavailable)"

    peaks = []   # (abs_pitch_mm, signed_pitch_mm, idx, duration_s)
    for s, e, dur in brake_windows:
        seg = d["pitch_f"][s:e + 1]
        local_idx = int(np.argmax(np.abs(seg)))
        idx = s + local_idx
        peaks.append((abs(float(seg[local_idx])), float(seg[local_idx]), idx, dur))

    return {
        "path": path, "t": t, "dt": d["dt"],
        "pitch_raw": d["pitch_raw"], "pitch_f": d["pitch_f"],
        "brake_windows": brake_windows, "peaks": peaks,
        "window_source": window_source, "bp_saturated": d.get("bp_saturated", False),
        "baselines_found": d["baselines_found"],
        "baseline_fl": d["baseline_fl"], "baseline_fr": d["baseline_fr"],
        "baseline_rl": d["baseline_rl"], "baseline_rr": d["baseline_rr"],
    }


# ── AUTOCROSS/ENDURANCE: blind whole-file peak detection ─────────────────

def analyze_transient_file(path, event):
    d = load_pitch_signals(path, AUTOX_END_CUTOFF_HZ)
    if d is None:
        return None

    t = d["t"]
    idxs, vals = top_k_peaks(np.abs(d["pitch_f"]), t, TOP_K_PEAKS, prominence=PEAK_PROMINENCE_MM)

    return {
        "path": path, "event": event, "t": t, "dt": d["dt"],
        "pitch_raw": d["pitch_raw"], "pitch_f": d["pitch_f"],
        "peaks": list(zip(idxs.tolist(), vals.tolist())),
        "baselines_found": d["baselines_found"],
        "baseline_fl": d["baseline_fl"], "baseline_fr": d["baseline_fr"],
        "baseline_rl": d["baseline_rl"], "baseline_rr": d["baseline_rr"],
    }


# ── Plotting ─────────────────────────────────────────────────────────────

def build_before_after_plot(result, cutoff_hz, output_path):
    fig = go.Figure()
    t = result["t"]
    fig.add_trace(go.Scatter(x=t, y=result["pitch_raw"], mode="lines", name="pitch (raw, mm)",
                              line=dict(color="lightgreen", width=1), opacity=0.6))
    fig.add_trace(go.Scatter(x=t, y=result["pitch_f"], mode="lines", name="pitch (filtered, mm)",
                              line=dict(color="darkgreen", width=2)))
    fig.update_layout(
        title=f"{os.path.basename(result['path'])} — raw vs. {cutoff_hz} Hz low-pass filtered (pitch)",
        xaxis_title="Elapsed time (s)", yaxis_title="Front-avg minus rear-avg (mm)",
    )
    fig.update_xaxes(rangeslider_visible=True)
    fig.write_html(output_path, include_plotlyjs="cdn")


def build_pitch_angle_summary(summaries_by_event, output_path):
    """Grouped bar chart of the headline max pitch angle (deg) per event —
    the single 'here's the answer' chart for case3. SKIDPAD/ACCEL only
    have a 'typical' (steady median) bar — no separate peak concept, same
    treatment case2 gives skidpad roll. BRAKE/AUTOCROSS/ENDURANCE get
    both 'typical' (top-5 avg) and 'worst' (single highest)."""
    events = [e for e in CASE3_EVENTS if summaries_by_event.get(e) is not None]
    if not events:
        return

    fig = go.Figure()
    typical = [summaries_by_event[e].get("typical_deg") for e in events]
    worst = [summaries_by_event[e].get("worst_deg") for e in events]

    fig.add_trace(go.Bar(
        name="Typical", x=[e.upper() for e in events], y=typical,
        marker_color="#2a78d6",
        text=[f"{v:.2f}°" if v is not None else "n/a" for v in typical],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Worst (single highest)", x=[e.upper() for e in events], y=worst,
        marker_color="#e34948",
        text=[f"{v:.2f}°" if v is not None else "n/a" for v in worst],
        textposition="outside",
    ))

    fig.update_layout(
        title="Max Pitch Angle by Event (deg)",
        yaxis_title="Pitch angle (deg, magnitude)",
        barmode="group",
    )
    fig.write_html(output_path, include_plotlyjs="cdn")


# ── Reporting ────────────────────────────────────────────────────────────

def report_baselines(event, results):
    print(f"\n--- {event.upper()} static baselines (stopped-car reference, subtracted before differencing) ---")
    for r in results:
        fname = os.path.basename(r["path"])
        if not r["baselines_found"]:
            print(f"  {fname}: NOT baselined — no stopped-car window found")
            continue
        print(f"  {fname}: FL={r['baseline_fl']:.3f}mm  FR={r['baseline_fr']:.3f}mm  "
              f"RL={r['baseline_rl']:.3f}mm  RR={r['baseline_rr']:.3f}mm")


def report_steady(event, results):
    print(f"\n=== {event.upper()} PITCH (steady-state, {'2.0' if event == 'skidpad' else '5.0'} Hz low-pass) ===")
    if not results:
        print("  no data")
        return None

    all_medians = []
    for r in results:
        fname = os.path.basename(r["path"])
        if not r["runs"]:
            print(f"  [!] {fname}: no qualifying steady window found.")
            continue
        for i, run in enumerate(r["runs"], 1):
            deg = pitch_mm_to_deg(run["median_pitch_mm"])
            print(f"    {fname} run {i}: median pitch={run['median_pitch_mm']:+.3f}mm ({deg:+.4f} deg) "
                  f"({run['start_s']:.1f}s-{run['end_s']:.1f}s, dur={run['duration_s']:.1f}s after trimming)")
        if r["combined_median_mm"] is not None:
            print(f"    {fname} combined: median pitch={r['combined_median_mm']:+.3f}mm "
                  f"({pitch_mm_to_deg(r['combined_median_mm']):+.4f} deg)")
            all_medians.append(r["combined_median_mm"])

    if not all_medians:
        return None
    typical_mm = float(np.median(all_medians))
    print(f"  Across all files: typical pitch = {typical_mm:+.3f}mm ({pitch_mm_to_deg(typical_mm):+.4f} deg)")
    return {"typical_deg": pitch_mm_to_deg(abs(typical_mm)), "worst_deg": None}


def report_brake(results):
    print(f"\n=== BRAKE PITCH (window-local peak within each braking pulse, {AUTOX_END_CUTOFF_HZ} Hz low-pass) ===")
    if not results:
        print("  no data")
        return None
    for r in results:
        note = "  [!] brake pressure SATURATED at DBC ceiling — peak is a floor" if r.get("bp_saturated") else ""
        print(f"  {os.path.basename(r['path'])}: {len(r['brake_windows'])} braking window(s) "
              f"from {r.get('window_source', '?')} (>{BRAKING_PRESSURE_PSI:.0f} psi){note}")

    pool = []   # (abs_mm, signed_mm, r, idx, dur)
    for r in results:
        for abs_mm, signed_mm, idx, dur in r["peaks"]:
            pool.append((abs_mm, signed_mm, r, idx, dur))
    if not pool:
        print("  no braking windows found (check MIN_LON_G_FOR_MANEUVER / BRAKE_MIN_RUN_SECONDS)")
        return None
    pool.sort(key=lambda x: x[0], reverse=True)

    for abs_mm, signed_mm, r, idx, dur in pool:
        fname = os.path.basename(r["path"])
        print(f"    {fname} @ {r['t'][idx]:.2f}s (pulse dur={dur:.2f}s): "
              f"pitch={signed_mm:+.3f}mm ({pitch_mm_to_deg(signed_mm):+.4f} deg)")

    top = pool[:TOP_K_PEAKS]
    avg_mm = float(np.mean([abs_mm for abs_mm, *_ in top]))
    best_abs, best_signed, best_r, best_idx, best_dur = pool[0]
    print(f"  Top {len(top)} braking pulses averaged: {avg_mm:.3f} mm ({pitch_mm_to_deg(avg_mm):.4f} deg)")
    print(f"  Single hardest braking pulse: {best_signed:+.3f} mm ({pitch_mm_to_deg(best_signed):+.4f} deg) "
          f"— {os.path.basename(best_r['path'])} @ {best_r['t'][best_idx]:.2f}s")

    return {"typical_deg": pitch_mm_to_deg(avg_mm), "worst_deg": pitch_mm_to_deg(best_abs)}


def report_transient(event, results):
    print(f"\n=== {event.upper()} PITCH (whole-file peak detection, {AUTOX_END_CUTOFF_HZ} Hz low-pass) ===")
    if not results:
        print("  no data")
        return None

    pool = []
    for r in results:
        for idx, val in r["peaks"]:
            pool.append((val, r, idx))
    if not pool:
        print(f"  no peaks found (check PEAK_PROMINENCE_MM)")
        return None
    pool.sort(key=lambda x: x[0], reverse=True)

    top = pool[:TOP_K_PEAKS]
    avg_mm = float(np.mean([v for v, _, _ in top]))
    best_val, best_r, best_idx = pool[0]
    best_fname = os.path.basename(best_r["path"])
    best_t = best_r["t"][best_idx]
    best_signed = best_r["pitch_f"][best_idx]

    print(f"    Top {len(top)} peaks averaged: {avg_mm:.3f} mm ({pitch_mm_to_deg(avg_mm):.4f} deg) "
          f"(values: {', '.join(f'{v:.2f}' for v, _, _ in top)})")
    print(f"    Single highest peak: {best_val:.3f} mm ({pitch_mm_to_deg(best_val):.4f} deg) "
          f"— {best_fname} @ {best_t:.2f}s (signed: {best_signed:+.3f}mm)")

    return {"typical_deg": pitch_mm_to_deg(avg_mm), "worst_deg": pitch_mm_to_deg(best_val)}


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Folder containing CSVs")
    args = parser.parse_args()

    csv_paths = sorted(glob.glob(os.path.join(args.dir, "*.csv")))
    if not csv_paths:
        print(f"No CSVs found in '{args.dir}'.")
        sys.exit(1)

    grouped = group_by_event(csv_paths)

    print(f"Skidpad low-pass: {SKIDPAD_CUTOFF_HZ} Hz | Everything else low-pass: "
          f"{AUTOX_END_CUTOFF_HZ} Hz (both {FILTER_ORDER}th-order Butterworth, zero-phase)")
    print(f"Geometry: wheelbase={WHEELBASE_MM}mm | motion ratio (wheel/spring): "
          f"front={MOTION_RATIO_FRONT} rear={MOTION_RATIO_REAR}")
    print("Sign convention: pitch_mm > 0 ~ acceleration (squat), pitch_mm < 0 ~ braking (dive) — see module docstring.")

    summaries_by_event = {}

    for event in CASE3_EVENTS:
        paths = grouped.get(event, [])
        if not paths:
            print(f"\nNo files found for {event.upper()}.")
            continue

        out_dir = os.path.join(PLOTS_ROOT, event)
        os.makedirs(out_dir, exist_ok=True)

        if event == "skidpad":
            results = [r for p in paths if (r := analyze_skidpad_file(p)) is not None]
            cutoff = SKIDPAD_CUTOFF_HZ
        elif event == "accel":
            results = [r for p in paths if (r := analyze_accel_file(p)) is not None]
            cutoff = AUTOX_END_CUTOFF_HZ
        elif event == "brake":
            results = [r for p in paths if (r := analyze_brake_file(p)) is not None]
            cutoff = AUTOX_END_CUTOFF_HZ
        else:
            results = [r for p in paths if (r := analyze_transient_file(p, event)) is not None]
            cutoff = AUTOX_END_CUTOFF_HZ

        report_baselines(event, results)
        for r in results:
            fname = os.path.splitext(os.path.basename(r["path"]))[0]
            build_before_after_plot(r, cutoff, os.path.join(out_dir, f"{fname}_pitch_before_after.html"))

        if event in ("skidpad", "accel"):
            summary = report_steady(event, results)
        elif event == "brake":
            summary = report_brake(results)
        else:
            summary = report_transient(event, results)

        summaries_by_event[event] = summary
        if results:
            print(f"\n  Plots saved to: {out_dir}/")

    build_pitch_angle_summary(summaries_by_event, os.path.join(PLOTS_ROOT, "pitch_angle_summary.html"))
    print(f"\nHeadline chart saved to: {PLOTS_ROOT}/pitch_angle_summary.html")

    print("\nDone.")

    return summaries_by_event


if __name__ == "__main__":
    with report_page("case3_max_pitch", "Case 3 — Max Pitch", PLOTS_ROOT) as page:
        page.summary = main()
    write_index()
