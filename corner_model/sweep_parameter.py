 # sweep.py

import numpy as np
import matplotlib.pyplot as plt
from sweep.run_sweep import run_sweep, plot_sweep
from kinematics.quarter_car import simulate_sine

if __name__ == "__main__":
    results = run_sweep(
        param_name="Spring rate (n/mm)",
        param_values=np.linspace(26, 105, 20),
        simulate_fn=simulate_sine,
        metric_fn=lambda df: float(np.sqrt(np.mean(df["accel_sprung_g"] ** 2))),
        keyword="spring_rate",
        simulate_kwargs={"amplitude_mm": 15.0, "frequency_hz": 2.0},
    )
    plot_sweep(
        results,
        "Spring rate (N/mm)",
        "RMS Body Acceleration (g)",
        save_path="corner_model/results/sweep_spring_rate.png",
    )
    plt.show(),
