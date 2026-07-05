## Corner & Quarter Car Model — Setup Guide

This guide walks you through everything needed to run the kinematics and quarter car simulation model on your own machine, even if you have no prior coding experience. Follow each step in order.

---

## What this model does

The corner model simulates the suspension geometry of the left-front corner of the car. Given a set of hardpoint coordinates (measured from CAD), it computes:

- Camber, caster, KPI, and toe angles through bump and droop
- Scrub radius and mechanical trail
- Pushrod and bellcrank motion ratio through wheel travel
- Wheel rate and damping at the contact patch
- Quarter car dynamic response to step and sinusoidal road inputs
- Frequency response (transmissibility) across a range of road input frequencies

All of these update automatically when you change the hardpoints or spring/damper rates in a single file.


## File structure — what everything does

```
Full-Car-Simulation/corner-model/


├──full_corner_model           ← This is the script we run to generate plots
├── kinematics/                ← All simulation code lives here
│   ├── hardpoints.py          ← ⭐ THE ONLY FILE YOU NEED TO EDIT for your car
│   ├── geometry.py            ← Pure maths (angles, vectors) — don't edit
│   ├── suspension.py          ← Double-wishbone solver — don't edit
│   ├── rocker.py              ← Pushrod, bellcrank, motion ratio — don't edit
│   ├── quarter_car.py         ← Quarter car ODE simulation — don't edit
│   ├── steering.py            ← Ackermann and toe calculations — don't edit
│   └── plots.py               ← All plot functions — don't edit
│
└── results/                   ← Generated outputs (ignored by Git, local only)
```

**The only file you will normally edit is `kinematics/hardpoints.py`.**

Everything else is the model engine. If you need to change what the simulation does or add a sweep, talk to the team lead first.

---

## Run the model

Open the VS Code terminal with `Ctrl+~` (or **Terminal → New Terminal**) and run:

```
uv run full_corner_model.py
```

The terminal will print a geometry report and save all plots to the `results/` folder. Open that folder in File Explorer to see the outputs.

> **Common mistake:** Running `python quartercar.py` directly instead of `uv run quartercar.py`. Always use `uv run` — it makes sure the correct packages are loaded.

---

## Updating the car's geometry

Open `kinematics/hardpoints.py`. This file is divided into clearly labelled sections:

```
# Upper A-arm (UAA)
# Lower A-arm (LAA)
# Steering
# Pushrod / Bellcrank / Damper
# Spring / Damper Rates
```

Replace the numbers inside `np.array([X, Y, Z])` with your CAD coordinates. The coordinate system is:

| Axis | Direction |
|------|-----------|
| X    | Forward (toward front of car) |
| Y    | Left (driver's left — outboard on the left corner) |
| Z    | Up (ground = 0) |

After editing, save the file (`Ctrl+S`) and re-run `uv run quartercar.py`. The geometry report will print updated values immediately.

---

## Changing simulation parameters

Open `quartercar.py` and look for the config block near the top:

```python
SHOW_PLOTS    = True    # set False to save without opening windows
SINE_FREQ_HZ  = 2.0    # road input frequency in Hz
STEP_AMP_MM   = 25.0   # step bump height in mm
SINE_AMP_MM   = 15.0   # sine wave road amplitude in mm
```

These are the only values you need to touch for basic input changes. For longer simulations, find the simulate calls below and add a duration:

```python
# Default (2.5 seconds)
df_step = simulate_step(amplitude_mm=STEP_AMP_MM)

# Extended to 5 seconds
df_step = simulate_step(amplitude_mm=STEP_AMP_MM, t_span=(0.0, 5.0))
```

---

**Useful branch commands:**

```
git branch                        # list all your local branches
git switch main                   # go back to main
git switch jb/front-corner-hardpoints   # go back to your branch
git pull origin main              # pull latest main into your branch
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `uv: command not found` | Close and reopen PowerShell after installing uv |
| `git: command not found` | Add `C:\Program Files\Git\cmd` to your system PATH (see Prerequisites) |
| `ModuleNotFoundError: kinematics` | Make sure you are running `uv run quartercar.py` from the repo root folder, not from inside the `kinematics/` subfolder. Run `pwd` to check where you are. |
| `KeyError: 'pushrod_outboard'` | You accidentally deleted a hardpoint name in `hardpoints.py`. Check that all the key names in the file match the original. |
| Plots don't open | Make sure `SHOW_PLOTS = True` is set at the top of `quartercar.py` |
| Geometry checks all showing ⚠️ OUT | Normal until you enter your real CAD coordinates. The default values are placeholders. |
| File changes don't seem to have any effect | Check that you saved the file (`Ctrl+S`) — look for a dot (●) on the tab. Also confirm you are editing the file inside the cloned repo folder and not a downloaded copy somewhere else. Run `pwd` in the terminal to confirm your location. |
| `ssh -T git@github.com` gives an error | Re-do the SSH setup steps, making sure you added the key to GitHub under Settings → SSH keys |

---

## Getting help

If something is broken and you can't figure it out from the table above:
1. Copy the full error message from the terminal
2. Note exactly what command you ran and from which folder
3. Talk to Austin and then Andrew if Austin can't figure it out
