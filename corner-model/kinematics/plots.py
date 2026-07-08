"""
plots.py — All plotting functions for the FSAE corner model.

Call apply_style() once at the top of main.py before any plots.
All plot functions return the matplotlib Figure so callers can save or show them.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# ─────────────────────────────────────────────────────────────────────────────
# Style
# ─────────────────────────────────────────────────────────────────────────────

ACCENT = "#e8b84b"
BLUE   = "#4b9fe8"
GREEN  = "#4be87a"
RED    = "#e84b4b"
GREY   = "#888888"


def apply_style() -> None:
    """Apply dark FSAE theme to all subsequent matplotlib figures."""
    plt.rcParams.update({
        "figure.facecolor":  "#0f0f0f",
        "axes.facecolor":    "#1a1a1a",
        "axes.edgecolor":    "#444",
        "axes.labelcolor":   "#eee",
        "xtick.color":       "#aaa",
        "ytick.color":       "#aaa",
        "text.color":        "#eee",
        "grid.color":        "#333",
        "grid.linestyle":    "--",
        "grid.alpha":        0.5,
        "legend.facecolor":  "#222",
        "legend.edgecolor":  "#555",
        "font.family":       "monospace",
    })


def _zero_lines(ax) -> None:
    ax.axhline(0, color="#555", lw=0.8, ls=":")
    ax.axvline(0, color="#555", lw=0.8, ls=":")


# ─────────────────────────────────────────────────────────────────────────────
# Wheel travel kinematics
# ─────────────────────────────────────────────────────────────────────────────

def plot_wheel_travel(df: pd.DataFrame) -> plt.Figure:
    """6-panel plot of all kinematic metrics vs wheel travel."""
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle("FSAE Corner — Wheel Travel Kinematics", fontsize=14,
                 color=ACCENT, fontweight="bold")

    specs = [
        ("camber_deg",       "Camber (°)",          ACCENT,  axes[0, 0]),
        ("caster_deg",       "Caster (°)",           BLUE,   axes[0, 1]),
        ("kpi_deg",          "KPI (°)",              GREEN,  axes[0, 2]),
        ("toe_deg",          "Toe (°)",              RED,    axes[1, 0]),
        ("scrub_mm",         "Scrub Radius (mm)",    ACCENT, axes[1, 1]),
        ("track_change_mm",  "Track Change (mm)",    BLUE,   axes[1, 2]),
    ]

    for col, ylabel, color, ax in specs:
        ax.plot(df["travel_mm"], df[col], color=color, lw=2)
        _zero_lines(ax)
        ax.set_xlabel("Wheel Travel (mm)")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel, color=color)
        ax.grid(True)
        static_val = df.loc[df["travel_mm"].abs() < 0.1, col].values[0]
        ax.scatter([0], [static_val], color="white", s=60, zorder=5)
        ax.annotate(f"{static_val:.2f}", xy=(0, static_val),
                    xytext=(8, 8), textcoords="offset points",
                    color="white", fontsize=8)

    plt.tight_layout()
    return fig


def plot_camber_gain(df: pd.DataFrame) -> plt.Figure:
    """Camber and camber gain rate vs wheel travel."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Camber Gain Analysis", fontsize=13, color=ACCENT, fontweight="bold")

    ax1.plot(df["travel_mm"], df["camber_deg"], color=ACCENT, lw=2)
    _zero_lines(ax1)
    ax1.set_xlabel("Wheel Travel (mm)")
    ax1.set_ylabel("Camber (°)")
    ax1.set_title("Camber vs Travel", color=ACCENT)
    ax1.grid(True)

    gain = df["camber_gain"] * 1000  # °/m
    ax2.plot(df["travel_mm"], gain, color=GREEN, lw=2)
    ax2.axvline(0, color="#555", lw=0.8, ls=":")
    ax2.set_xlabel("Wheel Travel (mm)")
    ax2.set_ylabel("Camber Gain (°/m)")
    ax2.set_title("Camber Gain Rate", color=GREEN)
    ax2.grid(True)
    static_gain = df.loc[df["travel_mm"].abs() < 0.1, "camber_gain"].values[0] * 1000
    ax2.annotate(f"Static: {static_gain:.2f}°/m",
                 xy=(0, static_gain), xytext=(10, 10),
                 textcoords="offset points", color="white", fontsize=9,
                 arrowprops=dict(arrowstyle="->", color="white"))

    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Motion ratio / rocker
# ─────────────────────────────────────────────────────────────────────────────

def plot_motion_ratio(df_mr: pd.DataFrame) -> plt.Figure:
    """4-panel plot of motion ratio, damper displacement, wheel rate, bellcrank rotation."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("Pushrod / Bellcrank — Motion Ratio Analysis", fontsize=13,
                 color=ACCENT, fontweight="bold")

    specs = [
        ("motion_ratio",      "Motion Ratio",          ACCENT, axes[0, 0]),
        ("damper_disp_mm",    "Damper Displacement (mm)", BLUE, axes[0, 1]),
        ("wheel_rate_N_mm",   "Wheel Rate (N/mm)",      GREEN, axes[1, 0]),
        ("bellcrank_rot_deg", "Bellcrank Rotation (°)",  RED,  axes[1, 1]),
    ]

    for col, ylabel, color, ax in specs:
        ax.plot(df_mr["travel_mm"], df_mr[col], color=color, lw=2)
        _zero_lines(ax)
        ax.set_xlabel("Wheel Travel (mm)")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel, color=color)
        ax.grid(True)
        static = df_mr.loc[df_mr["travel_mm"].abs() < 0.1, col].values[0]
        ax.scatter([0], [static], color="white", s=60, zorder=5)
        ax.annotate(f"{static:.3f}", xy=(0, static),
                    xytext=(8, 8), textcoords="offset points",
                    color="white", fontsize=8)

    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Quarter car time response
# ─────────────────────────────────────────────────────────────────────────────

def plot_step_response(df: pd.DataFrame) -> plt.Figure:
    """Time-domain response to step bump input."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("Quarter Car — Step Bump Response", fontsize=13,
                 color=ACCENT, fontweight="bold")

    t = df["time_s"]

    # Displacement
    ax = axes[0, 0]
    ax.plot(t, df["road_mm"],       color=GREY,  lw=1.5, ls="--", label="Road input")
    ax.plot(t, df["z_sprung_mm"],   color=ACCENT, lw=2,            label="Sprung mass")
    ax.plot(t, df["z_unsprung_mm"], color=BLUE,  lw=1.5,           label="Unsprung mass")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Displacement (mm)")
    ax.set_title("Displacement", color=ACCENT)
    ax.legend(fontsize=8)
    ax.grid(True)

    # Suspension travel
    ax = axes[0, 1]
    ax.plot(t, df["susp_travel_mm"], color=GREEN, lw=2)
    ax.axhline(0, color="#555", lw=0.8, ls=":")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Suspension Travel (mm)")
    ax.set_title("Suspension Travel (z_u − z_s)", color=GREEN)
    ax.grid(True)

    # Body acceleration
    ax = axes[1, 0]
    ax.plot(t, df["accel_sprung_g"], color=RED, lw=2)
    ax.axhline(0, color="#555", lw=0.8, ls=":")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Body Acceleration (g)")
    ax.set_title("Sprung Mass Acceleration", color=RED)
    ax.grid(True)

    # Motion ratio over time
    ax = axes[1, 1]
    ax.plot(t, df["motion_ratio"], color=BLUE, lw=2)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Motion Ratio")
    ax.set_title("Instantaneous Motion Ratio", color=BLUE)
    ax.grid(True)

    plt.tight_layout()
    return fig


def plot_sine_response(df: pd.DataFrame, freq_hz: float) -> plt.Figure:
    """Time-domain response to sinusoidal road input."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(f"Quarter Car — Sinusoidal Response @ {freq_hz:.1f} Hz",
                 fontsize=13, color=ACCENT, fontweight="bold")

    t = df["time_s"]

    ax = axes[0, 0]
    ax.plot(t, df["road_mm"],       color=GREY,  lw=1.5, ls="--", label="Road")
    ax.plot(t, df["z_sprung_mm"],   color=ACCENT, lw=2,            label="Body")
    ax.plot(t, df["z_unsprung_mm"], color=BLUE,  lw=1.5,           label="Wheel")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Displacement (mm)")
    ax.set_title("Displacement", color=ACCENT)
    ax.legend(fontsize=8)
    ax.grid(True)

    ax = axes[0, 1]
    ax.plot(t, df["vel_sprung_mm_s"],   color=ACCENT, lw=2, label="Body vel")
    ax.plot(t, df["vel_unsprung_mm_s"], color=BLUE,  lw=1.5, label="Wheel vel")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Velocity (mm/s)")
    ax.set_title("Velocity", color=BLUE)
    ax.legend(fontsize=8)
    ax.grid(True)

    ax = axes[1, 0]
    ax.plot(t, df["accel_sprung_g"], color=RED, lw=2)
    ax.axhline(0, color="#555", lw=0.8, ls=":")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Body Acceleration (g)")
    ax.set_title("Sprung Mass Acceleration", color=RED)
    ax.grid(True)

    ax = axes[1, 1]
    ax.plot(t, df["susp_travel_mm"], color=GREEN, lw=2)
    ax.axhline(0, color="#555", lw=0.8, ls=":")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Suspension Travel (mm)")
    ax.set_title("Suspension Travel", color=GREEN)
    ax.grid(True)

    plt.tight_layout()
    return fig


def plot_frequency_response(df_freq: pd.DataFrame) -> plt.Figure:
    """Bode-style transmissibility and phase plot."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
    fig.suptitle("Quarter Car — Frequency Response (Transmissibility)",
                 fontsize=13, color=ACCENT, fontweight="bold")

    freqs = df_freq["freq_hz"]
    trans = df_freq["transmissibility"]
    phase = df_freq["phase_deg"]

    ax1.semilogx(freqs, trans, color=ACCENT, lw=2)
    ax1.axhline(1.0, color="#555", lw=0.8, ls="--", label="Unity (no isolation)")
    ax1.axhline(np.sqrt(2), color=RED, lw=0.8, ls="--", label="√2 amplification")
    ax1.set_ylabel("Transmissibility  z_body / z_road")
    ax1.set_title("Transmissibility", color=ACCENT)
    ax1.legend(fontsize=8)
    ax1.grid(True, which="both")
    ax1.set_ylim(bottom=0)

    # Mark natural frequency peaks
    peak_idx = trans.idxmax()
    ax1.scatter([freqs[peak_idx]], [trans[peak_idx]], color="white", s=80, zorder=5)
    ax1.annotate(f"Peak: {freqs[peak_idx]:.2f} Hz",
                 xy=(freqs[peak_idx], trans[peak_idx]),
                 xytext=(10, -20), textcoords="offset points",
                 color="white", fontsize=8,
                 arrowprops=dict(arrowstyle="->", color="white"))

    ax2.semilogx(freqs, phase, color=BLUE, lw=2)
    ax2.axhline(0,    color="#555", lw=0.8, ls=":")
    ax2.axhline(-90,  color="#444", lw=0.8, ls="--")
    ax2.axhline(-180, color="#444", lw=0.8, ls="--")
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Phase (°)")
    ax2.set_title("Phase", color=BLUE)
    ax2.grid(True, which="both")

    plt.tight_layout()
    return fig


def plot_3d_corner(hp: dict) -> plt.Figure:
    """3D visualisation of the full corner including pushrod and bellcrank."""
    fig = plt.figure(figsize=(13, 9))
    ax  = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#0f0f0f")

    def _arm(p1, p2, p_out, color, label):
        ax.plot([p1[0], p_out[0]], [p1[1], p_out[1]], [p1[2], p_out[2]], color=color, lw=2)
        ax.plot([p2[0], p_out[0]], [p2[1], p_out[1]], [p2[2], p_out[2]], color=color, lw=2,
                label=label)

    def _link(p1, p2, color, label, lw=2, ls="-"):
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                color=color, lw=lw, ls=ls, label=label)

    _arm(hp["UAA_front_inboard"], hp["UAA_rear_inboard"], hp["UAA_outboard"], ACCENT, "Upper A-arm")
    _arm(hp["LAA_front_inboard"], hp["LAA_rear_inboard"], hp["LAA_outboard"], BLUE,   "Lower A-arm")
    _link(hp["tie_rod_inboard"],    hp["tie_rod_outboard"],    GREEN,  "Tie rod")
    _link(hp["upper_BJ"],           hp["lower_BJ"],            RED,    "KPI axis",   lw=3, ls="--")
    _link(hp["pushrod_outboard"],   hp["pushrod_inboard"],     ACCENT, "Pushrod",    lw=2)
    _link(hp["bellcrank_pushrod_arm"], hp["bellcrank_pivot"],  "#ff9f43", "Bellcrank", lw=3)
    _link(hp["bellcrank_pivot"],    hp["bellcrank_damper_arm"],"#ff9f43", None,         lw=3)
    _link(hp["damper_outboard"],    hp["damper_inboard"],      "#a29bfe", "Damper",   lw=2)

    # Scatter all hardpoints
    for name, pt in hp.items():
        ax.scatter(*pt, color="white", s=30, zorder=5)

    # Bellcrank pivot marker
    piv = hp["bellcrank_pivot"]
    ax.scatter(*piv, color="#ff9f43", s=100, zorder=6, marker="D")

    # Ground plane
    xx, yy = np.meshgrid([-200, 200], [50, 400])
    ax.plot_surface(xx, yy, np.zeros_like(xx), alpha=0.06, color="white")

    ax.set_xlabel("X (fwd)", color="#aaa")
    ax.set_ylabel("Y (left)", color="#aaa")
    ax.set_zlabel("Z (up)", color="#aaa")
    ax.tick_params(colors="#666", labelsize=7)
    ax.set_title("LF Corner — Full Corner 3D Layout (Pushrod/Bellcrank/Damper)",
                 color=ACCENT, fontsize=11)

    # Deduplicate legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc="upper left", fontsize=8)

    plt.tight_layout()
    return fig
