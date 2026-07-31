# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
test_regression.py — pin every headline number, so a change that moves them
has to be a change someone MEANT to make.

WHY THIS EXISTS. Six real bugs were found and fixed in this analysis in
quick succession: VCPDU_lat/lon read as g when the DBC says m/s^2, a
hardcoded runs-per-direction cap that silently discarded data, shock-pot
step glitches winning the peak search, filtfilt edge artefacts, an inverted
roll sign convention in the docs, and a braketest2 "unreliable" verdict
that turned out to be an artefact of measuring std across a step. Every one
of those fixes changed published numbers. Nothing existed that would have
caught any of them going the other way.

WHAT IT IS NOT. Not a correctness test — it cannot tell you a number is
RIGHT, only that it is the SAME. That is the useful property while the
cutoff selection is in flight: when the per-signal cutoff table lands,
every roll/pitch/travel figure will move, and the question is whether they
moved the way you expected and only where you expected.

HOW IT AVOIDS DRIFTING FROM THE CASES. Same trick case_summary.py uses: it
does not reimplement anything. It calls case_summary's own collectors,
which call each case's real analyse/report functions. If a case changes
methodology, this picks it up rather than testing a stale copy.

Run it:
    uv run test_regression.py --dir comp2026_data          # check
    uv run test_regression.py --dir comp2026_data --update # re-pin

WHEN A CHECK FAILS, that is information, not an error to silence. Read the
diff, decide whether the change was intended, and if it was, re-pin with
--update and COMMIT THE DIFF. The commit is the record of what moved and
why — which is exactly what was missing before.
"""

import os
import sys
import glob
import json
import argparse

import numpy as np

from parse_influx import parse_influx
from case_common import (
    group_by_event, elapsed_seconds, find_step_glitches,
    CORNERS, CORNER_SIGNAL_NAMES,
)

import case_summary as cs

EXPECTED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "regression_expected.json")

# Numbers are deterministic on a given input, so any real change lands far
# above this. The tolerance only absorbs last-bit float noise, e.g. from a
# numpy/scipy version bump reassociating a sum.
RTOL = 1e-9
ATOL = 1e-12


def collect_case_summaries(grouped):
    """Every case's own summary dicts, via case_summary's collectors.

    case5 is included because its gradients are headline numbers — and
    because it is the only case affected by SUSPECT_CORNERS, so a change to
    that registry would otherwise move a published figure with nothing
    watching. (Cases 1-4 are immune: they report peaks, and the suspect
    channels under-report, so bad data never wins a peak search. Verified —
    adding the registry moved zero pinned values.)
    """
    return {
        "case1_max_gs": cs.collect_case1(grouped),
        "case2_max_roll": cs.collect_case2(grouped),
        "case3_max_pitch": cs.collect_case3(grouped),
        "case4_combined_roll_pitch": cs.collect_case4(grouped),
        "case5_gradients": cs.collect_case5(grouped),
    }


def collect_glitches(paths):
    """The step-glitch inventory: 12 events across 4 files.

    Pinned separately from the case summaries because it is the one piece
    of the pipeline whose OUTPUT is a list of events rather than a number,
    and because a change to GLITCH_STEP_MM would move it silently — the
    threshold sits in a 4.4mm-to-20.3mm empty gap, so anything that
    narrows that gap is worth noticing.
    """
    out = {}
    for path in sorted(paths):
        signals = parse_influx(path, verbose=False)

        names = [CORNER_SIGNAL_NAMES[c] for c in CORNERS]
        if not all(n in signals for n in names):
            continue

        t = elapsed_seconds(signals[names[0]].time)

        corners_raw = {
            c: np.asarray(signals[CORNER_SIGNAL_NAMES[c]].value, dtype=float)
            for c in CORNERS
        }

        _, events = find_step_glitches(corners_raw, t)

        if events:
            out[os.path.basename(path)] = [
                {"corner": c, "time_s": round(ts, 2), "jump_mm": round(j, 2)}
                for c, ts, j in events
            ]
    return out


def test_lockup_guard():
    """The lockup guard changes nothing on real data, so test it on made-up
    data instead.

    find_static_window's guard rejects candidate stops whose mean |lon G|
    reaches STATIC_MAX_LON_G, because VCFRONT_vehicleSpeed comes from wheel
    speed and reads ~zero during a four-wheel lockup while the car is still
    moving. Every genuine stop in comp2026_data averages 0.008-0.031 g, so
    the guard never fires there — which makes it indistinguishable from
    dead code without this.

    Returns a list of failure strings; empty means pass.
    """
    from case_common import find_static_window

    failures = []

    t = np.arange(0, 60, 0.01)

    # Two speed-zero windows. 5-15s is a real standstill; 30-40s is a
    # lockup, wheels stopped but the car decelerating at 1.05 g.
    speed = np.full_like(t, 12.0)
    speed[(t >= 5) & (t <= 15)] = 0.0
    speed[(t >= 30) & (t <= 40)] = 0.0

    lon = np.zeros_like(t)
    lon[(t >= 5) & (t <= 15)] = 0.005
    lon[(t >= 30) & (t <= 40)] = 1.05

    window = find_static_window(speed, t, lon_g=lon)
    if window is None or not (4.0 < t[window[0]] < 6.0):
        failures.append(
            f"lockup guard: with a real stop AND a lockup present, expected "
            f"the ~5-15s standstill, got "
            f"{'None' if window is None else f'{t[window[0]]:.1f}-{t[window[1]]:.1f}s'}"
        )

    # The dangerous case: the lockup is the ONLY speed-zero window. The
    # right answer is None, so baselines_found goes False and the caller
    # warns instead of baselining against a hard-braking car.
    speed2 = np.full_like(t, 12.0)
    speed2[(t >= 30) & (t <= 40)] = 0.0

    lon2 = np.zeros_like(t)
    lon2[(t >= 30) & (t <= 40)] = 1.05

    if find_static_window(speed2, t, lon_g=lon2) is not None:
        failures.append(
            "lockup guard: a lockup was accepted as a stopped-car window "
            "when it was the only speed-zero candidate"
        )

    # And without the guard it must still select the lockup — otherwise
    # this test would pass for the wrong reason.
    if find_static_window(speed2, t) is None:
        failures.append(
            "lockup guard test is not exercising anything: the unguarded "
            "call also rejected the lockup"
        )

    return failures


def build_snapshot(csv_dir):
    paths = sorted(glob.glob(os.path.join(csv_dir, "*.csv")))
    if not paths:
        sys.exit(f"No CSVs found in {csv_dir!r}.")

    grouped = group_by_event(paths)

    return {
        "files": [os.path.basename(p) for p in paths],
        "cases": collect_case_summaries(grouped),
        "glitches": collect_glitches(paths),
    }


# ── Comparison ───────────────────────────────────────────────────────────

def walk(expected, actual, path=""):
    """Yield (path, expected, actual) for every leaf that differs."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual)):
            sub = f"{path}.{key}" if path else str(key)
            if key not in expected:
                yield sub, "<missing>", actual[key]
            elif key not in actual:
                yield sub, expected[key], "<missing>"
            else:
                yield from walk(expected[key], actual[key], sub)

    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            yield path, f"{len(expected)} items", f"{len(actual)} items"
        else:
            for i, (e, a) in enumerate(zip(expected, actual)):
                yield from walk(e, a, f"{path}[{i}]")

    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)) \
            and not isinstance(expected, bool) and not isinstance(actual, bool):
        if not np.isclose(expected, actual, rtol=RTOL, atol=ATOL):
            yield path, expected, actual

    elif expected != actual:
        yield path, expected, actual


def report(diffs):
    print(f"\n{len(diffs)} value(s) changed:\n")

    for path, exp, act in diffs:
        print(f"  {path}")
        print(f"      pinned: {exp}")
        print(f"      now:    {act}")

        # Percentage is what makes a diff readable — "1.4953 -> 1.5738" is
        # hard to weigh, "+5.25%" is not.
        if isinstance(exp, (int, float)) and isinstance(act, (int, float)) \
                and not isinstance(exp, bool) and exp:
            print(f"      change: {100.0 * (act - exp) / abs(exp):+.3f}%")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Pin and check the analysis's headline numbers."
    )
    parser.add_argument("--dir", default="comp2026_data",
                        help="Folder of CSVs (default: comp2026_data)")
    parser.add_argument("--update", action="store_true",
                        help="Re-pin expected values to what the code "
                             "currently produces. Commit the resulting diff.")
    args = parser.parse_args()

    guard_failures = test_lockup_guard()
    if guard_failures:
        print("\nLOCKUP GUARD SELF-TEST FAILED:")
        for f in guard_failures:
            print(f"  {f}")
        return 1
    print("Lockup guard self-test: PASS")

    print(f"Running all four cases over {args.dir!r}...")
    snapshot = build_snapshot(args.dir)

    n_glitches = sum(len(v) for v in snapshot["glitches"].values())
    print(f"  {len(snapshot['files'])} files, "
          f"{n_glitches} step glitches across "
          f"{len(snapshot['glitches'])} file(s)")

    if args.update or not os.path.exists(EXPECTED_PATH):
        if not os.path.exists(EXPECTED_PATH):
            print(f"\nNo pinned values yet — creating {EXPECTED_PATH}.")
        with open(EXPECTED_PATH, "w") as fh:
            json.dump(snapshot, fh, indent=2, sort_keys=True)
        print(f"Pinned {os.path.basename(EXPECTED_PATH)}. "
              f"Commit it so the change is on the record.")
        return 0

    with open(EXPECTED_PATH) as fh:
        expected = json.load(fh)

    diffs = list(walk(expected, snapshot))

    if not diffs:
        print("\nPASS — every pinned value matches.")
        return 0

    report(diffs)
    print("If these changes were intended, re-pin with --update and commit "
          "the diff.\nIf not, something regressed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
