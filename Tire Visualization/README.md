# Tire Visualization

Interactive visualizer for MF-Tyre 6.2 (Magic Formula) tire data. It loads a
`.tir` coefficient file, evaluates the full steady-state Pacejka equations
(pure + combined slip, inflation-pressure and camber effects), and plots any
model output against any swept input.

There are two ways to use it: a **local web app** (recommended) and a
**command-line script**.

## Files

| File | What it is |
|------|------------|
| `run_tire_app.bat` | Double-click launcher for the web app |
| `tire_viz_app.py` | Web app server (Python standard library only) |
| `tire_viz_app.html` | Web app UI |
| `tire_visualizer.py` | The MF 6.2 tire model + interactive CLI version |
| `16inx18in_R20 1.tir` | Default tire coefficient file (CFR27) |

## Quick start — web app

Double-click **`run_tire_app.bat`**. It starts a local server and opens the
app in your browser at `http://127.0.0.1:<port>/`. Close the terminal window
(or press `Ctrl+C` in it) to stop the app.

From a terminal instead:

```powershell
cd "Tire Visualization"
..\.venv\Scripts\python.exe tire_viz_app.py
```

Options: `--port 8000` to pick a port, `--no-browser` to not open a browser,
or pass a path to a different `.tir` file:

```powershell
..\.venv\Scripts\python.exe tire_viz_app.py "path\to\other tire.tir"
```

The app runs entirely on your machine (it binds to `127.0.0.1` only) and has
no external dependencies — no internet needed.

### Using the app

The tire model takes 5 **inputs** and computes 5 **outputs**:

| Inputs (you set these) | Outputs (the model computes these) |
|---|---|
| Tire pressure [psi] | FX — longitudinal force [N] |
| FZ — vertical load [N] | FY — lateral force [N] |
| Slip angle [deg] | MX — overturning moment [N·m] |
| Slip ratio [–] | MY — rolling resistance moment [N·m] |
| Camber [deg] | MZ — aligning moment [N·m] |

1. Pick which input to **sweep** and which output to **plot** against it.
2. Set values for the other four (fixed) inputs.
3. Adjust the sweep min/max/points.

The chart updates live as you type. Hover for exact values, tick
"Put the output on the X axis" to flip the axes, and expand **Data table**
below the chart to see (or copy) the raw numbers. The page follows your
system light/dark theme.

Typical plots: FY vs slip angle (cornering stiffness / peak grip),
FX vs slip ratio (traction), FY vs FZ (load sensitivity),
FY vs pressure or camber (setup sensitivity).

## Command-line version

```powershell
cd "Tire Visualization"
..\.venv\Scripts\python.exe tire_visualizer.py
```

Same model, same choices as the web app, answered as terminal prompts. Shows
a matplotlib window and saves a PNG (`plot_<output>_vs_<input>.png`) next to
the `.tir` file.

## Requirements

Uses the repo's uv environment (see the root README for setup). The web app
needs only the standard library plus numpy; the CLI also uses matplotlib —
both are already in the project environment.

## Model notes

- Implements the MF-Tyre 6.1/6.2 steady-state equations (Pacejka, *Tire and
  Vehicle Dynamics*, 3rd ed.): pure-slip FX0/FY0, combined-slip weighting
  (Gxα, Gyκ), pneumatic trail + residual torque for MZ, and the PPX/PPY/
  PPZ/PPMX inflation-pressure terms — so pressure sweeps are meaningful.
- The UI works in psi and degrees; the `.tir` file itself is in Pa and
  radians and is converted internally.
- Outputs can never be fixed — they are functions of the inputs. That's why
  the app asks for one input to sweep and one output to plot, rather than
  letting you fix forces/moments.

### Known quirks of `16inx18in_R20 1.tir`

- `UNLOADED_RADIUS = 19.58` is labeled meters but is treated as centimeters
  (0.1958 m ≈ 16 in OD) — the only plausible reading.
- All rolling-resistance coefficients (QSY1–QSY8) are zero, so **MY ≡ 0**.
  The app shows a note when MY is selected.
- The aligning-moment fit has near-zero pneumatic trail (QDZ1 ≈ 5e-5,
  QCZ1 ≈ 116 where typical values are ~0.1 and ~1.2), so **MZ comes out
  near zero** (~0.1 N·m). If realistic aligning moments matter, that section
  of the `.tir` needs a better fit.
