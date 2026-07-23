"""
sweep/hardpoint_sweep.py — Sweep a single hardpoint coordinate over a range.

HOW TO USE
──────────────────────────────────────────────────────────────────────────────
Edit the CONFIGURATION block at the bottom of this file, then run:

    uv run sweep/hardpoint_sweep.py

The four things you set each time:
    POINT  — which hardpoint to move   (e.g. "upper_BJ")
    AXIS   — which direction to move it (0 = X, 1 = Y, 2 = Z)
    RANGE  — how far either side of the baseline value to sweep (mm)
    STEPS  — how many positions to evaluate across that range

Everything else is automatic. Results are saved to results/hardpoint_sweeps/.
──────────────────────────────────────────────────────────────────────────────

VALID POINT NAMES (copy exactly, including capitalisation):
    Upper A-arm : UAA_front_inboard  UAA_rear_inboard  UAA_outboard
    Lower A-arm : LAA_front_inboard  LAA_rear_inboard  LAA_outboard
    Steering    : tie_rod_inboard    tie_rod_outboard
    Ball joints : upper_BJ           lower_BJ
    Pushrod     : pushrod_outboard   pushrod_inboard
    Bellcrank   : bellcrank_pivot    bellcrank_pushrod_arm  bellcrank_damper_arm
    Damper      : damper_outboard    damper_inboard

AXIS VALUES:
    0 = X (forward/backward)
    1 = Y (inboard/outboard)
    2 = Z (up/down)
"""

import copy
import os
import sys

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pandas as pd

# ── Make sure the repo root is on the path when run directly ──────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kinematics.hardpoints import HP
from kinematics.suspension  import run_travel_sweep, static_report
from kinematics.rocker      import motion_ratio_at

# ─────────────────────────────────────────────────────────────────────────────
# STYLE
# ─────────────────────────────────────────────────────────────────────────────

ACCENT = "#e8b84b"
BLUE   = "#4b9fe8"
GREEN  = "#4be87a"
RED    = "#e84b4b"
GREY   = "#888888"

plt.rcParams.update({
    "figure.facecolor": "#0f0f0f", "axes.facecolor":  "#1a1a1a",
    "axes.edgecolor":   "#444",    "axes.labelcolor": "#eee",
    "xtick.color":      "#aaa",    "ytick.color":     "#aaa",
    "text.color":       "#eee",    "grid.color":      "#333",
    "grid.linestyle":   "--",      "grid.alpha":       0.5,
    "legend.facecolor": "#222",    "legend.edgecolor": "#555",
    "font.family":      "monospace",
})

AXIS_LABEL = {0: "X  (forward +)", 1: "Y  (outboard +)", 2: "Z  (up +)"}
AXIS_NAME  = {0: "X", 1: "Y", 2: "Z"}


# ─────────────────────────────────────────────────────────────────────────────
# CORE SWEEP LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def _make_hp(base_hp: dict, point: str, axis: int, offset_mm: float) -> dict:
    """
    Return a deep copy of base_hp with one coordinate shifted by offset_mm.

    If the point is upper_BJ or lower_BJ, the matching A-arm outboard point
    is kept in sync automatically so the model stays consistent.
    """
    hp = copy.deepcopy(base_hp)
    hp[point][axis] += offset_mm

    # Keep linked points in sync
    links = {
        "upper_BJ":           "UAA_outboard",
        "UAA_outboard":       "upper_BJ",
        "lower_BJ":           "LAA_outboard",
        "LAA_outboard":       "lower_BJ",
        "bellcrank_damper_arm": "damper_outboard",
        "damper_outboard":    "bellcrank_damper_arm",
        "bellcrank_pushrod_arm": "pushrod_inboard",
        "pushrod_inboard":    "bellcrank_pushrod_arm",
    }
    if point in links:
        hp[links[point]][axis] += offset_mm

    return hp


def _extract_static_metrics(hp: dict) -> dict:
    """
    Run static_report silently and return the geometry dict.
    Also adds motion ratio at static ride height.
    """
    vals = static_report(hp, print_output=False)
    vals["motion_ratio"] = motion_ratio_at(0.0, hp)
    vals["wheel_rate_N_mm"] = None   # filled after we know spring rate
    return vals


def run_hardpoint_sweep(
    point:      str,
    axis:       int,
    range_mm:   float   = 15.0,
    steps:      int     = 11,
    base_hp:    dict    = None,
    save_dir: str = os.path.join(os.path.dirname(__file__), "results/hardpoint_sweeps"),

) -> pd.DataFrame:
    """
    Sweep one coordinate of one hardpoint and return a summary DataFrame.

    Parameters
    ──────────
    point     : hardpoint name, e.g. "upper_BJ"
    axis      : 0 = X, 1 = Y, 2 = Z
    range_mm  : sweep ± this many mm from the baseline value
    steps     : number of positions to evaluate (odd number keeps baseline centred)
    base_hp   : hardpoint dict to use as baseline. Defaults to HP from hardpoints.py.
    save_dir  : folder where plots and CSV are saved

    Returns
    ───────
    pd.DataFrame — one row per step with all static geometry metrics and
                   camber gain at static ride height.
    """
    if base_hp is None:
        base_hp = HP

    if point not in base_hp:
        valid = "\n  ".join(sorted(base_hp.keys()))
        raise ValueError(
            f"'{point}' is not a valid hardpoint name.\nValid names:\n  {valid}"
        )
    if axis not in (0, 1, 2):
        raise ValueError("axis must be 0 (X), 1 (Y), or 2 (Z)")

    os.makedirs(save_dir, exist_ok=True)

    baseline_val = float(base_hp[point][axis])
    offsets      = np.linspace(-range_mm, range_mm, steps)
    axis_label   = AXIS_LABEL[axis]
    axis_name    = AXIS_NAME[axis]

    print(f"\n{'─'*55}")
    print(f"  HARDPOINT SWEEP")
    print(f"  Point : {point}")
    print(f"  Axis  : {axis_name}  ({axis_label})")
    print(f"  Range : {baseline_val - range_mm:.1f} → {baseline_val + range_mm:.1f} mm"
          f"  ({steps} steps)")
    print(f"{'─'*55}")

    # ── Collect results ───────────────────────────────────────────────────────
    travel_dfs   = {}   # keyed by offset value
    static_rows  = []

    for off in offsets:
        hp_mod  = _make_hp(base_hp, point, axis, off)
        abs_val = baseline_val + off

        # Travel sweep for overlay plots
        df_travel = run_travel_sweep(hp_mod)
        travel_dfs[off] = df_travel

        # Static metrics
        s = _extract_static_metrics(hp_mod)
        # Camber gain at static (°/100mm)
        camber_gain_static = float(
            np.gradient(df_travel["camber_deg"].values,
                        df_travel["travel_mm"].values)[len(df_travel)//2]
        ) * 100.0   # convert to °/100mm

        static_rows.append({
            f"{axis_name}_offset_mm":  round(off, 3),
            f"{axis_name}_absolute_mm": round(abs_val, 3),
            "camber_deg":              round(s["camber_deg"],  4),
            "caster_deg":              round(s["caster_deg"],  4),
            "kpi_deg":                 round(s["kpi_deg"],     4),
            "toe_deg":                 round(s["toe_deg"],     4),
            "scrub_mm":                round(s["scrub_mm"],    4),
            "trail_mm":                round(s["trail_mm"],    4),
            "arm_ratio":               round(s["arm_ratio"],   4),
            "camber_gain_deg_100mm":   round(camber_gain_static, 4),
            "motion_ratio":            round(s["motion_ratio"], 4),
        })

        marker = " ← baseline" if abs(off) < 1e-6 else ""
        print(f"  {axis_name} = {abs_val:+8.2f} mm  |  "
              f"camber {s['camber_deg']:+.3f}°  "
              f"caster {s['caster_deg']:+.3f}°  "
              f"scrub {s['scrub_mm']:+.2f} mm{marker}")

    summary_df = pd.DataFrame(static_rows)

    # ── Save CSV ──────────────────────────────────────────────────────────────
    csv_name = f"{point}_{axis_name}_sweep.csv"
    summary_df.to_csv(os.path.join(save_dir, csv_name), index=False)
    print(f"\n  CSV saved → {os.path.join(save_dir, csv_name)}")

    # ── Overlay plots ─────────────────────────────────────────────────────────
    _plot_overlay(
        travel_dfs, offsets, baseline_val, point, axis_name, axis_label, save_dir
    )

    # ── Static metrics plot ───────────────────────────────────────────────────
    _plot_static_metrics(summary_df, point, axis_name, axis_label, baseline_val, save_dir)

    # ── Ranked results table ──────────────────────────────────────────────────
    _print_ranked_table(summary_df, axis_name)

    return summary_df


# ─────────────────────────────────────────────────────────────────────────────
# PLOTTING
# ─────────────────────────────────────────────────────────────────────────────

def _plot_overlay(
    travel_dfs: dict,
    offsets: np.ndarray,
    baseline_val: float,
    point: str,
    axis_name: str,
    axis_label: str,
    save_dir: str,
) -> None:
    """6-panel overlay: kinematic metrics vs wheel travel, one curve per offset."""

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle(
        f"Hardpoint Sweep — {point}  [{axis_label}]",
        fontsize=13, color=ACCENT, fontweight="bold"
    )

    metrics = [
        ("camber_deg",      "Camber (°)",          ACCENT,  axes[0, 0]),
        ("caster_deg",      "Caster (°)",           BLUE,   axes[0, 1]),
        ("kpi_deg",         "KPI (°)",              GREEN,  axes[0, 2]),
        ("toe_deg",         "Toe (°)",              RED,    axes[1, 0]),
        ("scrub_mm",        "Scrub Radius (mm)",    ACCENT, axes[1, 1]),
        ("track_change_mm", "Track Change (mm)",    BLUE,   axes[1, 2]),
    ]

    cmap = plt.get_cmap("plasma", len(offsets))

    for col, ylabel, color, ax in metrics:
        for i, (off, df) in enumerate(travel_dfs.items()):
            is_baseline = abs(off) < 1e-6
            lw    = 2.5  if is_baseline else 1.0
            ls    = "-"  if is_baseline else "--"
            label = f"baseline" if is_baseline else f"{off:+.1f}mm"
            c     = "white" if is_baseline else cmap(i)
            ax.plot(df["travel_mm"], df[col], color=c, lw=lw, ls=ls, label=label)

        ax.axhline(0, color="#444", lw=0.8, ls=":")
        ax.axvline(0, color="#444", lw=0.8, ls=":")
        ax.set_xlabel("Wheel Travel (mm)")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel, color=color)
        ax.grid(True)

        # Only show legend on first panel to avoid clutter
        if col == "camber_deg":
            ax.legend(fontsize=6, ncol=2, loc="best")

    plt.tight_layout()
    fname = os.path.join(save_dir, f"{point}_{axis_name}_overlay.png")
    fig.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Overlay plot saved → {fname}")


def _plot_static_metrics(
    df: pd.DataFrame,
    point: str,
    axis_name: str,
    axis_label: str,
    baseline_val: float,
    save_dir: str,
) -> None:
    """
    6-panel plot of static geometry metrics vs the swept coordinate value.
    Each panel shows how one metric changes as the hardpoint moves.
    """
    x_col  = f"{axis_name}_absolute_mm"
    x_vals = df[x_col]

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle(
        f"Static Geometry vs {point}  [{axis_label}]",
        fontsize=13, color=ACCENT, fontweight="bold"
    )

    panels = [
        ("camber_deg",            "Static Camber (°)",         ACCENT, axes[0, 0]),
        ("caster_deg",            "Static Caster (°)",          BLUE,  axes[0, 1]),
        ("kpi_deg",               "Static KPI (°)",             GREEN, axes[0, 2]),
        ("scrub_mm",              "Scrub Radius (mm)",          RED,   axes[1, 0]),
        ("camber_gain_deg_100mm", "Camber Gain (°/100mm)",      ACCENT,axes[1, 1]),
        ("motion_ratio",          "Motion Ratio",               BLUE,  axes[1, 2]),
    ]

    for col, ylabel, color, ax in panels:
        if col not in df.columns:
            ax.set_visible(False)
            continue

        ax.plot(x_vals, df[col], color=color, lw=2, marker="o", markersize=4)

        # Mark baseline
        ax.axvline(baseline_val, color="white", lw=1.0, ls="--", alpha=0.6,
                   label="baseline")

        # Shade FSAE target ranges where applicable
        target_ranges = {
            "camber_deg":            (-2.0,  0.0),
            "caster_deg":            ( 3.0,  8.0),
            "kpi_deg":               ( 8.0, 14.0),
            "scrub_mm":              ( 0.0, 25.0),
            "camber_gain_deg_100mm": (-1.5, -0.5),
        }
        if col in target_ranges:
            lo, hi = target_ranges[col]
            ax.axhspan(lo, hi, color=GREEN, alpha=0.08, label="FSAE target")
            ax.legend(fontsize=7)

        ax.set_xlabel(f"{point}  {axis_name} position (mm)")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel, color=color)
        ax.grid(True)

    plt.tight_layout()
    fname = os.path.join(save_dir, f"{point}_{axis_name}_static.png")
    fig.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Static metrics plot saved → {fname}")


def _print_ranked_table(df: pd.DataFrame, axis_name: str) -> None:
    """
    Print a ranked summary table sorted by how well each position hits
    FSAE target ranges across all metrics simultaneously.

    Scoring: each metric that falls inside its target range scores 1 point.
    Higher score = more metrics simultaneously in range.
    """
    targets = {
        "camber_deg":            (-2.0,  0.0),
        "caster_deg":            ( 3.0,  8.0),
        "kpi_deg":               ( 8.0, 14.0),
        "toe_deg":               (-0.5,  0.5),
        "scrub_mm":              ( 0.0, 25.0),
        "trail_mm":              (10.0, 40.0),
        "camber_gain_deg_100mm": (-1.5, -0.5),
    }

    scores = []
    for _, row in df.iterrows():
        score = sum(
            1 for col, (lo, hi) in targets.items()
            if col in df.columns and lo <= row[col] <= hi
        )
        scores.append(score)

    df = df.copy()
    df["score"] = scores
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df.index += 1

    offset_col = f"{axis_name}_offset_mm"
    abs_col    = f"{axis_name}_absolute_mm"

    print(f"\n{'─'*70}")
    print(f"  RANKED RESULTS  (score = metrics simultaneously in FSAE target range)")
    print(f"{'─'*70}")
    print(f"  {'Rank':>4}  {offset_col:>14}  {abs_col:>14}  "
          f"{'camber':>8}  {'caster':>8}  {'scrub':>8}  {'score':>6}")
    print(f"  {'─'*4}  {'─'*14}  {'─'*14}  "
          f"{'─'*8}  {'─'*8}  {'─'*8}  {'─'*6}")

    for rank, row in df.iterrows():
        marker = " ◀ best" if rank == 1 else ""
        print(
            f"  {rank:>4}  {row[offset_col]:>+14.2f}  {row[abs_col]:>14.2f}  "
            f"{row['camber_deg']:>+8.3f}  {row['caster_deg']:>+8.3f}  "
            f"{row['scrub_mm']:>+8.2f}  {row['score']:>6}{marker}"
        )

    print(f"{'─'*70}")
    best = df.iloc[0]
    print(f"\n  Best position: {axis_name} = {best[abs_col]:.2f} mm "
          f"(offset {best[offset_col]:+.2f} mm from baseline)")
    print(f"  Hits {best['score']} of {len(targets)} target ranges simultaneously.")


# ─────────────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION — edit these four values, then run:  uv run sweep/hardpoint_sweep.py
# ══════════════════════════════════════════════════════════════════════════════
# ─────────────────────────────────────────────────────────────────────────────

POINT   = "upper_BJ"   # which hardpoint to move
AXIS    = 2            # 0 = X (fwd/back), 1 = Y (in/out), 2 = Z (up/down)
RANGE   = 15.0         # mm either side of baseline
STEPS   = 11           # number of steps (odd = baseline is included exactly)

# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = run_hardpoint_sweep(
        point    = POINT,
        axis     = AXIS,
        range_mm = RANGE,
        steps    = STEPS,
    )
