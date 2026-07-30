# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "matplotlib"]
# ///
"""
batch_signal_stats.py — min/max/mean for all 19 telemetry signals (plus
lat/lon in g's and vehicle speed in km/h), pooled by event type. Files are grouped by event type
(skidpad, autocross, endurance, brake, accel), detected from each
filename, and ALL samples from ALL files of the same event type are
combined into a single stats table per event — e.g. every accel_*.csv
file's data is pooled into one "ACCEL" table, not printed per file. A
final "ALL EVENTS COMBINED" table pools every file from every event
together, for an overall session-spanning view.

Run it on specific files:
    uv run batch_signal_stats.py accel_corinne1.csv accel_corinne2.csv

Or on every CSV in a folder:
    uv run batch_signal_stats.py --dir comp2026_data

Add --plot to also save, per event, a grid of time-series plots (one
subplot per signal, one line per file, x = elapsed seconds). PNGs go to
./plots by default, or --plot-dir <folder>:
    uv run batch_signal_stats.py --dir comp2026_data --plot
    uv run batch_signal_stats.py --dir comp2026_data --plot --plot-dir plots

See what is in a file WITHOUT parsing it — reads only the _field/_value
columns, writes no pickle cache, and reports n/min/max per signal. 1.0s on
the 234 MB endurance file against 3.8s for a cold full parse:
    uv run batch_signal_stats.py --dir comp2026_data --list-signals

This is also the only view that shows each signal's TRUE update rate,
because the stats table below counts samples on the resampled union grid.
Worth knowing: on skidpad, VCFRONT_brakePressure has 977 samples where the
shock pots have 9783 — roughly 10 Hz against 100 Hz.

Choose which signals to plot. The stats table always covers every signal;
only plotting is selectable, because a subplot grid stops being readable
well before the signal list does:
    uv run batch_signal_stats.py --dir comp2026_data --plot --signals VCPDU_lat,VCPDU_lon

With --plot and no --signals, you are prompted interactively (bare Enter
keeps all of them). The prompt is skipped when stdin is not a TTY, so
scripted and piped runs never block.

NEW SIGNALS NEED NO CODE CHANGE. parse_influx.py discovers signals from the
CSV's own _field column, and discover_signals() here reports everything
present, appending unrecognised names and flagging them.
PREFERRED_SIGNAL_ORDER is display order, not a filter.

Uses parse_influx.py (must be in the same folder, or importable).
"""

import sys
import glob
import os
import numpy as np
from parse_influx import parse_influx

# PREFERRED DISPLAY ORDER — not a filter.
#
# This list only controls the order familiar signals appear in; it does NOT
# limit what gets reported. discover_signals() below reports every signal
# actually present in the parsed files, appending anything not listed here
# and flagging it as new. So if the DBC gains channels (or you log a subset),
# this tool picks them up with no code change — which matters because it is
# the "look at everything first" tool, and silently omitting a new channel
# would defeat that.
#
# parse_influx.py is dynamic in the same way: it discovers signals from the
# CSV's own _field column rather than matching a fixed list.
#
# Note: VCPDU_lat / VCPDU_lon are lateral / longitudinal acceleration (m/s^2),
# not GPS coordinates.
PREFERRED_SIGNAL_ORDER = [
    "VCFRONT_brakePressure",
    "VCFRONT_shockpotVoltFL",
    "VCFRONT_shockpotVoltFR",
    "VCFRONT_shockpotdispFL",
    "VCFRONT_shockpotdispFR",
    "VCFRONT_steeringAngle",
    "VCFRONT_vehicleSpeed",
    "VCPDU_anglePitch",
    "VCPDU_angleRoll",
    "VCPDU_lat",
    "VCPDU_lon",
    "VCPDU_pitch",
    "VCPDU_roll",
    "VCPDU_yaw",
    "VCREAR_brakePressure",
    "VCREAR_shockpotVoltRL",
    "VCREAR_shockpotVoltRR",
    "VCREAR_shockpotdispRL",
    "VCREAR_shockpotdispRR",
]


def discover_signals(signals_list):
    """Return every signal name present in any of the parsed files, ordered:
    the PREFERRED_SIGNAL_ORDER entries that are actually present first, then
    anything else alphabetically.

    Also returns the list of unrecognised names, so the caller can point out
    that the data contains channels this script has never been told about.
    """
    present = set()
    for signals in signals_list:
        present.update(name for name in signals.keys())

    known = [n for n in PREFERRED_SIGNAL_ORDER if n in present]
    unknown = sorted(present - set(PREFERRED_SIGNAL_ORDER))
    return known + unknown, unknown


# Standard gravity, for converting VCPDU_lat/lon (m/s^2) to g's.
# 9.80665 is the standard value, matching case_common.py — an earlier 9.81
# here disagreed with the case scripts by 0.04%.
G = 9.80665

# Vehicle speed signal, and conversion factor from m/s to km/h.
SPEED_SIGNAL = "VCFRONT_vehicleSpeed"
KMH_PER_MS = 3.6

# Event type keywords to look for in filenames (checked in this order —
# first match wins). Matching is case-insensitive substring search, e.g.
# "braketest1.csv" matches "brake", "accel_corinne1.csv" matches "accel".
EVENT_KEYWORDS = ["skidpad", "autocross", "endurance", "brake", "accel"]


def detect_event_type(filename):
    """Return the matching event keyword found in the filename, or
    'unknown' if none of EVENT_KEYWORDS appear."""
    lower = os.path.basename(filename).lower()
    for keyword in EVENT_KEYWORDS:
        if keyword in lower:
            return keyword
    return "unknown"


def group_by_event(csv_paths):
    """Group file paths by detected event type, preserving EVENT_KEYWORDS
    order (with 'unknown' last), and preserving file order within a group."""
    groups = {kw: [] for kw in EVENT_KEYWORDS}
    groups["unknown"] = []
    for path in csv_paths:
        groups[detect_event_type(path)].append(path)
    return groups


def compute_pooled_stats(signals_list, signal_names):
    """Return {signal_name: {min, max, mean, n_samples}} pooled across ALL
    files in signals_list (each a parse_influx result) — i.e. min/max/mean
    computed over every valid sample from every file combined, not per file.
    Adds *_g rows for lat/lon accel."""

    results = {}
    for name in signal_names:
        pooled = []
        for signals in signals_list:
            if name not in signals:
                continue
            values = np.asarray(signals[name].value, dtype=float)
            valid = values[~np.isnan(values)]
            if valid.size:
                pooled.append(valid)

        if not pooled:
            continue

        all_valid = np.concatenate(pooled)
        results[name] = {
            "min": float(np.min(all_valid)),
            "max": float(np.max(all_valid)),
            "mean": float(np.mean(all_valid)),
            "n_samples": int(all_valid.size),
        }

    for accel_name in ("VCPDU_lat", "VCPDU_lon"):
        if accel_name in results:
            r = results[accel_name]
            results[f"{accel_name}_g"] = {
                "min": r["min"] / G,
                "max": r["max"] / G,
                "mean": r["mean"] / G,
                "n_samples": r["n_samples"],
            }

    if SPEED_SIGNAL in results:
        r = results[SPEED_SIGNAL]
        results[f"{SPEED_SIGNAL}_kmh"] = {
            "min": r["min"] * KMH_PER_MS,
            "max": r["max"] * KMH_PER_MS,
            "mean": r["mean"] * KMH_PER_MS,
            "n_samples": r["n_samples"],
        }

    return results


def print_stats(results):
    header = f"{'signal':30s} {'min':>12s} {'max':>12s} {'mean':>12s} {'n':>8s}"
    print(header)
    print("-" * len(header))
    for name, s in results.items():
        print(
            f"{name:30s} {s['min']:12.4f} {s['max']:12.4f} "
            f"{s['mean']:12.4f} {s['n_samples']:8d}"
        )


# Cap on points drawn per line. The union grid can be millions of samples;
# drawing every one is slow and adds no visible detail at figure resolution,
# so lines longer than this are stride-decimated for plotting only (stats
# above are always computed on the full data).
PLOT_MAX_POINTS = 20000


def _elapsed_seconds(time_index):
    """Seconds elapsed since the first sample, for use as a plot x-axis
    (files run at different absolute times, so absolute timestamps wouldn't
    line up — elapsed time puts every file on a common 'seconds into run')."""
    t = np.asarray(time_index, dtype="datetime64[ns]")
    if t.size == 0:
        return t.astype(float)
    return (t - t[0]) / np.timedelta64(1, "s")


def _decimate(x, y, max_points=PLOT_MAX_POINTS):
    """Stride-decimate a line to at most max_points for plotting."""
    n = len(x)
    if n <= max_points:
        return x, y
    step = int(np.ceil(n / max_points))
    return x[::step], y[::step]


def plot_event_timeseries(event, signals_list, paths, signal_names, out_dir):
    """Save one PNG for the event: a grid of subplots, one per signal, with
    each file drawn as its own line vs elapsed time. NaN gaps (a signal that
    starts late / ends early on the union grid) show as line breaks."""

    # Imported lazily so stats-only runs don't pay matplotlib's import cost.
    import matplotlib
    matplotlib.use("Agg")            # headless: render straight to PNG
    import matplotlib.pyplot as plt

    # Only plot signals that appear in at least one file.
    names = [n for n in signal_names
             if any(n in s for s in signals_list)]
    if not names:
        print(f"  [!] No plottable signals for event '{event}', skipping plot.")
        return

    ncols = 4
    nrows = int(np.ceil(len(names) / ncols))
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(ncols * 4.5, nrows * 2.8), squeeze=False
    )
    labels = [os.path.basename(p) for p in paths]

    for idx, name in enumerate(names):
        ax = axes[idx // ncols][idx % ncols]
        for signals, label in zip(signals_list, labels):
            if name not in signals:
                continue
            sig = signals[name]
            t = _elapsed_seconds(sig.time)
            v = np.asarray(sig.value, dtype=float)
            t, v = _decimate(t, v)
            ax.plot(t, v, linewidth=0.6, label=label)
        ax.set_title(name, fontsize=8)
        ax.tick_params(labelsize=6)
        ax.grid(True, alpha=0.3)

    # Blank out any unused cells in the last row.
    for j in range(len(names), nrows * ncols):
        axes[j // ncols][j % ncols].axis("off")

    # One shared file legend for the whole figure.
    handles, legend_labels = axes[0][0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, legend_labels, loc="lower center",
                   ncol=min(len(legend_labels), 4), fontsize=7)

    fig.suptitle(f"{event.upper()} — time series ({len(paths)} file(s))",
                 fontsize=12)
    fig.supxlabel("elapsed time (s)", fontsize=9)
    fig.tight_layout(rect=[0, 0.05, 1, 0.97])

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{event}_timeseries.png")
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print(f"  [plot] saved {out_path}")


def resolve_csv_paths(argv):
    """Turn CLI args into a list of CSV paths. Supports explicit filenames
    and/or --dir <folder> (all *.csv in that folder, non-recursive)."""

    paths = []
    i = 0
    while i < len(argv):
        if argv[i] == "--dir":
            folder = argv[i + 1]
            found = sorted(glob.glob(os.path.join(folder, "*.csv")))
            if not found:
                print(f"  [!] No CSVs found in '{folder}'")
            paths.extend(found)
            i += 2
        else:
            paths.append(argv[i])
            i += 1
    return paths


def peek_signals(csv_path):
    """List the signals in a csv WITHOUT a full parse, with n/min/max.

    Reads only the _field and _value columns and groups — no pivot, no union
    time grid, no pickle cache written. Measured on the 234 MB
    endurance_full.csv: 1.0s, against 3.8s for a cold full parse. Reading
    _value alongside _field costs almost nothing (1.1x over names alone),
    which is why the range is included: it makes this enough to spot a dead
    or railed channel before committing to a parse.

    Returns {signal_name: {n, min, max}}, or None if the file isn't in the
    expected long format.
    """
    import pandas as pd
    try:
        df = pd.read_csv(csv_path, usecols=["_field", "_value"], low_memory=False)
    except (ValueError, KeyError):
        return None
    grouped = df.groupby("_field")["_value"].agg(["count", "min", "max"])
    return {name: {"n": int(r["count"]), "min": float(r["min"]), "max": float(r["max"])}
            for name, r in grouped.iterrows()}


def print_signal_listing(csv_paths):
    """--list-signals: what is in these files, cheaply."""
    for path in csv_paths:
        print(f"\n{os.path.basename(path)}")
        found = peek_signals(path)
        if found is None:
            print("  [!] not in the expected long format (_field/_value columns)")
            continue
        unknown = sorted(set(found) - set(PREFERRED_SIGNAL_ORDER))
        order = [n for n in PREFERRED_SIGNAL_ORDER if n in found] + unknown
        print(f"  {'signal':32s} {'n':>9s} {'min':>12s} {'max':>12s}")
        print("  " + "-" * 68)
        for name in order:
            s = found[name]
            flag = "  <- NEW" if name in unknown else ""
            print(f"  {name:32s} {s['n']:9d} {s['min']:12.4f} {s['max']:12.4f}{flag}")
        if unknown:
            print(f"  [i] {len(unknown)} signal(s) not in PREFERRED_SIGNAL_ORDER "
                  f"(reported anyway — the list is display order, not a filter)")


def choose_signals_interactively(signal_names):
    """Prompt for which signals to plot. Bare Enter keeps every signal, so
    the prompt is a filter you reach for rather than a gate you pass through.

    Only called when stdin is a TTY — a scripted or piped run must never
    block waiting for input, so main() falls back to all signals instead.
    Accepts 'all', numbers, comma lists and ranges: '1,4,7' or '2-6,9'.
    """
    print("\nSignals available to plot:")
    for i, name in enumerate(signal_names, 1):
        print(f"  {i:3d}. {name}")
    print("\nWhich to plot? Enter numbers (e.g. 1,4,7 or 2-6,9), 'all', "
          "or press Enter for all.")
    try:
        raw = input("> ").strip()
    except EOFError:
        return signal_names
    if not raw or raw.lower() == "all":
        return signal_names

    chosen = []
    for part in raw.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            lo, _, hi = part.partition("-")
            try:
                for k in range(int(lo), int(hi) + 1):
                    if 1 <= k <= len(signal_names):
                        chosen.append(signal_names[k - 1])
            except ValueError:
                print(f"  [!] ignoring '{part}' — not a range")
        else:
            try:
                k = int(part)
                if 1 <= k <= len(signal_names):
                    chosen.append(signal_names[k - 1])
                else:
                    print(f"  [!] ignoring '{part}' — out of range")
            except ValueError:
                print(f"  [!] ignoring '{part}' — not a number")

    seen, unique = set(), []
    for name in chosen:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    if not unique:
        print("  [!] nothing valid selected — plotting all signals.")
        return signal_names
    print(f"  plotting {len(unique)} signal(s): {', '.join(unique)}")
    return unique


def parse_flags(argv):
    """Pull the flags out of argv, returning
    (remaining_args, do_plot, plot_dir, list_only, chosen_signals).
    Everything left is passed on to resolve_csv_paths as files / --dir args."""
    do_plot = False
    plot_dir = "plots"
    list_only = False
    chosen = None
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == "--plot":
            do_plot = True
            i += 1
        elif argv[i] == "--plot-dir":
            plot_dir = argv[i + 1]
            i += 2
        elif argv[i] == "--list-signals":
            list_only = True
            i += 1
        elif argv[i] == "--signals":
            chosen = [s for s in argv[i + 1].replace(" ", "").split(",") if s]
            i += 2
        else:
            rest.append(argv[i])
            i += 1
    return rest, do_plot, plot_dir, list_only, chosen


def main():
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  uv run batch_signal_stats.py <file1>.csv [<file2>.csv ...]\n"
            "  uv run batch_signal_stats.py --dir <folder>\n"
            "  add --plot [--plot-dir <folder>] to save per-event time-series PNGs\n"
            "  --list-signals            list signals per file (fast, no full parse) and exit\n"
            "  --signals A,B,C           plot only these signals (stats always cover all)"
        )
        sys.exit(1)

    args, do_plot, plot_dir, list_only, chosen_signals = parse_flags(sys.argv[1:])
    csv_paths = resolve_csv_paths(args)

    if not csv_paths:
        print("No CSV files to process.")
        sys.exit(1)

    # --list-signals is a cheap peek: no parse, no cache written, then exit.
    if list_only:
        print_signal_listing(csv_paths)
        return

    grouped = group_by_event(csv_paths)

    all_signals_list = []  # collected across every event, for the final combined table

    for event, paths in grouped.items():
        if not paths:
            continue

        print(f"\n{'#' * 60}")
        print(f"# EVENT: {event.upper()}  ({len(paths)} file(s))")
        print(f"{'#' * 60}")
        for p in paths:
            print(f"  - {p}")

        signals_list = []
        for csv_path in paths:
            try:
                signals_list.append(parse_influx(csv_path))
            except Exception as e:
                print(f"  [!] Failed to parse '{csv_path}': {e}")

        if not signals_list:
            print("  [!] No files parsed successfully for this event, skipping.")
            continue

        all_signals_list.extend(signals_list)

        print()
        # Report whatever this event's files actually contain, not a fixed
        # list — see discover_signals().
        signal_names, unknown = discover_signals(signals_list)
        if unknown:
            print(f"  [i] {len(unknown)} signal(s) not in PREFERRED_SIGNAL_ORDER, "
                  f"reported at the end of the table: {', '.join(unknown)}")
            print()
        results = compute_pooled_stats(signals_list, signal_names)
        print_stats(results)

        if do_plot:
            # Stats above always cover every signal. Plotting is selectable,
            # because a subplot grid stops being readable well before the
            # signal list does.
            if chosen_signals is not None:
                missing = [n for n in chosen_signals if n not in signal_names]
                if missing:
                    print(f"  [!] not present in {event} files, skipping: {', '.join(missing)}")
                plot_names = [n for n in chosen_signals if n in signal_names]
                if not plot_names:
                    print(f"  [!] none of --signals present for {event}, plotting all instead.")
                    plot_names = signal_names
            elif sys.stdin.isatty():
                plot_names = choose_signals_interactively(signal_names)
            else:
                plot_names = signal_names
            plot_event_timeseries(
                event, signals_list, paths, plot_names, plot_dir
            )

    if all_signals_list:
        print(f"\n{'#' * 60}")
        print(f"# ALL EVENTS COMBINED  ({len(all_signals_list)} file(s))")
        print(f"{'#' * 60}\n")
        all_names, _ = discover_signals(all_signals_list)
        results = compute_pooled_stats(all_signals_list, all_names)
        print_stats(results)


if __name__ == "__main__":
    main()
