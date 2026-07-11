## Forces Model — Setup Guide

This guide walks you through running the suspension linkage force calculator on your own machine, even if you have no prior coding experience. Follow each step in order.

---

## What this model does

Given the same car data used elsewhere in this repo (mass, track, wheelbase, aero) plus a set of driving conditions (G's, slip angle, slip ratio, tire pressure), this model computes:

- **Wheel load** — the vertical load on one corner, including static weight, longitudinal/lateral load transfer, and aero downforce (`wheel_loads.py`)
- **Tire forces** — lateral and longitudinal contact-patch force from a Pacejka tire model, read from the `.tir` coefficient file (`tire_model.py`)
- **Linkage forces** — the tension/compression force in each of the six main suspension links (upper/lower A-arm fore & aft, pushrod, tie rod), solved from a full 3-force + 3-moment equilibrium of the upright/wheel assembly against the tire's contact-patch wrench and the real hardpoint geometry (`linkage_forces.py`)
- **A 3D picture** of those forces on the actual suspension geometry, colored by tension (green) / compression (red), darker meaning more force (`visualize_linkage_forces.py`)

All of it reads hardpoints from `../kinematics/hardpoints.py` — the same file used by the kinematics model — so geometry only needs to be entered once.

---

## File structure — what everything does

```
Full-Car-Simulation/corner-model/Forces/

├── run_linkage_calculation.py     ← ⭐ Run this for the interactive calculator
├── visualize_linkage_forces.py    ← ⭐ Run this for the 3D force diagram
├── car_data.py                    ← Car mass, track, wheelbase, aero — edit for your car
├── wheel_loads.py                 ← Vertical load transfer — don't edit
├── tire_model.py                  ← Pacejka tire model — don't edit
├── linkages.py                    ← Linkage hardpoint geometry / unit vectors — don't edit
├── linkage_forces.py              ← Combines the above into linkage force balance — don't edit
└── 16inx18in_R20 1.tir            ← Tire coefficient file (from TTC data) — don't edit
```

**The only file you will normally edit is `car_data.py`** (for overall car parameters) or `../kinematics/hardpoints.py` (for suspension geometry — see `KINEMATICS_README.md` one level up).

---

## Run the calculator

Open the VS Code terminal with `` Ctrl+` `` and run, from the repo root:

```
uv run corner-model/Forces/run_linkage_calculation.py
```

or, from inside this `Forces/` folder:

```
uv run run_linkage_calculation.py
```

It will prompt you for:

| Prompt | What to enter |
|---|---|
| Axle | `front` or `rear` |
| Longitudinal G | positive = braking load transfer to the front, negative = acceleration |
| Lateral G | positive = load transfer to this corner while cornering |
| Slip angle (degrees) | tire slip angle, e.g. `5` |
| Slip ratio | fraction, e.g. `0.1` for 10% wheel slip |
| Tire pressure (psi) | e.g. `14.5` |

It prints the force in each linkage in Newtons, labeled `tension` or `compression`.

> **Common mistake:** Running `python run_linkage_calculation.py` instead of `uv run run_linkage_calculation.py`. Always use `uv run` — it makes sure the correct packages (numpy) are loaded. Plain `python` also works as long as you have numpy installed, but `uv run` is guaranteed to work.

---

## Run the 3D force visualization

```
uv run corner-model/Forces/visualize_linkage_forces.py
```

This uses a fixed example condition (1.0g lateral, 0.2g longitudinal, front axle, 4.6° slip angle) and:

- Opens an interactive 3D plot window you can rotate/zoom
- Saves a PNG to `../results/linkage_forces_front.png`
- Prints the same force list as the calculator

To visualize different conditions, open `visualize_linkage_forces.py` and edit the constants near the top of `main()`:

```python
axle: Literal["front", "rear"] = "front"
lateral_g = 1.0
long_g = 0.2
slip_angle_rad = 0.08
slip_ratio = 0.1
pressure_pa = 100000.0
```

**Reading the plot:**
- **Green** members are in tension, **red** members are in compression.
- Darker / more saturated color = higher force magnitude. The thickness of the line also scales with force.
- Each member is labeled with its exact force in Newtons at its midpoint.
- The dashed grey line is the kingpin axis — shown for orientation only, it doesn't carry a computed force.

---

## Updating the car's parameters

Open `car_data.py` and edit the class constants:

```python
MASS_KG = 200
CG_HEIGHT_MM = 315
FRONT_TRACK_MM = 1219
REAR_TRACK_MM = 1168
WHEELBASE_MM = 1545
TOTAL_DOWNFORCE_N = 477
CENTER_OF_PRESSURE = 0.3801   # fraction of downforce on the rear axle
CENTER_OF_MASS = 0.5          # fraction of mass on the front axle
```

For suspension geometry (hardpoint coordinates), edit `../kinematics/hardpoints.py` instead — see `../KINEMATICS_README.md`.

---

## How the linkage force solve works

Each of the six linkages is treated as a two-force member (force only along its own axis) connecting a chassis point to an upright point. The upright + wheel is treated as one rigid body in equilibrium under those six reactions plus the tire's contact-patch wrench (3 force components + 3 moment components — overturning, rolling resistance, aligning torque — all from the Pacejka tire model). Six unknown member forces, six independent equilibrium equations (taken about the contact patch) — that's statically **determinate**, so it's solved directly (`np.linalg.solve`), not approximated.

**Sign convention:** a positive force means **tension** (the member pulling its chassis and upright ends together); negative means **compression**.

---

## A note on accuracy

This is a **simplified** force model, useful for sizing/comparing linkages, not a final structural sign-off tool:

- **Pushrod simplification.** The pushrod's outboard end is physically mounted on the lower A-arm, not the upright (see the `# lower arm pickup` comment on `pushrod_outboard` in `hardpoints.py`). This model treats it as if it reacts directly against the upright/wheel assembly instead of solving the lower A-arm as its own rigid body. This is a standard simplification for this kind of hand-check model, but it means the pushrod (and, to a lesser extent, the lower A-arm legs) number isn't from a full multi-body solve.
- **Rear contact patch is approximated.** The front axle has an exact `contact_patch` hardpoint from CAD. The rear axle doesn't have one yet, so `linkages.py` approximates it as directly below `rear_wheel_center` by the nominal wheel radius. Add a real `rear_contact_patch` point to `hardpoints.py` for exact rear-axle results.
- **Rear tie rod geometry looks unfinished.** As of this writing, `rear_tie_rod_inboard` and `rear_tie_rod_outboard` share the exact same Y coordinate (832.4617mm) — meaning that link currently has *zero* ability to react lateral load directly. Under cornering conditions this forces very large compensating forces through the other rear links via moment leverage (you'll see rear-axle numbers in the thousands of Newtons even for modest inputs). If those look real to you rather than a placeholder, they're a red flag worth double-checking in CAD before trusting rear-axle output. Front-axle results don't have this issue.
- The tire model implements the standard Pacejka "Magic Formula" pure-slip equations for lateral and longitudinal force, but not combined-slip (simultaneous braking + cornering) effects.

If you need numbers for final component sizing, cross-check against a proper multibody solver (e.g. ADAMS/Car, a Jacobian-based FBD, or hand calculations at the critical load case).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `uv: command not found` | Close and reopen PowerShell after installing uv |
| `ModuleNotFoundError: No module named 'kinematics'` or `'Forces'` | Shouldn't happen anymore — every script in this folder finds its imports automatically regardless of your working directory. If you do see this, make sure you didn't move a file out of `Forces/` on its own. |
| `KeyError: 'rear_...'` | A rear-axle hardpoint is missing from `../kinematics/hardpoints.py`. Every `rear_...` point must exist alongside its front-axle counterpart. |
| Plot window doesn't open | Some remote/headless terminals can't show a window — the PNG is still saved to `../results/linkage_forces_front.png` even if the window doesn't appear. |
| Forces look too small / too large | The interactive calculator takes degrees/psi directly, so this shouldn't bite there. If you're editing `slip_angle_rad`/`pressure_pa` constants directly in `visualize_linkage_forces.py`, remember those two are still in **radians**/**Pa**, not degrees/psi. |
| Rear-axle forces look huge (thousands of N) under lateral load | Likely the rear tie rod geometry issue described in "A note on accuracy" above, not a bug — check `rear_tie_rod_inboard`/`outboard` in `hardpoints.py`. |
| File changes don't seem to have any effect | Check that you saved the file (`Ctrl+S`) — look for a dot (●) on the tab. |

---

## Getting help

If something is broken and you can't figure it out from the table above:
1. Copy the full error message from the terminal
2. Note exactly what command you ran and from which folder

