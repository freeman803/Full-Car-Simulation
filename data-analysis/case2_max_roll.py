# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
case2_max_roll.py — Case 2: max roll angle, for SKIDPAD, AUTOCROSS, and
ENDURANCE (kept separate), derived from the 4 shock-pot linear-displacement
signals (NOT the VCPDU IMU roll signal — this is an independent
mechanical-linkage estimate of roll, useful as a cross-check against it).

Roll, per axle, per sample (right-side travel minus left-side travel):
    roll_front_mm = wheel FR - wheel FL
    roll_rear_mm  = wheel RR - wheel RL

SIGN CONVENTION — verified against real data, and the OPPOSITE of what the
formula suggests at a glance. A HIGHER mm reading is more EXTENSION on this
car's shock-pot calibration (established empirically in case3_max_pitch.py
against vehicle speed), so the corner reading higher is the UNLOADED one:

    roll_*_mm > 0  ~  right side EXTENDED, LEFT side compressed
    roll_*_mm < 0  ~  left side extended, RIGHT side compressed

Measured on skidpad to confirm: during negative lateral G, FL sits at
-6.53mm (compressed) and FR at +15.97mm (extended), giving roll_front of
+22.55mm. Correlation between lateral G and roll_front is -0.998, so the
relationship is unambiguous.

An earlier version of this comment claimed positive meant the RIGHT side was
more compressed — inverted, and it would have made every roll direction read
backwards. Magnitudes were never affected, only the interpretation.

mm -> degrees via atan (EXACT for this geometry — not the small-angle
approximation this line used to claim). NOTE the motion ratio is applied PER CORNER
upstream (front 1.188, rear 1.038 differ), so the mm below are already WHEEL
travel:
    roll_deg = atan(roll_mm / track_width_mm) * 180/pi

The whole-car "avg" figure converts the mean of front and rear mm over the
mean of the two track widths. That is an approximation — strictly it should
be the mean of the two separately-converted angles — but the two tracks
differ by only 4.3%, so the error is 0.17-0.19% (e.g. 1.6201 deg reported
against 1.6231 deg exact at the endurance peak). Documented rather than
"fixed", so published numbers stay comparable.

Filtering is IDENTICAL to case1_max_gs.py (imported from case_common, not
redefined here): 4th-order Butterworth, filtfilt, 10 Hz for every event.
Retuned 2026-07-31 from cutoff_sweep.py, which showed low cutoffs are the
UNSTABLE region and the old 5 Hz sat on that slope — see the README.

Methodology (mirrors case1_max_gs.py exactly):
- SKIDPAD (10 Hz low-pass): same steady-state segment detection as case1
  (using filtered LATERAL G to find the steady-circling windows — roll
  itself is not used to detect the windows, only to report a value once
  the window is known). Reports MEDIAN front/rear/avg roll over each
  segment's trimmed middle, matching the "average over the steady lap"
  approach case1 uses for lateral G.

- AUTOCROSS / ENDURANCE (10 Hz low-pass): peak detection directly on
  |roll_front|, |roll_rear|, |roll_avg| (prominence + minimum spacing to
  reject noise / avoid double-counting one corner), top 5 pooled across
  all files in that event, plus the single highest peak with its front/
  rear/avg roll at that instant.

Outputs (all under plots/case2_max_roll/ — case2 owns this subtree, kept
separate from case1_max_gs.py's plots/case1_max_gs/):
- Console report, including a breakdown of the front vs. rear vs. IMU
  comparison and the constants used.
- One before/after low-pass filter plot per file (front + rear roll
  overlaid raw vs. filtered) -> <event>/<file>_roll_before_after.html
- One front-vs-rear roll scatter per event (a rigid, non-articulated
  chassis should show front and rear roll tracking each other closely;
  scatter well off the y=x line at the highlighted points is a red flag)
  -> <event>/roll_diagram.html
- ONE headline chart across all 3 events: roll_angle_summary.html —
  max roll angle (deg), front/rear/avg, skidpad vs autocross vs endurance

Run it:
    uv run case2_max_roll.py --dir comp2026_data

Uses parse_influx.py and case_common.py (must be in the same folder, or
importable). Vehicle geometry constants below are plain hardcoded values —
deliberately NOT imported from corner-model/ (kept independent of that or
any other simulation model for now).
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
    CASE_EVENTS as CASE2_EVENTS,
    group_by_event,
    lowpass, elapsed_seconds, trim_window,
    find_steady_segments, top_k_peaks,
    baseline_corner_displacements, to_wheel_travel,
    MOTION_RATIO_FRONT, MOTION_RATIO_REAR,
    TRIM_SECONDS, TOP_K_PEAKS,
    FRONT_TRACK_MM, REAR_TRACK_MM, mm_to_deg,
    to_ground_referenced,
    build_raw_vs_filtered, thin_scatter, PLOT_TEMPLATE, format_peak_shape,
    titled,
)

# Vehicle geometry and the mm -> degree conversion now come from
# case_common too. They used to be redefined here, in case3 and in case4;
# the values agreed, but nothing enforced it.

# Motion ratio comes from case_common (measured: 1.188 front, 1.038 rear,
# wheel/spring displacement) and is applied PER CORNER via
# to_wheel_travel() before the roll difference is taken — front and rear
# ratios differ, so it cannot be applied afterwards. Everything below works
# in WHEEL millimetres. This replaces an earlier 1:1 placeholder, which
# understated front roll by 15% and rear roll by ~4%.

# Peak-detection prominence for roll, in mm. Checked against real data:
# measuring the filtered roll signal's own noise during each file's
# stopped-car window (car isn't rolling, so any wiggle there is pure
# sensor noise) gave std ~0.12mm / peak-to-peak ~1.3-2.7mm on the files
# tested — comfortably below 2mm. A sweep from 0.5mm to 10mm also left the
# reported top-5 peaks and single highest peak completely unchanged (only
# the *total* peak count moved, which isn't reported) — so the numbers
# this script prints aren't sensitive to the exact value here.
PEAK_PROMINENCE_MM = 2.0

# Plots go under their own case-named subtree (plots/case2_max_roll/<event>/...)
# rather than plots/<event>/ shared with other case scripts — see
# case1_max_gs.py's PLOTS_ROOT comment for why.
PLOTS_ROOT = os.path.join("plots", "case2_max_roll")


# ── Parsing / derived signals ────────────────────────────────────────────

REQUIRED_SIGNALS = [
    "VCFRONT_shockpotdispFL", "VCFRONT_shockpotdispFR",
    "VCREAR_shockpotdispRL", "VCREAR_shockpotdispRR",
    "VCPDU_lat", "VCFRONT_vehicleSpeed",
]


def load_roll_signals(path, cutoff_hz):
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
    # VCPDU_lat is m/s^2 in the DBC (range [-32|32]) — convert to g, exactly
    # as case1_max_gs.py does. Without this, find_steady_segments' 0.3
    # threshold (which means 0.3 g) was being applied to m/s^2, gating at an
    # effective 0.031 g and letting near-straight-line coasting into the
    # "turning" windows.
    lat_raw = np.asarray(signals["VCPDU_lat"].value, dtype=float) / G
    speed = np.asarray(signals["VCFRONT_vehicleSpeed"].value, dtype=float)

    t_raw = np.asarray(signals["VCFRONT_shockpotdispFL"].time)
    dt = float(np.median(np.diff(t_raw)) / np.timedelta64(1, "s"))
    t = elapsed_seconds(t_raw)

    # Zero each corner against its own stopped-car reading, so a per-corner
    # sensor/calibration offset (or a genuine static cross-weight
    # difference) doesn't get counted as cornering-induced roll. Without
    # this, roll_front = FR - FL would carry whatever offset existed
    # between those two pots even at rest.
    # Via the SHARED helper. This used to be four inline static_baseline()
    # calls, duplicated verbatim in case3 — and that duplication is exactly
    # why both files missed the piecewise-baseline fix that case4 (already
    # using the helper) got for free. See segmented_baselines().
    corners_raw, baselines, baselines_found = baseline_corner_displacements(
        signals, t, speed)
    if not baselines_found:
        print(f"  [!] {os.path.basename(path)}: no stopped-car window found — "
              f"roll is NOT baselined for this file (raw FR-FL / RR-RL used as-is).")
    baseline_fl, baseline_fr = baselines["FL"], baselines["FR"]
    baseline_rl, baseline_rr = baselines["RL"], baselines["RR"]

    # Shock-pot mm -> WHEEL mm per corner (front 1.188, rear 1.038) BEFORE
    # differencing. Front and rear ratios differ, so this cannot be applied
    # to the roll difference afterwards.
    wheel = to_wheel_travel(corners_raw)

    # +ve = right side EXTENDED / left side compressed — higher mm is more
    # extension on this car. See the sign-convention note in the docstring;
    # the obvious reading of this line is backwards.
    roll_front_raw = wheel["FR"] - wheel["FL"]
    roll_rear_raw = wheel["RR"] - wheel["RL"]

    roll_front_f = lowpass(roll_front_raw, dt, cutoff_hz)
    roll_rear_f = lowpass(roll_rear_raw, dt, cutoff_hz)
    roll_avg_f = (roll_front_f + roll_rear_f) / 2.0
    lat_f = lowpass(lat_raw, dt, cutoff_hz)   # only used to find turning windows (skidpad)

    return {
        "path": path, "t_raw": t_raw, "dt": dt, "t": t,
        "roll_front_raw": roll_front_raw, "roll_rear_raw": roll_rear_raw,
        "roll_front_f": roll_front_f, "roll_rear_f": roll_rear_f,
        "roll_avg_f": roll_avg_f, "lat_f": lat_f,
        "baselines_found": baselines_found,
        "baseline_fl": baseline_fl, "baseline_fr": baseline_fr,
        "baseline_rl": baseline_rl, "baseline_rr": baseline_rr,
    }


def analyze_skidpad_file(path):
    d = load_roll_signals(path, SKIDPAD_CUTOFF_HZ)
    if d is None:
        return None

    t = d["t"]
    segments = find_steady_segments(d["lat_f"], t)   # windows come from lat G, same as case1

    results = {}
    for sg, run_list in segments.items():
        per_run = []
        pooled_front, pooled_rear, pooled_avg = [], [], []
        for s, e, dur in run_list:
            ts, te = trim_window(t, s, e, TRIM_SECONDS)
            seg_front = d["roll_front_f"][ts:te + 1]
            seg_rear = d["roll_rear_f"][ts:te + 1]
            seg_avg = d["roll_avg_f"][ts:te + 1]
            per_run.append({
                "median_front_mm": float(np.median(seg_front)),
                "median_rear_mm": float(np.median(seg_rear)),
                "median_avg_mm": float(np.median(seg_avg)),
                "duration_s": dur, "start_s": float(t[ts]), "end_s": float(t[te]),
            })
            pooled_front.append(seg_front)
            pooled_rear.append(seg_rear)
            pooled_avg.append(seg_avg)

        results[sg] = {
            "runs": per_run,
            "combined_median_front_mm": float(np.median(np.concatenate(pooled_front))),
            "combined_median_rear_mm": float(np.median(np.concatenate(pooled_rear))),
            "combined_median_avg_mm": float(np.median(np.concatenate(pooled_avg))),
        }

    return {
        "path": path, "t": t, "dt": d["dt"],
        "roll_front_raw": d["roll_front_raw"], "roll_rear_raw": d["roll_rear_raw"],
        "roll_front_f": d["roll_front_f"], "roll_rear_f": d["roll_rear_f"],
        "segments": results,
        "baselines_found": d["baselines_found"],
        "baseline_fl": d["baseline_fl"], "baseline_fr": d["baseline_fr"],
        "baseline_rl": d["baseline_rl"], "baseline_rr": d["baseline_rr"],
    }


def analyze_transient_file(path, event):
    d = load_roll_signals(path, AUTOX_END_CUTOFF_HZ)
    if d is None:
        return None

    t = d["t"]
    front_idxs, front_vals = top_k_peaks(np.abs(d["roll_front_f"]), t, TOP_K_PEAKS,
                                          prominence=PEAK_PROMINENCE_MM)
    rear_idxs, rear_vals = top_k_peaks(np.abs(d["roll_rear_f"]), t, TOP_K_PEAKS,
                                        prominence=PEAK_PROMINENCE_MM)
    avg_idxs, avg_vals = top_k_peaks(np.abs(d["roll_avg_f"]), t, TOP_K_PEAKS,
                                      prominence=PEAK_PROMINENCE_MM)

    return {
        "path": path, "event": event, "t": t, "dt": d["dt"],
        "roll_front_raw": d["roll_front_raw"], "roll_rear_raw": d["roll_rear_raw"],
        "roll_front_f": d["roll_front_f"], "roll_rear_f": d["roll_rear_f"],
        "roll_avg_f": d["roll_avg_f"],
        "front_peaks": list(zip(front_idxs.tolist(), front_vals.tolist())),
        "rear_peaks": list(zip(rear_idxs.tolist(), rear_vals.tolist())),
        "avg_peaks": list(zip(avg_idxs.tolist(), avg_vals.tolist())),
        "baselines_found": d["baselines_found"],
        "baseline_fl": d["baseline_fl"], "baseline_fr": d["baseline_fr"],
        "baseline_rl": d["baseline_rl"], "baseline_rr": d["baseline_rr"],
    }


# ── Plotting ─────────────────────────────────────────────────────────────

def steady_spans(result):
    """POST-TRIM (start_s, end_s) windows the skidpad medians came from.

    Empty for the transient events, which report peaks rather than
    windows — see case1.steady_spans() for the full note.
    """
    spans = []
    for sign_result in (result.get("segments") or {}).values():
        for run in sign_result.get("runs", []):
            spans.append((run["start_s"], run["end_s"]))
    return sorted(spans)


def peak_markers(result):
    """{panel: [(t, label, y)]} for the front/rear roll peaks this file
    reports. Panel 0 is front, panel 1 rear; y from the FILTERED trace,
    which is the one the peak was found in."""
    markers = {}
    for panel, (key, sig) in enumerate([("front_peaks", "roll_front_f"),
                                        ("rear_peaks", "roll_rear_f")]):
        rows = [(float(result["t"][idx]), f"#{rank}", float(result[sig][idx]))
                for rank, (idx, _val) in enumerate(result.get(key, []), 1)]
        if rows:
            markers[panel] = rows
    return markers


def build_before_after_plot(result, cutoff_hz, output_path):
    build_raw_vs_filtered(
        panels=[
            ("Front roll (FR − FL)", result["roll_front_raw"],
             result["roll_front_f"], "Wheel travel difference (mm)"),
            ("Rear roll (RR − RL)", result["roll_rear_raw"],
             result["roll_rear_f"], "Wheel travel difference (mm)"),
        ],
        t=result["t"],
        title=f"{os.path.basename(result['path'])} — roll",
        output_path=output_path,
        cutoff_hz=cutoff_hz,
        shade=steady_spans(result),
        shade_label="steady-state window used for the skidpad median",
        markers=peak_markers(result),
    )


def build_roll_diagram(event, background_points, highlighted, output_path):
    fig = go.Figure()

    for fname, front, rear in background_points:
        front_thin, rear_thin = thin_scatter(front, rear)
        fig.add_trace(go.Scattergl(
            x=front_thin, y=rear_thin, mode="markers", name=fname,
            marker=dict(size=3, opacity=0.25),
            hovertemplate="front=%{x:.2f}mm<br>rear=%{y:.2f}mm<extra>" + fname + "</extra>",
        ))

    all_vals = np.concatenate([np.concatenate([f, r]) for _, f, r in background_points]) if background_points else np.array([0.0])
    lim = float(np.max(np.abs(all_vals))) * 1.05 if all_vals.size else 1.0
    fig.add_trace(go.Scatter(
        x=[-lim, lim], y=[-lim, lim], mode="lines", name="front = rear (rigid chassis)",
        line=dict(color="gray", dash="dash"), hoverinfo="skip",
    ))

    for label, front_vals, rear_vals, texts, color in highlighted:
        fig.add_trace(go.Scatter(
            x=front_vals, y=rear_vals, mode="markers", name=label,
            marker=dict(size=14, symbol="star", color=color, line=dict(width=1, color="black")),
            text=texts, hovertemplate="%{text}<br>front=%{x:.2f}mm<br>rear=%{y:.2f}mm<extra></extra>",
        ))

    fig.update_layout(
        xaxis_title="Front roll (FR − FL, mm)",
        yaxis_title="Rear roll (RR − RL, mm)",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        template=PLOT_TEMPLATE,
    )
    titled(
        fig, f"{event.upper()} — Front vs. Rear Roll Diagram",
        "distance from the dashed line is the front/rear roll disagreement. "
        "Overlapping markers thinned for display — the outer envelope is exact.",
    )
    fig.write_html(output_path, include_plotlyjs="cdn")


def build_roll_angle_summary(summaries_by_event, output_path):
    """Grouped bar chart of the headline max roll angle (deg) per event,
    per axle. This is the single 'here's the answer' chart for case2 — the
    per-event before/after and roll-diagram plots are supporting detail.

    For skidpad, the bar is the largest-magnitude steady-state combined
    median across the two turn directions (there's no 'peak' concept for a
    steady-state metric). For autocross/endurance, it's the single highest
    peak already reported in the console output — same number, just
    visualized here."""
    events = [e for e in CASE2_EVENTS if summaries_by_event.get(e) is not None]
    if not events:
        return

    fig = go.Figure()
    for axle, color in [("front_deg", "red"), ("rear_deg", "blue"), ("avg_deg", "green")]:
        values = [summaries_by_event[e].get(axle) for e in events]
        fig.add_trace(go.Bar(
            name=axle.replace("_deg", "").capitalize(),
            x=[e.upper() for e in events], y=values,
            marker_color=color,
            text=[f"{v:.2f}°" if v is not None else "n/a" for v in values],
            textposition="outside",
        ))

    fig.update_layout(
        title="Max Roll Angle by Event (deg)",
        yaxis_title="Roll angle (deg)",
        barmode="group",
    )
    fig.write_html(output_path, include_plotlyjs="cdn")


# ── Reporting ────────────────────────────────────────────────────────────


# Ground-referenced roll sits ALONGSIDE the measured figure, never instead
# of it — the shock pots measure suspension-referenced and that stays
# primary. The whole-car "avg" is rebuilt from the two AXLE angles with
# their own multipliers rather than scaled from the suspension avg, because
# front and rear differ (1.307 vs 1.357). See case_common.
def _with_ground(summary):
    front, rear = summary.get("front_deg"), summary.get("rear_deg")
    summary["front_deg_ground"] = to_ground_referenced(front, "front")
    summary["rear_deg_ground"] = to_ground_referenced(rear, "rear")
    summary["avg_deg_ground"] = to_ground_referenced(summary.get("avg_deg"), "avg")
    return summary


def report_skidpad(results):
    print(f"\n=== SKIDPAD ROLL (steady-state segments, {SKIDPAD_CUTOFF_HZ} Hz low-pass) ===")
    if not results:
        print("  no data")
        return [], None
    highlight_points = []
    max_front_mm = max_rear_mm = max_avg_mm = 0.0
    for r in results:
        fname = os.path.basename(r["path"])
        if not r["segments"]:
            print(f"  [!] {fname}: no qualifying steady segments found.")
            continue
        for sg, info in sorted(r["segments"].items()):
            direction = "positive-lateral-G direction" if sg > 0 else "negative-lateral-G direction"
            print(f"  {fname} — {direction} ({len(info['runs'])} run(s) found):")
            run_fronts, run_rears, run_texts = [], [], []
            for i, run in enumerate(info["runs"], 1):
                front_deg = mm_to_deg(run["median_front_mm"], FRONT_TRACK_MM)
                rear_deg = mm_to_deg(run["median_rear_mm"], REAR_TRACK_MM)
                print(f"    Run {i}: front={run['median_front_mm']:+.3f}mm ({front_deg:+.4f} deg), "
                      f"rear={run['median_rear_mm']:+.3f}mm ({rear_deg:+.4f} deg) "
                      f"({run['start_s']:.1f}s-{run['end_s']:.1f}s, dur={run['duration_s']:.1f}s after trimming)")
                run_fronts.append(run["median_front_mm"])
                run_rears.append(run["median_rear_mm"])
                run_texts.append(f"{fname} {direction} run {i}")
            avg_track = (FRONT_TRACK_MM + REAR_TRACK_MM) / 2.0
            avg_deg = mm_to_deg(info["combined_median_avg_mm"], avg_track)
            print(f"    Combined (all runs pooled): front={info['combined_median_front_mm']:+.3f}mm "
                  f"({mm_to_deg(info['combined_median_front_mm'], FRONT_TRACK_MM):+.4f} deg), "
                  f"rear={info['combined_median_rear_mm']:+.3f}mm "
                  f"({mm_to_deg(info['combined_median_rear_mm'], REAR_TRACK_MM):+.4f} deg), "
                  f"avg={info['combined_median_avg_mm']:+.3f}mm ({avg_deg:+.4f} deg)")

            max_front_mm = max(max_front_mm, abs(info["combined_median_front_mm"]))
            max_rear_mm = max(max_rear_mm, abs(info["combined_median_rear_mm"]))
            max_avg_mm = max(max_avg_mm, abs(info["combined_median_avg_mm"]))

            highlight_points.append((
                f"{fname} {direction} — individual runs",
                run_fronts, run_rears, run_texts, "gold",
            ))
            highlight_points.append((
                f"{fname} {direction} — combined",
                [info["combined_median_front_mm"]], [info["combined_median_rear_mm"]],
                [f"{fname} {direction} combined"], "orange",
            ))

    avg_track = (FRONT_TRACK_MM + REAR_TRACK_MM) / 2.0
    summary = _with_ground({
        "front_deg": mm_to_deg(max_front_mm, FRONT_TRACK_MM),
        "rear_deg": mm_to_deg(max_rear_mm, REAR_TRACK_MM),
        "avg_deg": mm_to_deg(max_avg_mm, avg_track),
    })
    return highlight_points, summary


def report_transient(event, results):
    print(f"\n=== {event.upper()} ROLL (peak detection, {AUTOX_END_CUTOFF_HZ} Hz low-pass) ===")
    if not results:
        print("  no data")
        return [], None

    def pooled(peak_key):
        pooled_list = []
        for r in results:
            for idx, val in r[peak_key]:
                pooled_list.append((val, r, idx))
        pooled_list.sort(key=lambda x: x[0], reverse=True)
        return pooled_list

    highlight_points = []
    summary = {}
    instants = []        # deep-link targets for the report page

    for label, key, track_mm, color, summary_key, sig_key in [
        ("Front roll", "front_peaks", FRONT_TRACK_MM, "red", "front_deg", "roll_front_f"),
        ("Rear roll", "rear_peaks", REAR_TRACK_MM, "blue", "rear_deg", "roll_rear_f"),
        ("Avg roll", "avg_peaks", (FRONT_TRACK_MM + REAR_TRACK_MM) / 2.0, "green",
         "avg_deg", "roll_avg_f"),
    ]:
        pool = pooled(key)
        if not pool:
            print(f"  {label}: no peaks found (check PEAK_PROMINENCE_MM)")
            summary[summary_key] = None
            continue
        top = pool[:TOP_K_PEAKS]
        avg_mm = float(np.mean([v for v, _, _ in top]))
        best_val, best_r, best_idx = pool[0]
        best_fname = os.path.basename(best_r["path"])
        best_t = best_r["t"][best_idx]
        best_front = best_r["roll_front_f"][best_idx]
        best_rear = best_r["roll_rear_f"][best_idx]

        print(f"  {label}:")
        print(f"    Top {len(top)} peaks averaged: {avg_mm:.3f} mm ({mm_to_deg(avg_mm, track_mm):.4f} deg) "
              f"(values: {', '.join(f'{v:.2f}' for v, _, _ in top)})")
        print(f"    Single highest peak: {best_val:.3f} mm ({mm_to_deg(best_val, track_mm):.4f} deg) "
              f"— {best_fname} @ {best_t:.2f}s"
              # Peaks were found on np.abs(...), so the shape check is too.
              + format_peak_shape(np.abs(best_r[sig_key]), best_r["t"],
                                  best_idx, " mm"))
        print(f"    At that instant: front={best_front:+.3f}mm, rear={best_rear:+.3f}mm")

        summary[summary_key] = mm_to_deg(best_val, track_mm)
        instants.append({
            "event": event, "path": best_r["path"], "t": float(best_t),
            "label": f"peak {label.lower()} — "
                     f"{mm_to_deg(best_val, track_mm):.3f}°",
            "detail": f"front {best_front:+.2f}mm, rear {best_rear:+.2f}mm",
        })

        highlight_points.append((
            f"{label} — top {len(top)} peaks",
            [r["roll_front_f"][idx] for _, r, idx in top],
            [r["roll_rear_f"][idx] for _, r, idx in top],
            [f"{os.path.basename(r['path'])} @ {r['t'][idx]:.2f}s" for _, r, idx in top],
            color,
        ))

    _with_ground(summary)

    # Navigation metadata, not a number — underscore-prefixed so
    # case_summary's scalar sweep and the regression snapshot skip it.
    summary["_instants"] = instants
    return highlight_points, summary


def report_baselines(event, results):
    print(f"\n--- {event.upper()} static baselines (stopped-car reference, subtracted before differencing) ---")
    for r in results:
        fname = os.path.basename(r["path"])
        if not r["baselines_found"]:
            print(f"  {fname}: NOT baselined — no stopped-car window found")
            continue
        print(f"  {fname}: FL={r['baseline_fl']:.3f}mm  FR={r['baseline_fr']:.3f}mm  "
              f"RL={r['baseline_rl']:.3f}mm  RR={r['baseline_rr']:.3f}mm")


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

    print(f"Skidpad low-pass: {SKIDPAD_CUTOFF_HZ} Hz | Autocross/Endurance low-pass: "
          f"{AUTOX_END_CUTOFF_HZ} Hz (both {FILTER_ORDER}th-order Butterworth, zero-phase)")
    print(f"Geometry: front track={FRONT_TRACK_MM}mm, rear track={REAR_TRACK_MM}mm "
          f"| motion ratio (wheel/spring): front={MOTION_RATIO_FRONT} rear={MOTION_RATIO_REAR}")

    summaries_by_event = {}

    for event in CASE2_EVENTS:
        paths = grouped.get(event, [])
        if not paths:
            print(f"\nNo files found for {event.upper()}.")
            continue

        out_dir = os.path.join(PLOTS_ROOT, event)
        os.makedirs(out_dir, exist_ok=True)

        if event == "skidpad":
            results = [r for p in paths if (r := analyze_skidpad_file(p)) is not None]
            report_baselines(event, results)
            for r in results:
                fname = os.path.splitext(os.path.basename(r["path"]))[0]
                build_before_after_plot(r, SKIDPAD_CUTOFF_HZ,
                                         os.path.join(out_dir, f"{fname}_roll_before_after.html"))
            highlight, summary = report_skidpad(results)
            background = [(os.path.basename(r["path"]), r["roll_front_f"], r["roll_rear_f"]) for r in results]
        else:
            results = [r for p in paths if (r := analyze_transient_file(p, event)) is not None]
            report_baselines(event, results)
            for r in results:
                fname = os.path.splitext(os.path.basename(r["path"]))[0]
                build_before_after_plot(r, AUTOX_END_CUTOFF_HZ,
                                         os.path.join(out_dir, f"{fname}_roll_before_after.html"))
            highlight, summary = report_transient(event, results)
            background = [(os.path.basename(r["path"]), r["roll_front_f"], r["roll_rear_f"]) for r in results]

        summaries_by_event[event] = summary

        if results:
            build_roll_diagram(event, background, highlight, os.path.join(out_dir, "roll_diagram.html"))
            print(f"\n  Plots saved to: {out_dir}/")

    build_roll_angle_summary(summaries_by_event, os.path.join(PLOTS_ROOT, "roll_angle_summary.html"))
    print(f"\nHeadline chart saved to: {PLOTS_ROOT}/roll_angle_summary.html")

    print("\nDone.")

    return summaries_by_event


CONVENTIONS = [
    "<b>Roll is right-side travel minus left-side travel</b>, and a HIGHER "
    "mm reading is more EXTENSION on this car. So "
    "<code>roll &gt; 0 = right side extended, LEFT side compressed</code> — "
    "the opposite of what the formula suggests at a glance. Verified on "
    "skidpad: correlation with lateral G is −0.998.",
    "These are <b>wheel</b> millimetres — the motion ratio (1.188 front, "
    "1.038 rear) is applied per corner <i>before</i> the difference is "
    "taken, because the two ratios differ.",
    "The whole-car <b>avg</b> angle converts mean-mm over mean-track rather "
    "than averaging two separately-converted angles. The error is "
    "0.17–0.19% and is documented rather than fixed, so published numbers "
    "stay comparable.",
    "<b>Front and rear roll disagree by 7–27%</b> on this car for reasons "
    "not yet explained — see the README's known data problems. Two "
    "autocross runs additionally have unusable front pots and are flagged "
    "in place below.",
    "A peak is <b>one instantaneous sample</b> of the filtered trace. The "
    "bracketed <code>0.2s mean</code> next to it says whether that instant "
    "was a sustained plateau or an isolated spike.",
]


if __name__ == "__main__":
    with report_page("case2_max_roll", "Case 2 — Max Roll", PLOTS_ROOT) as page:
        page.summary = main()
        for text in CONVENTIONS:
            page.add_convention(text)
        for event_summary in (page.summary or {}).values():
            for item in (event_summary or {}).get("_instants", []):
                page.add_instant(item["event"], item["path"], item["t"],
                                 item["label"], item["detail"])
    write_index()
