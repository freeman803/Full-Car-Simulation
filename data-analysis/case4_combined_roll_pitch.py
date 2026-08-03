# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
case4_combined_roll_pitch.py — Case 4: combined roll + pitch loading, for
ACCEL, BRAKE, SKIDPAD, AUTOCROSS and ENDURANCE (kept separate), from the same
4 shock-pot displacement signals case2_max_roll.py and case3_max_pitch.py use.

WHY THIS ISN'T "sqrt(roll^2 + pitch^2)" — the obvious formulation was tried
first and rejected against real data. Two measurements killed it:

  1. Roll and pitch peaks essentially never coincide. Measured gap between
     each file's worst-|roll| instant and worst-|pitch| instant:
     endurance_full 869s, autocross_andrew1 53s, autocross_josh1 26s,
     autocross_andrew2 20s. These are independent events, not one combined
     event.
  2. Roll is 2-4x larger than pitch on this car (max |roll| ~1.45 deg vs
     max |pitch| ~0.81 deg), so a root-sum-square is captured almost
     entirely by roll. On endurance_full the "combined" answer came out
     1.450 deg at an instant where pitch was +0.034 deg — i.e. identical
     to case2's max-roll answer, to three decimals. It measured nothing new.

So case4 reports PER-CORNER WHEEL TRAVEL instead. That is where roll and
pitch genuinely superpose: a single corner's displacement is the physical
sum of every attitude mode acting at that moment. It also needs no
arbitrary "both axes elevated" threshold, and it is the quantity that
actually decides whether a spring/damper runs out of travel — which is the
number you want when setting roll and pitch targets for the next
suspension.

THE FOUR MODES, in words. Any way four corners can move is exactly one
combination of these four, and they are mutually independent — that is what
makes the decomposition an identity rather than a fit.

  HEAVE — all four corners move the SAME way at once. The whole car rising
    or squatting flat, with no attitude change. Comes from aero load, a
    crest or a dip, or the car settling. Large heave means the springs are
    absorbing load evenly; it is the mode a driver feels as the car getting
    lower, not as it leaning.

  ROLL — left pair and right pair move OPPOSITE ways. Cornering lean.

  PITCH — front pair and rear pair move OPPOSITE ways. Dive under braking,
    squat under acceleration.

  WARP — the DIAGONALS move opposite ways: FL and RR go one way while FR and
    RL go the other. This is the chassis being TWISTED along its length,
    like wringing a towel, rather than leaned or pitched. It is what a
    single-wheel bump or a one-wheel kerb strike produces, and it is the one
    mode that shows up in neither case2 nor case3 — both of those average
    corners in pairs, which cancels warp exactly. Worth watching because
    warp load goes into chassis torsional stiffness rather than into the
    springs, and because a car with high warp on a smooth surface is
    usually telling you something about diagonal weight distribution.

MODAL DECOMPOSITION — the headline number is decomposed exactly (this is an
algebraic identity, not an approximation or a fit):

    heave = (FL + FR + RL + RR) / 4
    roll  = ((FR + RR) - (FL + RL)) / 4
    pitch = ((FL + FR) - (RL + RR)) / 4
    warp  = ((FL + RR) - (FR + RL)) / 4

    FL = heave - roll + pitch + warp
    FR = heave + roll + pitch - warp
    RL = heave - roll - pitch - warp
    RR = heave + roll - pitch + warp

Every corner is reconstructed to within floating-point error (asserted at
runtime). So at the worst instant we can say precisely how many mm came
from roll vs pitch vs heave vs warp. WARP (diagonal load transfer) is
visible here and in neither case2 nor case3 — worth watching, since large
warp means the chassis is being twisted diagonally rather than rolled or
pitched cleanly.

SIGN CONVENTION — inherited from case3's empirical verification against
vehicle speed (see that file's docstring; a HIGHER mm reading is more
EXTENSION on this car's shock-pot calibration). Applied to a single corner
relative to its own static baseline:
    travel_mm < 0  ~ COMPRESSION (bump)  <- this is what bottoms a damper
    travel_mm > 0  ~ EXTENSION (droop)   <- this is what tops one out
Both extremes are reported, since both have a mechanical limit.

Filtering is IDENTICAL to case1/case2/case3 (imported from case_common, not
redefined): 4th-order Butterworth, filtfilt, 10 Hz for every event.
Retuned 2026-07-31 from cutoff_sweep.py — see the README.

Methodology per event — all five events are covered, which corrects the
original scoping assumption. It was assumed skidpad/accel/brake were
effectively single-axis and could be skipped; measuring the fraction of
samples with BOTH |latG| and |lonG| above 0.3 g showed otherwise:
endurance 75.9%, autocross 44-75%, SKIDPAD 59.0%, BRAKE 19-40%,
accel 15-22%. Skidpad in particular is a two-run file including entry, exit
and the transit between circles, so it is not the pure steady-state case
its name suggests.

- ALL EVENTS: worst-case per-corner travel via peak detection on the
  4-corner envelope max(|FL|,|FR|,|RL|,|RR|) (prominence + minimum
  spacing, same helper case1/2/3 use), top 5 pooled + single worst, with
  the full modal decomposition reported at that single worst instant.
  Worst case is the question case4 is asking, so this is applied uniformly
  rather than switching methodology per event.

- SKIDPAD and ACCEL additionally get a SUSTAINED number: median per-corner
  travel over the same steady-state segments case2/case3 use (lateral-G
  segments for skidpad, negative-longitudinal-G segments for accel).
  A sustained value is the more useful target for those two quasi-steady
  events, and it is reported alongside the worst-case peak rather than
  instead of it.

Peak-detection prominence is 2.0mm, matching case2. Justified against real
data the same way: per-corner noise std during each file's stopped-car
window is 0.002-0.132mm across 10 of 11 files (median 0.031mm), while real
event magnitudes are 7-25mm. NOTE the exception — braketest2.csv shows
0.394mm (FL) and 0.667mm (FR), 10-20x every other file, so its
stopped-car window is probably not genuinely stopped; its numbers deserve
more suspicion than the rest.

Outputs (all under plots/case4_combined_roll_pitch/):
- Console report per event.
- Per-file 4-corner travel plot -> <event>/<file>_corner_travel.html
- Per-event roll-pitch envelope scatter -> <event>/roll_pitch_envelope.html
- ONE headline chart: corner_travel_summary.html

Run it:
    uv run case4_combined_roll_pitch.py --dir comp2026_data

Uses parse_influx.py and case_common.py (must be in the same folder, or
importable). Vehicle geometry constants below are plain hardcoded values —
deliberately NOT imported from corner-model/ (kept independent of that or
any other simulation model, same as case2/case3).
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
    FILTER_ORDER, SKIDPAD_CUTOFF_HZ, AUTOX_END_CUTOFF_HZ,
    group_by_event,
    lowpass, elapsed_seconds, trim_window,
    find_steady_segments, top_k_peaks,
    baseline_corner_displacements, to_wheel_travel, find_step_glitches,
    CORNERS, MOTION_RATIO_FRONT, MOTION_RATIO_REAR,
    TRIM_SECONDS, TOP_K_PEAKS,
    FRONT_TRACK_MM, REAR_TRACK_MM, WHEELBASE_MM, AVG_TRACK_MM, mm_to_deg,
    PLOT_TEMPLATE, PLOT_STEADY_FILL, decimate_for_plot, thin_scatter, titled,
    format_peak_shape, DEEP_LINK_SCRIPT,
)

# Vehicle geometry and the mm -> degree conversion now come from
# case_common too. They used to be redefined here, in case2 and in case3;
# the values agreed, but nothing enforced it. See case_common for the note
# on AVG_TRACK_MM being an approximation for whole-car roll.

# Motion ratio now comes from case_common (measured: 1.188 front, 1.038
# rear, wheel/spring displacement) and is applied PER CORNER before any
# modal arithmetic — see case_common.to_wheel_travel(). Everything below
# this point works in WHEEL millimetres, not shock-pot millimetres.
#
# For the record on the earlier placeholder: the IMU's own
# VCPDU_angleRoll/anglePitch were checked as an independent reference and
# are NOT usable — they read +/-20-36 deg against +/-1.3 deg derived here
# (20-30x), consistent with an uncalibrated gravity-vector tilt rather
# than chassis attitude (the DBC carries IMU_UNCALIBRATED and
# IMU_YAW_CALIBRATION_FAILED warnings).

# Longitudinal-G threshold for "accelerating hard", same as case3.
MIN_LON_G_FOR_MANEUVER = 0.3   # g

# Peak-detection prominence for per-corner travel, in mm — see docstring
# for the noise-floor measurement behind this.
PEAK_PROMINENCE_MM = 2.0

# filtfilt pads at the array boundaries, so a file that ends mid-event
# overshoots there. The peak-detection path is immune (find_peaks needs a
# turning point, which a boundary ramp has not got), but the raw min/max
# per-corner extremes are NOT — so they ignore this much of each end.
# Confirmed real on accel_corinne1: filtered pitch peaked at 17.36mm
# against a 16.33mm raw peak, at sample 74944 of 75545, because the file
# simply stops while pitch is still at 16.19mm. Interior peak was 13.31mm.
EDGE_EXCLUDE_FRACTION = 0.02

CASE4_EVENTS = ["accel", "brake", "skidpad", "autocross", "endurance"]
STEADY_EVENTS = ("skidpad", "accel")   # these also get a sustained number

PLOTS_ROOT = os.path.join("plots", "case4_combined_roll_pitch")

CORNER_COLORS = {"FL": "#2a78d6", "FR": "#e34948", "RL": "#48b56b", "RR": "#d69a2a"}


# ── mm -> deg conversions (mm_to_deg imported from case_common) ──────────

def roll_deg(roll_mm):
    return mm_to_deg(roll_mm, AVG_TRACK_MM)


def pitch_deg(pitch_mm):
    return mm_to_deg(pitch_mm, WHEELBASE_MM)


# ── Modal decomposition ──────────────────────────────────────────────────

def decompose_modes(fl, fr, rl, rr):
    """Exact heave/roll/pitch/warp decomposition of four corner travels.

    Returns a dict of four arrays. This is an algebraic identity — see the
    module docstring for the reconstruction formulas. Note the mm scale
    here is 'per corner': each mode's value is the number of mm it
    contributes to any one corner, so the four modes sum (with the right
    signs) to exactly that corner's travel.
    """
    return {
        "heave": (fl + fr + rl + rr) / 4.0,
        "roll": ((fr + rr) - (fl + rl)) / 4.0,
        "pitch": ((fl + fr) - (rl + rr)) / 4.0,
        "warp": ((fl + rr) - (fr + rl)) / 4.0,
    }


# Sign of each mode's contribution to each corner (see docstring identity).
MODE_SIGNS = {
    "FL": {"heave": +1, "roll": -1, "pitch": +1, "warp": +1},
    "FR": {"heave": +1, "roll": +1, "pitch": +1, "warp": -1},
    "RL": {"heave": +1, "roll": -1, "pitch": -1, "warp": -1},
    "RR": {"heave": +1, "roll": +1, "pitch": -1, "warp": +1},
}


def reconstruct(modes, corner, idx=None):
    """Rebuild one corner's travel from the modes, to verify the identity."""
    signs = MODE_SIGNS[corner]
    total = sum(signs[m] * (modes[m] if idx is None else modes[m][idx])
                for m in ("heave", "roll", "pitch", "warp"))
    return total


# ── Parsing / derived signals ────────────────────────────────────────────

REQUIRED_SIGNALS = [
    "VCFRONT_shockpotdispFL", "VCFRONT_shockpotdispFR",
    "VCREAR_shockpotdispRL", "VCREAR_shockpotdispRR",
    "VCPDU_lat", "VCPDU_lon", "VCFRONT_vehicleSpeed",
]


def load_corner_signals(path, cutoff_hz):
    try:
        signals = parse_influx(path, verbose=False)
    except Exception as e:
        print(f"  [!] Failed to parse '{path}': {e}")
        return None
    if any(name not in signals for name in REQUIRED_SIGNALS):
        print(f"  [!] '{path}' missing required signals, skipping.")
        return None

    # VCPDU_lat/VCPDU_lon are m/s^2 in the DBC (range [-32|32]) — convert to
    # g, as case1_max_gs.py does. case2/case3 originally omitted this and
    # gated their steady-segment detection at an effective 0.031 g; see those
    # files' comments.
    lat_raw = np.asarray(signals["VCPDU_lat"].value, dtype=float) / G
    lon_raw = np.asarray(signals["VCPDU_lon"].value, dtype=float) / G
    speed = np.asarray(signals["VCFRONT_vehicleSpeed"].value, dtype=float)

    t_raw = np.asarray(signals["VCFRONT_shockpotdispFL"].time)
    dt = float(np.median(np.diff(t_raw)) / np.timedelta64(1, "s"))
    t = elapsed_seconds(t_raw)

    # Per-corner static baselining (shared helper — case2/case3 do the same
    # thing inline; this is the pattern factored into case_common).
    corners_raw, baselines, baselines_found = baseline_corner_displacements(
        signals, t, speed)
    if not baselines_found:
        print(f"  [!] {os.path.basename(path)}: no stopped-car window found — "
              f"corner travel is NOT baselined for this file (raw values used as-is).")

    # Step-glitch detection on RAW shock-pot mm, before filtering or the
    # motion-ratio conversion — see case_common.find_step_glitches(). These
    # steps are bigger than any real event, so without masking they win the
    # peak search outright.
    glitch_mask, glitch_events = find_step_glitches(corners_raw, t)
    if glitch_events:
        print(f"  [!] {os.path.basename(path)}: {len(glitch_events)} step glitch(es) "
              f"excluded — " + ", ".join(f"{c} {j:.1f}mm @{ts:.2f}s"
                                          for c, ts, j in glitch_events))

    # Shock-pot mm -> WHEEL mm, per corner (front 1.188, rear 1.038) BEFORE
    # any roll/pitch/modal arithmetic. Everything downstream is wheel travel.
    corners_wheel = to_wheel_travel(corners_raw)
    travel = {c: lowpass(corners_wheel[c], dt, cutoff_hz) for c in CORNERS}
    modes = decompose_modes(travel["FL"], travel["FR"], travel["RL"], travel["RR"])

    # The decomposition is an identity — assert it rather than trust it.
    for c in CORNERS:
        if not np.allclose(reconstruct(modes, c), travel[c], atol=1e-9):
            raise AssertionError(f"modal decomposition failed to reconstruct {c} in {path}")

    # 4-corner envelope: the largest-magnitude corner at each instant.
    stack = np.column_stack([travel[c] for c in CORNERS])
    envelope = np.max(np.abs(stack), axis=1)
    worst_corner_at = np.array(CORNERS, dtype=object)[np.argmax(np.abs(stack), axis=1)]

    # Zero the envelope across glitch windows so the peak search cannot pick
    # them. Zeroing (rather than NaN) is safe because the envelope is a
    # magnitude: it leaves a notch, never a spurious peak.
    envelope = np.where(glitch_mask, 0.0, envelope)

    # case2/case3-compatible whole-car roll and pitch, for the scatter plot
    # and for cross-referencing back to those cases. roll_avg here is the
    # mean of front and rear roll, exactly as case2 defines it.
    #
    # SIGN CONVENTION — the OPPOSITE of what these two lines suggest at a
    # glance, so read this before interpreting the sign of any roll number
    # below. A HIGHER mm reading is more EXTENSION on this car's shock-pot
    # calibration (established empirically in case3_max_pitch.py against
    # vehicle speed), so the corner reading higher is the UNLOADED one:
    #
    #     roll_* > 0  ~  right side EXTENDED, LEFT side compressed
    #     roll_* < 0  ~  left side extended, RIGHT side compressed
    #
    # Verified on skidpad: at negative lateral G, FL = -6.53mm (compressed)
    # and FR = +15.97mm (extended), giving roll_front = +22.55mm, with a
    # correlation of -0.998 against lateral G. case2 carried the inverted
    # description in its docs for a while (fixed in fe05750) — magnitudes
    # were never wrong, but anyone reading it concluded the car rolled the
    # other way. Same trap applies here.
    roll_front = travel["FR"] - travel["FL"]
    roll_rear = travel["RR"] - travel["RL"]
    roll_avg = (roll_front + roll_rear) / 2.0
    front_avg = (travel["FL"] + travel["FR"]) / 2.0
    rear_avg = (travel["RL"] + travel["RR"]) / 2.0
    pitch_mm = front_avg - rear_avg

    return {
        "path": path, "t": t, "dt": dt, "cutoff": cutoff_hz,
        "travel": travel, "modes": modes,
        "envelope": envelope, "worst_corner_at": worst_corner_at,
        "glitch_mask": glitch_mask, "glitch_events": glitch_events,
        "roll_mm": roll_avg, "pitch_mm": pitch_mm,
        "roll_deg": roll_deg(roll_avg), "pitch_deg": pitch_deg(pitch_mm),
        "lat_f": lowpass(lat_raw, dt, cutoff_hz),
        "lon_f": lowpass(lon_raw, dt, cutoff_hz),
        # Kept so describe_instant() can say how fast the car was going.
        # Coarse gate only — never differentiated (see case3's docstring).
        "speed": np.asarray(speed, dtype=float),
        "baselines_found": baselines_found, "baselines": baselines,
    }


# ── Worst-case analysis (all events) ─────────────────────────────────────

def analyze_worst_case(path, cutoff_hz):
    d = load_corner_signals(path, cutoff_hz)
    if d is None:
        return None
    idxs, vals = top_k_peaks(d["envelope"], d["t"], TOP_K_PEAKS,
                             prominence=PEAK_PROMINENCE_MM)
    d["peaks"] = list(zip(idxs.tolist(), vals.tolist()))
    return d


# ── Sustained analysis (skidpad / accel only) ────────────────────────────

def analyze_sustained(d, event):
    """Median per-corner travel over the steady-state segments case2/case3
    use — lateral-G segments for skidpad, the accelerating (negative) branch
    of longitudinal-G segments for accel. Returns None if no window found."""
    t = d["t"]
    if event == "skidpad":
        segments = find_steady_segments(d["lat_f"], t)
    else:
        segments = find_steady_segments(d["lon_f"], t, threshold=MIN_LON_G_FOR_MANEUVER)
        segments = {sg: runs for sg, runs in segments.items() if np.sign(sg) < 0}

    pooled = {c: [] for c in CORNERS}
    pooled_modes = {m: [] for m in ("heave", "roll", "pitch", "warp")}
    n_runs = 0
    for runs in segments.values():
        for s, e, _dur in runs:
            ts, te = trim_window(t, s, e, TRIM_SECONDS)
            n_runs += 1
            for c in CORNERS:
                pooled[c].append(d["travel"][c][ts:te + 1])
            for m in pooled_modes:
                pooled_modes[m].append(d["modes"][m][ts:te + 1])
    if not n_runs:
        return None
    return {
        "n_runs": n_runs,
        "corner_median_mm": {c: float(np.median(np.concatenate(pooled[c]))) for c in CORNERS},
        "mode_median_mm": {m: float(np.median(np.concatenate(pooled_modes[m])))
                            for m in pooled_modes},
    }


# ── Plotting ─────────────────────────────────────────────────────────────

def steady_spans(d, event):
    """POST-TRIM (start_s, end_s) of the windows the SUSTAINED number came
    from, for shading. Only skidpad and accel have one — the other three
    events are worst-case-only, so there is no window to mark."""
    if event not in STEADY_EVENTS:
        return []
    t = d["t"]
    if event == "skidpad":
        segments = find_steady_segments(d["lat_f"], t)
    else:
        segments = find_steady_segments(d["lon_f"], t, threshold=MIN_LON_G_FOR_MANEUVER)
        segments = {sg: runs for sg, runs in segments.items() if np.sign(sg) < 0}

    spans = []
    for runs in segments.values():
        for s, e, _dur in runs:
            ts, te = trim_window(t, s, e, TRIM_SECONDS)
            spans.append((float(t[ts]), float(t[te])))
    return sorted(spans)


def build_corner_travel_plot(d, output_path, event=None):
    fig = go.Figure()
    t = d["t"]

    # Steady windows go down FIRST and as a layer="below" shape, so the
    # four traces are never tinted by the fill.
    spans = steady_spans(d, event) if event else []
    for start_s, end_s in spans:
        fig.add_vrect(x0=start_s, x1=end_s, fillcolor=PLOT_STEADY_FILL,
                      line_width=0, layer="below")

    # Display-only, and the worst-instant marker below is still indexed off
    # the FULL arrays — decimation cannot move where the peak was found.
    t_plot, travel_plot = decimate_for_plot(t, [d["travel"][c] for c in CORNERS])

    for c, values in zip(CORNERS, travel_plot):
        fig.add_trace(go.Scattergl(x=t_plot, y=values, mode="lines", name=f"{c} travel",
                                    line=dict(color=CORNER_COLORS[c], width=1.4)))
    if d.get("peaks"):
        worst_idx = max(d["peaks"], key=lambda p: p[1])[0]
        fig.add_vline(x=t[worst_idx], line=dict(color="black", width=1, dash="dot"))
        fig.add_annotation(x=t[worst_idx], y=d["envelope"][worst_idx],
                           text=f"worst: {d['worst_corner_at'][worst_idx]} "
                                f"{d['travel'][d['worst_corner_at'][worst_idx]][worst_idx]:+.1f}mm",
                           showarrow=True, arrowhead=2)
    subtitle = f"{d['cutoff']} Hz low-pass · negative = compression (bump)"
    if spans:
        subtitle += (f" · <span style='color:#1baf7a'>green</span> = "
                     f"steady-state window behind the sustained number "
                     f"({len(spans)})")

    fig.update_layout(
        xaxis_title="Elapsed time (s)",
        yaxis_title="Travel vs. static (mm)",
        template=PLOT_TEMPLATE,
        hovermode="x unified",
    )
    titled(fig, f"{os.path.basename(d['path'])} — per-corner wheel travel",
           subtitle)
    fig.update_xaxes(rangeslider_visible=True)
    # post_script makes '#t=116.59' zoom this plot to that instant — the
    # report page's key-instants table links here that way.
    fig.write_html(output_path, include_plotlyjs="cdn",
                   post_script=DEEP_LINK_SCRIPT)


# ── Travel limits ────────────────────────────────────────────────────────
#
# NOT KNOWN YET — set these and the distribution plot becomes a MARGIN
# plot, which is the whole point of it. Until then it reports how much
# travel the car USES, which is still worth having but is only half the
# question.
#
# What is needed is WHEEL travel at the bump stop and at full droop,
# relative to the static ride height these numbers are already zeroed to.
# Signs follow the rest of case4: negative = compression (bump), positive =
# extension (droop). So e.g. BUMP_LIMIT_MM = -35.0, DROOP_LIMIT_MM = +30.0.
#
# If they are only known as SHOCK travel, divide by the motion ratio per
# corner (front 1.188, rear 1.038) before entering them here — everything in
# this file is wheel millimetres.
BUMP_LIMIT_MM = None      # most negative wheel travel available
DROOP_LIMIT_MM = None     # most positive wheel travel available

# Percentiles reported per corner. p1/p99 rather than the raw min/max is
# what tells you about the working range: an extreme is one instant and can
# be a kerb strike, while p99 is where the corner actually lives when it is
# working hard.
TRAVEL_PERCENTILES = (1, 50, 99)


def build_travel_distribution(event, results, output_path):
    """How much of its available travel each corner actually uses.

    A histogram per corner, on a shared axis so the four are directly
    comparable. With BUMP/DROOP limits set it also shades the unusable
    region and the plot answers "how much margin is left"; without them it
    answers "how much travel is used", which is the same measurement
    without the reference.

    Glitch-masked and edge-trimmed the same way report_event's per-corner
    extremes are — otherwise a step glitch or a filtfilt boundary overshoot
    lands in the histogram as real travel.
    """
    fig = go.Figure()

    pooled = {c: [] for c in CORNERS}
    for r in results:
        for corner in CORNERS:
            values = r["travel"][corner]
            edge = int(EDGE_EXCLUDE_FRACTION * len(values))
            keep = ~r["glitch_mask"]
            if edge and len(values) > 2 * edge:
                keep[:edge] = False
                keep[len(values) - edge:] = False
            pooled[corner].append(values[keep])

    stats = {}
    for corner in CORNERS:
        values = np.concatenate(pooled[corner]) if pooled[corner] else np.array([])
        values = values[np.isfinite(values)]
        if not values.size:
            continue
        stats[corner] = {
            "p": {q: float(np.percentile(values, q)) for q in TRAVEL_PERCENTILES},
            "min": float(values.min()), "max": float(values.max()),
        }
        fig.add_trace(go.Histogram(
            x=values, name=corner, opacity=0.55, nbinsx=120,
            marker=dict(color=CORNER_COLORS[corner]),
            hovertemplate=f"{corner}: %{{x:.1f}}mm<br>%{{y}} samples<extra></extra>",
        ))

    if not stats:
        return None

    for limit, label, colour in [(BUMP_LIMIT_MM, "bump stop", "#e34948"),
                                 (DROOP_LIMIT_MM, "full droop", "#eda100")]:
        if limit is not None:
            fig.add_vline(x=limit, line=dict(color=colour, width=2, dash="dash"),
                          annotation_text=f"{label} ({limit:+.0f}mm)")

    fig.add_vline(x=0, line=dict(color="#888", width=1),
                  annotation_text="static ride height")

    if BUMP_LIMIT_MM is None and DROOP_LIMIT_MM is None:
        note = ("Travel USED. Set BUMP_LIMIT_MM / DROOP_LIMIT_MM in "
                "case4_combined_roll_pitch.py and this becomes a MARGIN plot.")
    else:
        note = "Dashed lines are the mechanical limits — the gap to them is your margin."

    fig.update_layout(
        xaxis_title="Wheel travel vs. static (mm)",
        yaxis_title="samples",
        barmode="overlay", template=PLOT_TEMPLATE,
    )
    titled(fig, f"{event.upper()} — per-corner wheel travel distribution",
           f"negative = compression (bump), positive = extension (droop). {note}")
    fig.write_html(output_path, include_plotlyjs="cdn")
    return stats


def report_travel_distribution(event, stats):
    if not stats:
        return
    print(f"\n    Travel distribution across all {event.upper()} files "
          f"(glitch-masked, outer {EDGE_EXCLUDE_FRACTION:.0%} trimmed):")
    print(f"      {'corner':6} {'p1':>8} {'median':>8} {'p99':>8} "
          f"{'min':>8} {'max':>8} {'p1-p99 range':>13}")
    for corner in CORNERS:
        if corner not in stats:
            continue
        s = stats[corner]
        span = s["p"][99] - s["p"][1]
        print(f"      {corner:6} {s['p'][1]:+8.2f} {s['p'][50]:+8.2f} "
              f"{s['p'][99]:+8.2f} {s['min']:+8.2f} {s['max']:+8.2f} "
              f"{span:12.2f}mm")

    if BUMP_LIMIT_MM is None and DROOP_LIMIT_MM is None:
        print(f"      -> This is travel USED. For MARGIN, set BUMP_LIMIT_MM / "
              f"DROOP_LIMIT_MM in {os.path.basename(__file__)}.")
        return

    print(f"      Margin to the mechanical limits:")
    for corner in CORNERS:
        if corner not in stats:
            continue
        s = stats[corner]
        bits = []
        if BUMP_LIMIT_MM is not None:
            bits.append(f"bump {s['min'] - BUMP_LIMIT_MM:+6.2f}mm")
        if DROOP_LIMIT_MM is not None:
            bits.append(f"droop {DROOP_LIMIT_MM - s['max']:+6.2f}mm")
        print(f"        {corner}: " + "   ".join(bits))


def build_roll_pitch_envelope(event, results, output_path):
    """Scatter of every sample's (roll, pitch) in degrees, per file, with the
    convex hull of the pooled cloud drawn on top. The hull is the useful
    part: it shows which roll+pitch COMBINATIONS the car actually reaches,
    which is what case2 and case3 individually cannot show."""
    fig = go.Figure()
    all_roll, all_pitch = [], []
    for r in results:
        roll, pitch = r["roll_deg"], r["pitch_deg"]
        all_roll.append(roll)
        all_pitch.append(pitch)
        roll_thin, pitch_thin = thin_scatter(roll, pitch)
        fig.add_trace(go.Scattergl(
            x=roll_thin, y=pitch_thin, mode="markers",
            name=os.path.basename(r["path"]),
            marker=dict(size=2, opacity=0.35),
        ))

    roll_all = np.concatenate(all_roll)
    pitch_all = np.concatenate(all_pitch)
    try:
        from scipy.spatial import ConvexHull
        pts = np.column_stack([roll_all, pitch_all])
        finite = pts[np.isfinite(pts).all(axis=1)]
        if len(finite) >= 3:
            hull = ConvexHull(finite)
            loop = np.append(hull.vertices, hull.vertices[0])
            fig.add_trace(go.Scatter(
                x=finite[loop, 0], y=finite[loop, 1], mode="lines",
                name="envelope (convex hull)",
                line=dict(color="black", width=2),
            ))
    except Exception as e:
        print(f"  [!] {event}: convex hull skipped ({e})")

    fig.add_hline(y=0, line=dict(color="grey", width=1))
    fig.add_vline(x=0, line=dict(color="grey", width=1))
    fig.update_layout(
        xaxis_title="Roll angle (deg)", yaxis_title="Pitch angle (deg)",
        template=PLOT_TEMPLATE,
    )
    titled(
        fig, f"{event.upper()} — roll vs. pitch envelope",
        "the hull is the useful part: which roll+pitch COMBINATIONS the car "
        "actually reaches, which case2 and case3 individually cannot show. "
        "Hull computed from every sample; markers thinned for display.",
    )
    fig.write_html(output_path, include_plotlyjs="cdn")


def build_summary(summaries_by_event, output_path):
    """Headline chart: worst per-corner travel per event, with the modal
    contributions at that instant shown as a grouped breakdown underneath."""
    events = [e for e in CASE4_EVENTS if summaries_by_event.get(e)]
    if not events:
        return

    labels = [e.upper() for e in events]
    worst = [summaries_by_event[e]["worst_travel_mm"] for e in events]
    corners_hit = [summaries_by_event[e]["worst_corner"] for e in events]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Worst corner travel (|mm|)", x=labels, y=[abs(v) for v in worst],
        marker_color="#e34948",
        text=[f"{v:+.1f}mm ({c})" for v, c in zip(worst, corners_hit)],
        textposition="outside",
    ))
    for mode, color in (("roll", "#2a78d6"), ("pitch", "#48b56b"),
                        ("heave", "#d69a2a"), ("warp", "#8e5bd6")):
        fig.add_trace(go.Bar(
            name=f"{mode} contribution (|mm|)", x=labels,
            y=[abs(summaries_by_event[e]["worst_modes"][mode]) for e in events],
            marker_color=color, opacity=0.85,
        ))

    fig.update_layout(
        title="Case 4 — Worst Per-Corner Wheel Travel by Event, "
              "with exact modal breakdown at that instant",
        yaxis_title="Millimetres (magnitude)",
        barmode="group",
    )
    fig.write_html(output_path, include_plotlyjs="cdn")


# ── Reporting ────────────────────────────────────────────────────────────

def report_baselines(event, results):
    print(f"\n--- {event.upper()} static baselines (stopped-car reference, subtracted per corner) ---")
    for r in results:
        fname = os.path.basename(r["path"])
        if not r["baselines_found"]:
            print(f"  {fname}: NOT baselined — no stopped-car window found")
            continue
        b = r["baselines"]
        print(f"  {fname}: " + "  ".join(f"{c}={b[c]:.3f}mm" for c in CORNERS))


# Thresholds for turning the G's at an instant into words. Deliberately the
# same 0.3 g the segment finders use for "really turning" / "accelerating
# hard", so the description cannot disagree with the segmentation.
DESCRIBE_G = 0.3
DESCRIBE_G_HARD = 0.8

# Below this the car is not meaningfully driving, so a travel peak here is
# not a driving load. Same threshold case_common.find_braking_windows uses
# to reject "braking" pulses with the car parked, and for the same reason.
#
# THIS IS NOT COSMETIC. autocross_andrew1's worst corner travel — 27.98mm,
# the largest in the whole dataset and the number the summary table quotes
# as AUTOCROSS's design case — occurs at 116.59s, at 1.29 m/s, 1.3 seconds
# AFTER the car stopped moving (it is rolling above 3 m/s only up to
# 115.24s). The worst peak in that file while genuinely driving is 17.14mm,
# 39% lower. braketest1 has the same problem at 0.00 m/s.
#
# The peak is real in the sense that the corner really did move that far and
# it is a 0.2s plateau, not a spike — it is just not a driving event, and
# nothing in the report said so. Flagged rather than filtered, because
# excluding it would move a published headline number and that is a
# methodology decision, not a display one.
ROLLING_MIN_SPEED_MS = 3.0


def describe_instant(d, idx):
    """One plain sentence: what was the car doing at this sample?

    WHY THIS EXISTS. The report has always printed "FR -27.98mm @ 116.59s,
    lateral G=+0.03g longitudinal G=+0.42g" — correct, complete, and it
    still takes a reader who knows the sign conventions to work out that
    this was a braking event and not a corner. The number is the deliverable
    but the CONTEXT is what makes it actionable: a corner-travel peak that
    happens under braking is fixed by a different change than one that
    happens mid-corner.

    Sign conventions are case3's, verified empirically against vehicle
    speed: lon G POSITIVE = slowing down.
    """
    lat = float(d["lat_f"][idx])
    lon = float(d["lon_f"][idx])

    lateral = abs(lat) >= DESCRIBE_G
    longitudinal = abs(lon) >= DESCRIBE_G

    if longitudinal:
        hard = "hard " if abs(lon) >= DESCRIBE_G_HARD else ""
        long_phrase = f"{hard}braking" if lon > 0 else f"{hard}accelerating"
    else:
        long_phrase = ""

    if lateral:
        hard = "hard " if abs(lat) >= DESCRIBE_G_HARD else ""
        side = "left" if lat > 0 else "right"
        lat_phrase = f"cornering {hard}to the {side}"
    else:
        lat_phrase = ""

    if lat_phrase and long_phrase:
        what = f"{long_phrase} while {lat_phrase} — a COMBINED-load instant"
    elif long_phrase:
        what = f"{long_phrase} in a straight line"
    elif lat_phrase:
        what = f"{lat_phrase} at steady throttle"
    else:
        what = "neither cornering nor braking hard — a bump or kerb strike"

    speed = d.get("speed")
    speed_note, stopped_note = "", ""
    if speed is not None and idx < len(speed) and np.isfinite(speed[idx]):
        v = float(speed[idx])
        speed_note = f", at {v:.1f} m/s"
        if v < ROLLING_MIN_SPEED_MS:
            what = "car essentially STOPPED"
            stopped_note = (
                f"\n      [!] NOT A DRIVING EVENT — the car is below "
                f"{ROLLING_MIN_SPEED_MS:.0f} m/s here. This peak is real "
                f"motion but it is not a load the car saw on track."
            )

    return (f"{what}{speed_note}\n"
            f"      ({lat:+.2f} g lateral, {lon:+.2f} g longitudinal; "
            f"+lon = slowing down, +lat = left)" + stopped_note)


def worst_while_rolling(results, min_speed=ROLLING_MIN_SPEED_MS):
    """The worst peak that happened with the car actually driving.

    Reported ALONGSIDE the headline peak, never instead of it — see the
    ROLLING_MIN_SPEED_MS note. Returns (value, result, idx) or None.
    """
    pool = []
    for r in results:
        speed = r.get("speed")
        if speed is None:
            continue
        for idx, val in r["peaks"]:
            if idx < len(speed) and np.isfinite(speed[idx]) and speed[idx] >= min_speed:
                pool.append((val, r, idx))
    return max(pool, key=lambda x: x[0]) if pool else None


def dominant_modes(contribs, n=2):
    """The n modes carrying the most mm, as 'pitch and heave'."""
    ranked = sorted(contribs, key=lambda m: abs(contribs[m]), reverse=True)
    picked = ranked[:n]
    if len(picked) == 1:
        return picked[0]
    return " and ".join([", ".join(picked[:-1]), picked[-1]])


def report_event(event, results):
    print(f"\n=== {event.upper()} — WORST PER-CORNER TRAVEL "
          f"(peak detection on 4-corner envelope) ===")
    if not results:
        print("  no data")
        return None

    pool = []   # (envelope_mm, result, idx)
    for r in results:
        for idx, val in r["peaks"]:
            pool.append((val, r, idx))
    if not pool:
        print(f"  no peaks found (check PEAK_PROMINENCE_MM={PEAK_PROMINENCE_MM})")
        return None
    pool.sort(key=lambda x: x[0], reverse=True)

    top = pool[:TOP_K_PEAKS]
    print(f"  Top {len(top)} worst instants (pooled across files):")
    for val, r, idx in top:
        c = r["worst_corner_at"][idx]
        print(f"    {os.path.basename(r['path']):26} @ {r['t'][idx]:8.2f}s  "
              f"{c} {r['travel'][c][idx]:+7.2f}mm   "
              f"roll={r['roll_deg'][idx]:+.3f}° pitch={r['pitch_deg'][idx]:+.3f}°")
    avg_mm = float(np.mean([v for v, _, _ in top]))
    print(f"  Top {len(top)} averaged: {avg_mm:.2f}mm")

    # Single worst instant — full exact modal decomposition.
    best_val, best_r, best_idx = pool[0]
    c = best_r["worst_corner_at"][best_idx]
    signed = float(best_r["travel"][c][best_idx])
    modes = {m: float(best_r["modes"][m][best_idx]) for m in ("heave", "roll", "pitch", "warp")}
    signs = MODE_SIGNS[c]
    contribs = {m: signs[m] * modes[m] for m in modes}
    recon = sum(contribs.values())

    direction = "COMPRESSION (bump)" if signed < 0 else "EXTENSION (droop)"
    print(f"\n  SINGLE WORST INSTANT — {os.path.basename(best_r['path'])} "
          f"@ {best_r['t'][best_idx]:.2f}s")
    print(f"    corner {c}: {signed:+.2f}mm  [{direction}]"
          # Plateau or spike? The envelope is what the peak search ran on.
          + format_peak_shape(best_r["envelope"], best_r["t"], best_idx, "mm"))

    # WHAT THE CAR WAS DOING — the context that makes the number
    # actionable. See describe_instant().
    print(f"    what the car was doing: {describe_instant(best_r, best_idx)}")

    print(f"    exact modal breakdown of that {signed:+.2f}mm:")
    for m in ("roll", "pitch", "heave", "warp"):
        pct = (abs(contribs[m]) / sum(abs(v) for v in contribs.values()) * 100
               if any(contribs.values()) else 0.0)
        print(f"      {m:6}: {contribs[m]:+7.2f}mm  ({pct:4.1f}% of total mm moved)")
    print(f"      {'sum':6}: {recon:+7.2f}mm  (identity check vs {signed:+.2f}mm)")
    print(f"    whole-car attitude at that instant: "
          f"roll={best_r['roll_deg'][best_idx]:+.3f}°  "
          f"pitch={best_r['pitch_deg'][best_idx]:+.3f}°")

    # The one-line takeaway, spelling out which knob moves this number.
    top_modes = dominant_modes(contribs)
    print(f"    -> this corner was loaded mostly by {top_modes.upper()}. "
          f"Changing what drives {top_modes.split(' and ')[0]} is what moves "
          f"this number.")

    # If the headline peak turned out not to be a driving event, give the
    # worst one that was, so the report carries both numbers rather than
    # leaving the reader to wonder what the on-track answer is.
    best_speed = best_r.get("speed")
    if (best_speed is not None and best_idx < len(best_speed)
            and best_speed[best_idx] < ROLLING_MIN_SPEED_MS):
        rolling = worst_while_rolling(results)
        if rolling:
            rv, rr, ri = rolling
            rc = rr["worst_corner_at"][ri]
            print(f"\n    WORST WHILE ACTUALLY DRIVING (>= "
                  f"{ROLLING_MIN_SPEED_MS:.0f} m/s): "
                  f"{rr['travel'][rc][ri]:+.2f}mm at {rc} — "
                  f"{os.path.basename(rr['path'])} @ {rr['t'][ri]:.2f}s, "
                  f"{float(rr['speed'][ri]):.1f} m/s "
                  f"({100 * (best_val - rv) / best_val:.0f}% below the "
                  f"headline peak above)")
            print(f"      -> {describe_instant(rr, ri)}")

    # Per-corner signed extremes across the whole event — both mechanical
    # limits. Unlike the peak-detection path above, a raw min/max WILL pick
    # up filtfilt's boundary overshoot, so trim each file's ends first.
    print(f"\n    Per-corner extremes across all {event.upper()} files "
          f"(outer {EDGE_EXCLUDE_FRACTION:.0%} of each file excluded):")
    for corner in CORNERS:
        mins, maxs = [], []
        for r in results:
            values = r["travel"][corner]
            edge = int(EDGE_EXCLUDE_FRACTION * len(values))
            keep = ~r["glitch_mask"]
            if edge and len(values) > 2 * edge:
                keep[:edge] = False
                keep[len(values) - edge:] = False
            interior = values[keep]
            if not len(interior):
                continue
            mins.append(float(np.min(interior)))
            maxs.append(float(np.max(interior)))
        print(f"      {corner}: max compression {min(mins):+7.2f}mm   "
              f"max extension {max(maxs):+7.2f}mm")

    # Deep-linkable instants for the report page. Underscore-prefixed so
    # case_summary's scalar sweep ignores it — it collects numbers, and this
    # is navigation metadata riding along with them.
    instants = [{
        "event": event, "path": best_r["path"], "t": float(best_r["t"][best_idx]),
        "label": f"worst corner travel — {c} {signed:+.2f}mm",
        "detail": describe_instant(best_r, best_idx).split("\n")[0],
    }]
    rolling = worst_while_rolling(results)
    if rolling and rolling[2] != best_idx:
        rv, rr, ri = rolling
        rc = rr["worst_corner_at"][ri]
        instants.append({
            "event": event, "path": rr["path"], "t": float(rr["t"][ri]),
            "label": f"worst while driving — {rc} {rr['travel'][rc][ri]:+.2f}mm",
            "detail": describe_instant(rr, ri).split("\n")[0],
        })

    return {
        "worst_travel_mm": signed, "worst_corner": c,
        "worst_modes": contribs, "top_avg_mm": avg_mm,
        "worst_roll_deg": float(best_r["roll_deg"][best_idx]),
        "worst_pitch_deg": float(best_r["pitch_deg"][best_idx]),
        "_instants": instants,
    }


def report_sustained(event, results):
    print(f"\n  --- {event.upper()} SUSTAINED (median over steady-state segments) ---")
    any_found = False
    pooled = {c: [] for c in CORNERS}
    pooled_modes = {m: [] for m in ("heave", "roll", "pitch", "warp")}
    for r in results:
        s = analyze_sustained(r, event)
        if s is None:
            print(f"    [!] {os.path.basename(r['path'])}: no qualifying steady window.")
            continue
        any_found = True
        print(f"    {os.path.basename(r['path'])} ({s['n_runs']} run(s)): " +
              "  ".join(f"{c}={s['corner_median_mm'][c]:+.2f}mm" for c in CORNERS))
        for c in CORNERS:
            pooled[c].append(s["corner_median_mm"][c])
        for m in pooled_modes:
            pooled_modes[m].append(s["mode_median_mm"][m])
    if not any_found:
        return
    print(f"    Across files: " +
          "  ".join(f"{c}={np.median(pooled[c]):+.2f}mm" for c in CORNERS))
    rm = float(np.median(pooled_modes["roll"]))
    pm = float(np.median(pooled_modes["pitch"]))
    print(f"    Sustained modes: roll={rm:+.2f}mm/corner  pitch={pm:+.2f}mm/corner  "
          f"heave={np.median(pooled_modes['heave']):+.2f}mm  "
          f"warp={np.median(pooled_modes['warp']):+.2f}mm")
    # roll mode is mm-per-corner; full left-right difference is 2x that.
    print(f"    -> sustained roll angle ~{roll_deg(2 * abs(rm)):.3f}°   "
          f"sustained pitch angle ~{pitch_deg(2 * abs(pm)):.3f}°")


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

    print(f"Skidpad low-pass: {SKIDPAD_CUTOFF_HZ} Hz | Everything else: "
          f"{AUTOX_END_CUTOFF_HZ} Hz (both {FILTER_ORDER}th-order Butterworth, zero-phase)")
    print(f"Geometry: front track={FRONT_TRACK_MM}mm rear track={REAR_TRACK_MM}mm "
          f"wheelbase={WHEELBASE_MM}mm")
    print(f"Motion ratio (wheel/spring): front={MOTION_RATIO_FRONT} "
          f"rear={MOTION_RATIO_REAR} — applied per corner before roll/pitch/modal maths")
    print("All travel figures below are WHEEL millimetres, not shock-pot millimetres.")
    print("Sign convention: travel < 0 = COMPRESSION (bump), > 0 = EXTENSION (droop).")
    print(f"Peak prominence: {PEAK_PROMINENCE_MM}mm on the 4-corner envelope.")

    summaries_by_event = {}

    for event in CASE4_EVENTS:
        paths = grouped.get(event, [])
        if not paths:
            print(f"\nNo files found for {event.upper()}.")
            continue

        cutoff = SKIDPAD_CUTOFF_HZ if event == "skidpad" else AUTOX_END_CUTOFF_HZ
        out_dir = os.path.join(PLOTS_ROOT, event)
        os.makedirs(out_dir, exist_ok=True)

        results = [r for p in paths if (r := analyze_worst_case(p, cutoff)) is not None]
        if not results:
            print(f"\nNo usable files for {event.upper()}.")
            continue

        report_baselines(event, results)
        summary = report_event(event, results)
        if event in STEADY_EVENTS:
            report_sustained(event, results)
        summaries_by_event[event] = summary

        for r in results:
            fname = os.path.splitext(os.path.basename(r["path"]))[0]
            build_corner_travel_plot(r, os.path.join(out_dir, f"{fname}_corner_travel.html"),
                                     event=event)
        build_roll_pitch_envelope(event, results,
                                  os.path.join(out_dir, "roll_pitch_envelope.html"))
        stats = build_travel_distribution(
            event, results, os.path.join(out_dir, "travel_distribution.html"))
        report_travel_distribution(event, stats)
        print(f"\n  Plots saved to: {out_dir}/")

    os.makedirs(PLOTS_ROOT, exist_ok=True)
    build_summary(summaries_by_event, os.path.join(PLOTS_ROOT, "corner_travel_summary.html"))
    print(f"\nHeadline chart saved to: {PLOTS_ROOT}/corner_travel_summary.html")

    # Cross-event answer to the question case4 exists to answer.
    print("\n" + "=" * 72)
    print("WORST CASE ACROSS ALL EVENTS")
    print("=" * 72)
    ranked = sorted(
        ((e, s) for e, s in summaries_by_event.items() if s),
        key=lambda kv: abs(kv[1]["worst_travel_mm"]), reverse=True)
    for e, s in ranked:
        print(f"  {e.upper():10} {s['worst_corner']} {s['worst_travel_mm']:+7.2f}mm   "
              f"(roll {s['worst_roll_deg']:+.3f}°, pitch {s['worst_pitch_deg']:+.3f}°)  "
              f"roll mode {s['worst_modes']['roll']:+.2f}mm / "
              f"pitch mode {s['worst_modes']['pitch']:+.2f}mm")
    if ranked:
        e, s = ranked[0]
        print(f"\n  -> Design-driving case: {e.upper()}, corner {s['worst_corner']}, "
              f"{s['worst_travel_mm']:+.2f}mm")

    print("\nDone.")

    return summaries_by_event


CONVENTIONS = [
    "<b>Per-corner wheel travel</b>, relative to that corner's own "
    "stopped-car baseline. <code>negative = COMPRESSION (bump)</code>, "
    "<code>positive = EXTENSION (droop)</code>. Both have a mechanical "
    "limit, so both extremes are reported.",
    "These are <b>wheel</b> millimetres, not shock-pot millimetres — the "
    "motion ratio (1.188 front, 1.038 rear) is applied per corner "
    "<i>before</i> any roll/pitch/modal arithmetic.",
    "<b>heave</b> = all four corners moving together (no attitude change). "
    "<b>roll</b> = left pair vs right pair. <b>pitch</b> = front pair vs "
    "rear pair. <b>warp</b> = the diagonals opposing each other — the "
    "chassis being twisted. Each mode's mm is its contribution to "
    "<i>one</i> corner, and the four sum exactly to that corner's travel.",
    "<b>Longitudinal G positive = slowing down</b> (verified empirically "
    "against vehicle speed, not assumed). Lateral G positive = cornering "
    "left.",
    "A peak flagged <b>NOT A DRIVING EVENT</b> happened below 3 m/s. The "
    "motion is real, but it is not a load the car saw on track.",
]


if __name__ == "__main__":
    with report_page("case4_combined_roll_pitch", "Case 4 — Combined Roll + Pitch", PLOTS_ROOT) as page:
        page.summary = main()
        for text in CONVENTIONS:
            page.add_convention(text)
        for event_summary in (page.summary or {}).values():
            for item in (event_summary or {}).get("_instants", []):
                page.add_instant(item["event"], item["path"], item["t"],
                                 item["label"], item["detail"])
    write_index()
