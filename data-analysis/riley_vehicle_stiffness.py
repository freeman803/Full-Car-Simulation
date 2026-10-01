# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
riley_vehicle_stiffness.py — Riley & George's one-wheel-bump chart (SAE
2002-01-3300): vehicle stiffness vs. frame stiffness, one curve per
suspension-structure stiffness, for CFR27's corner spring rates.

Different question from cfr27_target.py, which sizes K_ch for Deakin's
tuning-authority criterion. This asks what a twist rig would read
wheel-to-wheel with the road springs left in circuit (not locked out):

    1/K_vehicle = 1/K_frame + 1/K_suspension + 1/K1+1/K2+1/K3+1/K4

Headline: CFR27's four corner springs alone cap vehicle_stiffness at ~54
N*m/deg, two orders of magnitude below the 2177 Deakin target -- the whole
point of Riley's result, and why a real twist test locks the springs out
(spindle_to_spindle() in torsional_stiffness.py, CHASSIS_TASKS.md 6a).

Writes two charts: the CFR27 one above (absolute N*m/deg), and a second one
normalized by a single wheel rate -- Riley's own convention, reproducing his
Fig. 12/13 generically rather than for CFR27's two different corner rates.

    uv run riley_vehicle_stiffness.py
"""

import os
from datetime import datetime

import numpy as np
import plotly.graph_objects as go

import cfr27_target as c27
import torsional_stiffness as ts

# palette: dataviz skill's validate_palette.js, 5-way. Line dash is the CVD
# secondary encoding (matched in the legend), not a floating text label --
# labels placed at each curve's end point overlapped each other and the
# legend once the curves converged near the springs' ceiling.
CURVE_COLORS = ["#2a78d6", "#e34948", "#1baf7a", "#eda100", "#8a5fd6"]
CURVE_DASHES = ["solid", "dash", "dot", "dashdot", "longdash"]
TEMPLATE = "plotly_white"

OUTPUT_PATH = os.path.join("plots", "riley_vehicle_stiffness", "chart.html")
OUTPUT_PATH_NORMALIZED = os.path.join("plots", "riley_vehicle_stiffness", "normalized_chart.html")


def cfr27_corner_rates(spring_front_lbf_in=225.0, spring_rear_lbf_in=250.0):
    """CFR27's four corner torsional rates, N*m/deg, from the confirmed cfr27_target.py params."""
    assert c27.missing() == [], "fill cfr27_target.py's P dict first"
    mr_f, mr_r = c27.P["motion_ratio_front"], c27.P["motion_ratio_rear"]
    tf, tr = c27.P["track_front_mm"], c27.P["track_rear_mm"]
    k_f = ts.corner_torsional_rate(spring_front_lbf_in, mr_f, tf)
    k_r = ts.corner_torsional_rate(spring_rear_lbf_in, mr_r, tr)
    return k_f, k_f, k_r, k_r


def build_figure(k1, k2, k3, k4, k_frame_max=2400.0, n=400):
    springs_ceiling = ts.series_stiffness(k1, k2, k3, k4)

    # suspension-structure categories, referenced to the springs' ceiling
    categories = [
        ("suspension = 20x springs' ceiling", 20.0 * springs_ceiling),
        ("suspension = 10x springs' ceiling", 10.0 * springs_ceiling),
        ("suspension = 5x springs' ceiling", 5.0 * springs_ceiling),
        ("suspension = equal to springs' ceiling", 1.0 * springs_ceiling),
        ("suspension rigid (a-arms not yet known)", np.inf),
    ]

    k_frame = np.linspace(1.0, k_frame_max, n)
    fig = go.Figure()
    for (label, k_susp), color, dash in zip(categories, CURVE_COLORS, CURVE_DASHES):
        y = np.array([ts.vehicle_stiffness(kf, k_susp, k1, k2, k3, k4) for kf in k_frame])
        fig.add_trace(go.Scatter(
            x=k_frame, y=y, mode="lines", name=label,
            line=dict(color=color, width=2.5, dash=dash),
            hovertemplate="frame %{x:.0f} N*m/deg<br>vehicle %{y:.1f} N*m/deg<extra>" + label + "</extra>",
        ))

    # top-left corner: curves start near 0 there, so it's clear of both the
    # legend (right) and the converged curve cluster (near the ceiling, right)
    fig.add_hline(y=springs_ceiling, line=dict(color="#888", width=1.5, dash="dot"),
                 annotation_text=f"springs-alone ceiling, {springs_ceiling:.1f} N*m/deg (4 corners in series)",
                 annotation_position="top left")

    deakin_floor = c27.target()[1]
    for x, label in ((deakin_floor, f"CFR27 Deakin floor, {deakin_floor:.0f}"),
                     (1100.0, "CFR26 FEA (frame-only), 1100")):
        if x <= k_frame_max:
            fig.add_vline(x=x, line=dict(color="#444", width=1, dash="dash"),
                         annotation_text=label, annotation_position="top")

    fig.update_layout(
        template=TEMPLATE,
        title="CFR27 vehicle (wheel-to-wheel) torsional stiffness vs. frame stiffness"
              "<br><sup>Riley & George SAE 2002-01-3300, one-wheel-bump chain, springs left in circuit</sup>",
        xaxis_title="Frame stiffness, N*m/deg",
        yaxis_title="Vehicle stiffness, N*m/deg",
        xaxis=dict(range=[0, k_frame_max], showgrid=True, gridcolor="#eee"),
        yaxis=dict(range=[0, springs_ceiling * 1.15], showgrid=True, gridcolor="#eee"),
        hovermode="closest",
        showlegend=True,
        legend=dict(x=1.02, y=1.0, xanchor="left", yanchor="top"),
        margin=dict(r=260, t=90),
    )
    return fig, springs_ceiling


# same 80/85/90/95% milestones Deakin's criterion uses elsewhere (cfr27_target.py)
CRITERIA = (0.80, 0.85, 0.90, 0.95)


def _frame_for_fraction(frac, k_susp, wheel_rate=1.0):
    """Inverse of the 3-term chain: k_frame (as a multiple of wheel rate) that reaches `frac` of rigid."""
    denom = 1.0 / frac - 1.0 / k_susp - 1.0 / wheel_rate
    return 1.0 / denom if denom > 0 else np.inf


def build_normalized_figure(k_frame_max=30.0, n=400, y_range=(0.0, 1.05), zoomed=False):
    """
    Riley & George's OWN chart, normalized by a single wheel rate (his
    convention -- not CFR27-specific, since CFR27's front/rear corner rates
    differ ~46% and there is no one "wheel rate" to normalize by; see
    build_figure() for the CFR27 chart in absolute units). k1 = wheel rate,
    k2..k4 = inf collapses vehicle_stiffness's six-term chain to Riley's
    three-term one (frame, suspension structure, wheel rate) -- same setup
    as test_vehicle_stiffness_matches_rileys_worked_example.

    `y_range` also drives the zoomed-in variant below -- same curves, same
    data, just a tighter axis on the saturation region.
    """
    wheel_rate = 1.0
    categories = [
        ("suspension = 1x wheel rate", 1.0),
        ("suspension = 5x wheel rate", 5.0),
        ("suspension = 10x wheel rate", 10.0),
        ("suspension = 60x wheel rate", 60.0),
        ("suspension rigid", np.inf),
    ]

    k_frame = np.linspace(0.01, k_frame_max, n)
    fig = go.Figure()
    for (label, k_susp), color, dash in zip(categories, CURVE_COLORS, CURVE_DASHES):
        y = np.array([ts.vehicle_stiffness(kf, k_susp, wheel_rate, np.inf, np.inf, np.inf)
                      for kf in k_frame])
        fig.add_trace(go.Scatter(
            x=k_frame, y=y, mode="lines", name=label,
            line=dict(color=color, width=2.5, dash=dash),
            hovertemplate="frame %{x:.2f}x<br>vehicle %{y:.3f}x<extra>" + label + "</extra>",
        ))

    # the paper's own worked example: frame = 10x, suspension = 60x -> 0.90
    wx, wy = 10.0, ts.vehicle_stiffness(10.0, 60.0, wheel_rate, np.inf, np.inf, np.inf)
    if y_range[0] <= wy <= y_range[1]:
        fig.add_trace(go.Scatter(
            x=[wx], y=[wy], mode="markers+text", showlegend=False,
            marker=dict(size=9, color="#000"),
            text=[f"paper's worked example, {wy:.2f}"], textposition="top left",
        ))
    if y_range[0] <= 1.0 <= y_range[1]:
        fig.add_hline(y=1.0, line=dict(color="#888", width=1, dash="dot"))

    # criterion milestones for the 60x-wheel-rate curve (the one highlighted above) --
    # each curve would cross these at a different x, so these are NOT generic gridlines
    for th in CRITERIA:
        x = _frame_for_fraction(th, k_susp=60.0)
        if x <= k_frame_max:
            fig.add_vline(x=x, line=dict(color="#aaa", width=1, dash="dash"),
                         annotation_text=f"{100*th:.0f}% (60x susp)", annotation_position="top",
                         annotation=dict(font=dict(size=10, color="#888")))

    title = "Riley & George's own chart, normalized by wheel rate"
    subtitle = ("zoomed, vehicle/wheel rate 0.85-1.0" if zoomed
               else "Fig. 12/13 reproduction -- generic, not CFR27-specific")
    fig.update_layout(
        template=TEMPLATE,
        title=f"{title}<br><sup>{subtitle}</sup>",
        xaxis_title="Frame stiffness / wheel rate",
        yaxis_title="Vehicle stiffness / wheel rate",
        xaxis=dict(range=[0, k_frame_max], showgrid=True, gridcolor="#eee"),
        yaxis=dict(range=list(y_range), showgrid=True, gridcolor="#eee"),
        hovermode="closest",
        showlegend=True,
        legend=dict(x=1.02, y=1.0, xanchor="left", yanchor="top"),
        margin=dict(r=220, t=90),
    )
    return fig


def report(k1, k2, k3, k4, springs_ceiling):
    print("=" * 70)
    print("RILEY & GEORGE ONE-WHEEL-BUMP CHAIN -- CFR27, PLANNED SPRINGS (225F/250R)")
    print("=" * 70)
    print(f"\n  corner rates, N*m/deg   FL/FR {k1:.1f}   RL/RR {k3:.1f}")
    print(f"  springs-alone ceiling (frame & suspension both rigid): {springs_ceiling:.1f} N*m/deg")
    print(f"\n  For comparison -- these are FRAME-ONLY numbers, a different question:")
    print(f"    CFR26 FEA (frame-only)            1100 N*m/deg")
    print(f"    CFR27 Deakin target (criterion)    2177 N*m/deg")
    print(f"\n  With springs live, vehicle_stiffness saturates near the springs'")
    print(f"  ceiling well before either of those frame numbers is reached --")
    print(f"  which is exactly why a real twist test locks the springs out.")
    print()


def main():
    k1, k2, k3, k4 = cfr27_corner_rates()
    fig, ceiling = build_figure(k1, k2, k3, k4)
    report(k1, k2, k3, k4, ceiling)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    fig.write_html(OUTPUT_PATH, include_plotlyjs="cdn")
    print(f"  chart written to {os.path.abspath(OUTPUT_PATH)}\n")

    norm_fig = build_normalized_figure()
    zoom_fig = build_normalized_figure(y_range=(0.85, 1.0), zoomed=True)
    page = (
        "<!doctype html><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Riley & George, normalized</title>"
        f"<p style='color:#888;font:12px monospace'>generated "
        f"{datetime.now():%Y-%m-%d %H:%M:%S} -- "
        f"if your browser shows a different time here, it's a stale tab/cache, not a stale file.</p>"
        + norm_fig.to_html(full_html=False, include_plotlyjs="cdn")
        + zoom_fig.to_html(full_html=False, include_plotlyjs=False)
    )
    with open(OUTPUT_PATH_NORMALIZED, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"  normalized charts written to {os.path.abspath(OUTPUT_PATH_NORMALIZED)}\n")


if __name__ == "__main__":
    main()
