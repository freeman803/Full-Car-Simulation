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

    Note the ~1200 Hz "sampling frequency" printed below is the density of
    the InfluxDB union time grid, not a real sample rate — see
    case_common.py's module docstring. It is the correct fs to design the
    filter against, since these arrays really do live on that grid, but it
    is not evidence that any signal is genuinely sampled that fast.

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


--zoom-on-peak:

    The default zoom window starts at ZOOM_START (600 s), falling back to
    the file midpoint when the file is shorter. That is fine for long mixed
    runs (endurance, autocross) but lands on arbitrary quiet track for
    accel and brake files, whose interesting content is a handful of short
    events. --zoom-on-peak instead centres each zoom on that signal's own
    largest-magnitude moment. Recommended for accel/brake.


Outputs:

    filter_compare_results/
        filename/
            lateral_full.png
            longitudinal_full.png
            combined_full.png
            roll_full.png
            pitch_full.png
            vehicle_speed_full.png
            brake_pressure_front_full.png
            brake_pressure_rear_full.png
            ... and a _zoom.png for each of the above

"""


import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import butter, filtfilt

from parse_influx import parse_influx



# ============================================================
# SETTINGS
# ============================================================

G = 9.80665

FILTER_ORDER = 4

OUTPUT_DIR = Path("filter_compare_results")


# Same zoom behavior as previous script
ZOOM_START = 600
ZOOM_DURATION = 20


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

            mask = (
                (time >= ZOOM_START)
                &
                (time <= ZOOM_START + ZOOM_DURATION)
            )


            # fallback for shorter files
            if not np.any(mask):

                midpoint = time[len(time)//2]

                mask = (
                    (time >= midpoint)
                    &
                    (time <= midpoint + ZOOM_DURATION)
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



    plt.figure(
        figsize=(14,6)
    )


    plt.plot(
        time_plot,
        raw_plot,
        label="Raw",
        alpha=0.5
    )


    for cutoff, data in filtered_plot.items():

        plt.plot(
            time_plot,
            data,
            label=f"{cutoff} Hz"
        )


    plt.title(
        title
    )

    plt.xlabel(
        "Time (s)"
    )

    plt.ylabel(
        ylabel
    )

    plt.grid(True)

    plt.legend()

    plt.tight_layout()


    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )


    plt.close()



# ============================================================
# PROCESS FILE
# ============================================================

def process_csv(csv_file, cutoff_frequencies, zoom_on_peak=False, zoom_at=None):


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



    valid = (
        np.isfinite(lat_ms2)
        &
        np.isfinite(lon_ms2)
    )


    time = time[valid]

    lat_ms2 = lat_ms2[valid]

    lon_ms2 = lon_ms2[valid]


    if shockpots is not None:

        shockpots = {
            corner: fill_nans(
                values[valid]
            )
            for corner, values in shockpots.items()
        }



    extras = {}


    for name, title, ylabel, stem in EXTRA_SIGNALS:

        if name not in signals:

            print(
                f"  [!] {name} not in this file — skipped."
            )

            continue


        extras[name] = fill_nans(
            np.asarray(
                signals[name].value,
                dtype=float
            )[valid]
        )



    time_s = (
        time - time[0]
    ).total_seconds()



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



    fs = estimate_sample_rate(
        time
    )



    print("\nTelemetry Information")

    print(
        f"Samples: {len(time_s)}"
    )

    print(
        f"Duration: {time_s[-1]:.2f} s"
    )

    print(
        f"Sampling frequency: {fs:.2f} Hz"
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


    def interior_peak(values):

        """Largest |value| ignoring the filtfilt edge transients."""

        trimmed = (
            values[edge:len(values) - edge]
            if edge and len(values) > 2 * edge
            else values
        )

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


    for raw, filtered, title, ylabel, name in plots:

        raw_peak = interior_peak(raw)


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
            f"Saved {full_path}"
        )

        print(
            f"Saved {zoom_path}"
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


    args = parser.parse_args()



    for csv in args.csv_files:


        if csv.exists():

            process_csv(
                csv,
                args.freqs,
                zoom_on_peak=args.zoom_on_peak,
                zoom_at=args.zoom_at
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