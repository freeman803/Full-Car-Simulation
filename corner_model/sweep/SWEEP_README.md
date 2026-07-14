# Sweep Tools — User Guide

This guide explains how to use the parameter sweep tools to study how changes to the car's geometry and setup affect its behaviour. You only ever change a few numbers at the top of a file.

---

## What a sweep is

A sweep runs the simulation many times in a row, changing one value each time, and collects all the results so you can compare them side by side. For example, a spring rate sweep runs the step bump simulation at ten different spring rates and shows you how the body acceleration changes across all of them on a single plot.

This lets you answer questions like:
- What happens to camber gain if I move the upper ball joint 10mm higher?
- How does peak suspension travel change as I increase the damper rate?
- Which position for the tie rod outboard point gives me the best combination of geometry targets?

---

## The two sweep tools

There are two separate scripts in the `corner_model/` folder:

| Script | What it sweeps | When to use it |
|--------|---------------|----------------|
| `corner_model/hardpoint_sweep.py` | One hardpoint coordinate (X, Y, or Z) | Optimising suspension geometry |
| `corner_model/sweep_parameter.py` | Spring rate, damper rate, mass, tyre stiffness | Optimising setup and dynamics |

Both follow the same procedure: edit a small config block at the bottom of the file, save, and run.

IMPORTANT: Run these from the project root (Full-Car-Simulation>) as follows: uv run corner_model/sweep_parameter.py or uv run corner_model/hardpoint_sweep.py

---

## Tool 1 — Hardpoint sweep

### What it does

Moves one hardpoint (e.g. the upper ball joint) in one direction (e.g. up and down) across a small range, runs the full kinematic analysis at each position, and shows you how your geometry metrics respond.

### The four settings to change

Open `corner_model/hardpoint_sweep.py` and scroll to the very bottom. You will see:

```python
POINT   = "upper_BJ"   # which hardpoint to move
AXIS    = 2            # 0 = X, 1 = Y, 2 = Z
RANGE   = 15.0         # mm either side of baseline
STEPS   = 11           # how many positions to try
```

**POINT** — the name of the hardpoint you want to move. Copy the name exactly from the list below, including capitalisation:

```
Upper A-arm:   UAA_front_inboard    UAA_rear_inboard    UAA_outboard
Lower A-arm:   LAA_front_inboard    LAA_rear_inboard    LAA_outboard
Steering:      tie_rod_inboard      tie_rod_outboard
Ball joints:   upper_BJ             lower_BJ
Pushrod:       pushrod_outboard     pushrod_inboard
Bellcrank:     bellcrank_pivot      bellcrank_pushrod_arm    bellcrank_damper_arm
Damper:        damper_outboard      damper_inboard
```

**AXIS** — which direction to move it:
- `0` = X — forward and backward along the car
- `1` = Y — inboard and outboard (side to side)
- `2` = Z — up and down

**RANGE** — how far either side of the baseline position to sweep, in mm. A value of `15.0` means the point will be tested from 15mm below its current position to 15mm above it.

**STEPS** — how many positions to test across that range. `11` is a good default — it gives you the baseline in the middle plus 5 positions either side. More steps gives smoother plots but takes longer to run.

### Example — sweep the upper ball joint up and down

```python
POINT   = "upper_BJ"
AXIS    = 2            # Z = up/down
RANGE   = 15.0         # test ±15mm from current position
STEPS   = 11
```

### Example — sweep the tie rod outboard point inboard and outboard

```python
POINT   = "tie_rod_outboard"
AXIS    = 1            # Y = inboard/outboard
RANGE   = 10.0
STEPS   = 9
```

### How to run it

Open the VS Code terminal (`Ctrl+~`) and run:

```
uv run sweep/hardpoint_sweep.py
```

### What you get

Three outputs, all saved to `results/hardpoint_sweeps/`:

**Overlay plot** (`_overlay.png`) — the standard 6-panel kinematic plot with one curve per hardpoint position. The baseline is shown as a solid white line. All other positions are shown as coloured dashed lines so you can see exactly how each metric shifts as the point moves.

**Static metrics plot** (`_static.png`) — 6 panels each showing one geometry value (camber, caster, KPI, scrub radius, camber gain, motion ratio) plotted against the hardpoint position. A green shaded band shows the FSAE target range for that metric. This makes it easy to read off which position satisfies your targets.

**Ranked results table** — printed in the terminal and saved as a CSV file. Every position is scored by how many geometry metrics fall inside their FSAE target range at the same time. The best position is marked with a ◀ symbol.

### How to edit the FSAE target ranges

The green shading on the static metrics plot and the scoring in the ranked table both use target ranges that you can change to match your car's specific design targets.

Find the `target_ranges` dict inside `_plot_static_metrics` (around line 150) and the `targets` dict inside `_print_ranked_table` (around line 190). Both look like this:

```python
target_ranges = {
    "camber_deg":  (-2.0,  0.0),   # (lower limit, upper limit)
    "caster_deg":  ( 3.0,  8.0),
    "kpi_deg":     ( 8.0, 14.0),
    ...
}
```

Change the numbers in brackets to your targets. Make sure to update both dicts so the plot shading and the ranking agree with each other.

---

## Tool 2 — Setup parameter sweep

### What it does

Runs the quarter car dynamic simulation (step bump or sine road input) at many different values of a setup parameter and shows you how the car's dynamic response changes.

### The five settings to change

Open `corner_model/sweep_parameter.py` and look for the configuration block. The five things you set each time are:

**param_name** — a label that appears on the plot axis. Write whatever is clear to you, for example `"Spring Rate (N/mm)"`.

**param_values** — the list of values to test. You define this using `np.linspace(start, end, number_of_steps)`:

```python
np.linspace(20.0, 60.0, 9)   # 9 evenly spaced values from 20 to 60
```

**simulate_fn** — which simulation to use. Either `simulate_step` (for a single bump) or `simulate_sine` (for a continuous wave input).

**metric_fn** — what to measure from each simulation result. This is written as `lambda df:` followed by a calculation on the results table. The available columns are:

```
accel_sprung_g      body acceleration in g
susp_travel_mm      suspension travel in mm
z_sprung_mm         body displacement in mm
z_unsprung_mm       wheel displacement in mm
vel_sprung_mm_s     body velocity in mm/s
```

Common metric examples:
```python
lambda df: df["accel_sprung_g"].abs().max()        # peak body acceleration
lambda df: df["susp_travel_mm"].abs().max()        # peak suspension travel
lambda df: float(np.sqrt(np.mean(df["accel_sprung_g"]**2)))   # RMS body acceleration
```

**keyword** — the exact name of the parameter being passed to the simulation. Must be one of:

```
spring_rate       damper_rate       sprung_mass
unsprung_mass     tyre_stiffness
```

### Example — sweep spring rate, measure peak body acceleration

```python
results = run_sweep(
    param_name      = "Spring Rate (N/mm)",
    param_values    = np.linspace(20.0, 60.0, 9),
    simulate_fn     = simulate_step,
    metric_fn       = lambda df: df["accel_sprung_g"].abs().max(),
    keyword         = "spring_rate",
    simulate_kwargs = {"amplitude_mm": 25.0, "t_span": (0.0, 3.0)},
)
plot_sweep(results, "Spring Rate (N/mm)", "Peak Body Acceleration (g)",
           save_path="results/sweep_spring_rate.png")
```

### Example — sweep damper rate, measure peak suspension travel

```python
results = run_sweep(
    param_name      = "Damper Rate (N·s/mm)",
    param_values    = np.linspace(1.0, 6.0, 9),
    simulate_fn     = simulate_step,
    metric_fn       = lambda df: df["susp_travel_mm"].abs().max(),
    keyword         = "damper_rate",
    simulate_kwargs = {"amplitude_mm": 25.0, "t_span": (0.0, 3.0)},
)
plot_sweep(results, "Damper Rate (N·s/mm)", "Peak Suspension Travel (mm)",
           save_path="results/sweep_damper_rate.png")
```

### How to run it

```
uv run corner_model/sweep_parameter.py
```

### What you get

A single plot saved to `results/` showing your chosen metric on the Y axis against the swept parameter on the X axis. The terminal also prints one line per step so you can watch the results build up as it runs.

---

## Running a sweep then committing your results

After running a sweep, your results are saved locally in `results/hardpoint_sweeps/` or `results/`. The `results/` folder is ignored by Git — it is intentionally not shared with teammates because each person generates their own outputs locally.

If you want to share a result with the team, the best approach is to copy the plot image into a shared folder or attach it directly in your team communication. Do not try to commit files from the `results/` folder.

If you changed the target ranges or any settings inside the sweep scripts themselves, commit those file changes so teammates get your updated configuration:

```
git add sweep/hardpoint_sweep.py
git commit -m "update FSAE target ranges to match design spec"
git push
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: kinematics` | Make sure you are running the command from the repo root folder, not from inside the `sweep/` subfolder. Run `pwd` to check — it should end in `Full-Car-Simulation`. |
| `ValueError: 'my_point' is not a valid hardpoint name` | You mistyped the point name in `POINT`. Copy it exactly from the valid names list above, including capitalisation and underscores. |
| The sweep runs but plots don't open | Add `plt.show()` at the end of the script, or check that `SHOW_PLOTS = True` is set. |
| The ranked table shows score 0 for every position | Your actual geometry values are all outside the FSAE target ranges. This is expected if you are still using placeholder hardpoints. Enter your real CAD coordinates first. |
| The sweep takes a very long time | Reduce `STEPS` to a smaller number like `5` or `7` while testing, then increase it once you are happy with the setup. |
| `np.linspace` gives an error | Make sure all three values inside are numbers with decimal points: `np.linspace(20.0, 60.0, 9)` not `np.linspace(20, 60, 9)`. |

---

