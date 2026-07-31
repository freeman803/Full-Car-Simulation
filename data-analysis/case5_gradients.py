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

Prior estimate to check against: 0.83-0.94 deg/g, derived by hand from four
independent estimates. That was never computed by any script until now.

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
    CORNERS, CORNER_SIGNAL_NAMES, TRIM_SECONDS,
)
from parse_influx import parse_influx

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

def report_fit(label, fit, expect_negative=True):
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

    print(f"    {label:<22}{magnitude:6.3f} deg/g   "
          f"R²={fit['r2']:.3f}  n={fit['n']:,}  "
          f"G range {fit['g_range']:.2f}  "
          f"intercept {fit['intercept']:+.3f} deg{flag}")

    return magnitude


def build_scatter(fits, title, xlabel, output_path):
    """Roll/pitch against G, with the fitted line. The CLOUD is the point:
    a tight line means the relationship is linear and lag-free; an open
    loop is hysteresis through transients."""
    fig = go.Figure()

    for label, fit in fits.items():
        if fit is None:
            continue

        # Thin dense clouds so the plot stays interactive; the fit itself
        # always uses every sample.
        stride = max(1, fit["n"] // 4000)

        fig.add_trace(go.Scattergl(
            x=fit["g"][::stride], y=fit["angle"][::stride],
            mode="markers", name=f"{label} (data)",
            marker=dict(size=3, opacity=0.25, color=COLORS.get(label, "#888")),
        ))

        xs = np.array([fit["g"].min(), fit["g"].max()])
        fig.add_trace(go.Scatter(
            x=xs, y=fit["slope"] * xs + fit["intercept"],
            mode="lines",
            name=f"{label}: {abs(fit['slope']):.3f} deg/g (R²={fit['r2']:.2f})",
            line=dict(color=COLORS.get(label, "#888"), width=2.5),
        ))

    fig.update_layout(
        title=title, xaxis_title=xlabel, yaxis_title="angle (deg)",
        template="plotly_white", hovermode="closest",
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(output_path, include_plotlyjs="cdn")


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
    print("CASE 5 — ROLL AND PITCH GRADIENTS (deg/g)")
    print("=" * 78)
    print("Prior hand-derived estimate to check against: 0.83-0.94 deg/g")

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
        for which in ("front", "rear", "avg"):
            g = np.concatenate([s["lat"][s["keep"]] for s in series])
            a = np.concatenate([s[which][s["keep"]] for s in series])
            pooled[which] = fit_gradient(g, a)

        for which in ("front", "rear", "avg"):
            summary[f"{event}_roll_{which}"] = report_fit(which, pooled[which])

        # PER-FILE, ALWAYS. A pooled gradient is only meaningful if every
        # file came off the same car. On autocross they did not: two of the
        # four sessions show a front gradient of 0.29-0.31 deg/g against
        # 0.78-0.79 for the other two, so pooling them produced a 0.542 that
        # describes no session that was actually run. Printing the spread
        # makes a split population impossible to miss.
        per_file = []
        for s in series:
            f = fit_gradient(s["lat"][s["keep"]], s["front"][s["keep"]])
            r = fit_gradient(s["lat"][s["keep"]], s["rear"][s["keep"]])
            if f and r:
                per_file.append((os.path.basename(s["path"]),
                                 abs(f["slope"]), f["r2"],
                                 abs(r["slope"]), r["r2"]))

        if len(per_file) > 1:
            print(f"\n    per file:")
            print(f"      {'file':<26}{'front':>9}{'R²':>7}{'rear':>9}{'R²':>7}"
                  f"{'rear/front':>12}")
            for name, fs, fr2, rs, rr2 in per_file:
                print(f"      {name[:25]:<26}{fs:>9.3f}{fr2:>7.3f}"
                      f"{rs:>9.3f}{rr2:>7.3f}{rs / fs:>11.2f}x")

            fronts = [p[1] for p in per_file]
            spread = max(fronts) / min(fronts)
            if spread > 1.5:
                print(f"\n      [!] FRONT GRADIENT VARIES {spread:.1f}x ACROSS FILES "
                      f"({min(fronts):.3f} to {max(fronts):.3f} deg/g).")
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
                g = np.concatenate([s["lat"][s["keep"] & steady_mask(s)] for s in series])
                a = np.concatenate([s[which][s["keep"] & steady_mask(s)] for s in series])
                steady[which] = fit_gradient(g, a)
            for which in ("front", "rear", "avg"):
                summary[f"skidpad_steady_roll_{which}"] = report_fit(which, steady[which])

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

        g = np.concatenate([s["lon"][s["keep"]] for s in series])
        a = np.concatenate([s["pitch"][s["keep"]] for s in series])
        fit = fit_gradient(g, a)

        # Braking is positive lon G and pitches the nose DOWN, which on this
        # car's convention is negative pitch_mm — so the same negative slope
        # as roll. Verified, not assumed: case3 established the convention
        # against vehicle speed.
        summary[f"{event}_pitch"] = report_fit("pitch", fit)

        build_scatter(
            {"pitch": fit}, f"Pitch gradient — {event}", "longitudinal G (g)",
            os.path.join(PLOTS_ROOT, event, "pitch_gradient.html"))

    print("\n" + "-" * 78)
    print(f"Plots: {PLOTS_ROOT}/<event>/")
    print("The SCATTER is as much the result as the slope — a tight line means")
    print("linear and lag-free, an open loop means hysteresis through transients.")
    print("-" * 78 + "\n")


if __name__ == "__main__":
    main()
