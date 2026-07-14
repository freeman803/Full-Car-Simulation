
import numpy as np
import matplotlib.pyplot as plt
from kinematics.quarter_car import natural_frequencies, simulate_sine, simulate_step
from kinematics.hardpoints import HP, DAMPER_RATE, SPRUNG_MASS, UNSPRUNG_MASS, TYRE_STIFFNESS
from sweep.run_sweep import run_sweep, plot_sweep



def freq_from_spring_rate(spring_rate, **kwargs):
    return natural_frequencies(
        spring_rate    = spring_rate,
        damper_rate    = DAMPER_RATE,
        sprung_mass    = SPRUNG_MASS,
        unsprung_mass  = UNSPRUNG_MASS,
        tyre_stiffness = TYRE_STIFFNESS,
        hp             = HP,
    )

results = run_sweep(
    param_name      = "Spring Rate (N/mm)",
    param_values    = np.linspace(20.0, 60.0, 11),
    simulate_fn     = freq_from_spring_rate,
    metric_fn       = lambda result: result["f_ride_hz"],
    keyword         = "spring_rate",
)

plot_sweep(results, "Spring Rate (N/mm)", "Ride Frequency (Hz)",
           save_path="results/sweep_spring_rate_ride_freq.png")

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
