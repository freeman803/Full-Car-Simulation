
"""
Quarter-Car-Model.py — FSAE Corner Model entry point.

Run with:  uv run main.py

Produces all plots and saves results to the results/ folder.
Edit kinematics/hardpoints.py to update your car's geometry and rates.
"""

import os
import numpy as np
import matplotlib.pyplot as plt

from kinematics.hardpoints import HP, SPRING_RATE, DAMPER_RATE
from kinematics.suspension  import static_report, run_travel_sweep
from kinematics.rocker      import motion_ratio_sweep, motion_ratio_report
from kinematics.quarter_car import (
    simulate_step,
    simulate_sine,
    frequency_sweep,
    natural_frequencies,
)
from kinematics.plots import (
    apply_style,
    plot_wheel_travel,
    plot_camber_gain,
    plot_motion_ratio,
    plot_step_response,
    plot_sine_response,
    plot_frequency_response,
    plot_3d_corner,
)

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

RESULTS_DIR   = "results"
SHOW_PLOTS    = True    # set False to just save without opening windows
SINE_FREQ_HZ  = 2.0    # frequency for sinusoidal road input
STEP_AMP_MM   = 25.0   # step bump amplitude
SINE_AMP_MM   = 15.0   # sinusoidal road amplitude

os.makedirs(RESULTS_DIR, exist_ok=True)


def save(fig: plt.Figure, name: str) -> None:
    path = os.path.join(RESULTS_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Saved → {path}")
    if not SHOW_PLOTS:
        plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    apply_style()

    # ── 1. Static geometry ────────────────────────────────────────
    print("\n── STATIC GEOMETRY ─────────────────────────────────────")
    static_report(HP)

    # ── 2. Wheel travel sweep ─────────────────────────────────────
    print("\n── WHEEL TRAVEL SWEEP ──────────────────────────────────")
    df_travel = run_travel_sweep(HP)
    df_travel.to_csv(os.path.join(RESULTS_DIR, "kinematics_travel.csv"), index=False)
    print(f"  Travel sweep: {len(df_travel)} points")

    fig = plot_wheel_travel(df_travel)
    save(fig, "wheel_travel.png")

    fig = plot_camber_gain(df_travel)
    save(fig, "camber_gain.png")

    # ── 3. Motion ratio ───────────────────────────────────────────
    print("\n── MOTION RATIO ────────────────────────────────────────")
    motion_ratio_report(HP)
    df_mr = motion_ratio_sweep(HP)
    df_mr.to_csv(os.path.join(RESULTS_DIR, "motion_ratio.csv"), index=False)

    fig = plot_motion_ratio(df_mr)
    save(fig, "motion_ratio.png")

    # ── 4. 3D corner layout ───────────────────────────────────────
    print("\n── 3D CORNER LAYOUT ────────────────────────────────────")
    fig = plot_3d_corner(HP)
    save(fig, "corner_3d.png")

    # ── 5. Natural frequencies ────────────────────────────────────
    print("\n── NATURAL FREQUENCIES ─────────────────────────────────")
    natural_frequencies()

    # ── 6. Step response ─────────────────────────────────────────
    print("\n── STEP BUMP RESPONSE ──────────────────────────────────")
    df_step = simulate_step(amplitude_mm=STEP_AMP_MM)
    df_step.to_csv(os.path.join(RESULTS_DIR, "step_response.csv"), index=False)
    print(f"  Peak body accel : {df_step['accel_sprung_g'].abs().max():.4f} g")
    print(f"  Peak susp travel: {df_step['susp_travel_mm'].abs().max():.2f} mm")

    fig = plot_step_response(df_step)
    save(fig, "step_response.png")

    # ── 7. Sinusoidal response ────────────────────────────────────
    print(f"\n── SINUSOIDAL RESPONSE @ {SINE_FREQ_HZ} Hz ──────────────────────")
    df_sine = simulate_sine(amplitude_mm=SINE_AMP_MM, frequency_hz=SINE_FREQ_HZ)
    df_sine.to_csv(os.path.join(RESULTS_DIR, "sine_response.csv"), index=False)

    fig = plot_sine_response(df_sine, SINE_FREQ_HZ)
    save(fig, "sine_response.png")

    # ── 8. Frequency response ─────────────────────────────────────
    print("\n── FREQUENCY SWEEP (this takes ~20s) ───────────────────")
    df_freq = frequency_sweep(frequencies=np.logspace(np.log10(0.3), np.log10(25.0), 35))
    df_freq.to_csv(os.path.join(RESULTS_DIR, "frequency_response.csv"), index=False)
    peak_f = df_freq.loc[df_freq["transmissibility"].idxmax(), "freq_hz"]
    print(f"  Peak transmissibility at: {peak_f:.2f} Hz")

    fig = plot_frequency_response(df_freq)
    save(fig, "frequency_response.png")

    # ── Done ──────────────────────────────────────────────────────
    print(f"\n✅ All outputs saved to ./{RESULTS_DIR}/")
    if SHOW_PLOTS:
        plt.show()


if __name__ == "__main__":
    main()
