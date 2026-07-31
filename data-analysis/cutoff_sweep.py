# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
cutoff_sweep.py — how much does the cutoff actually change the answer?

The review pages show what a cutoff does to a TRACE. This shows what it does
to the NUMBER you report, which is the thing you actually care about. For
several quantities the answer turns out to be "almost nothing", and knowing
which those are means not agonising over them.

It re-runs the entire case1-case4 pipeline at each frequency by patching the
cutoff constants on the case modules and calling case_summary's collectors —
so nothing is reimplemented and nothing can drift from what the cases really
do. A full pass over 11 files and 4 cases is ~20s, so a seven-point sweep is
a couple of minutes.

BOTH constants are set to the same value at each step, so every event is
filtered at the swept frequency and each row shows that event's own
sensitivity. This is deliberately NOT how production runs (skidpad uses 2 Hz
and everything else 5 Hz) — the point is to isolate the effect of the cutoff
itself, not to reproduce the current configuration.

READ THE SENSITIVITY COLUMN FIRST. It is the spread across the whole sweep
as a percentage of the value at the current production cutoff:

    under ~2%   the cutoff does not matter for this number; pick on other
                grounds and stop worrying about it
    2-10%       matters; the plots are worth studying
    over 10%    the number is largely a statement about your filter, and
                should be quoted with the cutoff attached

CAVEAT — VCFRONT_brakePressure is sampled at 10 Hz, so its 5 Hz Nyquist
makes any swept value at or above 5 Hz meaningless for the brake-window
detection case3 uses it for. Brake-event rows above 5 Hz are not wrong so
much as undefined; treat them as noise.

Run it:
    uv run cutoff_sweep.py --dir comp2026_data
    uv run cutoff_sweep.py --dir comp2026_data --freqs 2 3 4 5 6 8 10 15 20
"""

import os
import sys
import glob
import argparse

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from case_common import group_by_event, SKIDPAD_CUTOFF_HZ, AUTOX_END_CUTOFF_HZ

import case_summary as cs
import case1_max_gs as c1
import case2_max_roll as c2
import case3_max_pitch as c3
import case4_combined_roll_pitch as c4

PLOTS_ROOT = os.path.join("plots", "cutoff_sweep")

DEFAULT_FREQS = [2.0, 3.0, 5.0, 8.0, 10.0, 15.0, 20.0]

# Below this spread, the cutoff is not what determines the number.
INSENSITIVE_PCT = 2.0
SENSITIVE_PCT = 10.0

# Modules whose module-global cutoff constants have to be patched. Each case
# imports the constants into its own namespace and reads them at call time,
# so setting the attribute here really does change what they filter at.
PATCH_TARGETS = [cs, c1, c2, c3, c4]


def set_cutoff(value):
    for module in PATCH_TARGETS:
        if hasattr(module, "SKIDPAD_CUTOFF_HZ"):
            module.SKIDPAD_CUTOFF_HZ = value
        if hasattr(module, "AUTOX_END_CUTOFF_HZ"):
            module.AUTOX_END_CUTOFF_HZ = value


def flatten(prefix, obj, out):
    """Flatten the nested case summaries to dotted scalar keys."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            flatten(f"{prefix}.{key}" if prefix else str(key), value, out)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out[prefix] = float(obj)
    return out


def collect_at(cutoff, grouped):
    set_cutoff(cutoff)

    summaries = {
        "case1": cs.collect_case1(grouped),
        "case2": cs.collect_case2(grouped),
        "case3": cs.collect_case3(grouped),
        "case4": cs.collect_case4(grouped),
    }

    return flatten("", summaries, {})


def main():
    parser = argparse.ArgumentParser(
        description="Measure how much each headline number depends on the cutoff."
    )
    parser.add_argument("--dir", default="comp2026_data")
    parser.add_argument("--freqs", nargs="+", type=float, default=DEFAULT_FREQS)
    args = parser.parse_args()

    paths = sorted(glob.glob(os.path.join(args.dir, "*.csv")))
    if not paths:
        sys.exit(f"No CSVs found in {args.dir!r}.")

    grouped = group_by_event(paths)

    freqs = sorted(args.freqs)

    # Production baseline first, so sensitivity is expressed against the
    # numbers currently published rather than an arbitrary sweep point.
    print(f"Baseline (production: skidpad {SKIDPAD_CUTOFF_HZ} Hz, "
          f"everything else {AUTOX_END_CUTOFF_HZ} Hz)...", flush=True)

    baseline_skid, baseline_autox = SKIDPAD_CUTOFF_HZ, AUTOX_END_CUTOFF_HZ

    for module in PATCH_TARGETS:
        if hasattr(module, "SKIDPAD_CUTOFF_HZ"):
            module.SKIDPAD_CUTOFF_HZ = baseline_skid
        if hasattr(module, "AUTOX_END_CUTOFF_HZ"):
            module.AUTOX_END_CUTOFF_HZ = baseline_autox

    baseline = flatten("", {
        "case1": cs.collect_case1(grouped),
        "case2": cs.collect_case2(grouped),
        "case3": cs.collect_case3(grouped),
        "case4": cs.collect_case4(grouped),
    }, {})

    results = {}
    for cutoff in freqs:
        print(f"  {cutoff:.1f} Hz...", flush=True)
        results[cutoff] = collect_at(cutoff, grouped)

    keys = sorted(set(baseline) & set.intersection(*(set(r) for r in results.values())))

    rows = []
    for key in keys:
        values = np.array([results[f].get(key, np.nan) for f in freqs])
        base = baseline.get(key, np.nan)

        if not np.isfinite(base) or base == 0 or not np.all(np.isfinite(values)):
            continue

        # SPREAD ON MAGNITUDE, and sign flips flagged separately.
        #
        # These are signed quantities, and several of them flip sign across
        # the sweep — skidpad's worst travel reads +18.5mm at 5 Hz and
        # -19.8mm at 8 Hz. That is not a 216% change in the physical answer;
        # it is the peak search picking the other direction, which on a
        # both-ways skidpad is a near-equal candidate whose tie the filter
        # happens to break. Differencing raw signed values reported exactly
        # that nonsense, and put seven such rows at the top of the table.
        #
        # The magnitude spread is the honest number (14.5% for that row) and
        # the sign flip is reported as its own fact, because "which instant
        # won" changing IS worth knowing — just not as a percentage.
        magnitudes = np.abs(values)
        spread = 100.0 * (magnitudes.max() - magnitudes.min()) / abs(base)

        flipped = bool(np.any(np.sign(values) != np.sign(values[0])))

        rows.append((key, base, values, spread, flipped))

    rows.sort(key=lambda r: -r[3])

    print(f"\n{'=' * 100}")
    print("HOW MUCH THE CUTOFF CHANGES EACH NUMBER")
    print(f"spread = (max - min) across {freqs[0]:.0f}-{freqs[-1]:.0f} Hz, "
          f"as % of the production value")
    print(f"{'=' * 100}")

    header = f"{'quantity':<52}{'production':>11}" + "".join(
        f"{f:>8.0f}Hz" for f in freqs) + f"{'spread':>9}"
    print(header)

    for key, base, values, spread, flipped in rows:
        flag = ""
        if spread >= SENSITIVE_PCT:
            flag = "  <-- filter-dominated"
        elif spread < INSENSITIVE_PCT:
            flag = "  (insensitive)"

        if flipped:
            flag += "  [SIGN FLIPS — the winning instant changes, not the magnitude]"

        print(f"{key[:51]:<52}{base:>11.4f}"
              + "".join(f"{v:>10.4f}" for v in values)
              + f"{spread:>8.1f}%{flag}")

    n_insensitive = sum(1 for r in rows if r[3] < INSENSITIVE_PCT)
    n_sensitive = sum(1 for r in rows if r[3] >= SENSITIVE_PCT)
    n_flipped = sum(1 for r in rows if r[4])

    print(f"\n{'=' * 100}")
    print(f"  {n_insensitive} of {len(rows)} numbers move less than "
          f"{INSENSITIVE_PCT}% across the whole sweep — for those, the cutoff "
          f"is not the thing")
    print(f"  {n_sensitive} move more than {SENSITIVE_PCT}% and should be "
          f"quoted with the cutoff attached")
    if n_flipped:
        print(f"  {n_flipped} change SIGN across the sweep — near-equal "
              f"candidates whose tie the filter breaks, not a magnitude change")
    print(f"{'=' * 100}")

    os.makedirs(PLOTS_ROOT, exist_ok=True)

    # TWO CHARTS, because there are two different questions and one chart
    # answering both answers neither. An earlier version drew all 65
    # quantities as lines on a single normalised axis — unreadable, and it
    # forced you to decode "% of production value" before it said anything.

    # 1. WHICH numbers care about the cutoff? A ranked bar chart. This is
    #    the one to read first: it turns 65 quantities into a short list of
    #    the ones worth thinking about.
    bar = go.Figure()

    case_colors = {"case1": "#2a78d6", "case2": "#eb6834",
                   "case3": "#1baf7a", "case4": "#eda100"}

    ordered = sorted(rows, key=lambda r: r[3])

    bar.add_trace(go.Bar(
        x=[r[3] for r in ordered],
        y=[r[0] for r in ordered],
        orientation="h",
        marker=dict(color=[case_colors.get(r[0].split(".")[0], "#888")
                           for r in ordered]),
        hovertemplate="%{y}<br>moves %{x:.1f}%<extra></extra>",
    ))

    bar.add_vline(x=INSENSITIVE_PCT, line=dict(color="#1baf7a", dash="dash"),
                  annotation_text=f"{INSENSITIVE_PCT:.0f}% — below this the "
                                  f"cutoff isn't what decides the number")
    bar.add_vline(x=SENSITIVE_PCT, line=dict(color="#e34948", dash="dash"),
                  annotation_text=f"{SENSITIVE_PCT:.0f}% — above this, quote "
                                  f"the cutoff with the number")

    bar.update_layout(
        title=f"How much each number changes across a {freqs[0]:.0f}-"
              f"{freqs[-1]:.0f} Hz cutoff sweep",
        xaxis_title="change from lowest to highest cutoff (% of today's value)",
        yaxis_title="",
        template="plotly_white",
        height=max(600, 18 * len(ordered)),
        margin=dict(l=380),
        showlegend=False,
    )

    out_bar = os.path.join(PLOTS_ROOT, "which_numbers_care.html")
    bar.write_html(out_bar, include_plotlyjs="cdn")

    # 2. HOW do the sensitive ones move? Small multiples in each quantity's
    #    OWN units, so nothing needs normalising or decoding. Only the ones
    #    that actually move — plotting the flat ones wastes the space.
    movers = [r for r in rows if r[3] >= INSENSITIVE_PCT][:24]

    ncols = 4
    nrows = int(np.ceil(len(movers) / ncols)) or 1

    panels = make_subplots(
        rows=nrows, cols=ncols,
        subplot_titles=[f"{r[0].split('.', 1)[-1][:34]}<br>"
                        f"<sub>{r[3]:.0f}%</sub>" for r in movers],
        vertical_spacing=0.08, horizontal_spacing=0.06,
    )

    for i, (key, base, values, spread, flipped) in enumerate(movers):
        panels.add_trace(
            go.Scatter(x=freqs, y=np.abs(values), mode="lines+markers",
                       line=dict(color=case_colors.get(key.split(".")[0], "#888"),
                                 width=2),
                       showlegend=False),
            row=i // ncols + 1, col=i % ncols + 1,
        )
        # Where the number sits today, so the panel reads as "what would
        # change" rather than as an abstract curve.
        panels.add_hline(y=abs(base), line=dict(color="#999", dash="dot"),
                         row=i // ncols + 1, col=i % ncols + 1)

    panels.update_layout(
        title="How each cutoff-sensitive number moves — real units, "
              "dotted line = today's value",
        template="plotly_white",
        height=260 * nrows,
        showlegend=False,
    )
    panels.update_xaxes(title_text="cutoff (Hz)", row=nrows)

    out_panels = os.path.join(PLOTS_ROOT, "how_they_move.html")
    panels.write_html(out_panels, include_plotlyjs="cdn")

    print(f"\nPlots:")
    print(f"  {out_bar}")
    print(f"      WHICH numbers care — read this first")
    print(f"  {out_panels}")
    print(f"      HOW the sensitive ones move, in their own units\n")


if __name__ == "__main__":
    main()
