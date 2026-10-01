# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
deakin_lltd_sweep.py — reproduces Deakin et al.'s Figures 9-12 (SAE
2000-01-3554): front lateral load transfer as % of total, plotted against
front roll stiffness as % of total, one line per chassis torsional
stiffness, one panel per total suspension roll stiffness.

NOTHING IS RE-DERIVED HERE. Every curve is torsional_stiffness.lltd(), the
same Deakin two-mass model cfr27_target.py and headline() already use --
this script only sweeps it over a grid and plots the result.

    uv run deakin_lltd_sweep.py

Writes plots/deakin_lltd_sweep/report.html.

PANELS. 500 / 1500 / 5000 / 15000 N*m/deg are Deakin's own figures 9-12,
reproduced under his own assumption (50:50 static mass split). 658.6 is
CFR26's actual ground-referenced total (torsional_stiffness.cfr26_axle_
stiffness()), plotted with CFR26's MEASURED 0.507 front mass fraction and
its actual 44.8% front roll-stiffness point marked.

CFR27 IS NOT PLOTTED. Every parameter cfr27_target.py needs -- motion
ratio, track, ARB settings -- is still None (CHASSIS_TASKS.md item 1), so
it has no real total roll stiffness yet. Re-run this once that lands.

CHASSIS STIFFNESSES. 1000-2000 N*m/deg is where CFR26/CFR27 actually live,
so that band is densely sampled; 100 and 10000 are Deakin-style bookends
included only for comparison (a real frame is never going to be either).
1341 is CFR26's own 90%-criterion, build-loss-adjusted target (see
torsional_stiffness.headline()) and is called out in its own legend entry.
"""

import os

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import case_common as cc
import torsional_stiffness as ts

OUTPUT_PATH = os.path.join("plots", "deakin_lltd_sweep", "report.html")

# Ascending. The label carries the meaning; the value doesn't need to be a
# round number.
CHASSIS_STIFFNESSES = [
    (100, "100 N·m/deg (very soft, comparison only)"),
    (1000, "1000 N·m/deg"),
    (1200, "1200 N·m/deg"),
    (1341, "1341 N·m/deg (CFR26's 90% criterion target)"),
    (1500, "1500 N·m/deg"),
    (1750, "1750 N·m/deg"),
    (2000, "2000 N·m/deg"),
    (10000, "10000 N·m/deg (very stiff, comparison only)"),
]

# Same validated categorical set filter_compare.py uses for its own
# ordered-magnitude sweep (cutoff frequency): a sequential single-hue ramp
# was tried first there and found hard to separate at a glance past ~3
# lines on one busy axis. Fixed ascending assignment, never cycled.
STIFFNESS_COLORS = [
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100",
    "#e87ba4", "#008300", "#4a3aa7", "#e34948",
]

_CFR26_KF, _CFR26_KR = ts.cfr26_axle_stiffness()
CFR26_TOTAL = _CFR26_KF + _CFR26_KR
CFR26_FRONT_PCT = 100.0 * _CFR26_KF / CFR26_TOTAL

# (k_total, panel label, front_mass_fraction, actual-point % or None)
PANELS = [
    (500, "500 N·m/deg (Deakin)", 0.5, None),
    (CFR26_TOTAL, f"{CFR26_TOTAL:.0f} N·m/deg — CFR26 actual",
     ts.FRONT_MASS_FRACTION, CFR26_FRONT_PCT),
    (1500, "1500 N·m/deg (Deakin)", 0.5, None),
    (5000, "5000 N·m/deg (Deakin)", 0.5, None),
    (15000, "15000 N·m/deg (Deakin)", 0.5, None),
]

PANEL_COLUMNS = 3
N_POINTS = 101


def build_figure():
    n_rows = -(-len(PANELS) // PANEL_COLUMNS)
    fig = make_subplots(
        rows=n_rows, cols=PANEL_COLUMNS,
        subplot_titles=[p[1] for p in PANELS],
        horizontal_spacing=0.06, vertical_spacing=0.16,
    )

    pct_front = np.linspace(0.0, 100.0, N_POINTS)

    for i, (k_total, _label, mass_fraction, actual_pct) in enumerate(PANELS):
        row, col = i // PANEL_COLUMNS + 1, i % PANEL_COLUMNS + 1
        k_front = pct_front / 100.0 * k_total
        k_rear = k_total - k_front

        for j, (k_chassis, chassis_label) in enumerate(CHASSIS_STIFFNESSES):
            y = [ts.lltd(kf, kr, k_chassis, front_mass_fraction=mass_fraction)
                 for kf, kr in zip(k_front, k_rear)]
            fig.add_trace(
                go.Scatter(
                    x=pct_front, y=y, mode="lines", name=chassis_label,
                    legendgroup=chassis_label,
                    showlegend=(i == 0),
                    line=dict(color=STIFFNESS_COLORS[j],
                              width=3 if k_chassis == 1341 else 2),
                    hovertemplate=(f"{chassis_label}<br>"
                                    "front roll stiffness: %{x:.0f}%<br>"
                                    "front load transfer: %{y:.1f}%"
                                    "<extra></extra>"),
                ),
                row=row, col=col,
            )

        if actual_pct is not None:
            fig.add_vline(x=actual_pct, line=dict(color=cc.PLOT_PEAK_COLOR,
                                                   width=1.4, dash="dot"),
                           row=row, col=col)
            fig.add_annotation(
                x=actual_pct, y=8, xref=f"x{'' if i == 0 else i + 1}",
                yref=f"y{'' if i == 0 else i + 1}",
                text=f"actual, {actual_pct:.1f}% front",
                showarrow=False, font=dict(size=10, color=cc.PLOT_PEAK_COLOR),
                xanchor="left",
            )

        fig.update_xaxes(range=[0, 100], row=row, col=col,
                          gridcolor=cc.PLOT_GRID_COLOR)
        fig.update_yaxes(range=[0, 100], row=row, col=col,
                          gridcolor=cc.PLOT_GRID_COLOR)
        if row == n_rows or i + PANEL_COLUMNS >= len(PANELS):
            fig.update_xaxes(title_text="front roll stiffness (% of total)",
                              row=row, col=col)
        if col == 1:
            fig.update_yaxes(title_text="front load transfer (% of total)",
                              row=row, col=col)

    fig.update_layout(
        template=cc.PLOT_TEMPLATE,
        height=430 * n_rows, width=1500,
        legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center",
                     title_text="chassis torsional stiffness"),
    )

    title_px = cc.titled(
        fig,
        "Delivered load-transfer fraction vs. chassis stiffness",
        "Front lateral load transfer (% of total) vs. front roll stiffness "
        "(% of total), Deakin et al. SAE 2000-01-3554 Figures 9-12. Each "
        "panel holds total suspension roll stiffness fixed; each line is a "
        "chassis torsional stiffness. A flat line means the chassis is "
        "absorbing the roll-stiffness split instead of delivering it to the "
        "tyres -- diagonal (y=x) is the rigid-chassis limit. 500/1500/5000/"
        "15000 N·m/deg use Deakin's own 50:50 mass-split assumption; the "
        "CFR26 panel uses CFR26's measured 0.507 front mass fraction and "
        "marks its actual 44.8% front roll-stiffness split. CFR27 has no "
        "real total roll stiffness yet (suspension parameters still "
        "placeholders in cfr27_target.py) so it isn't plotted here.",
        extra_top_px=20,
    )
    fig.update_layout(margin=dict(t=title_px + 20, b=120))
    return fig


def main():
    out_dir = os.path.dirname(OUTPUT_PATH)
    os.makedirs(out_dir, exist_ok=True)
    fig = build_figure()
    fig.write_html(OUTPUT_PATH, include_plotlyjs="cdn")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
