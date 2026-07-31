# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "matplotlib", "plotly"]
# ///
"""
Filter Comparison Validation Tool

Purpose:
    Compare different low-pass filter cutoff frequencies on telemetry data.

Usage example:

    uv run filter_compare.py comp2026_data/endurance_full.csv --freqs 3 4 5

Multiple files:

    uv run filter_compare.py comp2026_data/*.csv --freqs 2 3 4 5

Accel / brake (see --zoom-on-peak note below):

    uv run filter_compare.py comp2026_data/accel_*.csv \
        comp2026_data/braketest*.csv --freqs 2 3 4 5 8 10 --zoom-on-peak


Signals compared:

    Lateral G, Longitudinal G, Combined G   (from VCPDU_lat / VCPDU_lon)
    Roll, Pitch                             (from the 4 shock pots)
    Vehicle speed                           (VCFRONT_vehicleSpeed)
    Front / rear brake pressure             (VC*_brakePressure)

    Anything the analysis scripts use to make a decision gets a cutoff
    validated here, not just the signals that end up as headline numbers.
    Vehicle speed is the case in point: no case script filters it, but
    case_common.find_static_window thresholds it RAW at 0.5 m/s to pick the
    stopped-car window that every shock pot is baselined against, so speed
    noise around that threshold can silently corrupt a whole file's
    baseline. Brake pressures are not consumed yet — included so a cutoff
    exists before anything starts segmenting brake events with them.

    Signals absent from a given file are skipped with a warning.

    Roll and pitch are included because those are what case2_max_roll.py,
    case3_max_pitch.py and case4_combined_roll_pitch.py actually report on
    — picking a cutoff by looking only at the G traces leaves the cutoff
    for the shock-pot-derived signals unvalidated. Same definitions those
    cases use:

        roll_mm  = avg(FR - FL, RR - RL)
        pitch_mm = avg(FL, FR) - avg(RL, RR)

    Both are plotted centred on their own median. A constant offset has no
    effect on filter behaviour, so no static baselining is done here — that
    matters for reporting absolute angles (which the case scripts do), not
    for choosing a cutoff.


SOURCE SAMPLE RATES (from the firmware repo — these bound which cutoffs
mean anything at all):

    Shock pots      100 Hz   (shockpot.c, periodic100Hz_CLK)   Nyquist 50 Hz
    IMU lat/lon     100 Hz   (imu.c, periodic100Hz_CLK)        Nyquist 50 Hz
    Steering angle   10 Hz   (steeringAngle.c, periodic10Hz)   Nyquist  5 Hz

    So 2-10 Hz cutoffs are comfortably valid for the shock pots and the
    accelerometers, but at or past Nyquist for steering angle.

    This tool RESAMPLES to a true 100 Hz grid before filtering, so 100 Hz
    is the fs every filter here is designed against. The union-grid density
    is still printed alongside for context, but it is NOT a sample rate —
    it is how often some signal happened to update, it is built by
    zero-order hold, and designing a filter against it is what this used to
    do wrongly.

    The IMU also applies its own low-pass in firmware (imu.c:47,
    IMU_LPF_CUTOFF_HZ = 100.0 with IMU_LPF_DT_S = 0.01). A 100 Hz cutoff at
    a 100 Hz sample rate is above Nyquist, so that filter is effectively a
    pass-through and the offline filtering here is doing all the real work.


PEAK ATTENUATION TABLE:

    Alongside the plots, a table is printed showing how much of each
    signal's peak magnitude survives each cutoff. This is the numerical
    version of the same question the plots answer by eye — if the peak
    barely moves between 2 Hz and 10 Hz, the cutoff choice does not matter
    for that signal; if it moves a lot, it matters and the plots are worth
    studying carefully.


ZOOM WINDOW SELECTION:

    By default the zoom window is placed where the signal is MOST ACTIVE —
    the `--zoom-duration` window with the highest standard deviation of the
    raw signal. No flag needed; it adapts per signal, so roll lands on a
    corner and brake pressure lands on a braking pulse.

    This replaced a fixed ZOOM_START of 600 s (falling back to the file
    midpoint), which picked a moment for reasons unrelated to whether
    anything was happening at it. It routinely landed on a stationary car:
    the skidpad roll zoom sat at 49-59 s with the car parked until 55 s, so
    six of the ten seconds were flat line. Flat data cannot discriminate
    between cutoffs — every cutoff reproduces a constant perfectly.

    --zoom-on-peak centres on the signal's single largest sample instead.
    Now rarely needed, and NOT recommended as a default: a peak is one
    sample and can be an artefact (the IMU 2-sample spikes and the
    shock-pot step glitches both win a peak search), whereas variance over
    a whole window cannot be dominated by two samples.

    --zoom-at <seconds> pins the window manually.


Outputs:

    Each signal produces THREE views, at both full-file and zoom extents.
    See the PLOTTING section for why one overlay was not enough — briefly,
    high cutoffs sit almost on top of the raw trace and hide everything
    beneath them, which gets worse the more frequencies you sweep.

    filter_compare_results/
        filename/
            roll_zoom_overlay.png     all cutoffs on one axis
            roll_zoom_panels.png      one panel per cutoff, raw behind each
            roll_zoom_residual.png    raw - filtered: what each cutoff DISCARDS
            ... same three for _full, and for every other signal

    WHICH VIEW TO USE. `_panels` is the primary view and `_residual` is
    what actually settles a borderline call — coherent structure in the
    residual means the cutoff is deleting real signal, not noise.

    Prefer the _zoom views for choosing a cutoff. At full-file extent
    (endurance_full is 869 s) every cutoff collapses into the same solid
    smear and the views are useful only as context.

"""


import argparse
import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import butter, filtfilt

from parse_influx import parse_influx
from case_common import uniform_resample, UNIFORM_RATE_HZ, signal_rate_hz



# ============================================================
# SETTINGS
# ============================================================

G = 9.80665

FILTER_ORDER = 4

OUTPUT_DIR = Path("filter_compare_results")


# Same zoom behavior as previous script.
#
# ZOOM_DURATION was 20s, which made the small-multiple panels too cramped to
# judge — seven panels across a 20s window leaves each cutoff a few hundred
# pixels of trace. 10s doubles the horizontal detail without losing the
# manoeuvre, since the events being judged (a corner entry, a braking pulse)
# are 0.3-3s. Override with --zoom-duration when you want the wider view.
ZOOM_START = 600
ZOOM_DURATION = 10


# The four shock pots, for the roll / pitch traces. Same signal names the
# case*_*.py scripts use.
SHOCKPOT_SIGNALS = {
    "FL": "VCFRONT_shockpotdispFL",
    "FR": "VCFRONT_shockpotdispFR",
    "RL": "VCREAR_shockpotdispRL",
    "RR": "VCREAR_shockpotdispRR",
}


# Other signals the analysis scripts consume (or are likely to), plotted
# straight through. Anything used to make a decision deserves a validated
# cutoff, not just the signals that get reported as headline numbers.
#
# Vehicle speed matters here even though no case script filters it: it is
# used RAW by case_common.find_static_window, thresholded at 0.5 m/s, to
# choose the stopped-car window that every shock pot gets baselined
# against. Speed noise around that threshold can let a not-actually-
# stationary stretch qualify as "stopped", which quietly corrupts the
# baseline for the whole file.
#
# Brake pressures are not consumed by any case script yet — included so a
# cutoff exists before one starts using them for brake-event segmentation.
#
#   (signal name, plot title, y label, output file stem)
EXTRA_SIGNALS = [
    (
        "VCFRONT_vehicleSpeed",
        "Vehicle Speed",
        "Speed (m/s)",
        "vehicle_speed"
    ),
    (
        "VCFRONT_brakePressure",
        "Front Brake Pressure",
        "Pressure (PSI)",
        "brake_pressure_front"
    ),
    (
        "VCREAR_brakePressure",
        "Rear Brake Pressure",
        "Pressure (PSI)",
        "brake_pressure_rear"
    ),
    # UNUSABLE SIGNAL — plotted for visibility only. DO NOT use it for
    # segmentation or reporting in any case script.
    #
    # Two separate problems, both traced to firmware
    # (firmware/components/vc/front/src/steeringAngle.c):
    #
    # 1. MISSING ZERO CALIBRATION. The interpolation map is +-0.78 V ->
    #    -+90 deg, i.e. -115.3846 deg/V, applied to
    #    (voltage - steeringCalibration_data.zero). That zero is only ever
    #    written when SWS_requestCalibSteerAngle is commanded (line 97). It
    #    is evidently still 0 V, so with the sensor resting at ~1.5 V every
    #    reading carries an offset of -115.3846 * 1.5 = -173.077 deg —
    #    exactly the -173.0 seen in all 11 comp2026_data files. This is NOT
    #    a DBC decode rail and NOT an electrical fault: lines 108-111 set
    #    angle = 0.0f when faulted, so a faulted sensor would read 0 deg,
    #    and the implied voltages (0.589-1.499 V) sit comfortably inside the
    #    0.25/2.75 V fault window.
    #
    # 2. ONLY ONE STEERING DIRECTION REGISTERS. Even after removing that
    #    offset the signal is one-sided: voltage only ever moves DOWN from
    #    its 1.4993 V rest, where it sits for 73% of a file, across just 69
    #    distinct values. The pot appears mechanically mis-clocked, so
    #    re-zeroing recovers the offset but not the missing half of travel.
    #
    # case1_max_gs.py already avoids the absolute value for this reason and
    # used only its rate of change (that gating was later abandoned). The
    # delta is NOT a safe fallback either: while the signal sits at rest its
    # derivative is identically zero, which any "is the driver holding a
    # steady line?" test would read as steady when the sensor is simply
    # flat-lined.
    #
    # Also note this module is periodic10Hz_CLK — 10 Hz, so Nyquist is
    # 5 Hz. Cutoffs of 5 Hz and above are meaningless for this signal even
    # if it were healthy.
    (
        "VCFRONT_steeringAngle",
        "Steering Angle (BROKEN SENSOR — see comment)",
        "Steering angle (deg) — UNUSABLE",
        "steering_angle_BROKEN"
    ),
]


# filtfilt pads at the array boundaries, so a file that ends mid-event
# overshoots there. Peak stats ignore this much of each end. Confirmed
# real: accel_corinne1's filtered pitch peaked at 17.36mm against a raw
# peak of 16.33mm (106%), located at sample 74944 of 75545 — the file
# simply stops while pitch is still at 16.19mm. Interior peak was 13.31mm.
EDGE_EXCLUDE_FRACTION = 0.02



# ============================================================
# FILTERING
# ============================================================

def butter_lowpass_filter(data, cutoff, fs, order=4):

    nyquist = 0.5 * fs

    normal_cutoff = cutoff / nyquist

    b, a = butter(
        order,
        normal_cutoff,
        btype="low"
    )

    return filtfilt(
        b,
        a,
        data
    )



# ============================================================
# SAMPLE RATE
# ============================================================

def estimate_sample_rate(time):

    dt = (
        np.diff(
            time.astype("int64")
        )
        /
        1e9
    )

    return 1 / np.median(dt)



# ============================================================
# GAP FILLING
# ============================================================

def fill_nans(values):

    """
    Linearly interpolate NaN gaps — filtfilt cannot handle NaNs.

    The InfluxDB union time grid leaves a NaN wherever a given signal was
    not updated, so the shock pots are full of them. Interpolating on
    sample position (rather than dropping rows) matches what
    case_common.fill_gaps does, so the traces here line up with what the
    case scripts actually filter.
    """

    values = np.asarray(
        values,
        dtype=float
    )


    finite = np.isfinite(values)


    if finite.all() or not finite.any():

        return values


    positions = np.arange(
        len(values)
    )


    return np.interp(
        positions,
        positions[finite],
        values[finite]
    )



# ============================================================
# PLOTTING
# ============================================================
#
# THREE VIEWS PER SIGNAL, not one overlay. The single-overlay layout this
# replaced hid the data it was supposed to show, and the cause is
# structural rather than a bad colour choice:
#
#   The higher the cutoff, the closer the filtered trace is to raw.
#
# So the 15 and 20 Hz traces land almost exactly on top of the raw trace
# and — being drawn last — paint over both the raw trace and every lower
# cutoff. Adding more frequencies to the sweep makes it strictly worse, so
# no palette or alpha tweak fixes it. The views are:
#
#   _overlay   all cutoffs on one axis. Still the best view for judging
#              WHERE traces separate, but z-order is now reversed (highest
#              cutoff drawn first) so the lowest cutoff — the one most
#              different from raw — ends on top instead of buried.
#
#   _panels    small multiples, one panel per cutoff, shared y-axis. Raw is
#              redrawn pale behind each one, so it can never be occluded
#              because nothing competes with it. This is the primary view.
#
#   _residual  raw minus filtered, one panel per cutoff. The most
#              decision-relevant view: it shows exactly WHAT IS BEING
#              DISCARDED at each cutoff. A formless residual means the
#              cutoff is safe; a visibly coherent oscillation means real
#              signal is being deleted. Note spectral_analysis.py found no
#              consistent resonance in any mode, so structure here is road
#              and sensor content rather than a vehicle mode.
#
# COLOUR: distinct hues, not shades of one.
#
# Cutoff frequency is strictly an ordered magnitude, which argues for a
# sequential single-hue ramp — and that is what this used first. In
# practice it was hard to read: seven steps of the same blue are not
# separable at a glance on a busy time series, and telling "the third blue"
# from "the fourth blue" is exactly what you have to do to use the overlay.
# Distinguishability wins here, so these are the validated categorical
# hues in fixed slot order, assigned by ASCENDING cutoff.
#
# Validated at 7 slots on the light surface (#fcfcfb): worst adjacent CVD
# ΔE 9.1 (protan), worst adjacent normal-vision ΔE 19.6 — both clear.
# Aqua, yellow and magenta sit below 3:1 contrast, so the relief rule
# applies: every view ships visible labels (panel titles, or the overlay
# legend), never colour alone.
CATEGORICAL = [
    "#2a78d6",   # 1 blue
    "#eb6834",   # 2 orange
    "#1baf7a",   # 3 aqua
    "#eda100",   # 4 yellow
    "#e87ba4",   # 5 magenta
    "#008300",   # 6 green
    "#4a3aa7",   # 7 violet
    "#e34948",   # 8 red
]

RAW_COLOR = "#a8a7a1"        # neutral grey — reference, never competes
RAW_LINEWIDTH = 2.6
FILTERED_LINEWIDTH = 1.4
GRID_COLOR = "#e4e3df"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"

# 3 columns, not 4. With 7 cutoffs this gives a 3/3/1 grid of noticeably
# larger panels — 4 columns squeezed each panel to 3.6in, too small to see
# what a cutoff was doing to a transient.
PANEL_COLUMNS = 3
PANEL_WIDTH_IN = 5.2
PANEL_HEIGHT_IN = 3.4

# 220 dpi, not 150. The review pages scale these down to fit the column,
# and the lightbox then blows them back up to inspect a transient — 150 dpi
# went soft under that second step. Panels are also physically small
# (3.6 x 2.4 in), so their tick labels were the first thing to blur.
PLOT_DPI = 220


def cutoff_colors(cutoffs):

    """
    Map cutoffs to categorical slots in fixed order, lowest cutoff first.

    Fixed order matters: a cutoff keeps the same colour across every signal
    and every file, so "the orange one" means 3 Hz everywhere. Slots are
    never cycled — past 8 cutoffs the palette runs out, which is the
    signal to sweep fewer at once rather than to reuse a hue.
    """

    ordered = sorted(cutoffs)


    if len(ordered) > len(CATEGORICAL):

        raise ValueError(
            f"{len(ordered)} cutoffs exceeds the {len(CATEGORICAL)} "
            f"categorical slots. Sweep fewer frequencies at a time — "
            f"cycling hues would make two cutoffs share a colour."
        )


    return {
        cutoff: CATEGORICAL[i]
        for i, cutoff in enumerate(ordered)
    }


# Target point count per trace in the interactive overlay. Data now arrives
# on the true 100 Hz grid, so a 10s window is ~1000 samples per trace and
# this ceiling rarely binds — it is kept as a guard for long --zoom-duration
# values, where 8 traces could otherwise ship a lot of points into the
# browser for detail below one screen pixel.
INTERACTIVE_MAX_POINTS = 3000


def resample_all(signals, csv_file):
    """Every signal this tool plots, on ONE shared uniform grid.

    A shared grid is required, not a convenience: roll and pitch are
    DIFFERENCES between corners, so the corners must be sampled at the same
    instants or the difference silently mixes in a time offset. Everything
    downstream also indexes a single `time_s`.

    Signals slower than the grid (front brake pressure at 10 Hz) are
    linearly interpolated up onto it. That adds no information and no
    artefact — but it also does not raise their Nyquist, which is why the
    caller warns separately about cutoffs above it.
    """
    wanted = (
        ["VCPDU_lat", "VCPDU_lon"]
        + list(SHOCKPOT_SIGNALS.values())
        + [name for name, _, _, _ in EXTRA_SIGNALS]
    )

    present = [n for n in wanted if n in signals]

    per_signal = {
        name: uniform_resample(signals[name], target_hz=UNIFORM_RATE_HZ, name=name)
        for name in present
    }

    per_signal = {k: v for k, v in per_signal.items() if len(v[0]) > 1}

    # Overlap of all signals — they do not start and end together.
    start = max(t[0] for t, _ in per_signal.values())
    end = min(t[-1] for t, _ in per_signal.values())

    step = 1.0 / UNIFORM_RATE_HZ
    grid = np.arange(start, end + step / 2.0, step)

    print(
        f"  Resampled to {UNIFORM_RATE_HZ:.0f} Hz: "
        f"{len(grid):,} samples over {grid[-1] - grid[0]:.1f}s "
        f"(union grid was non-uniform, zero-order held)"
    )

    return grid, {
        name: np.interp(grid, t, v)
        for name, (t, v) in per_signal.items()
    }


ACTIVITY_CANDIDATES = 400   # candidate window starts scanned per signal


def most_active_window_start(time, raw, duration, candidates=ACTIVITY_CANDIDATES):
    """Start time of the `duration`-second window with the most going on.

    "Most going on" is the highest standard deviation of the raw signal
    inside the window. That is the right criterion for choosing a cutoff:
    the whole question is what a filter does to signal CHANGE, and a window
    where nothing changes answers it for no cutoff at all.

    Scans `candidates` evenly-spaced starts rather than every sample —
    the union grid runs to a million samples per file, and window placement
    does not need sample precision.
    """
    time = np.asarray(time, dtype=float)

    values = np.asarray(raw, dtype=float)


    span = time[-1] - time[0]

    if span <= duration:
        return time[0]


    starts = np.linspace(time[0], time[-1] - duration, candidates)

    best_start = starts[0]

    best_score = -1.0


    for start in starts:

        lo = int(np.searchsorted(time, start, side="left"))
        hi = int(np.searchsorted(time, start + duration, side="right"))

        if hi - lo < 10:
            continue

        window = values[lo:hi]

        finite = window[np.isfinite(window)]

        if finite.size < 10:
            continue

        score = float(np.std(finite))

        if score > best_score:
            best_score = score
            best_start = start


    return best_start


def write_interactive_overlay(time_plot, raw_plot, filtered_plot, title,
                              ylabel, output_path):
    """Plotly version of the overlay, where each cutoff can be toggled from
    the legend.

    This exists because the PNG overlay cannot answer "what does it look
    like WITHOUT the 15 and 20 Hz traces" — and that is the question you
    actually ask once you've narrowed the choice to two or three
    candidates. Click a legend entry to hide it, double-click to isolate
    it. Box-zoom and pan come free.

    Decimated for display only (see INTERACTIVE_MAX_POINTS) — the filtering
    itself still happens at full grid density, so what you see is the real
    filtered signal, just not every redundant sample of it.
    """
    import plotly.graph_objects as go

    cutoffs = sorted(filtered_plot)

    colors = cutoff_colors(cutoffs)

    stride = max(1, len(time_plot) // INTERACTIVE_MAX_POINTS)

    # Rounded before serialising. Plotly writes every array as JSON text and
    # repeats the x array per trace, so full float64 repr costs ~2x the file
    # size for precision far below one screen pixel. 4dp on time is 0.1ms;
    # 4dp on value is well under any sensor's resolution.
    t = np.round(np.asarray(time_plot, dtype=float)[::stride], 4)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=t,
        y=np.round(np.asarray(raw_plot, dtype=float)[::stride], 4),
        name="Raw",
        mode="lines",
        line=dict(color=RAW_COLOR, width=2.6),
    ))


    for cutoff in cutoffs:

        fig.add_trace(go.Scatter(
            x=t,
            y=np.round(np.asarray(filtered_plot[cutoff], dtype=float)[::stride], 4),
            name=f"{cutoff} Hz",
            mode="lines",
            line=dict(color=colors[cutoff], width=1.6),
        ))


    fig.update_layout(
        title=dict(text=f"{title} — click legend to show/hide", font=dict(size=15)),
        xaxis_title="Time (s)",
        yaxis_title=ylabel,
        hovermode="x unified",
        template="plotly_white",
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers"),
        margin=dict(l=70, r=30, t=60, b=60),
    )

    fig.update_xaxes(showspikes=True, spikemode="across", spikethickness=1)


    # include_plotlyjs="directory" writes plotly.min.js once per output
    # folder and references it, instead of embedding ~3 MB in every file.
    # Matters at 99 charts. Keeps working offline, unlike "cdn".
    fig.write_html(
        str(output_path),
        include_plotlyjs="directory",
        full_html=True,
    )


def style_axis(ax, ylabel=None, xlabel=None):

    ax.grid(True, color=GRID_COLOR, linewidth=0.8)

    ax.set_axisbelow(True)


    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(GRID_COLOR)


    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)


    if ylabel:
        ax.set_ylabel(ylabel, color=TEXT_SECONDARY, fontsize=10)

    if xlabel:
        ax.set_xlabel(xlabel, color=TEXT_SECONDARY, fontsize=10)


def plot_filters(
    time,
    raw,
    filtered,
    title,
    ylabel,
    output_path,
    zoom=False,
    zoom_on_peak=False,
    zoom_at=None
):

    if zoom:

        if zoom_at is not None:

            half = ZOOM_DURATION / 2.0

            mask = (
                (time >= zoom_at - half)
                &
                (time <= zoom_at + half)
            )


            if not np.any(mask):

                print(
                    f"  [!] --zoom-at {zoom_at}s is outside this file "
                    f"(0-{time[-1]:.0f}s) — using midpoint."
                )

                midpoint = time[len(time)//2]

                mask = (
                    (time >= midpoint)
                    &
                    (time <= midpoint + ZOOM_DURATION)
                )


        elif zoom_on_peak:

            # Centre the window on this signal's own biggest moment, which
            # for accel/brake is the actual event rather than arbitrary
            # quiet track.
            peak_time = time[
                int(
                    np.nanargmax(
                        np.abs(raw)
                    )
                )
            ]

            half = ZOOM_DURATION / 2.0

            mask = (
                (time >= peak_time - half)
                &
                (time <= peak_time + half)
            )


        else:

            # MOST ACTIVE WINDOW, not a fixed clock time.
            #
            # This used to start at ZOOM_START (600s), falling back to the
            # file midpoint. Both pick a moment for reasons unrelated to
            # whether anything is HAPPENING at it, and they routinely landed
            # on a stationary car: the skidpad zoom sat at 49-59s with the
            # car parked until 55s, so six of the ten seconds were a flat
            # line. Flat data says nothing about a cutoff — every cutoff
            # reproduces a constant perfectly.
            #
            # Instead, score candidate windows by the standard deviation of
            # the RAW signal inside them and take the busiest. That is
            # exactly "where is this signal doing the most", so it adapts
            # per signal (a braking pulse for brake pressure, a corner for
            # roll) and can never select a stationary stretch, because a
            # stationary stretch has near-zero variance.
            #
            # Preferred over --zoom-on-peak as the default because a peak is
            # a single sample and can be a step glitch (see the README's
            # known data problems); variance over a window cannot be.
            start = most_active_window_start(time, raw, ZOOM_DURATION)

            mask = (
                (time >= start)
                &
                (time <= start + ZOOM_DURATION)
            )


        time_plot = time[mask]

        raw_plot = raw[mask]


        filtered_plot = {
            cutoff: data[mask]
            for cutoff, data in filtered.items()
        }


    else:

        time_plot = time

        raw_plot = raw

        filtered_plot = filtered



    raw_plot = fill_nans(raw_plot)

    cutoffs = sorted(filtered_plot)

    colors = cutoff_colors(cutoffs)


    # output_path arrives as ".../<name>_full.png" or ".../<name>_zoom.png";
    # the three views become siblings of it.
    base = Path(output_path)

    stem = base.with_suffix("").name


    def sibling(view):
        return base.parent / f"{stem}_{view}.png"


    # ── View 1: overlay ──────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(
        time_plot,
        raw_plot,
        color=RAW_COLOR,
        linewidth=RAW_LINEWIDTH,
        label="Raw",
        zorder=1
    )


    # Highest cutoff first, so the lowest cutoff ends up on top. Drawing in
    # ascending order is what buried the informative traces before.
    for depth, cutoff in enumerate(reversed(cutoffs)):

        ax.plot(
            time_plot,
            filtered_plot[cutoff],
            color=colors[cutoff],
            linewidth=FILTERED_LINEWIDTH,
            label=f"{cutoff} Hz",
            zorder=2 + depth
        )


    ax.set_title(title, color=TEXT_PRIMARY, fontsize=11)

    style_axis(ax, ylabel=ylabel, xlabel="Time (s)")

    ax.legend(
        loc="upper right",
        fontsize=8,
        framealpha=0.9,
        labelcolor=TEXT_SECONDARY
    )

    fig.tight_layout()

    fig.savefig(sibling("overlay"), dpi=PLOT_DPI, bbox_inches="tight")

    plt.close(fig)


    # ── View 1b: interactive overlay ─────────────────────────────────────
    # Same data, but with the cutoffs toggleable from the legend — the one
    # question the static overlay cannot answer.
    #
    # ZOOM EXTENT ONLY. At full-file extent every cutoff collapses into the
    # same smear, so an interactive version of it answers nothing while
    # doubling the number of charts on disk.
    if zoom:
        write_interactive_overlay(
            time_plot,
            raw_plot,
            filtered_plot,
            title,
            ylabel,
            base.parent / f"{stem}_overlay.html",
        )


    # ── View 2: small multiples ──────────────────────────────────────────
    # One cutoff per panel with raw redrawn behind it. Shared y-axis, so
    # panels are directly comparable.
    ncols = min(PANEL_COLUMNS, len(cutoffs))

    nrows = int(np.ceil(len(cutoffs) / ncols))


    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(PANEL_WIDTH_IN * ncols, PANEL_HEIGHT_IN * nrows),
        sharex=True,
        sharey=True,
        squeeze=False
    )


    for idx, cutoff in enumerate(cutoffs):

        ax = axes[idx // ncols][idx % ncols]


        ax.plot(
            time_plot,
            raw_plot,
            color=RAW_COLOR,
            linewidth=RAW_LINEWIDTH,
            zorder=1
        )

        ax.plot(
            time_plot,
            filtered_plot[cutoff],
            color=colors[cutoff],
            linewidth=FILTERED_LINEWIDTH,
            zorder=2
        )


        ax.set_title(
            f"{cutoff} Hz",
            color=TEXT_PRIMARY,
            fontsize=11
        )

        style_axis(ax)


    # Blank any unused cells in the grid.
    for idx in range(len(cutoffs), nrows * ncols):
        axes[idx // ncols][idx % ncols].axis("off")


    for row in range(nrows):
        axes[row][0].set_ylabel(ylabel, color=TEXT_SECONDARY, fontsize=10)

    for col in range(ncols):
        # The BOTTOM-MOST PANEL THAT ACTUALLY EXISTS in this column, not
        # blindly the last row. With 7 cutoffs in a 3-wide grid the last row
        # holds one panel and two blanks, so labelling row nrows-1 put the
        # time axis on a single panel and left the other six unlabelled —
        # sharex hides inner tick labels, and the "inner" ones here have
        # nothing below them.
        bottom = max(r for r in range(nrows) if r * ncols + col < len(cutoffs))

        ax_b = axes[bottom][col]

        ax_b.set_xlabel("Time (s)", color=TEXT_SECONDARY, fontsize=10)

        ax_b.tick_params(labelbottom=True)


    fig.suptitle(
        f"{title} — raw (grey) vs each cutoff",
        color=TEXT_PRIMARY,
        fontsize=11
    )

    fig.tight_layout()

    fig.savefig(sibling("panels"), dpi=PLOT_DPI, bbox_inches="tight")

    plt.close(fig)


    # ── View 3: residuals ────────────────────────────────────────────────
    # raw - filtered, i.e. exactly what each cutoff throws away. Shared
    # y-axis across panels so the growth of the discarded content with
    # decreasing cutoff is visible at a glance.
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(PANEL_WIDTH_IN * ncols, PANEL_HEIGHT_IN * nrows),
        sharex=True,
        sharey=True,
        squeeze=False
    )


    for idx, cutoff in enumerate(cutoffs):

        ax = axes[idx // ncols][idx % ncols]

        residual = raw_plot - filtered_plot[cutoff]


        ax.axhline(0, color=GRID_COLOR, linewidth=1.0, zorder=1)

        ax.plot(
            time_plot,
            residual,
            color=colors[cutoff],
            linewidth=1.0,
            zorder=2
        )


        # RMS quantifies what the eye is judging: how much was removed.
        ax.set_title(
            f"{cutoff} Hz — RMS {np.sqrt(np.nanmean(residual ** 2)):.3f}",
            color=TEXT_PRIMARY,
            fontsize=10
        )

        style_axis(ax)


    for idx in range(len(cutoffs), nrows * ncols):
        axes[idx // ncols][idx % ncols].axis("off")


    # Deliberately short — the full ylabel is long enough to collide
    # between rows, and the suptitle already carries the units.
    for row in range(nrows):
        axes[row][0].set_ylabel("raw − filtered", color=TEXT_SECONDARY, fontsize=9)

    for col in range(ncols):
        # The BOTTOM-MOST PANEL THAT ACTUALLY EXISTS in this column, not
        # blindly the last row. With 7 cutoffs in a 3-wide grid the last row
        # holds one panel and two blanks, so labelling row nrows-1 put the
        # time axis on a single panel and left the other six unlabelled —
        # sharex hides inner tick labels, and the "inner" ones here have
        # nothing below them.
        bottom = max(r for r in range(nrows) if r * ncols + col < len(cutoffs))

        ax_b = axes[bottom][col]

        ax_b.set_xlabel("Time (s)", color=TEXT_SECONDARY, fontsize=10)

        ax_b.tick_params(labelbottom=True)


    fig.suptitle(
        f"{title} — DISCARDED content, {ylabel}. "
        f"Structure here means real signal is being removed.",
        color=TEXT_PRIMARY,
        fontsize=11
    )

    fig.tight_layout()

    fig.savefig(sibling("residual"), dpi=PLOT_DPI, bbox_inches="tight")

    plt.close(fig)



# ============================================================
# PROCESS FILE
# ============================================================

def process_csv(csv_file, cutoff_frequencies, zoom_on_peak=False, zoom_at=None,
                skip_plots=False):


    print("\n" + "="*50)

    print(
        f"Processing: {csv_file.name}"
    )

    print("="*50)



    output = (
        OUTPUT_DIR /
        csv_file.stem
    )

    output.mkdir(
        parents=True,
        exist_ok=True
    )



    print(
        "Loading telemetry..."
    )


    signals = parse_influx(
        str(csv_file)
    )


    print(
        "Telemetry loaded."
    )



    lat_signal = signals.VCPDU_lat

    lon_signal = signals.VCPDU_lon



    time = lat_signal.time



    lat_ms2 = lat_signal.value

    lon_ms2 = lon_signal.value



    # Shock pots, pulled before masking so they stay aligned with lat/lon.
    have_shockpots = all(
        name in signals
        for name in SHOCKPOT_SIGNALS.values()
    )


    if have_shockpots:

        shockpots = {
            corner: np.asarray(
                signals[name].value,
                dtype=float
            )
            for corner, name in SHOCKPOT_SIGNALS.items()
        }


    else:

        shockpots = None

        print(
            "  [!] shock pot signals missing — roll/pitch plots skipped."
        )



    # ── RESAMPLE TO A TRUE UNIFORM GRID BEFORE FILTERING ─────────────────
    #
    # Everything below used to run on the InfluxDB union grid. That grid is
    # not a sample rate — it is the merged timestamps of every signal in the
    # file, built by ZERO-ORDER HOLD, so between a shock pot's real 100 Hz
    # updates it simply repeats the last value. The "raw" trace was
    # therefore a STAIRCASE sampled at ~2577 Hz, and a staircase's step
    # edges carry high-frequency energy that no sensor measured.
    #
    # That mattered most for exactly the view this tool exists to provide.
    # Measured residual (raw - filtered) RMS at 5 Hz, union grid against a
    # true 100 Hz grid:
    #
    #   skidpad_austin_both   0.5497 vs 0.3935    +40%
    #   braketest2            0.5274 vs 0.3262    +62%
    #   endurance_full        1.5706 vs 0.4155   +278%
    #   autocross_andrew2     2.6763 vs 0.4579   +485%
    #
    # So the residual panels were showing up to six times more "discarded
    # content" than was real, which would push a cutoff choice higher than
    # the data warrants. Resampling from the RAW per-signal samples removes
    # the artefact entirely.
    time_s, resampled = resample_all(signals, csv_file)

    lat_ms2 = resampled["VCPDU_lat"]

    lon_ms2 = resampled["VCPDU_lon"]


    if shockpots is not None:

        shockpots = {
            corner: resampled[name]
            for corner, name in SHOCKPOT_SIGNALS.items()
        }


    extras = {}


    for name, title, ylabel, stem in EXTRA_SIGNALS:

        if name not in signals:

            print(
                f"  [!] {name} not in this file — skipped."
            )

            continue


        extras[name] = resampled[name]


    # Nyquist warning. VCFRONT_brakePressure is sampled at 10 Hz, not 100 —
    # measured, and matching its firmware task rate. Its Nyquist is 5 Hz, so
    # every swept cutoff at or above 5 Hz is meaningless for that channel,
    # and comparing them is comparing noise. Say so rather than plotting
    # seven indistinguishable traces and letting someone pick one.
    for name in list(resampled):

        rate = signal_rate_hz(name)

        over = [c for c in cutoff_frequencies if c >= rate / 2.0]

        if over:
            print(
                f"  [!] {name} is sampled at {rate:.0f} Hz (Nyquist "
                f"{rate / 2.0:.1f} Hz) — cutoffs {over} are at or above "
                f"Nyquist and carry no meaning for it."
            )



    lat_g = lat_ms2 / G

    lon_g = lon_ms2 / G



    combined_raw = np.sqrt(
        lat_g**2 +
        lon_g**2
    )



    # Roll / pitch, same definitions as case2 / case3 / case4. Centred on
    # their own median purely so the y-axis reads sensibly — a constant
    # offset does not change how the filter behaves.
    if shockpots is not None:

        roll_raw = (
            (shockpots["FR"] - shockpots["FL"])
            +
            (shockpots["RR"] - shockpots["RL"])
        ) / 2.0


        pitch_raw = (
            (shockpots["FL"] + shockpots["FR"])
            -
            (shockpots["RL"] + shockpots["RR"])
        ) / 2.0


        roll_raw = roll_raw - np.median(roll_raw)

        pitch_raw = pitch_raw - np.median(pitch_raw)


    else:

        roll_raw = None

        pitch_raw = None



    # fs MUST match the grid the data is actually on. This used to call
    # estimate_sample_rate(time) against the original union timestamps —
    # correct while the arrays lived on that grid, and badly wrong once they
    # were resampled: it would have designed every filter for ~875 Hz while
    # feeding it 100 Hz data, so a nominal 5 Hz cutoff would really have
    # been 5 * 100/875 = 0.57 Hz.
    fs = UNIFORM_RATE_HZ

    union_fs = estimate_sample_rate(time)


    print("\nTelemetry Information")

    print(
        f"Samples: {len(time_s)}"
    )

    print(
        f"Duration: {time_s[-1]:.2f} s"
    )

    print(
        f"Sampling frequency: {fs:.2f} Hz (true rate, resampled)"
    )

    print(
        f"  (the union grid this came from was {union_fs:.0f} Hz of "
        f"non-uniform, zero-order-held timestamps — not a sample rate)"
    )


    print(
        f"Lateral:      {lat_g.min():.2f} to {lat_g.max():.2f} g"
    )

    print(
        f"Longitudinal: {lon_g.min():.2f} to {lon_g.max():.2f} g"
    )

    print(
        f"Combined:     {combined_raw.min():.2f} to {combined_raw.max():.2f} g"
    )



    lat_filtered = {}

    lon_filtered = {}

    combined_filtered = {}

    roll_filtered = {}

    pitch_filtered = {}

    extras_filtered = {}



    for cutoff in cutoff_frequencies:


        print(
            f"Applying {cutoff} Hz filter..."
        )


        lat_f = butter_lowpass_filter(
            lat_g,
            cutoff,
            fs,
            FILTER_ORDER
        )


        lon_f = butter_lowpass_filter(
            lon_g,
            cutoff,
            fs,
            FILTER_ORDER
        )


        lat_filtered[cutoff] = lat_f

        lon_filtered[cutoff] = lon_f


        # IMPORTANT:
        # calculate combined AFTER filtering
        combined_filtered[cutoff] = np.sqrt(
            lat_f**2 +
            lon_f**2
        )


        if roll_raw is not None:

            roll_filtered[cutoff] = butter_lowpass_filter(
                roll_raw,
                cutoff,
                fs,
                FILTER_ORDER
            )


            pitch_filtered[cutoff] = butter_lowpass_filter(
                pitch_raw,
                cutoff,
                fs,
                FILTER_ORDER
            )


        for name, values in extras.items():

            extras_filtered.setdefault(
                name,
                {}
            )[cutoff] = butter_lowpass_filter(
                values,
                cutoff,
                fs,
                FILTER_ORDER
            )



    plots = [

        (
            lat_g,
            lat_filtered,
            "Lateral G",
            "Lateral G (g)",
            "lateral"
        ),

        (
            lon_g,
            lon_filtered,
            "Longitudinal G",
            "Longitudinal G (g)",
            "longitudinal"
        ),

        (
            combined_raw,
            combined_filtered,
            "Combined G",
            "Combined G (g)",
            "combined"
        )

    ]


    if roll_raw is not None:

        plots.append(
            (
                roll_raw,
                roll_filtered,
                "Roll (shock pots)",
                "Roll (mm, median-centred)",
                "roll"
            )
        )


        plots.append(
            (
                pitch_raw,
                pitch_filtered,
                "Pitch (shock pots)",
                "Pitch (mm, median-centred)",
                "pitch"
            )
        )



    for name, title, ylabel, stem in EXTRA_SIGNALS:

        if name not in extras:

            continue


        plots.append(
            (
                extras[name],
                extras_filtered[name],
                title,
                ylabel,
                stem
            )
        )



    # ── Peak attenuation table ──────────────────────────────────────
    # How much of each signal's peak magnitude survives each cutoff. If a
    # row barely changes across cutoffs, the choice does not matter for
    # that signal.

    edge = int(
        EDGE_EXCLUDE_FRACTION * len(time_s)
    )


    def interior(values):

        """Drop the filtfilt edge transients from both ends."""

        return (
            values[edge:len(values) - edge]
            if edge and len(values) > 2 * edge
            else values
        )


    def interior_peak(values):

        """Largest |value| ignoring the filtfilt edge transients."""

        trimmed = interior(values)

        return float(
            np.nanmax(
                np.abs(trimmed)
            )
        )


    print(
        f"\nPeak attenuation (max |value| retained vs unfiltered, "
        f"outer {EDGE_EXCLUDE_FRACTION:.0%} of each end excluded)"
    )


    header = "  {:<38}{:>10}".format(
        "signal",
        "raw"
    )

    for cutoff in cutoff_frequencies:

        header += "{:>16}".format(
            f"{cutoff} Hz"
        )

    print(header)


    # Also captured as data, not only printed — build_cutoff_review.py reads
    # this to put the numbers beside the plots in the review worksheet.
    attenuation = {
        "file": csv_file.stem,
        "cutoffs": list(cutoff_frequencies),
        "signals": {}
    }


    for raw, filtered, title, ylabel, name in plots:

        raw_peak = interior_peak(raw)


        # A ROBUST reference alongside the max, because the max is
        # sometimes a 1-2 sample spike rather than the real peak of the
        # manoeuvre. endurance_full's raw lateral G maxes at 2.813 g and
        # holds 33 samples above 2.0 g — not physical for this car, which
        # tops out nearer 1.5-1.8 g. Every "% of raw retained" for that
        # signal is then measured against a glitch, so the filters look
        # like they are destroying signal (57-66%) when they are correctly
        # rejecting an outlier. When max and p99.9 diverge, trust p99.9.
        raw_p999 = float(
            np.nanpercentile(
                np.abs(interior(raw)),
                99.9
            )
        )


        attenuation["signals"][name] = {
            "title": title,
            "ylabel": ylabel,
            "raw_peak": raw_peak,
            "raw_p999": raw_p999,
            "spike_dominated": bool(raw_p999 > 0 and raw_peak / raw_p999 > 1.3),
            "retained": {
                str(cutoff): (
                    interior_peak(filtered[cutoff]) / raw_peak
                    if raw_peak
                    else 0.0
                )
                for cutoff in cutoff_frequencies
            }
        }


        row = "  {:<38}{:>10.3f}".format(
            title,
            raw_peak
        )


        for cutoff in cutoff_frequencies:

            peak = interior_peak(
                filtered[cutoff]
            )


            pct = (
                100.0 * peak / raw_peak
                if raw_peak
                else 0.0
            )


            row += "{:>16}".format(
                f"{peak:.3f} ({pct:.0f}%)"
            )


        print(row)


    with open(output / "peak_attenuation.json", "w") as fh:
        json.dump(attenuation, fh, indent=2)


    if skip_plots:

        print("\n(--skip-plots: attenuation data written, plots not regenerated)")

        return



    for raw, filtered, title, ylabel, name in plots:


        full_path = (
            output /
            f"{name}_full.png"
        )


        zoom_path = (
            output /
            f"{name}_zoom.png"
        )


        plot_filters(
            time_s,
            raw,
            filtered,
            f"{title} - {csv_file.stem}",
            ylabel,
            full_path,
            zoom=False
        )


        plot_filters(
            time_s,
            raw,
            filtered,
            f"{title} Zoom - {csv_file.stem}",
            ylabel,
            zoom_path,
            zoom=True,
            zoom_on_peak=zoom_on_peak,
            zoom_at=zoom_at
        )


        print(
            f"Saved {name}_[full|zoom]_[overlay|panels|residual].png"
        )



# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":


    parser = argparse.ArgumentParser(
        description=
        "Compare low-pass filter frequencies on telemetry data."
    )


    parser.add_argument(
        "csv_files",
        nargs="+",
        type=Path,
        help="CSV telemetry files"
    )


    parser.add_argument(
        "--freqs",
        nargs="+",
        type=float,
        required=True,
        help="Filter frequencies to compare (Hz)"
    )


    parser.add_argument(
        "--zoom-on-peak",
        action="store_true",
        help=
        "Centre each zoom plot on that signal's largest-magnitude moment "
        "instead of the fixed 600 s window. Recommended for accel/brake, "
        "whose events are short and would otherwise be missed."
    )


    parser.add_argument(
        "--zoom-at",
        type=float,
        default=None,
        help=
        "Centre every zoom plot on this elapsed time (seconds). Takes "
        "precedence over --zoom-on-peak. Use when the automatic peak lands "
        "on a sensor glitch rather than real motion."
    )


    parser.add_argument(
        "--zoom-duration",
        type=float,
        default=ZOOM_DURATION,
        help=f"Width of the zoom window in seconds (default {ZOOM_DURATION}). "
             f"Narrower gives more horizontal detail in the small-multiple "
             f"panels; widen it to see more context around an event."
    )

    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Write peak_attenuation.json only, without regenerating the "
             "plots. Fast way to refresh the numbers the review worksheet "
             "reads when the plots are already current."
    )


    args = parser.parse_args()


    # Rebind the module global, matching how ZOOM_START is already consumed
    # inside plot_filters rather than threaded through every call. This
    # block runs at module scope, so no `global` declaration is needed (or
    # allowed).
    ZOOM_DURATION = args.zoom_duration



    for csv in args.csv_files:


        if csv.exists():

            process_csv(
                csv,
                args.freqs,
                zoom_on_peak=args.zoom_on_peak,
                zoom_at=args.zoom_at,
                skip_plots=args.skip_plots
            )


        else:

            print(
                f"Missing file: {csv}"
            )



    print("\n==============================")

    print(
        "Filter comparison complete."
    )

    print(
        f"Results saved in: {OUTPUT_DIR.resolve()}"
    )

    print("==============================")