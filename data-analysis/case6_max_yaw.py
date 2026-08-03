# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
case6_max_yaw.py — Case 6: MAX YAW RATE, in degrees per second, plus the
cornering geometry that falls out of it.

Yaw rate is how fast the car is ROTATING about its vertical axis. Cases 1-5
all measure what the car does to itself under load — how hard it corners,
how far it leans, how much a corner compresses. None of them measure how
quickly it changes direction, which is the other half of what makes a lap
time and the quantity a driver actually feels as "responsive" or "lazy".

WHY THIS EXISTS AT ALL — the README used to say the IMU's roll, pitch AND
yaw were all unusable. Measured 2026-07-31, that is wrong about yaw, and it
is the only one of the three that is wrong. VCPDU_yaw validates against an
identity that shares no sensor with the gyro:

    a_lat = v * omega_yaw          (steady cornering, no sideslip)

with lateral G from the IMU accelerometer and speed from the front wheels:

    skidpad    r=+0.989  slope=1.181
    autocross  r=+0.959  slope=1.067
    endurance  r=+0.983  slope=1.164

The slope exceeding 1.0 is expected rather than error — the identity is
exact only with zero sideslip, and VCFRONT_vehicleSpeed is front-wheel
derived so it under-reads through a corner. See README "Known data
problems" #9 for the full characterisation, including why the roll and
pitch channels of the SAME sensor are not usable (chassis roll is 0.82
deg/s RMS against a 0.45 deg/s noise floor; yaw is 49.6 against 0.36).

WHAT THIS DOES *NOT* DO — dead-reckon a path. A 7-18% scale error is
harmless instantaneously and fatal once integrated: over a 60-second run it
accumulates tens of degrees of heading error, which is exactly why the
autocross course integrates to ~365 m while start and end land 156-177 m
apart. Every quantity here is INSTANTANEOUS or a ratio of instantaneous
values, never an integral. That restriction is the whole reason these
numbers are trustworthy when a track map is not.

WHAT IT REPORTS

- MAX YAW RATE per event, by the same peak detection cases 1-4 use
  (prominence + minimum spacing, top 5 pooled + single highest), with the
  0.2s plateau check so a spike cannot masquerade as a sustained rotation.

- CORNER RADIUS at that instant, R = v / omega. This is the geometric
  radius the car is actually following, which is not the same as the
  radius of the corner painted on the track — the difference is the
  driver's line. Reported in metres, and it is the number to compare
  against the 15.25 m skidpad circle as a sanity check.

- SUSTAINED yaw rate on skidpad, as a median over the same steady-state
  segments case1/case2 use. A skidpad is a constant-radius constant-speed
  circle, so this is the cleanest yaw-rate measurement in the dataset and
  the one that validates the whole channel.

- LATERAL ACCELERATION CHECK per file, as the correlation and slope of
  a_lat against v*omega. This is the validation above, recomputed on every
  file every run rather than trusted from a note — if a future export
  breaks the yaw channel, this number moves and the report says so.

SIGN CONVENTION — established here by cross-reference against lateral G,
the same way case3 established the pitch convention against speed rather
than assuming it. Positive lateral G is cornering LEFT (case1's
convention), and yaw rate correlates POSITIVELY with lateral G at r=+0.96
to +0.99, so:

    yaw > 0  ~  rotating LEFT (counter-clockwise seen from above)
    yaw < 0  ~  rotating RIGHT

FILTERING is identical to every other case (imported from case_common, not
redefined): 4th-order Butterworth, filtfilt, 10 Hz. VCPDU_yaw is sampled at
100 Hz like the rest of the IMU, so 10 Hz is well inside Nyquist.

Outputs (all under plots/case6_max_yaw/):
- Console report per event.
- Per-file yaw trace, raw vs filtered -> <event>/<file>_yaw_before_after.html
- Per-event yaw-vs-lateral-G validation scatter -> <event>/yaw_validation.html
- ONE headline chart: yaw_rate_summary.html

Run it:
    uv run case6_max_yaw.py --dir comp2026_data

Uses parse_influx.py and case_common.py (must be in the same folder, or
importable).
"""

import os
import sys
import glob
import argparse

import numpy as np
import plotly.graph_objects as go

from parse_influx import parse_influx
from case_report import report_page, write_index
from case_common import (
    G,
    SKIDPAD_CUTOFF_HZ, AUTOX_END_CUTOFF_HZ,
    group_by_event,
    lowpass, elapsed_seconds, fill_gaps, trim_window,
    find_steady_segments, top_k_peaks,
    TRIM_SECONDS, TOP_K_PEAKS,
    build_raw_vs_filtered, thin_scatter, format_peak_shape,
    PLOT_TEMPLATE, DEEP_LINK_SCRIPT, titled,
)

CASE6_EVENTS = ["skidpad", "accel", "brake", "autocross", "endurance"]
STEADY_EVENTS = ("skidpad",)

PLOTS_ROOT = os.path.join("plots", "case6_max_yaw")

REQUIRED_SIGNALS = ["VCPDU_yaw", "VCPDU_lat", "VCFRONT_vehicleSpeed"]

# Peak-detection prominence for yaw rate, in deg/s. Justified the same way
# every other case justifies its prominence — against the signal's own
# noise floor measured while the car is stopped, which is 0.36 deg/s std
# (see the module docstring). 5 deg/s is ~14x that, and real event
# magnitudes are 50-80 deg/s, so this rejects noise without being anywhere
# near the signal.
PEAK_PROMINENCE_DEG_S = 5.0

# Below this the car is not meaningfully cornering, so v/omega is a radius
# through essentially straight-line noise and means nothing. Same 0.3 g
# idea as MIN_LAT_G_FOR_TURN, expressed in yaw rate: at 10 m/s, 0.3 g is
# about 17 deg/s.
MIN_YAW_FOR_CORNER = 10.0     # deg/s

# Radius is v/omega, which explodes as omega goes to zero. Gate on both:
# the car must be rotating (above) and actually moving.
MIN_SPEED_FOR_RADIUS = 3.0    # m/s

# The validation fit only means anything where the identity it tests is
# actually valid — the car must be moving and genuinely turning.
VALIDATION_MIN_SPEED_MS = 5.0
VALIDATION_MIN_LAT_MS2 = 3.0

# ── Course geometry, from the rulebook ───────────────────────────────────
#
# FSAE Rules 2027 DRAFT (V0.0, 21 July 2026), D.10.1.1 Course Design:
#     Inner circles   15.25 m in diameter
#     Outer circles   21.25 m in diameter
#     Driving path    the 3.0 m wide path between the inner and outer circles
#
# So the car may legally run any radius from 7.625 m (hugging the inner
# cones) to 10.625 m (against the outer edge), and the centre of the lane is
# 9.125 m. This is a REAL cross-check on the yaw channel, not decoration:
# R = v/omega is computed from two sensors that know nothing about the
# course, so a measured radius landing inside the legal band — and near the
# middle of it — is independent confirmation that both are calibrated.
SKIDPAD_INNER_RADIUS_M = 15.25 / 2      # 7.625 — the fastest legal line
SKIDPAD_OUTER_RADIUS_M = 21.25 / 2      # 10.625
SKIDPAD_CENTRE_RADIUS_M = (SKIDPAD_INNER_RADIUS_M + SKIDPAD_OUTER_RADIUS_M) / 2

# D.11.1.1 Autocross Layout, for context on the corner radii reported here:
#     Constant Turns   23 m to 45 m diameter   -> 11.5-22.5 m radius
#     Hairpin Turns    9 m minimum OUTSIDE diameter
#     Slaloms          cones 7.62 m to 12.19 m apart
#     Minimum track width 3.5 m
# A hairpin's 4.5 m outside radius is the tightest thing on the course, so a
# measured radius near that is a hairpin and one near 11-22 m is a constant
# turn. Endurance uses the same specifications (D.12).
AUTOX_CONSTANT_TURN_RADIUS_M = (11.5, 22.5)
AUTOX_HAIRPIN_OUTER_RADIUS_M = 4.5

EVENT_COLORS = {"skidpad": "#2a78d6", "accel": "#eda100", "brake": "#e34948",
                "autocross": "#1baf7a", "endurance": "#8b5cd6"}


# ── Parsing / derived signals ────────────────────────────────────────────

def load_yaw_signals(path, cutoff_hz):
    try:
        signals = parse_influx(path, verbose=False)
    except Exception as e:
        print(f"  [!] Failed to parse '{path}': {e}")
        return None
    if any(name not in signals for name in REQUIRED_SIGNALS):
        print(f"  [!] '{path}' missing required signals, skipping.")
        return None

    t_raw = np.asarray(signals["VCPDU_yaw"].time)
    dt = float(np.median(np.diff(t_raw)) / np.timedelta64(1, "s"))
    t = elapsed_seconds(t_raw)

    yaw_raw = fill_gaps(np.asarray(signals["VCPDU_yaw"].value, dtype=float))
    # VCPDU_lat is m/s^2 in the DBC — case1 divides by G to get g, and the
    # v*omega identity below needs SI, so both forms are kept explicitly
    # rather than one being silently reused for the other.
    lat_ms2 = fill_gaps(np.asarray(signals["VCPDU_lat"].value, dtype=float))
    speed = fill_gaps(np.asarray(signals["VCFRONT_vehicleSpeed"].value, dtype=float))

    yaw_f = lowpass(yaw_raw, dt, cutoff_hz)
    lat_f = lowpass(lat_ms2, dt, cutoff_hz)

    return {
        "path": path, "t": t, "dt": dt, "cutoff": cutoff_hz,
        "yaw_raw": yaw_raw, "yaw_f": yaw_f,
        "lat_ms2": lat_f, "lat_g": lat_f / G,
        "speed": speed,
    }


def validate_yaw(d):
    """Recompute the a_lat = v*omega check on THIS file.

    Returned every run rather than trusted from a note in the docstring:
    if a future export breaks or rescales the yaw channel, this moves and
    the report says so. Returns None where the file never corners fast
    enough for the identity to be meaningful (accel and brake runs mostly).
    """
    m = ((d["speed"] > VALIDATION_MIN_SPEED_MS)
         & (np.abs(d["lat_ms2"]) > VALIDATION_MIN_LAT_MS2))
    if m.sum() < 100:
        return None

    predicted = d["speed"][m] * np.radians(d["yaw_f"][m])
    measured = d["lat_ms2"][m]

    slope = float(np.polyfit(predicted, measured, 1)[0])
    r = float(np.corrcoef(predicted, measured)[0, 1])
    return {"r": r, "slope": slope, "n": int(m.sum())}


def classify_corner(radius_m):
    """Name the corner type from its radius, per FSAE 2027 D.11.1.1.

    Turns the abstract "R = 6.0 m" into "this was a hairpin", which is what
    makes the number mean something without a track map — and a track map
    is exactly what this data cannot produce (see the module docstring).
    """
    if radius_m is None:
        return ""
    if radius_m <= AUTOX_HAIRPIN_OUTER_RADIUS_M * 1.6:
        return "hairpin (rules: 9 m min outside diameter)"
    lo, hi = AUTOX_CONSTANT_TURN_RADIUS_M
    if lo <= radius_m <= hi:
        return f"constant turn (rules: {lo:.0f}-{hi:.0f} m radius)"
    if radius_m < lo:
        return "tight turn — between hairpin and constant-turn spec"
    return "long sweeper / slalom transition"


def corner_radius(d, idx):
    """R = v / omega at one instant, in metres, or None where meaningless.

    Radius is a ratio of two measured quantities and blows up as omega
    approaches zero, so both gates matter — see the constants above.
    """
    v = float(d["speed"][idx])
    omega = float(d["yaw_f"][idx])
    if v < MIN_SPEED_FOR_RADIUS or abs(omega) < MIN_YAW_FOR_CORNER:
        return None
    return v / abs(np.radians(omega))


# ── Analysis ─────────────────────────────────────────────────────────────

def analyze_file(path, cutoff_hz):
    d = load_yaw_signals(path, cutoff_hz)
    if d is None:
        return None

    # Peaks on |yaw|, exactly as case1 does for |lat G| — the car rotates
    # both ways and the question is "how fast", not "which way".
    idxs, vals = top_k_peaks(np.abs(d["yaw_f"]), d["t"], TOP_K_PEAKS,
                             prominence=PEAK_PROMINENCE_DEG_S)
    d["peaks"] = list(zip(idxs.tolist(), vals.tolist()))
    d["validation"] = validate_yaw(d)
    return d


def analyze_sustained(d):
    """Median |yaw rate| over the skidpad steady-state segments.

    Same windows case1/case2/case3 use, found from filtered lateral G — so
    a skidpad yaw number here is directly comparable to the lateral G and
    roll numbers those cases report for the same segments.
    """
    t = d["t"]
    segments = find_steady_segments(d["lat_g"], t)

    runs = []
    for sign, run_list in segments.items():
        for s, e, dur in run_list:
            ts, te = trim_window(t, s, e, TRIM_SECONDS)
            seg_yaw = d["yaw_f"][ts:te + 1]
            seg_speed = d["speed"][ts:te + 1]
            median_yaw = float(np.median(seg_yaw))
            median_speed = float(np.median(seg_speed))
            radius = (median_speed / abs(np.radians(median_yaw))
                      if abs(median_yaw) > MIN_YAW_FOR_CORNER else None)
            runs.append({
                "sign": int(sign), "duration_s": dur,
                "start_s": float(t[ts]), "end_s": float(t[te]),
                "median_yaw_deg_s": median_yaw,
                "median_speed_ms": median_speed,
                "radius_m": radius,
            })
    return sorted(runs, key=lambda r: r["start_s"])


def steady_spans(d):
    """POST-TRIM (start_s, end_s) of the segments the sustained number came
    from, for shading — same convention as case1/case2/case3."""
    return sorted((r["start_s"], r["end_s"]) for r in analyze_sustained(d))


# ── Plotting ─────────────────────────────────────────────────────────────

def peak_markers(d):
    rows = [(float(d["t"][idx]), f"#{rank}", float(d["yaw_f"][idx]))
            for rank, (idx, _v) in enumerate(d.get("peaks", []), 1)]
    return {0: rows} if rows else {}


def build_before_after_plot(d, output_path, event):
    build_raw_vs_filtered(
        panels=[("Yaw rate", d["yaw_raw"], d["yaw_f"], "deg/s")],
        t=d["t"],
        title=f"{os.path.basename(d['path'])} — yaw rate",
        output_path=output_path,
        cutoff_hz=d["cutoff"],
        shade=steady_spans(d) if event in STEADY_EVENTS else [],
        shade_label="steady-state window used for the sustained median",
        markers=peak_markers(d),
    )


def build_validation_plot(event, results, output_path):
    """a_lat against v*omega, the check that says the channel still works.

    A working yaw channel puts every file on the 1:1 line. This is the
    plot to look at first if a number here ever looks wrong — it separates
    "the car did something surprising" from "the sensor changed".
    """
    fig = go.Figure()

    lim = 0.0
    for r in results:
        m = ((r["speed"] > VALIDATION_MIN_SPEED_MS)
             & (np.abs(r["lat_ms2"]) > VALIDATION_MIN_LAT_MS2))
        if m.sum() < 100:
            continue
        predicted = r["speed"][m] * np.radians(r["yaw_f"][m])
        measured = r["lat_ms2"][m]
        px, py = thin_scatter(predicted, measured)
        lim = max(lim, float(np.max(np.abs(predicted))), float(np.max(np.abs(measured))))
        v = r["validation"] or {}
        fig.add_trace(go.Scattergl(
            x=px, y=py, mode="markers",
            name=f"{os.path.basename(r['path'])} (r={v.get('r', float('nan')):.3f})",
            marker=dict(size=3, opacity=0.30),
            hovertemplate="v·ω=%{x:.2f}<br>a_lat=%{y:.2f} m/s²<extra></extra>",
        ))

    if lim == 0.0:
        return False

    lim *= 1.05
    fig.add_trace(go.Scatter(
        x=[-lim, lim], y=[-lim, lim], mode="lines",
        name="perfect agreement (1:1)",
        line=dict(color="black", width=2, dash="dash"), hoverinfo="skip",
    ))

    fig.update_layout(
        xaxis_title="v · ω  — predicted lateral acceleration (m/s²)",
        yaxis_title="a_lat — measured lateral acceleration (m/s²)",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        template=PLOT_TEMPLATE,
    )
    titled(
        fig, f"{event.upper()} — yaw-rate validation",
        "a_lat vs v·ω. These share no sensor: lateral G is the IMU "
        "accelerometer, speed is the front wheels, yaw is the gyro. Points on "
        "the dashed line mean the yaw channel is sound.",
    )
    fig.write_html(output_path, include_plotlyjs="cdn")
    return True


def build_summary(summaries_by_event, output_path):
    """Headline chart: peak yaw rate per event, with the sustained skidpad
    value alongside where one exists."""
    events = [e for e in CASE6_EVENTS if summaries_by_event.get(e)]
    if not events:
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[e.upper() for e in events],
        y=[abs(summaries_by_event[e]["peak_yaw_deg_s"]) for e in events],
        name="peak yaw rate",
        marker=dict(color=[EVENT_COLORS.get(e, "#888") for e in events]),
        text=[f"{abs(summaries_by_event[e]['peak_yaw_deg_s']):.1f}" for e in events],
        textposition="outside",
    ))

    sustained = [(e.upper(), abs(summaries_by_event[e]["sustained_yaw_deg_s"]))
                 for e in events
                 if summaries_by_event[e].get("sustained_yaw_deg_s") is not None]
    if sustained:
        fig.add_trace(go.Bar(
            x=[e for e, _ in sustained], y=[v for _, v in sustained],
            name="sustained (steady-state median)",
            marker=dict(color="#a8a7a1"),
            text=[f"{v:.1f}" for _, v in sustained], textposition="outside",
        ))

    fig.update_layout(
        yaxis_title="Yaw rate (deg/s)",
        template=PLOT_TEMPLATE, barmode="group",
    )
    titled(fig, "Peak yaw rate by event",
           "how fast the car rotates about its vertical axis. Grey = "
           "sustained value where the event has one.")
    fig.write_html(output_path, include_plotlyjs="cdn",
                   post_script=DEEP_LINK_SCRIPT)


# ── Reporting ────────────────────────────────────────────────────────────

# Below this many qualifying samples the fit is describing a handful of
# marginal moments rather than the channel. Accel and brake are
# straight-line events by design — a weak r there says the CAR did not
# corner, not that the SENSOR is wrong, and reporting it as a failure sent
# exactly the wrong signal.
VALIDATION_MIN_SAMPLES = 10000


def report_validation(event, results):
    print(f"\n  --- {event.upper()} yaw-channel validation (a_lat vs v*omega) ---")
    conclusive = False
    for r in results:
        v = r["validation"]
        if v is None:
            print(f"    {os.path.basename(r['path']):26} not a cornering event "
                  f"— too few samples above {VALIDATION_MIN_SPEED_MS:.0f} m/s "
                  f"and {VALIDATION_MIN_LAT_MS2:.0f} m/s² lateral to test")
            continue

        if v["n"] < VALIDATION_MIN_SAMPLES:
            verdict = "inconclusive — barely corners, not a test of the channel"
        elif v["r"] > 0.9:
            verdict = "GOOD"
            conclusive = True
        elif v["r"] > 0.7:
            verdict = "WEAK"
            conclusive = True
        else:
            verdict = "FAILS — do not trust yaw on this file"
            conclusive = True

        print(f"    {os.path.basename(r['path']):26} r={v['r']:+.4f}  "
              f"slope={v['slope']:.3f}  ({v['n']} samples)   [{verdict}]")

    if conclusive:
        print(f"    slope >1 is expected: the identity assumes zero sideslip, "
              f"and wheel speed under-reads through a corner.")


def report_event(event, results):
    print(f"\n=== {event.upper()} — MAX YAW RATE "
          f"(peak detection, {results[0]['cutoff']} Hz low-pass) ===")

    pool = []
    for r in results:
        for idx, val in r["peaks"]:
            pool.append((val, r, idx))
    if not pool:
        print(f"  no peaks found (check PEAK_PROMINENCE_DEG_S="
              f"{PEAK_PROMINENCE_DEG_S})")
        return None
    pool.sort(key=lambda x: x[0], reverse=True)

    top = pool[:TOP_K_PEAKS]
    print(f"  Top {len(top)} peaks (pooled across files):")
    for val, r, idx in top:
        radius = corner_radius(r, idx)
        radius_s = f"R={radius:6.1f}m" if radius else "R=  —   "
        direction = "left" if r["yaw_f"][idx] > 0 else "right"
        print(f"    {os.path.basename(r['path']):26} @ {r['t'][idx]:8.2f}s  "
              f"{r['yaw_f'][idx]:+7.2f}°/s ({direction:5})  "
              f"v={r['speed'][idx]:5.1f}m/s  {radius_s}")

    avg = float(np.mean([v for v, _, _ in top]))
    print(f"  Top {len(top)} averaged: {avg:.2f}°/s")

    best_val, best_r, best_idx = pool[0]
    signed = float(best_r["yaw_f"][best_idx])
    radius = corner_radius(best_r, best_idx)

    print(f"\n  SINGLE HIGHEST — {os.path.basename(best_r['path'])} "
          f"@ {best_r['t'][best_idx]:.2f}s")
    print(f"    yaw rate: {signed:+.2f}°/s  "
          f"({'rotating LEFT' if signed > 0 else 'rotating RIGHT'})"
          + format_peak_shape(np.abs(best_r["yaw_f"]), best_r["t"],
                              best_idx, "°/s"))
    print(f"    at that instant: speed={best_r['speed'][best_idx]:.1f} m/s, "
          f"lateral={best_r['lat_g'][best_idx]:+.2f} g")
    if radius:
        print(f"    corner radius being followed: {radius:.1f} m "
              f"(R = v/omega — the line the driver took, not the corner's "
              f"painted radius)")
        kind = classify_corner(radius)
        if kind and event not in STEADY_EVENTS:
            print(f"    that radius is a {kind}")
    else:
        print(f"    corner radius: not meaningful here (needs "
              f">{MIN_SPEED_FOR_RADIUS:.0f} m/s and "
              f">{MIN_YAW_FOR_CORNER:.0f}°/s)")

    summary = {
        "peak_yaw_deg_s": signed,
        "top_avg_yaw_deg_s": avg,
        "peak_radius_m": radius,
        "sustained_yaw_deg_s": None,
        "sustained_radius_m": None,
        "_instants": [{
            "event": event, "path": best_r["path"],
            "t": float(best_r["t"][best_idx]),
            "label": f"peak yaw rate — {signed:+.1f}°/s",
            "detail": (f"{best_r['speed'][best_idx]:.1f} m/s"
                       + (f", R={radius:.1f} m" if radius else "")),
        }],
    }
    return summary


def report_sustained(event, results, summary):
    print(f"\n  --- {event.upper()} SUSTAINED (median over steady-state "
          f"segments, same windows as case1/case2) ---")
    pooled_yaw, pooled_radius = [], []
    for r in results:
        runs = analyze_sustained(r)
        if not runs:
            print(f"    [!] {os.path.basename(r['path'])}: no qualifying "
                  f"steady window.")
            continue
        for i, run in enumerate(runs, 1):
            radius_s = (f"R={run['radius_m']:5.1f}m" if run["radius_m"]
                        else "R=  —   ")
            print(f"    {os.path.basename(r['path']):26} run {i} "
                  f"({run['duration_s']:4.1f}s): "
                  f"{run['median_yaw_deg_s']:+7.2f}°/s  "
                  f"v={run['median_speed_ms']:5.1f}m/s  {radius_s}")
            pooled_yaw.append(abs(run["median_yaw_deg_s"]))
            if run["radius_m"]:
                pooled_radius.append(run["radius_m"])

    if not pooled_yaw:
        return

    median_yaw = float(np.median(pooled_yaw))
    summary["sustained_yaw_deg_s"] = median_yaw
    print(f"    Across runs: {median_yaw:.2f}°/s")

    if pooled_radius:
        median_radius = float(np.median(pooled_radius))
        summary["sustained_radius_m"] = median_radius

        # GEOMETRY CROSS-CHECK. R = v/omega comes from two sensors that know
        # nothing about the course, so where it lands relative to the
        # rulebook's fixed circles is independent evidence about the
        # calibration of both. Rulebook figures: D.10.1.1.
        print(f"    Median radius followed: {median_radius:.2f} m")
        print(f"    FSAE 2027 D.10.1.1 — legal band "
              f"{SKIDPAD_INNER_RADIUS_M:.3f} m (inner cones) to "
              f"{SKIDPAD_OUTER_RADIUS_M:.3f} m (outer edge), "
              f"lane centre {SKIDPAD_CENTRE_RADIUS_M:.3f} m")

        if SKIDPAD_INNER_RADIUS_M <= median_radius <= SKIDPAD_OUTER_RADIUS_M:
            offset = median_radius - SKIDPAD_INNER_RADIUS_M
            print(f"    -> INSIDE the legal 3.0 m lane, {offset:.2f} m out "
                  f"from the inner cones. The yaw channel and the wheel-speed "
                  f"channel independently agree with the course geometry.")
            print(f"       Line note: the inner edge is the fastest legal "
                  f"line, so {offset:.2f} m of margin is lap time left on the "
                  f"table — a driver observation, not a data problem.")
        else:
            side = "INSIDE the inner cones" if median_radius < SKIDPAD_INNER_RADIUS_M \
                   else "OUTSIDE the outer edge"
            print(f"    -> [!] {side} — physically impossible on a legal run. "
                  f"Suspect the yaw scale or the speed calibration before "
                  f"trusting anything else on this page.")


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

    print(f"Low-pass: {SKIDPAD_CUTOFF_HZ} Hz skidpad, "
          f"{AUTOX_END_CUTOFF_HZ} Hz everything else "
          f"(4th-order Butterworth, zero-phase)")
    print(f"Yaw sign: positive = rotating LEFT (established against lateral "
          f"G, see module docstring)")

    summaries_by_event = {}

    for event in CASE6_EVENTS:
        paths = grouped.get(event, [])
        if not paths:
            continue

        cutoff = SKIDPAD_CUTOFF_HZ if event == "skidpad" else AUTOX_END_CUTOFF_HZ
        results = [r for p in paths
                   if (r := analyze_file(p, cutoff)) is not None]
        if not results:
            continue

        out_dir = os.path.join(PLOTS_ROOT, event)
        os.makedirs(out_dir, exist_ok=True)

        report_validation(event, results)
        summary = report_event(event, results)

        if summary and event in STEADY_EVENTS:
            report_sustained(event, results, summary)

        for r in results:
            fname = os.path.splitext(os.path.basename(r["path"]))[0]
            build_before_after_plot(
                r, os.path.join(out_dir, f"{fname}_yaw_before_after.html"), event)

        build_validation_plot(event, results,
                              os.path.join(out_dir, "yaw_validation.html"))

        summaries_by_event[event] = summary
        print(f"\n  Plots saved to: {out_dir}/")

    os.makedirs(PLOTS_ROOT, exist_ok=True)
    build_summary(summaries_by_event,
                  os.path.join(PLOTS_ROOT, "yaw_rate_summary.html"))

    print("\n" + "=" * 72)
    print("PEAK YAW RATE ACROSS ALL EVENTS")
    print("=" * 72)
    ranked = sorted(((e, s) for e, s in summaries_by_event.items() if s),
                    key=lambda kv: abs(kv[1]["peak_yaw_deg_s"]), reverse=True)
    for e, s in ranked:
        radius = (f"R={s['peak_radius_m']:.1f}m" if s.get("peak_radius_m")
                  else "R=—")
        print(f"  {e.upper():10} {s['peak_yaw_deg_s']:+7.2f}°/s   {radius}")
    if ranked:
        e, s = ranked[0]
        print(f"\n  -> Fastest rotation: {e.upper()}, "
              f"{abs(s['peak_yaw_deg_s']):.1f}°/s")

    print("\nDone.")
    return summaries_by_event


CONVENTIONS = [
    "<b>Yaw rate positive = rotating LEFT</b> (counter-clockwise seen from "
    "above), matching case1's lateral-G convention. Established by "
    "cross-reference against lateral G (r = +0.96 to +0.99), not assumed.",
    "<b>Corner radius is R = v/ω</b> — the radius of the line the car is "
    "actually following, which is <i>not</i> the painted radius of the "
    "corner. The difference is the driver's line.",
    "<b>This channel is validated every run</b>, not trusted from a note. "
    "The identity <code>a_lat = v·ω</code> shares no sensor with the gyro, "
    "so the per-file r and slope in the validation section say whether the "
    "yaw channel is still sound. A slope above 1.0 is expected — the "
    "identity assumes zero sideslip and wheel speed under-reads in a corner.",
    "<b>Nothing here is integrated.</b> Yaw rate has a 7–18% scale error "
    "that is harmless instantaneously and fatal once accumulated — it is "
    "why dead-reckoning a track map fails. Every number on this page is an "
    "instantaneous value or a ratio of two, never an integral.",
    "The roll and pitch channels of this <i>same sensor</i> are NOT usable: "
    "chassis roll is 0.82 °/s RMS against a 0.45 °/s noise floor, while yaw "
    "is 49.6 against 0.36. Use the shock pots for roll and pitch.",
]


if __name__ == "__main__":
    with report_page("case6_max_yaw", "Case 6 — Max Yaw Rate",
                     PLOTS_ROOT) as page:
        page.summary = main()
        for text in CONVENTIONS:
            page.add_convention(text)
        for event_summary in (page.summary or {}).values():
            for item in (event_summary or {}).get("_instants", []):
                page.add_instant(item["event"], item["path"], item["t"],
                                 item["label"], item["detail"])
    write_index()
