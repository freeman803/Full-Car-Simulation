# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
case5_gradients.py — Case 5: ROLL GRADIENT and PITCH GRADIENT, in degrees
per g.

This is the headline suspension metric and the one number the rest of the
analysis was building toward. Cases 1-4 answer "how much did the car roll?"
That is a property of the run — a driver who pushed harder gets a bigger
number. Roll GRADIENT answers "how much does this car roll PER UNIT of
lateral acceleration", which is a property of the CAR, independent of how
hard it was driven. It is what you compare against a target, and it is the
bridge to a roll stiffness in N*m/deg.

    roll gradient  = d(roll angle)  / d(lateral G)        deg/g
    pitch gradient = d(pitch angle) / d(longitudinal G)   deg/g

NOTHING IS REIMPLEMENTED HERE. Roll comes from case2_max_roll's loader and
pitch from case3_max_pitch's, so the angles behind these gradients are the
exact same numbers those cases report — same filtering, same baselining,
same motion-ratio conversion, same sign conventions. If a case changes
methodology this follows automatically.

REFERENCE. Gradients are reported GROUND-referenced — chassis attitude
against the ROAD, tyre deflection included — because that is what a design
gradient means and what the Simplified Steady State Suspension Spreadsheet
predicts (roll 1.307 deg/g, pitch 0.901 deg/g). The raw fitted slope
is suspension-referenced (all a shock pot can see) and is carried beside
each headline as [susp-ref ...]. See case_common's reference note.

CROSS-CHECKED AGAINST THE SPRINGS, which is the only check here that does
not route through the shock pots. It checks the SUSPENSION-referenced
slope, since springs alone set that one and no tyre term enters. With no
ARB the four springs (225 lbf/in front, 200 rear) make the entire roll
stiffness: wheel rates 27.92 / 32.51 N/mm give 749 N*m/deg (mind the units
— see the derivation in case_common). Against the measured 0.898 deg/g
that is a roll moment of ~673 N*m per g. Note MR enters stiffness as MR^2,
so this is twice as sensitive to a motion-ratio error as the angles are.

WHAT IT DOES NOT ESTABLISH: an absolute scale. Turning 673 N*m/g into a CG
height needs a sprung mass and a roll-axis height, neither of which has
been measured on this car, so that step is not taken here. (An earlier
version of this note asserted "CG 0.280 m above the roll axis at 245 kg
sprung"; the 245 kg was never sourced and conflicts with the 215.5 kg
competition mass without driver. Retracted.)

A "should be at least 2x higher" expectation is still ruled out, and the
argument needs no absolute CG: roll moment per g is proportional to sprung
mass x CG-height, so 1.80 deg/g suspension-referenced against a fixed
749 N*m/deg would need DOUBLE the sprung-mass x CG-height this car can
plausibly have. Nothing else in the chain can supply that factor.

An earlier note here cited a "0.83-0.94 deg/g hand-derived estimate from
four independent estimates" as corroboration. Its derivation appears
nowhere in this repo or its history, and the other confirmations once
claimed alongside it (endurance vs skidpad, case2-roll / case1-lat-G) share
the same shock pots and motion ratio, so they measured repeatability rather
than calibration. Retracted.

SIGN CONVENTION. A HIGHER shock-pot mm reading is more EXTENSION on this
car (see case2/case3), so roll_front_mm = FR - FL is POSITIVE when the
right side is extended, i.e. in a LEFT-hand turn. Lateral G is negative in
that same turn, so the raw slope of roll against lateral G is NEGATIVE.
Gradients are reported as MAGNITUDES, with the sign checked rather than
assumed — a positive raw slope would mean the convention has flipped
somewhere and is reported as an error rather than silently absolute-valued.

WHAT IS EXCLUDED, and why each matters:

  - Step glitches (case_common.find_step_glitches). A step is a huge
    apparent roll with no corresponding lateral G, so it drags the fit.
  - Stationary and crawling samples (speed < 2 m/s). A parked car
    contributes a dense cluster at (0, 0) that inflates R^2 without
    telling you anything about how the car rolls.
  - Nothing else. In particular, transients are KEPT — the scatter they
    produce is a result, not contamination. See the hysteresis note below.

HYSTERESIS IS THE POINT OF THE SCATTER PLOT. Roll lags lateral G through a
transient, so a corner entry and the matching exit trace different paths
and the cloud opens into a loop. A single slope cannot show that, which is
why the scatter is a deliverable rather than a diagnostic. Steady-state
events (skidpad) should give a tight line; autocross and endurance will
not, and the width is the information.

STEADY-STATE ESTIMATE. Alongside the all-samples fit, skidpad also gets a
fit restricted to its steady circling segments (the same windows case1 and
case2 use). That is the cleanest possible estimate of this metric — no
transient lag, no driver variation — and it is the number to quote if you
quote one.

Run it:
    uv run case5_gradients.py --dir comp2026_data
"""

import os
import sys
import glob
import argparse
import contextlib
import io

import numpy as np
import plotly.graph_objects as go

from case_common import (
    group_by_event, SKIDPAD_CUTOFF_HZ, AUTOX_END_CUTOFF_HZ,
    find_step_glitches, find_steady_segments, trim_window,
    baseline_corner_displacements, to_wheel_travel, lowpass,
    mm_to_deg, FRONT_TRACK_MM, REAR_TRACK_MM, AVG_TRACK_MM, WHEELBASE_MM,
    CORNERS, CORNER_SIGNAL_NAMES, TRIM_SECONDS, is_suspect,
    to_ground_referenced, susp_note, SUSP_SUFFIX, GROUND_MULT,
    GROUND_MULT_ROLL_FRONT, GROUND_MULT_ROLL_REAR, GROUND_MULT_PITCH,
    TYRE_RATE_N_MM,
)
from parse_influx import parse_influx
from case_report import report_page, write_index

import case2_max_roll as c2
import case3_max_pitch as c3

ROLL_EVENTS = ["skidpad", "autocross", "endurance"]
PITCH_EVENTS = ["accel", "brake", "autocross", "endurance"]

# Below this the car is parked or crawling; those samples cluster at the
# origin and flatter the fit without informing it.
MIN_SPEED_MS = 2.0

# A fit over a narrow range of G is not a gradient, it is an extrapolation.
MIN_G_RANGE = 0.4

# A pot is out of stroke when it never leaves the extension end of its
# range — judged by the TOP of its operating band, not the bottom.
#
# The bottom is the wrong test and was tried first: autocross_josh1 dips to
# 0.32 V yet has a perfectly normal gradient (0.794 deg/g), because it
# sweeps all the way up to 1.20 V. What distinguishes the bad runs is that
# they never get there — josh2 spans only 0.18-0.46 V and andrew1
# 0.19-0.88 V, against 0.32-1.20 and 0.46-1.20 for the two good runs.
POT_VOLT_CEILING = 1.00

PLOTS_ROOT = os.path.join("plots", "case5_gradients")

COLORS = {"front": "#2a78d6", "rear": "#eb6834", "avg": "#1baf7a",
          "pitch": "#4a3aa7"}


# A quantity is only as trustworthy as the corners it is built from. Rear
# roll survives a bad front pair; whole-car roll does not.
QUANTITY_CORNERS = {
    "front": ("FL", "FR"),
    "rear":  ("RL", "RR"),
    "avg":   ("FL", "FR", "RL", "RR"),
    "pitch": ("FL", "FR", "RL", "RR"),
}


def usable_series(series, which):
    """Drop runs whose data for THIS quantity is known bad.

    Per quantity rather than per file, so a bad front pair does not cost us
    the rear data in the same run. See case_common.SUSPECT_CORNERS.
    """
    corners = QUANTITY_CORNERS[which]
    return [s for s in series if not is_suspect(s["path"], corners)]


def _quiet(fn, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


def fit_gradient(g, angle_deg):
    """Least-squares slope of angle against G, plus the diagnostics needed
    to know whether to believe it.

    The intercept is FITTED, not forced through zero. Physically the car is
    level at 0 g, so a large intercept is not a free parameter to shrug at
    — it is evidence that a baseline is off, and reporting it is the point.
    """
    ok = np.isfinite(g) & np.isfinite(angle_deg)
    g, angle_deg = g[ok], angle_deg[ok]

    if g.size < 100:
        return None

    g_range = float(np.percentile(g, 99) - np.percentile(g, 1))
    if g_range < MIN_G_RANGE:
        return None

    slope, intercept = np.polyfit(g, angle_deg, 1)

    predicted = slope * g + intercept
    ss_res = float(np.sum((angle_deg - predicted) ** 2))
    ss_tot = float(np.sum((angle_deg - np.mean(angle_deg)) ** 2))

    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r2": 1.0 - ss_res / ss_tot if ss_tot else float("nan"),
        "n": int(g.size),
        "g_range": g_range,
        "g": g,
        "angle": angle_deg,
    }


def usable_mask(t, speed, glitch_mask):
    """Samples that can inform a gradient."""
    return (~glitch_mask) & (np.abs(speed) > MIN_SPEED_MS)


def roll_series(path, cutoff):
    """Roll angles + lateral G for one file, from case2's own loader."""
    d = _quiet(c2.load_roll_signals, path, cutoff)
    if d is None:
        return None

    signals = parse_influx(path, verbose=False)
    t = d["t"]

    corners_raw = {
        c: np.asarray(signals[CORNER_SIGNAL_NAMES[c]].value, dtype=float)
        for c in CORNERS
    }
    glitch_mask, _ = find_step_glitches(corners_raw, t)

    speed = np.asarray(signals["VCFRONT_vehicleSpeed"].value, dtype=float)
    speed = np.nan_to_num(speed, nan=0.0)

    keep = usable_mask(t, speed, glitch_mask)

    # Per-corner filtered wheel travel, for the diagnostic table. Baselined
    # and motion-ratio-converted the same way case2 does it.
    corners_baselined, _, _ = baseline_corner_displacements(signals, t, speed)
    wheel = to_wheel_travel(corners_baselined)
    corner_mm = {c: lowpass(wheel[c], d["dt"], cutoff) for c in CORNERS}

    return {
        "path": path,
        "t": t,
        "keep": keep,
        "corner_mm": corner_mm,
        "lat": d["lat_f"],
        "front": mm_to_deg(d["roll_front_f"], FRONT_TRACK_MM),
        "rear": mm_to_deg(d["roll_rear_f"], REAR_TRACK_MM),
        "avg": mm_to_deg(d["roll_avg_f"], AVG_TRACK_MM),
        "lat_f": d["lat_f"],
        "baselines_found": d["baselines_found"],
    }


def pitch_series(path, cutoff):
    """Pitch angle + longitudinal G for one file, from case3's own loader."""
    d = _quiet(c3.load_pitch_signals, path, cutoff)
    if d is None:
        return None

    signals = parse_influx(path, verbose=False)
    t = d["t"]

    corners_raw = {
        c: np.asarray(signals[CORNER_SIGNAL_NAMES[c]].value, dtype=float)
        for c in CORNERS
    }
    glitch_mask, _ = find_step_glitches(corners_raw, t)

    speed = np.nan_to_num(np.asarray(d["speed"], dtype=float), nan=0.0)
    keep = usable_mask(t, speed, glitch_mask)

    return {
        "path": path,
        "t": t,
        "keep": keep,
        "lon": d["lon_f"],
        "pitch": mm_to_deg(d["pitch_f"], WHEELBASE_MM),
        "baselines_found": d["baselines_found"],
    }


def steady_mask(series):
    """Only the steady circling segments, for the cleanest skidpad number.

    Same windows case1 and case2 use, trimmed the same way, so this is
    directly comparable to the roll figures those cases report.
    """
    t = series["t"]
    mask = np.zeros(len(t), dtype=bool)

    segments = find_steady_segments(series["lat_f"], t)
    for sign_segments in segments.values():
        for s, e, _ in sign_segments:
            ts, te = trim_window(t, s, e, TRIM_SECONDS)
            mask[ts:te + 1] = True

    return mask


# ── Reporting ────────────────────────────────────────────────────────────

def fit_magnitude(fit):
    return abs(fit["slope"]) if fit else None


def ground_values(pooled):
    """{which: GROUND-referenced gradient} for a {which: fit} dict.

    These are the headline numbers of this case — deg/g of chassis attitude
    against the ROAD, which is what a design roll or pitch gradient means and
    what the Simplified Steady State Suspension Spreadsheet predicts
    (roll 1.307 deg/g, pitch 0.901 deg/g). The suspension-referenced slope the fit
    actually produced is reported beside each as a labelled secondary.

    Each axle carries its own multiplier; the whole-car "avg" carries one
    stiffness-weighted multiplier rather than being rebuilt from the axles —
    see case_common's reference note for why.
    """
    out = {}
    if "pitch" in pooled:
        out["pitch"] = to_ground_referenced(fit_magnitude(pooled["pitch"]), "pitch")
    front, rear = fit_magnitude(pooled.get("front")), fit_magnitude(pooled.get("rear"))
    out["front"] = to_ground_referenced(front, "front")
    out["rear"] = to_ground_referenced(rear, "rear")
    out["avg"] = to_ground_referenced(fit_magnitude(pooled.get("avg")), "avg")
    return out


def emit_gradient(out, key, fit, which):
    """Write one gradient into the flat summary, GROUND-referenced first.

    `key` holds the ground-referenced figure — the headline — and
    `key + "_susp"` the raw fitted slope. Both are written even when the fit
    is None, so a missing gradient stays a visible None rather than a key
    that silently isn't there.
    """
    susp = fit_magnitude(fit)
    out[key] = to_ground_referenced(susp, which)
    out[key + SUSP_SUFFIX] = susp


def report_fit(label, fit, expect_negative=True, ground=None):
    if fit is None:
        print(f"    {label:<22}—  (insufficient data or G range)")
        return None

    slope = fit["slope"]
    magnitude = abs(slope)

    # Check the sign rather than absolute-valuing it silently: a flipped
    # sign means a convention broke somewhere upstream, and that is worth
    # a loud line rather than a plausible-looking number.
    sign_ok = (slope < 0) if expect_negative else (slope > 0)
    flag = "" if sign_ok else "   [!] SIGN UNEXPECTED — convention may have flipped"

    # The GROUND-referenced gradient leads; the raw slope the fit produced
    # follows as a labelled secondary. R², n, G range and intercept all
    # belong to the fit and are reference-independent — the conversion is a
    # constant multiplier, so it cannot change the quality of the fit.
    headline = ground if ground is not None else magnitude
    susp_txt = susp_note(magnitude, ".3f", " deg/g") if ground is not None else ""

    print(f"    {label:<22}{headline:6.3f} deg/g{susp_txt}   "
          f"R²={fit['r2']:.3f}  n={fit['n']:,}  "
          f"G range {fit['g_range']:.2f}  "
          f"intercept {fit['intercept']:+.3f} deg{flag}")

    return magnitude


def build_scatter(fits, title, xlabel, output_path):
    """Roll/pitch against G, with the fitted line. The CLOUD is the point:
    a tight line means the relationship is linear and lag-free; an open
    loop is hysteresis through transients.

    Angles are plotted GROUND-referenced, so the slope in the legend is the
    same number the console and the summary table quote. The fits are keyed
    "front"/"rear"/"avg"/"pitch", which are exactly GROUND_MULT's keys.
    Scaling is a constant per trace, so the shape of the cloud, the R² and
    the hysteresis loop are all untouched — only the y axis changes.
    """
    fig = go.Figure()

    for label, fit in fits.items():
        if fit is None:
            continue

        mult = GROUND_MULT.get(label, 1.0)

        # Thin dense clouds so the plot stays interactive; the fit itself
        # always uses every sample.
        stride = max(1, fit["n"] // 4000)

        fig.add_trace(go.Scattergl(
            x=fit["g"][::stride], y=fit["angle"][::stride] * mult,
            mode="markers", name=f"{label} (data)",
            marker=dict(size=3, opacity=0.25, color=COLORS.get(label, "#888")),
        ))

        xs = np.array([fit["g"].min(), fit["g"].max()])
        fig.add_trace(go.Scatter(
            x=xs, y=(fit["slope"] * xs + fit["intercept"]) * mult,
            mode="lines",
            name=f"{label}: {abs(fit['slope']) * mult:.3f} deg/g "
                 f"(R²={fit['r2']:.2f})",
            line=dict(color=COLORS.get(label, "#888"), width=2.5),
        ))

    fig.update_layout(
        title=title, xaxis_title=xlabel,
        yaxis_title="angle vs. ground (deg)",
        template="plotly_white", hovermode="closest",
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(output_path, include_plotlyjs="cdn")


def summary_only(grouped):
    """The gradient numbers, without plots or console output.

    For case_summary.py, which wants the figures but not the 30 seconds of
    plotting. Reuses roll_series / pitch_series / fit_gradient rather than
    duplicating the fit, so it cannot disagree with what main() reports.

    Returns the same FLAT shape main() does: "<event>_roll_<which>",
    "skidpad_steady_roll_<which>", "<event>_pitch".
    """
    out = {}

    for event in ROLL_EVENTS:
        paths = grouped.get(event, [])
        if not paths:
            continue

        cutoff = SKIDPAD_CUTOFF_HZ if event == "skidpad" else AUTOX_END_CUTOFF_HZ
        series = [s for p in paths if (s := roll_series(p, cutoff)) is not None]
        if not series:
            continue

        fits = {}
        for which in ("front", "rear", "avg"):
            use = usable_series(series, which)
            if not use:
                fits[which] = None
                emit_gradient(out, f"{event}_roll_{which}", None, which)
                continue
            g = np.concatenate([s["lat"][s["keep"]] for s in use])
            a = np.concatenate([s[which][s["keep"]] for s in use])
            fits[which] = fit_gradient(g, a)
            emit_gradient(out, f"{event}_roll_{which}", fits[which], which)

        # Skidpad's steady-segment fit is the cleanest estimate and the one
        # the summary table should show.
        if event == "skidpad":
            sfits = {}
            for which in ("front", "rear", "avg"):
                use = usable_series(series, which)
                masks = [s["keep"] & steady_mask(s) for s in use]
                g = np.concatenate([s["lat"][m] for s, m in zip(use, masks)])
                a = np.concatenate([s[which][m] for s, m in zip(use, masks)])
                sfits[which] = fit_gradient(g, a)
                emit_gradient(out, f"skidpad_steady_roll_{which}",
                              sfits[which], which)

    for event in PITCH_EVENTS:
        paths = grouped.get(event, [])
        if not paths:
            continue

        series = [s for p in paths
                  if (s := pitch_series(p, AUTOX_END_CUTOFF_HZ)) is not None]
        if not series:
            continue

        use = usable_series(series, "pitch")
        if not use:
            emit_gradient(out, f"{event}_pitch", None, "pitch")
            continue
        g = np.concatenate([s["lon"][s["keep"]] for s in use])
        a = np.concatenate([s["pitch"][s["keep"]] for s in use])
        emit_gradient(out, f"{event}_pitch", fit_gradient(g, a), "pitch")

    return out


def main():
    parser = argparse.ArgumentParser(
        description="Roll and pitch gradients (deg/g)."
    )
    parser.add_argument("--dir", default="comp2026_data")
    args = parser.parse_args()

    paths = sorted(glob.glob(os.path.join(args.dir, "*.csv")))
    if not paths:
        sys.exit(f"No CSVs found in {args.dir!r}.")

    grouped = group_by_event(paths)

    print("\n" + "=" * 78)
    print("CASE 5 — ROLL AND PITCH GRADIENTS (deg/g, GROUND-REFERENCED)")
    print("=" * 78)
    print("Headline figures include tyre deflection (chassis vs. ROAD), which "
          "is the reference")
    print("design targets use. [susp-ref ...] is the raw fitted slope the "
          "shock pots see.")
    print("Roll stiffness from the springs (225/200 lbf/in, no ARB): "
          "749 N*m/deg, i.e. ~673 N*m per g")
    print("at the measured 0.898 deg/g susp-ref. Not an absolute scale "
          "check — see the module docstring.")

    summary = {}

    # ── Roll ──
    for event in ROLL_EVENTS:
        event_paths = grouped.get(event, [])
        if not event_paths:
            continue

        cutoff = SKIDPAD_CUTOFF_HZ if event == "skidpad" else AUTOX_END_CUTOFF_HZ
        series = [s for p in event_paths if (s := roll_series(p, cutoff)) is not None]
        if not series:
            continue

        print(f"\n=== {event.upper()} — ROLL GRADIENT ({cutoff} Hz low-pass) ===")

        pooled = {}
        dropped = {}
        for which in ("front", "rear", "avg"):
            use = usable_series(series, which)
            dropped[which] = len(series) - len(use)
            if not use:
                pooled[which] = None
                continue
            g = np.concatenate([s["lat"][s["keep"]] for s in use])
            a = np.concatenate([s[which][s["keep"]] for s in use])
            pooled[which] = fit_gradient(g, a)

        if any(dropped.values()):
            print(f"    [!] excluded runs with known-bad channels: "
                  + ", ".join(f"{w} -{n}" for w, n in dropped.items() if n)
                  + "  (see case_common.SUSPECT_CORNERS)")

        pooled_ground = ground_values(pooled)
        for which in ("front", "rear", "avg"):
            report_fit(which, pooled[which], ground=pooled_ground.get(which))
            emit_gradient(summary, f"{event}_roll_{which}",
                          pooled[which], which)

        # PER-FILE, ALWAYS. A pooled gradient is only meaningful if every
        # file came off the same car. On autocross they did not: two of the
        # four sessions show a front gradient of 0.30-0.32 deg/g against
        # 0.80-0.82 for the other two, so pooling all four produces a 0.557
        # that describes no session that was actually run. Printing the
        # spread makes a split population impossible to miss.
        #
        # The table lists EVERY file, including any dropped from the pooled
        # fit — seeing the bad runs next to the good ones is the point. The
        # warning below is scoped to the POOLED files only, because it talks
        # about the pooled number.
        front_pooled = {s["path"] for s in usable_series(series, "front")}
        per_file = []
        for s in series:
            f = fit_gradient(s["lat"][s["keep"]], s["front"][s["keep"]])
            r = fit_gradient(s["lat"][s["keep"]], s["rear"][s["keep"]])
            if f and r:
                per_file.append((os.path.basename(s["path"]),
                                 abs(f["slope"]), f["r2"],
                                 abs(r["slope"]), r["r2"],
                                 s["path"] in front_pooled))

        if len(per_file) > 1:
            print(f"\n    per file:")
            print(f"      {'file':<26}{'front':>9}{'R²':>7}{'rear':>9}{'R²':>7}"
                  f"{'rear/front':>12}")
            for name, fs, fr2, rs, rr2, pooled_in in per_file:
                flag = "" if pooled_in else "   [dropped from front fit]"
                print(f"      {name[:25]:<26}{fs:>9.3f}{fr2:>7.3f}"
                      f"{rs:>9.3f}{rr2:>7.3f}{rs / fs:>11.2f}x{flag}")

            # Scoped to the files the pooled fit ACTUALLY used. Measuring the
            # spread over every file instead told you not to quote a number
            # the known-bad runs were already excluded from — i.e. it
            # condemned the clean 0.809 autocross figure that the README
            # tells you to use.
            fronts = [p[1] for p in per_file if p[5]]
            if len(fronts) > 1:
                spread = max(fronts) / min(fronts)
                if spread > 1.5:
                    print(f"\n      [!] FRONT GRADIENT VARIES {spread:.1f}x ACROSS THE "
                          f"POOLED FILES ({min(fronts):.3f} to {max(fronts):.3f} deg/g).")
                    print(f"          The pooled figure above averages what look like "
                          f"different car")
                    print(f"          configurations and should NOT be quoted. See the "
                          f"README on the")
                    print(f"          front roll-stiffness split.")

        # PER-CORNER response, which is what isolates a front/rear split to
        # its cause. On autocross both front corners drop ~2.6x while both
        # rears are untouched — which first looked mechanical, but is not:
        # the runs are 2 minutes apart with identical lateral-G content, the
        # car has no anti-roll bar, and the raw pot VOLTAGE shows both front
        # sensors sitting at the bottom of their electrical range (0.2-0.8 V)
        # in exactly the affected files. It is the front shock pots running
        # out of stroke. See the README.
        #
        # The table stays because it is what distinguishes the two: a
        # one-channel fault moves one column, an axle-wide problem moves two
        # while preserving their ratio.
        print(f"\n    per-corner wheel travel per g "
              f"(mm/g — isolates a sensor fault from a setup change):")
        print(f"      {'file':<26}" + "".join(f"{c:>10}" for c in CORNERS))
        for s in series:
            row = f"      {os.path.basename(s['path'])[:25]:<26}"
            for corner in CORNERS:
                v = s["corner_mm"][corner][s["keep"]]
                lat = s["lat"][s["keep"]]
                row += f"{np.polyfit(lat, v, 1)[0]:>10.2f}"
            print(row)

        # RAW POT VOLTAGE, the check that separates "the car did something"
        # from "the sensor could not see it". A pot near either end of its
        # electrical range has run out of stroke, and its travel compresses
        # regardless of what the suspension actually did. Displacement alone
        # cannot show this, because disp is just a linear transform of volt
        # — the end-of-range is only visible in the volts.
        volts = {"FL": "VCFRONT_shockpotVoltFL", "FR": "VCFRONT_shockpotVoltFR",
                 "RL": "VCREAR_shockpotVoltRL", "RR": "VCREAR_shockpotVoltRR"}

        print(f"\n    raw pot voltage (V), 0.5-99.5 pctile band — a band that "
              f"never rises above {POT_VOLT_CEILING:.1f} V means out of stroke:")
        print(f"      {'file':<26}" + "".join(f"{c:>16}" for c in CORNERS))

        for s in series:
            sig = parse_influx(s["path"], verbose=False)
            row = f"      {os.path.basename(s['path'])[:25]:<26}"
            low = False
            for corner in CORNERS:
                if volts[corner] not in sig:
                    row += f"{'—':>16}"
                    continue
                v = np.asarray(sig[volts[corner]].value, dtype=float)
                v = v[np.isfinite(v)]
                lo, hi = np.percentile(v, 0.5), np.percentile(v, 99.5)
                if hi < POT_VOLT_CEILING:
                    low = True
                row += f"{f'{lo:.2f}-{hi:.2f}':>16}"
            print(row + ("   [!] OUT OF STROKE — never leaves the extension end" if low else ""))

        if pooled["front"] and pooled["rear"]:
            f, r = abs(pooled["front"]["slope"]), abs(pooled["rear"]["slope"])
            print(f"    {'rear vs front':<22}rear is {100 * (r - f) / f:+.1f}% "
                  f"of front — the known front/rear disagreement, in deg/g")

        build_scatter(
            pooled, f"Roll gradient — {event}", "lateral G (g)",
            os.path.join(PLOTS_ROOT, event, "roll_gradient.html"))

        # Steady-state-only estimate, skidpad's cleanest number.
        if event == "skidpad":
            print(f"\n    STEADY-STATE ONLY (the number to quote):")
            steady = {}
            for which in ("front", "rear", "avg"):
                use = usable_series(series, which)
                if not use:
                    steady[which] = None
                    continue
                g = np.concatenate([s["lat"][s["keep"] & steady_mask(s)] for s in use])
                a = np.concatenate([s[which][s["keep"] & steady_mask(s)] for s in use])
                steady[which] = fit_gradient(g, a)
            steady_ground = ground_values(steady)
            for which in ("front", "rear", "avg"):
                report_fit(which, steady[which],
                           ground=steady_ground.get(which))
                emit_gradient(summary, f"skidpad_steady_roll_{which}",
                              steady[which], which)

            build_scatter(
                steady, "Roll gradient — skidpad, steady segments only",
                "lateral G (g)",
                os.path.join(PLOTS_ROOT, "skidpad", "roll_gradient_steady.html"))

    # ── Pitch ──
    for event in PITCH_EVENTS:
        event_paths = grouped.get(event, [])
        if not event_paths:
            continue

        cutoff = AUTOX_END_CUTOFF_HZ
        series = [s for p in event_paths if (s := pitch_series(p, cutoff)) is not None]
        if not series:
            continue

        print(f"\n=== {event.upper()} — PITCH GRADIENT ({cutoff} Hz low-pass) ===")

        # Pitch is front-axle-average minus rear, so it needs all four
        # corners and a bad front pair disqualifies the run — same exclusion
        # as whole-car roll.
        use = usable_series(series, "pitch")
        if len(use) < len(series):
            print(f"    [!] excluded {len(series) - len(use)} run(s) with "
                  f"known-bad channels (see case_common.SUSPECT_CORNERS)")

        if not use:
            print("    no usable runs")
            continue

        g = np.concatenate([s["lon"][s["keep"]] for s in use])
        a = np.concatenate([s["pitch"][s["keep"]] for s in use])
        fit = fit_gradient(g, a)

        # Braking is positive lon G and pitches the nose DOWN, which on this
        # car's convention is negative pitch_mm — so the same negative slope
        # as roll. Verified, not assumed: case3 established the convention
        # against vehicle speed.
        report_fit("pitch", fit,
                   ground=to_ground_referenced(fit_magnitude(fit), "pitch"))
        emit_gradient(summary, f"{event}_pitch", fit, "pitch")

        build_scatter(
            {"pitch": fit}, f"Pitch gradient — {event}", "longitudinal G (g)",
            os.path.join(PLOTS_ROOT, event, "pitch_gradient.html"))

    print("\n" + "-" * 78)
    print(f"Plots: {PLOTS_ROOT}/<event>/")
    print("The SCATTER is as much the result as the slope — a tight line means")
    print("linear and lag-free, an open loop means hysteresis through transients.")
    print("-" * 78 + "\n")

    return summary


CONVENTIONS = [
    "<b>Every gradient here is GROUND-REFERENCED</b> — deg of chassis "
    "attitude per g, measured against the ROAD with tyre deflection "
    "included. That is what a design gradient means, so these compare "
    "directly against the Simplified Steady State Suspension Spreadsheet's predicted "
    "roll gradient (1.307 °/g) and predicted pitch gradient "
    "(0.901 °/g pitch).",
    "<b>Previously this page led with the raw fitted slope</b>, which is "
    "suspension-referenced — chassis against the wheel-centre line, all a "
    "shock pot spans. It is ~19% lower on roll and ~20% on pitch, and "
    "comparing it against a ground-referenced target is what made the "
    "measurement look far too small. It is still printed beside each "
    "headline as <code>[susp-ref …]</code>, because the spring check below "
    "validates <i>that</i> figure and you need it to audit the conversion.",
    "<b>R², n, G range and intercept belong to the fit and are "
    "reference-independent</b> — the conversion is a constant multiplier, so "
    "it cannot change how good the fit is. The scatter plots are drawn in "
    "the same ground reference as the slope.",
    "The <b>scatter is as much the result as the slope</b>. A tight line "
    "means the relationship is linear and lag-free; an open loop is "
    "hysteresis through transients, which is kept rather than filtered out.",
]


if __name__ == "__main__":
    with report_page("case5_gradients", "Case 5 — Roll and Pitch Gradient",
                     PLOTS_ROOT) as page:
        # Every number this case produces is a gradient, and none of its
        # summary keys carry a unit token ("roll_avg", "pitch"), so the
        # cards need telling.
        page.default_unit = "°/g"
        page.summary = main()
        for text in CONVENTIONS:
            page.add_convention(text)
    write_index()
