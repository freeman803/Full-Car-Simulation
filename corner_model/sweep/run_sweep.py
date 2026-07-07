#run_sweep.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from kinematics.quarter_car import simulate_step, simulate_sine

def run_sweep(
    param_name,        # what to call it in the results (e.g. "Spring Rate (N/mm)")
    param_values,      # the list of values to try
    simulate_fn,       # which simulation to use (simulate_step or simulate_sine)
    metric_fn,         # a function that takes a result df and returns one number
    keyword,           # the exact keyword argument name in the simulate function
    simulate_kwargs=None,   # any other fixed settings you want to pass
):
    """
    Run a parameter sweep and return a results DataFrame.

    param_name      : label used in plots and output
    param_values    : array of values to sweep (from np.linspace or np.arange)
    simulate_fn     : simulate_step or simulate_sine
    metric_fn       : function(df) -> float, e.g. lambda df: df["accel_sprung_g"].abs().max()
    keyword         : the argument name to pass the value to, e.g. "spring_rate"
    simulate_kwargs : dict of any other fixed arguments, e.g. {"t_span": (0.0, 3.0)}
    """
    if simulate_kwargs is None:
        simulate_kwargs = {}

    rows = []
    for value in param_values:
        # Build the call with the swept parameter injected
        kwargs = {**simulate_kwargs, keyword: value}
        df     = simulate_fn(**kwargs)
        metric = metric_fn(df)
        rows.append({"param_value": value, "metric": metric})
        print(f"  {param_name} = {value:.2f}  →  result = {metric:.4f}")

    return pd.DataFrame(rows)


def plot_sweep(results_df, param_name, metric_name, save_path=None):
    """Plot the results of a run_sweep() call."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(results_df["param_value"], results_df["metric"],
            color="#e8b84b", lw=2, marker="o", markersize=5)
    ax.set_xlabel(param_name)
    ax.set_ylabel(metric_name)
    ax.set_title(f"{metric_name} vs {param_name}")
    ax.grid(True)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig