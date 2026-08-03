# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
case1_max_gs.py — Case 1: max lateral G, max longitudinal G, max combined G,
for SKIDPAD, AUTOCROSS, and ENDURANCE (kept separate).

Methodology:
- SKIDPAD (10 Hz low-pass): the event is two sustained circles (one per
  direction), so we find the longest steady-state stretch of each
  direction and report the MEDIAN lateral G (+ mean longitudinal G) over
  its trimmed middle — matching how FSAE itself scores skidpad (average
  over the steady lap, not a peak).
  Direction is judged from the sign of filtered lateral G. "Steady" means
  lateral G is meaningfully non-zero AND the steering angle's RATE OF
  CHANGE is low. We deliberately never use the steering angle's absolute
  value (the sensor may be miscalibrated/maxing out) — only its delta,
  which is still meaningful for detecting active correction vs. holding
  a line.

- AUTOCROSS / ENDURANCE (10 Hz low-pass): these are transient corner
  sequences, so instead of one global max we detect real peaks (using
  prominence + minimum spacing to reject noise and avoid double-counting
  one corner) and average the top 5 pooled across all files in that
  event, for a robust "the car consistently achieves about this much"
  number. The single highest peak is also reported for reference,
  including WHEN it happened and the simultaneous lat/lon G's (i.e. the
  actual g-g diagram point for that instant).

Outputs:
- Console report with all of the above.
- One before/after low-pass filter plot per file (lateral + longitudinal
  G overlaid raw vs. filtered) -> plots/<event>/<file>_before_after.html
- One G-G diagram per event, with the representative points highlighted
  -> plots/<event>/gg_diagram.html

Run it:
    uv run case1_max_gs.py --dir comp2026_data

Uses parse_influx.py (must be in the same folder, or importable).
"""

import os
import sys
import glob
import argparse
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from parse_influx import parse_influx
from case_report import report_page, write_index
from case_common import (
    G, FILTER_ORDER, SKIDPAD_CUTOFF_HZ, AUTOX_END_CUTOFF_HZ,
    EVENT_KEYWORDS, CASE_EVENTS as CASE1_EVENTS,
    detect_event_type, group_by_event,
    fill_gaps, lowpass, elapsed_seconds, trim_window,
    find_steady_segments, top_k_peaks,
    MIN_LAT_G_FOR_TURN, MIN_RUN_SECONDS, TRIM_SECONDS, MIN_FRACTION_OF_LONGEST,
    TOP_K_PEAKS, PEAK_MIN_DISTANCE_S,
    build_raw_vs_filtered, thin_scatter, PLOT_TEMPLATE, format_peak_shape,
    titled,
)

# ── Tunable constants specific to this case (G-specific peak prominence) ──
PEAK_PROMINENCE_G = 0.3

# Plots go under their own case-named subtree (plots/case1_max_gs/<event>/...)
# rather than plots/<event>/ shared with other case scripts — each case
# script owns its own folder, so nothing collides and a whole case's
# output can be browsed or shared as one directory.
PLOTS_ROOT = os.path.join("plots", "case1_max_gs")


def analyze_skidpad_file(path):
    required = ["VCPDU_lat", "VCPDU_lon"]
    try:
        signals = parse_influx(path)
    except Exception as e:
        print(f"  [!] Failed to parse '{path}': {e}")
        return None
    if any(name not in signals for name in required):
        print(f"  [!] '{path}' missing required signals, skipping.")
        return None

    lat_raw = np.asarray(signals["VCPDU_lat"].value, dtype=float) / G
    lon_raw = np.asarray(signals["VCPDU_lon"].value, dtype=float) / G
    t_raw = np.asarray(signals["VCPDU_lat"].time)
    dt = float(np.median(np.diff(t_raw)) / np.timedelta64(1, "s"))

    lat_f = lowpass(lat_raw, dt, SKIDPAD_CUTOFF_HZ)
    lon_f = lowpass(lon_raw, dt, SKIDPAD_CUTOFF_HZ)

    t = elapsed_seconds(t_raw)
    segments = find_steady_segments(lat_f, t)

    results = {}
    for sg, run_list in segments.items():
        per_run = []
        pooled_lat, pooled_lon = [], []
        for s, e, dur in run_list:
            ts, te = trim_window(t, s, e, TRIM_SECONDS)
            seg_lat = lat_f[ts:te + 1]
            seg_lon = lon_f[ts:te + 1]
            per_run.append({
                "median_lat_g": float(np.median(seg_lat)),
                "mean_lon_g": float(np.mean(seg_lon)),
                "duration_s": dur,
                "start_s": float(t[ts]),
                "end_s": float(t[te]),
            })
            pooled_lat.append(seg_lat)
            pooled_lon.append(seg_lon)

        results[sg] = {
            "runs": per_run,
            "combined_median_lat_g": float(np.median(np.concatenate(pooled_lat))),
            "combined_mean_lon_g": float(np.mean(np.concatenate(pooled_lon))),
        }

    return {
        "path": path, "t": t, "lat_raw": lat_raw, "lon_raw": lon_raw,
        "lat_f": lat_f, "lon_f": lon_f, "dt": dt, "segments": results,
    }


# ── Autocross/Endurance: peak detection ──────────────────────────────────

def analyze_transient_file(path, event):
    required = ["VCPDU_lat", "VCPDU_lon"]
    try:
        signals = parse_influx(path)
    except Exception as e:
        print(f"  [!] Failed to parse '{path}': {e}")
        return None
    if any(name not in signals for name in required):
        print(f"  [!] '{path}' missing required signals, skipping.")
        return None

    lat_raw = np.asarray(signals["VCPDU_lat"].value, dtype=float) / G
    lon_raw = np.asarray(signals["VCPDU_lon"].value, dtype=float) / G
    t_raw = np.asarray(signals["VCPDU_lat"].time)
    dt = float(np.median(np.diff(t_raw)) / np.timedelta64(1, "s"))

    lat_f = lowpass(lat_raw, dt, AUTOX_END_CUTOFF_HZ)
    lon_f = lowpass(lon_raw, dt, AUTOX_END_CUTOFF_HZ)
    resultant = np.sqrt(lat_f ** 2 + lon_f ** 2)
    t = elapsed_seconds(t_raw)

    lat_idxs, lat_vals = top_k_peaks(np.abs(lat_f), t, TOP_K_PEAKS, prominence=PEAK_PROMINENCE_G)
    lon_idxs, lon_vals = top_k_peaks(np.abs(lon_f), t, TOP_K_PEAKS, prominence=PEAK_PROMINENCE_G)
    res_idxs, res_vals = top_k_peaks(resultant, t, TOP_K_PEAKS, prominence=PEAK_PROMINENCE_G)

    return {
        "path": path, "event": event, "t": t, "dt": dt,
        "lat_raw": lat_raw, "lon_raw": lon_raw, "lat_f": lat_f, "lon_f": lon_f,
        "resultant": resultant,
        "lat_peaks": list(zip(lat_idxs.tolist(), lat_vals.tolist())),
        "lon_peaks": list(zip(lon_idxs.tolist(), lon_vals.tolist())),
        "res_peaks": list(zip(res_idxs.tolist(), res_vals.tolist())),
    }


# ── Plotting ─────────────────────────────────────────────────────────────

def steady_spans(result):
    """The (start_s, end_s) windows this file's numbers were measured over.

    Only skidpad has them — the transient events report peaks, not
    windows. Returns [] otherwise, which the plot builder reads as "nothing
    to shade". These are the POST-TRIM bounds (TRIM_SECONDS is already off
    each end), so what gets shaded is exactly the data that went into the
    median, not the whole qualifying run.
    """
    spans = []
    for sign_result in (result.get("segments") or {}).values():
        for run in sign_result.get("runs", []):
            spans.append((run["start_s"], run["end_s"]))
    return sorted(spans)


def peak_markers(result):
    """{panel_index: [(t, label, y), ...]} for the peaks this file reports.

    Panel 0 is lateral G, panel 1 longitudinal. y is taken from the FILTERED
    trace, which is the one the peak was found in — putting the marker on
    raw would place it slightly off its own reported value.
    """
    markers = {}
    for panel, (key, sig) in enumerate([("lat_peaks", "lat_f"),
                                        ("lon_peaks", "lon_f")]):
        rows = []
        for rank, (idx, val) in enumerate(result.get(key, []), 1):
            rows.append((float(result["t"][idx]), f"#{rank}",
                         float(result[sig][idx])))
        if rows:
            markers[panel] = rows
    return markers


def build_before_after_plot(result, cutoff_hz, output_path):
    build_raw_vs_filtered(
        panels=[
            ("Lateral G", result["lat_raw"], result["lat_f"], "G"),
            ("Longitudinal G", result["lon_raw"], result["lon_f"], "G"),
        ],
        t=result["t"],
        title=os.path.basename(result["path"]),
        output_path=output_path,
        cutoff_hz=cutoff_hz,
        shade=steady_spans(result),
        shade_label="steady-state window used for the skidpad median",
        markers=peak_markers(result),
    )


def build_gg_diagram(event, background_points, highlighted, output_path):
    fig = go.Figure()

    for fname, lat, lon in background_points:
        lat_thin, lon_thin = thin_scatter(lat, lon)
        fig.add_trace(go.Scattergl(
            x=lat_thin, y=lon_thin, mode="markers", name=fname,
            marker=dict(size=3, opacity=0.25),
            hovertemplate="lat=%{x:.3f}g<br>lon=%{y:.3f}g<extra>" + fname + "</extra>",
        ))

    # THE FRICTION ENVELOPE. A g-g scatter shows where the car went; the
    # hull shows what it could REACH, which is the thing you compare against
    # a tyre model or a target and the only part of this chart that is a
    # design input. case4 has hulled its roll-vs-pitch cloud since it was
    # written; this one had none, so the usable friction budget was visible
    # nowhere in the analysis.
    #
    # Computed from the FULL arrays, never the thinned display set — an
    # extreme point is exactly what thin_scatter is allowed to drop if a
    # kept point already occupies its cell (see case_common.thin_scatter).
    hull_area = None
    if background_points:
        pts = np.column_stack([
            np.concatenate([lat for _, lat, _ in background_points]),
            np.concatenate([lon for _, _, lon in background_points]),
        ])
        finite = pts[np.isfinite(pts).all(axis=1)]
        try:
            from scipy.spatial import ConvexHull
            if len(finite) >= 3:
                hull = ConvexHull(finite)
                loop = np.append(hull.vertices, hull.vertices[0])
                hull_area = float(hull.volume)   # 'volume' is area in 2-D
                fig.add_trace(go.Scatter(
                    x=finite[loop, 0], y=finite[loop, 1],
                    mode="lines", name="friction envelope (convex hull)",
                    line=dict(color="black", width=2),
                    fill="toself", fillcolor="rgba(42,120,214,0.06)",
                    hoverinfo="skip",
                ))
        except Exception as e:
            print(f"  [!] {event}: g-g hull skipped ({e})")

    # Reference circles at whole-g radii. A tyre with equal grip in every
    # direction would fill a circle, so the gap between the hull and these
    # is the anisotropy — how much more the car does in one axis than
    # another, read directly off the chart.
    if background_points:
        limit = float(np.nanmax(np.abs(finite))) if len(finite) else 1.0
        theta = np.linspace(0, 2 * np.pi, 181)
        for radius in range(1, int(np.ceil(limit)) + 1):
            fig.add_trace(go.Scatter(
                x=radius * np.cos(theta), y=radius * np.sin(theta),
                mode="lines", name=f"{radius} g",
                line=dict(color="#c9c8c3", width=1, dash="dot"),
                hoverinfo="skip", showlegend=(radius == 1),
            ))

    for label, lat_vals, lon_vals, texts, color in highlighted:
        fig.add_trace(go.Scatter(
            x=lat_vals, y=lon_vals, mode="markers", name=label,
            marker=dict(size=14, symbol="star", color=color, line=dict(width=1, color="black")),
            text=texts, hovertemplate="%{text}<br>lat=%{x:.3f}g<br>lon=%{y:.3f}g<extra></extra>",
        ))

    area_note = (f" Envelope area {hull_area:.2f} g²."
                 if hull_area is not None else "")
    fig.update_layout(
        xaxis_title="Lateral G (a_y)",
        yaxis_title="Longitudinal G (a_x)",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        template=PLOT_TEMPLATE,
    )
    titled(
        fig, f"{event.upper()} — G-G Diagram",
        f"every sample the car reached; stars mark the reported peaks. The "
        f"black hull is the <b>usable friction envelope</b> — what the car "
        f"could reach, not just where it went.{area_note} Dotted circles are "
        f"whole-g references; a tyre with equal grip every direction would "
        f"fill one. Markers thinned for display, hull computed from every "
        f"sample."
        f"<br><b>alpha</b>, quoted with each peak, says where that point sits "
        f"on the circle: <b>90° = pure cornering</b> (out along the lateral "
        f"axis, no braking or acceleration), <b>0° = pure braking or "
        f"acceleration</b> (along the longitudinal axis), <b>45° = equal "
        f"parts of both</b> — the combined-load corner you are trying to use.",
    )
    fig.write_html(output_path, include_plotlyjs="cdn")
    return hull_area


# ── Reporting ────────────────────────────────────────────────────────────

def report_skidpad(results):
    print(f"\n=== SKIDPAD (steady-state segments, {SKIDPAD_CUTOFF_HZ} Hz low-pass) ===")
    if not results:
        print("  no data")
        return [], None
    highlight_points = []  # (label, [lat], [lon], [text], color)
    sustained_lat = []     # |median lateral G| per direction, for the summary
    for r in results:
        fname = os.path.basename(r["path"])
        if not r["segments"]:
            print(f"  [!] {fname}: no qualifying steady segments found — "
                  f"check MIN_LAT_G_FOR_TURN / MIN_RUN_SECONDS.")
            continue
        for sg, info in sorted(r["segments"].items()):
            direction = "positive-lateral-G direction" if sg > 0 else "negative-lateral-G direction"
            print(f"  {fname} — {direction} ({len(info['runs'])} run(s) found):")
            run_lats, run_lons, run_texts = [], [], []
            for i, run in enumerate(info["runs"], 1):
                print(f"    Run {i}: median lateral G={run['median_lat_g']:+.4f}g, "
                      f"mean longitudinal G={run['mean_lon_g']:+.4f}g "
                      f"({run['start_s']:.1f}s-{run['end_s']:.1f}s, "
                      f"dur={run['duration_s']:.1f}s after trimming)")
                run_lats.append(run["median_lat_g"])
                run_lons.append(run["mean_lon_g"])
                run_texts.append(f"{fname} {direction} run {i}")
            print(f"    Combined (all runs pooled): median lateral G="
                  f"{info['combined_median_lat_g']:+.4f}g, mean longitudinal G="
                  f"{info['combined_mean_lon_g']:+.4f}g")
            if len(info["runs"]) > 1:
                spread = max(r["median_lat_g"] for r in info["runs"]) - \
                         min(r["median_lat_g"] for r in info["runs"])
                print(f"    Run-to-run spread in lateral G: {spread:.4f}g")

            highlight_points.append((
                f"{fname} {direction} — individual runs",
                run_lats, run_lons, run_texts, "gold",
            ))
            highlight_points.append((
                f"{fname} {direction} — combined",
                [info["combined_median_lat_g"]], [info["combined_mean_lon_g"]],
                [f"{fname} {direction} combined"], "orange",
            ))
            sustained_lat.append(abs(info["combined_median_lat_g"]))

    # Headline numbers for case_summary.py. Built here, from the same values
    # printed above, so the summary table cannot drift from this report.
    # Skidpad is a SUSTAINED measurement (median over the steady lap), so it
    # has no separate "peak" — see the module docstring.
    summary = None
    if sustained_lat:
        summary = {
            "sustained_lat_g_min": min(sustained_lat),
            "sustained_lat_g_max": max(sustained_lat),
            "peak_lat_g": None, "peak_lon_g": None, "peak_combined_g": None,
        }
    return highlight_points, summary


def report_transient(event, results):
    print(f"\n=== {event.upper()} (peak detection, {AUTOX_END_CUTOFF_HZ} Hz low-pass) ===")
    if not results:
        print("  no data")
        return [], None

    def pooled(peak_key):
        pooled_list = []
        for r in results:
            for idx, val in r[peak_key]:
                pooled_list.append((val, r, idx))
        pooled_list.sort(key=lambda x: x[0], reverse=True)
        return pooled_list

    highlight_points = []
    peaks_by_axis = {}   # label -> single highest peak, for the summary
    instants = []        # deep-link targets for the report page

    for label, key, color in [
        ("Lateral G", "lat_peaks", "red"),
        ("Longitudinal G", "lon_peaks", "blue"),
        ("Combined G", "res_peaks", "green"),
    ]:
        pool = pooled(key)
        if not pool:
            print(f"  {label}: no peaks found (check PEAK_PROMINENCE_G / PEAK_MIN_DISTANCE_S)")
            continue
        top = pool[:TOP_K_PEAKS]
        avg = float(np.mean([v for v, _, _ in top]))
        best_val, best_r, best_idx = pool[0]
        best_fname = os.path.basename(best_r["path"])
        best_t = best_r["t"][best_idx]
        best_lat = best_r["lat_f"][best_idx]
        best_lon = best_r["lon_f"][best_idx]
        alpha = np.degrees(np.arctan2(abs(best_lat), abs(best_lon))) if best_lon != 0 else 90.0

        # Is the winning peak a sustained plateau or one isolated sample?
        # The peak search is run on np.abs(...), so the shape check has to
        # be too — otherwise a negative-lateral-G peak reads as inverted.
        shape_signal = (best_r["resultant"] if key == "res_peaks"
                        else np.abs(best_r["lat_f"]) if key == "lat_peaks"
                        else np.abs(best_r["lon_f"]))

        print(f"  {label}:")
        print(f"    Top {len(top)} peaks averaged: {avg:.4f} g "
              f"(values: {', '.join(f'{v:.3f}' for v, _, _ in top)})")
        print(f"    Single highest peak: {best_val:.4f} g — {best_fname} @ {best_t:.2f}s"
              + format_peak_shape(shape_signal, best_r["t"], best_idx, " g"))
        print(f"    At that instant: lateral={best_lat:+.3f}g, longitudinal={best_lon:+.3f}g, "
              f"alpha={alpha:.1f}°")

        highlight_points.append((
            f"{label} — top {len(top)} peaks",
            [r["lat_f"][idx] for _, r, idx in top],
            [r["lon_f"][idx] for _, r, idx in top],
            [f"{os.path.basename(r['path'])} @ {r['t'][idx]:.2f}s" for _, r, idx in top],
            color,
        ))
        peaks_by_axis[label] = best_val
        instants.append({
            "event": event, "path": best_r["path"], "t": float(best_t),
            "label": f"peak {label.lower()} — {best_val:.3f} g",
            "detail": f"lat {best_lat:+.2f} g, lon {best_lon:+.2f} g, "
                      f"alpha {alpha:.0f}°",
        })

    # Headline numbers for case_summary.py — same values printed above, so the
    # summary table cannot drift from this report. Transient events have no
    # sustained number (there is no steady lap to average over).
    summary = {
        "sustained_lat_g_min": None, "sustained_lat_g_max": None,
        "peak_lat_g": peaks_by_axis.get("Lateral G"),
        "peak_lon_g": peaks_by_axis.get("Longitudinal G"),
        "peak_combined_g": peaks_by_axis.get("Combined G"),
        # Navigation metadata, not a number — underscore-prefixed so
        # case_summary's scalar sweep and the regression snapshot skip it.
        "_instants": instants,
    } if peaks_by_axis else None

    return highlight_points, summary


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

    print(f"Skidpad low-pass: {SKIDPAD_CUTOFF_HZ} Hz | Autocross/Endurance low-pass: "
          f"{AUTOX_END_CUTOFF_HZ} Hz (both {FILTER_ORDER}th-order Butterworth, zero-phase)")

    summaries_by_event = {}

    for event in CASE1_EVENTS:
        paths = grouped.get(event, [])
        if not paths:
            print(f"\nNo files found for {event.upper()}.")
            continue

        out_dir = os.path.join(PLOTS_ROOT, event)
        os.makedirs(out_dir, exist_ok=True)

        if event == "skidpad":
            results = [r for p in paths if (r := analyze_skidpad_file(p)) is not None]
            for r in results:
                fname = os.path.splitext(os.path.basename(r["path"]))[0]
                build_before_after_plot(r, SKIDPAD_CUTOFF_HZ,
                                         os.path.join(out_dir, f"{fname}_before_after.html"))
            highlight, summary = report_skidpad(results)
            background = [(os.path.basename(r["path"]), r["lat_f"], r["lon_f"]) for r in results]
        else:
            results = [r for p in paths if (r := analyze_transient_file(p, event)) is not None]
            for r in results:
                fname = os.path.splitext(os.path.basename(r["path"]))[0]
                build_before_after_plot(r, AUTOX_END_CUTOFF_HZ,
                                         os.path.join(out_dir, f"{fname}_before_after.html"))
            highlight, summary = report_transient(event, results)
            background = [(os.path.basename(r["path"]), r["lat_f"], r["lon_f"]) for r in results]

        summaries_by_event[event] = summary

        if results:
            area = build_gg_diagram(event, background, highlight,
                                    os.path.join(out_dir, "gg_diagram.html"))
            # The envelope AREA, reported rather than left to be eyeballed
            # off the chart. It is the single number for "how much of the
            # friction circle this car actually used" — comparable across
            # events, and the thing a tyre model or a target is checked
            # against. Units are g^2 because both axes are in g.
            if area is not None:
                print(f"\n  Friction envelope (convex hull of the g-g cloud): "
                      f"{area:.2f} g²")
                if summary:
                    summary["gg_envelope_area_g2"] = area
            print(f"\n  Plots saved to: {out_dir}/")

    print("\nDone.")

    return summaries_by_event


CONVENTIONS = [
    "<b>Lateral G positive = cornering left.</b> "
    "<b>Longitudinal G positive = slowing down</b> — verified empirically "
    "against vehicle speed in case3, not assumed from the signal name.",
    "G's come from <code>VCPDU_lat</code> / <code>VCPDU_lon</code>, which "
    "are in <b>m/s²</b> in the raw data and divided by 9.80665 here. Any "
    "number on this page is already in g.",
    "<b>Skidpad is a sustained measurement</b> — a median over the steady "
    "circling segments — so it has no separate 'peak' by design. The other "
    "events report peaks.",
    "A peak is <b>one instantaneous sample</b> of the filtered trace. The "
    "bracketed <code>0.2s mean</code> next to it says whether that instant "
    "was a sustained plateau or an isolated spike.",
    "<b><code>alpha</code> is the direction of the g-g vector</b> at that "
    "instant — <code>atan2(|lat|, |lon|)</code> in degrees, i.e. where the "
    "point sits on the friction circle. <b>90° = pure cornering</b> "
    "(no braking or acceleration), <b>0° = pure straight-line</b> braking "
    "or acceleration, <b>45° = equal parts of both</b>, the combined-load "
    "corner of the circle. So <i>lat −1.60 g, lon +0.14 g, alpha 85°</i> "
    "was essentially pure lateral grip — cornering, not trail-braking. It "
    "tells you at a glance whether a peak is a single-axis event or a "
    "genuine combined-load one.",
]


if __name__ == "__main__":
    with report_page("case1_max_gs", "Case 1 — Max G's", PLOTS_ROOT) as page:
        page.summary = main()
        for text in CONVENTIONS:
            page.add_convention(text)
        for event_summary in (page.summary or {}).values():
            for item in (event_summary or {}).get("_instants", []):
                page.add_instant(item["event"], item["path"], item["t"],
                                 item["label"], item["detail"])
    write_index()
