# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
spectral_analysis.py — where the suspension's energy actually lives, and
what the modes are.

WHY. Every cutoff decision in this project is a decision about which
frequencies to keep, and until now nothing here had looked at the frequency
domain at all. The README records "a real 6-8 Hz mode carrying 5.88mm",
which if true is decisive: both 5 and 8 Hz sit ON that resonance, the worst
possible place, because the reported peak then becomes hypersensitive to the
exact cutoff. This tool checks that claim rather than inheriting it.

MUST RUN ON A UNIFORM GRID. A Fourier transform of non-uniformly sampled
data is not defined, and the InfluxDB union grid is emphatically not
uniform — median spacing 0.39ms with individual gaps from 0.019 to 19.3ms.
Worse, it is built by zero-order hold, and a staircase's step edges carry
broadband energy no sensor measured, which would appear in a PSD as
structure that does not exist. Everything here resamples from the RAW
per-signal samples via case_common.uniform_resample_corners().

WHAT DISTINGUISHES A MODE FROM DRIVER INPUT. A PSD peak alone does not
identify anything — 1-2 Hz content is mostly the driver steering, not a
resonance. The discriminator is HOW THE CORNERS MOVE RELATIVE TO EACH OTHER,
which is why this works in the modal basis (case4's exact heave/roll/pitch/
warp decomposition) and computes coherence between corner pairs:

    heave    all four corners in phase        sprung-mass bounce
    roll     left pair against right pair     body roll
    pitch    front pair against rear pair     body pitch
    warp     diagonals opposed                chassis torsion
    per-corner peak with LOW inter-corner coherence
                                              wheel hop (unsprung, local)

Typical FSAE figures for orientation, not as targets to match: sprung-mass
ride 2.5-4 Hz, wheel hop 12-15 Hz. A peak at 6-8 Hz sits awkwardly between
them, which is exactly why it needs identifying rather than assuming.

WHAT THIS DOES NOT DO. It cannot tell you a peak is mechanical rather than
track input — a repeating kerb or surface texture at constant speed shows up
as a peak too. Cross-file consistency is the check: a real vehicle mode
appears in every file at the same frequency; a track feature does not.

Run it:
    uv run spectral_analysis.py --dir comp2026_data
    uv run spectral_analysis.py --dir comp2026_data --band 4 12
"""

import os
import sys
import glob
import argparse

import numpy as np
import plotly.graph_objects as go
from scipy.signal import welch, coherence, detrend

from parse_influx import parse_influx
from case_common import (
    uniform_resample_corners, UNIFORM_RATE_HZ, to_wheel_travel,
    CORNERS, CORNER_SIGNAL_NAMES, group_by_event, detect_event_type,
    find_step_glitches,
)

import case4_combined_roll_pitch as c4

PLOTS_ROOT = os.path.join("plots", "spectral_analysis")

# 8-second Welch segments: 0.125 Hz resolution, and enough averaging on
# even the shortest file (72s) to suppress the noise floor.
SEGMENT_S = 8.0

# Below this is body motion and driver input, and it dominates the energy so
# completely that everything above it is invisible on a shared axis. The
# analysis band starts here.
BODY_MOTION_HZ = 1.0

# A mode has to be present in most files to be a property of the car rather
# than of one run or one piece of track.
MIN_FILES_FOR_MODE = 0.6

# ...and at the SAME frequency. Two files peaking at 1.4 and 21.9 Hz are not
# evidence of one mode, however prominent each peak is. +/-20% is generous
# for a structural resonance, which should repeat far tighter than that.
CLUSTER_TOL = 0.20

COLORS = {"heave": "#2a78d6", "roll": "#eb6834",
          "pitch": "#1baf7a", "warp": "#eda100"}


def load_modes(path):
    """Wheel travel per corner and the four modes, on a true 100 Hz grid."""
    signals = parse_influx(path, verbose=False)

    if not all(CORNER_SIGNAL_NAMES[c] in signals for c in CORNERS):
        return None

    t, raw = uniform_resample_corners(signals)

    # Glitches are step discontinuities — broadband in frequency, so they
    # would smear energy across the entire spectrum. Interpolate across
    # them rather than zeroing, which would itself be a step.
    mask, _ = find_step_glitches(raw, t)
    if mask.any():
        good = ~mask
        raw = {c: np.interp(t, t[good], v[good]) for c, v in raw.items()}

    wheel = to_wheel_travel(raw)

    modes = c4.decompose_modes(wheel["FL"], wheel["FR"], wheel["RL"], wheel["RR"])

    return {"path": path, "t": t, "corners": wheel, "modes": modes}


def psd(values):
    """Welch PSD, linearly detrended.

    Detrending matters more than it looks: an undetrended segment leaks its
    mean and slope into the lowest bins, and since body motion already
    dominates by orders of magnitude, that leakage can manufacture a
    shoulder that looks like a peak.
    """
    nperseg = int(SEGMENT_S * UNIFORM_RATE_HZ)
    nperseg = min(nperseg, len(values))
    f, p = welch(detrend(np.asarray(values, dtype=float), type="linear"),
                 fs=UNIFORM_RATE_HZ, nperseg=nperseg)
    return f, p


def find_peaks_in_band(f, p, lo, hi, top=3):
    """Local maxima, strongest first, within a band.

    Local maxima on a monotonically falling spectrum are mostly ripple, so
    each candidate must also stand PROMINENTLY above the local background —
    estimated as the median power in a window around it. Without that test
    this reports the roll-off shoulder as a mode, which is what an earlier
    quick look here did.
    """
    band = (f >= lo) & (f <= hi)
    fb, pb = f[band], p[band]

    if len(fb) < 5:
        return []

    out = []
    for i in range(1, len(pb) - 1):
        if not (pb[i] > pb[i - 1] and pb[i] > pb[i + 1]):
            continue

        # Local background: median over +/-1 Hz, excluding the peak itself.
        near = np.abs(fb - fb[i]) <= 1.0
        near[i] = False
        if not near.any():
            continue

        prominence = pb[i] / np.median(pb[near])
        out.append((fb[i], pb[i], prominence))

    out.sort(key=lambda r: -r[2])
    return out[:top]


def report_modes(rows, band):
    """Per-file peak table for each mode, plus a cross-file verdict."""
    lo, hi = band

    print(f"\n{'=' * 78}")
    print(f"MODAL PSD PEAKS, {lo}-{hi} Hz "
          f"(prominence = peak / local median; >2 is worth looking at)")
    print(f"{'=' * 78}")

    found = {m: [] for m in COLORS}

    for mode in COLORS:
        print(f"\n  {mode.upper()}")
        print(f"    {'file':<26}{'peak (Hz)':>12}{'prominence':>13}")

        for r in rows:
            f, p = psd(r["modes"][mode])
            peaks = find_peaks_in_band(f, p, lo, hi, top=1)

            if not peaks:
                print(f"    {os.path.basename(r['path'])[:25]:<26}{'—':>12}")
                continue

            hz, _, prom = peaks[0]
            found[mode].append((os.path.basename(r["path"]), hz, prom))
            print(f"    {os.path.basename(r['path'])[:25]:<26}{hz:>12.2f}{prom:>13.2f}")

    print(f"\n{'=' * 78}")
    print("VERDICT — a vehicle mode appears in most files at a consistent")
    print("frequency. A peak in one or two files is a run or a piece of track.")
    print(f"{'=' * 78}")

    for mode, hits in found.items():
        strong = [(n, hz, pr) for n, hz, pr in hits if pr >= 2.0]

        if len(strong) < MIN_FILES_FOR_MODE * len(rows):
            print(f"  {mode:<8} NO MODE — only {len(strong)}/{len(rows)} files "
                  f"have a prominent peak at all")
            continue

        freqs = np.array(sorted(hz for _, hz, _ in strong))

        # CLUSTERING IS THE TEST, not the count. Counting prominent peaks
        # and taking their median reports a "mode" from frequencies
        # scattered across the whole band — which is exactly what an
        # earlier version of this did, calling 1.12-21.88 Hz a 1.50 Hz
        # mode. A resonance is a property of the structure, so it must land
        # at the SAME frequency in file after file.
        #
        # Largest cluster within +/-CLUSTER_TOL of its own centre.
        best_members, best_centre = [], None
        for centre in freqs:
            members = freqs[np.abs(freqs - centre) <= CLUSTER_TOL * centre]
            if len(members) > len(best_members):
                best_members, best_centre = members, centre

        if len(best_members) < MIN_FILES_FOR_MODE * len(rows):
            print(f"  {mode:<8} NO MODE — {len(strong)}/{len(rows)} files have a "
                  f"prominent peak, but they do NOT cluster")
            print(f"           (peaks at {', '.join(f'{h:.1f}' for h in freqs)} Hz; "
                  f"largest cluster is only {len(best_members)} file(s))")
            continue

        print(f"  {mode:<8} {np.median(best_members):.2f} Hz "
              f"({len(best_members)}/{len(rows)} files clustered within "
              f"{CLUSTER_TOL:.0%}, spread "
              f"{best_members.min():.2f}-{best_members.max():.2f})")


def report_coherence(rows):
    """Inter-corner coherence, which is what separates a body mode from
    wheel hop.

    A body mode moves corners together (high coherence). Wheel hop is a
    local unsprung resonance — each corner does its own thing, so coherence
    collapses even where the per-corner PSDs both show a peak.
    """
    print(f"\n{'=' * 78}")
    print("INTER-CORNER COHERENCE (0-1). High = corners moving together, a")
    print("body mode. Low at a frequency where both corners peak = wheel hop.")
    print(f"{'=' * 78}")
    print(f"    {'file':<24}{'band':>10}{'FL-FR':>9}{'RL-RR':>9}{'FL-RL':>9}{'FR-RR':>9}")

    pairs = [("FL", "FR"), ("RL", "RR"), ("FL", "RL"), ("FR", "RR")]
    bands = [(1, 4), (4, 9), (9, 16)]
    totals = {}

    nperseg = int(SEGMENT_S * UNIFORM_RATE_HZ)

    for r in rows:
        for lo, hi in bands:
            cells = []
            for a, b in pairs:
                f, cxy = coherence(
                    detrend(r["corners"][a], type="linear"),
                    detrend(r["corners"][b], type="linear"),
                    fs=UNIFORM_RATE_HZ,
                    nperseg=min(nperseg, len(r["corners"][a])),
                )
                sel = (f >= lo) & (f <= hi)
                cells.append(float(np.mean(cxy[sel])) if sel.any() else float("nan"))

            label = os.path.basename(r["path"])[:23] if (lo, hi) == bands[0] else ""
            print(f"    {label:<24}{f'{lo}-{hi} Hz':>10}"
                  + "".join(f"{c:>9.2f}" for c in cells))
            totals.setdefault((lo, hi), []).append(cells)

    print(f"\n    {'MEAN ACROSS FILES':<24}{'':>10}"
          + "".join(f"{p[0]}-{p[1]:<6}" for p in pairs))
    for (lo, hi), rowset in totals.items():
        means = np.nanmean(np.array(rowset), axis=0)
        print(f"    {'':<24}{f'{lo}-{hi} Hz':>10}"
              + "".join(f"{m:>9.2f}" for m in means))

    print("\n    Coherence below ~0.5 means the corners are NOT moving together,")
    print("    so whatever is there is local to each corner rather than a body mode.")


def build_psd_plot(rows, band, output_path):
    """PSD per mode, one trace per file, log-y."""
    lo, hi = band

    fig = go.Figure()

    for r in rows:
        for mode, color in COLORS.items():
            f, p = psd(r["modes"][mode])
            sel = (f >= lo) & (f <= hi)
            fig.add_trace(go.Scatter(
                x=f[sel], y=p[sel], mode="lines",
                name=f"{os.path.basename(r['path'])[:16]} {mode}",
                legendgroup=mode,
                line=dict(color=color, width=1.2), opacity=0.75,
            ))

    fig.update_layout(
        title="Modal PSD — click legend to isolate a mode",
        xaxis_title="frequency (Hz)",
        yaxis_title="PSD (mm²/Hz)",
        yaxis_type="log",
        template="plotly_white",
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(output_path, include_plotlyjs="cdn")


def main():
    parser = argparse.ArgumentParser(
        description="Where the suspension's energy lives, and what the modes are."
    )
    parser.add_argument("--dir", default="comp2026_data")
    parser.add_argument("--band", nargs=2, type=float, default=[BODY_MOTION_HZ, 25.0],
                        metavar=("LO", "HI"),
                        help="Analysis band in Hz (default 1 25). Below 1 Hz is "
                             "body motion and driver input, which dominates.")
    args = parser.parse_args()

    paths = sorted(glob.glob(os.path.join(args.dir, "*.csv")))
    if not paths:
        sys.exit(f"No CSVs found in {args.dir!r}.")

    print(f"Loading and resampling to {UNIFORM_RATE_HZ:.0f} Hz...")
    rows = [r for p in paths if (r := load_modes(p)) is not None]

    if not rows:
        sys.exit("No files had all four shock pots.")

    print(f"  {len(rows)} files")

    report_modes(rows, args.band)
    report_coherence(rows)

    out = os.path.join(PLOTS_ROOT, "modal_psd.html")
    build_psd_plot(rows, args.band, out)
    print(f"\nPlot: {out}\n")


if __name__ == "__main__":
    main()
