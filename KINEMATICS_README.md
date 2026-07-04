# Corner & Quarter Car Model — Setup Guide

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

---

## Prerequisites — install these first

### 1. VS Code

VS Code is the code editor everyone on the team uses.

1. Go to **https://code.visualstudio.com**
2. Click **Download for Windows**
3. Run the installer — accept all defaults
4. When asked, tick **Add to PATH** if given the option

### 2. Git

Git is what lets you download the repo and sync changes with teammates.

```
winget install --id Git.Git -e --source winget
```

Run that in PowerShell (search **PowerShell** in the Start menu). Close and reopen PowerShell afterwards, then confirm it worked:

```
git --version
```

You should see a version number like `git version 2.x.x`. If you get an error, see the PATH fix below.

> **PATH fix for Git:** If `git --version` gives an error, open **Start → Search → Environment Variables → Edit the system environment variables → Environment Variables → System variables → Path → Edit → New** and add `C:\Program Files\Git\cmd`, then click OK and reopen PowerShell.

### 3. uv

uv manages the Python environment so everyone on the team gets exactly the same package versions without any manual setup.

```
winget install --id astral-sh.uv -e
```

Close and reopen PowerShell, then confirm:

```
uv --version
```

### 4. VS Code extensions

Open VS Code and install these two extensions:

1. Press `Ctrl+Shift+X` to open the Extensions panel
2. Search for **Python** (by Microsoft) → click Install
3. Search for **Pylance** (by Microsoft) → click Install

These give you syntax highlighting, autocomplete, and error highlighting inside `.py` files.

---

## Set up SSH for GitHub (one-time, per machine)

SSH lets you push and pull from GitHub without entering a password every time.

**1. Generate a key** — run this in PowerShell, replacing the email with your own:

```
ssh-keygen -t ed25519 -C "your_email@example.com"
```

Press Enter three times to accept all defaults (no passphrase needed for team use).

**2. Copy the public key to your clipboard:**

```
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard
```

**3. Add it to GitHub:**

Go to **github.com → Settings → SSH and GPG keys → New SSH key**, paste it in, and click Add.

**4. Confirm it works:**

```
ssh -T git@github.com
```

You should see a message greeting you by your GitHub username.

---

## Clone the repo

Navigate in PowerShell to the folder where you want the project to live, then clone it:

```
cd C:\Users\YourName\Documents     ← or wherever you want it
git clone git@github.com:freeman803/Full-Car-Simulation.git
cd Full-Car-Simulation
```

---

## Set up the Python environment

From inside the repo folder, run:

```
uv sync
```

This reads `pyproject.toml` and automatically installs all required packages (numpy, scipy, matplotlib, pandas) into an isolated environment. You only need to do this once, or again after a teammate adds a new dependency.

---

## Tell VS Code which Python to use

1. Open the repo folder in VS Code: **File → Open Folder** → select `Full-Car-Simulation`
2. Press `Ctrl+Shift+P`
3. Type **Python: Select Interpreter** and press Enter
4. Choose the option that contains `.venv` in the path — it will look like `.\.venv\Scripts\python.exe`

VS Code remembers this setting for the project so you only need to do it once.

> **Turn on Auto Save:** Go to **File → Auto Save**. This prevents the common mistake of editing a file and running it before saving.

---

## File structure — what everything does

```
Full-Car-Simulation/
│
├── full_corner_model.py       ← Entry point — run this to generate all outputs
│
├── pyproject.toml             ← Package list (managed by uv, don't edit manually)
├── uv.lock                    ← Exact package versions (commit this, don't edit)
├── .gitignore                 ← Tells Git which files to ignore
│
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

> **Common mistake:** Running `python full_corner_model.py` directly instead of `uv run full_corner_model.py`. Always use `uv run` — it makes sure the correct packages are loaded.

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

After editing, save the file (`Ctrl+S`) and re-run `uv run full_corner_model.py`. The geometry report will print updated values immediately.

---

## Changing simulation parameters

Open `full_corner_model.py` and look for the config block near the top:

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

## Everyday Git workflow

Every time you sit down to work, start by pulling the latest changes from GitHub so you have your teammates' updates:

```
git pull
```

When you've made changes and want to save them to the repo:

```
git add kinematics/hardpoints.py     ← add the specific file(s) you changed
git commit -m "update front corner hardpoints from CAD rev3"
git push
```

The message after `-m` should describe what you actually changed in plain English.

---

## Working on a branch

If you're working on something that isn't finished yet, do it on a branch so you don't break the main model for everyone else.

**Branch naming:** `initials/description` — for example `jb/front-corner-hardpoints`

```
git switch -c jb/front-corner-hardpoints    ← create and switch to new branch
```

Make your changes, then:

```
git add <files>
git commit -m "your message"
git push -u origin jb/front-corner-hardpoints    ← first push on a new branch
```

After the first push, plain `git push` works. When the work is ready, open a **Pull Request** on GitHub to merge it into `main`.

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
| `ModuleNotFoundError: kinematics` | Make sure you are running `uv run full_corner_model.py` from the repo root folder, not from inside the `kinematics/` subfolder. Run `pwd` to check where you are. |
| `KeyError: 'pushrod_outboard'` | You accidentally deleted a hardpoint name in `hardpoints.py`. Check that all the key names in the file match the original. |
| Plots don't open | Make sure `SHOW_PLOTS = True` is set at the top of `full_corner_model.py` |
| Geometry checks all showing ⚠️ OUT | Normal until you enter your real CAD coordinates. The default values are placeholders. |
| File changes don't seem to have any effect | Check that you saved the file (`Ctrl+S`) — look for a dot (●) on the tab. Also confirm you are editing the file inside the cloned repo folder and not a downloaded copy somewhere else. Run `pwd` in the terminal to confirm your location. |
| `ssh -T git@github.com` gives an error | Re-do the SSH setup steps, making sure you added the key to GitHub under Settings → SSH keys |

---

Do not edit any files other than `hardpoints.py` and the config block in `full_corner_model.py` without checking with the team lead first.
