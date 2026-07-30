# CFR26 Telemetry Analysis — `scripts/`

Analysis of the 2026 competition telemetry in `comp2026_data/`, answering: **what G's, roll and pitch did the car actually see, per event?** — so we know where we are before setting targets for the next suspension.

Everything here is **measurement-based**. Nothing imports from `corner-model/` or any other simulation model, deliberately.

## Running

Start here — one table across all four cases:

```powershell
uv run case_summary.py --dir comp2026_data
```

Then the individual cases for the detail behind any number:

```powershell
uv run case1_max_gs.py --dir comp2026_data
uv run case2_max_roll.py --dir comp2026_data
uv run case3_max_pitch.py --dir comp2026_data
uv run case4_combined_roll_pitch.py --dir comp2026_data
```

Each prints a console report and writes interactive plots under `plots/<case>/<event>/`, plus one headline summary chart per case.

| file | what it is |
|---|---|
| `parse_influx.py` | Andrew's InfluxDB CSV parser. **Do not modify.** |
| `case_common.py` | Shared constants and helpers — anything that must stay identical across cases lives here |
| `case1_max_gs.py` | Max lateral / longitudinal / combined G |
| `case2_max_roll.py` | Max roll angle |
| `case3_max_pitch.py` | Max pitch angle |
| `case4_combined_roll_pitch.py` | Combined roll + pitch, as per-corner wheel travel |
| `case_summary.py` | Consolidated "where the car is" table across all four cases |
| `filter_compare.py` | Cutoff-frequency comparison tool (9 signals + peak-attenuation table) |
| `old - ignore/` | Superseded exploratory work |

## The summary table

`case_summary.py` prints one row per event across all four cases, and writes `plots/case_summary.md` (for pasting into docs or a PR) and `plots/case_summary.html`.

| Event | Sustained lat G | Peak lat G | Peak lon G | Roll (deg) | Pitch (deg) | Worst corner travel |
|---|---|---|---|---|---|---|
| SKIDPAD | 1.26–1.35 g | — | — | 1.18 | 0.10* | +18.2 mm (FR) |
| ACCEL | — | — | — | — | 0.36* | +15.7 mm (RR) |
| BRAKE | — | — | — | — | 0.73 | −20.5 mm (FR) |
| AUTOCROSS | — | 1.73 | 1.34 | 1.44 | 0.91 | **−27.8 mm (FR)** |
| ENDURANCE | — | 1.78 | 1.65 | 1.57 | 0.89 | −23.9 mm (FR) |

`*` = sustained value; that event has no separate peak by design. `—` = not covered by that case, or the quantity doesn't apply.

**It does not recompute anything.** It imports case1–case4 and calls their own analyse and report functions, taking the summary dicts they already return with their console output suppressed. Change a case's methodology and this table follows automatically — so it cannot drift from what the individual scripts print. Verified: every value matches its source script (e.g. skidpad roll 1.18 vs case2's 1.1810°, brake pitch 0.73 vs case3's −0.7317°).

It skips only the plotting, so it's faster than running all four.

## Raw signal survey — `batch_signal_stats.py`

**Start here with a new data set**, before any case script. It answers "what's actually in these files and does it look sane?" — min/max/mean for every signal, pooled per event, plus optional time-series grids.

```powershell
uv run batch_signal_stats.py --dir comp2026_data --list-signals   # cheap peek, no parse
uv run batch_signal_stats.py --dir comp2026_data                  # stats tables
uv run batch_signal_stats.py --dir comp2026_data --plot           # + time-series grids
uv run batch_signal_stats.py comp2026_data/skidpad_austin_both.csv   # single file
```

**`--list-signals` first, with unfamiliar data.** It reads only the `_field`/`_value` columns — no pivot, no union grid, no pickle cache written — and reports `n`/`min`/`max` per signal. **1.0s on the 234 MB endurance file against 3.8s for a cold full parse.**

It's also the *only* view showing each signal's true update rate, since the stats tables count samples on the resampled union grid. That difference is real and easy to miss: on skidpad, `VCFRONT_brakePressure` has **977 samples where the shock pots have 9783** — roughly 10 Hz against 100 Hz.

`--plot` saves one PNG per event — a grid with a subplot per signal and a line per file, x-axis in elapsed seconds so files with different absolute start times overlay correctly. Lines longer than 20,000 points are stride-decimated for drawing only; the stats always use full data. PNGs go to `./plots`, or `--plot-dir <folder>`.

**Plotting is selectable; stats are not.** A subplot grid stops being readable well before the signal list does (19 signals is already a 2340×1820 image), but a text table costs nothing and narrowing it would hide the anomalies that make this tool diagnostic — you'd have to already suspect `FL` to select `FL`.

```powershell
uv run batch_signal_stats.py --dir comp2026_data --plot --signals VCPDU_lat,VCPDU_lon
```

With `--plot` and no `--signals`, you get an interactive numbered prompt accepting `all`, `1,4,7`, or ranges like `2-6,9`; bare Enter keeps everything, so the prompt is a filter you reach for rather than a gate you pass through. It's skipped when stdin isn't a TTY, so scripted and piped runs never block.

Files are grouped by event from the filename, and **all samples from all files of an event are pooled into one table** — every `accel_*.csv` becomes a single ACCEL row set, not one table per file. A final ALL EVENTS table pools everything.

It's genuinely diagnostic, not just descriptive. Reading the skidpad table alone surfaces three of the known data problems below: `steeringAngle` with a mean of −151° and a max of −69° (never positive), `shockpotdispFL` spanning 18.4mm against `shockpotdispFR`'s 34.4mm, and `VCPDU_lat` reaching ±20 (confirming m/s², not g).

## Will it handle new signals?

Mostly yes, automatically. The split is deliberate:

| script | new signals? | why |
|---|---|---|
| `parse_influx.py` | ✅ **automatic** | Discovers signals from the CSV's own `_field` column. Never had a fixed list |
| `batch_signal_stats.py` | ✅ **automatic** | `discover_signals()` reports everything present, appends unrecognised names at the end of the table and prints `[i] N signal(s) not in PREFERRED_SIGNAL_ORDER`. `PREFERRED_SIGNAL_ORDER` only controls display order — it is **not** a filter |
| `filter_compare.py` | ⚠️ **one-line edit** | Add a tuple to `EXTRA_SIGNALS`: `(signal_name, plot_title, y_label, file_stem)`. Curated on purpose — you pick which signals to compare cutoffs on. Missing signals are skipped with a warning |
| `case_common.py` | ⚠️ **explicit** | `CORNER_SIGNAL_NAMES` and `BRAKE_PRESSURE_SIGNALS` name specific physical sensors; there's no generic meaning to substitute |
| `case1`–`case4` | ⚠️ **explicit** | Each declares `REQUIRED_SIGNALS` and refuses to run a file without them. Correct by design — a case is a physics question, not a signal dump |

So a new channel appears in the survey with no code change, and only needs wiring where a specific physical meaning is required.

**Two things to watch when adding a signal:**

- **Check its units in the DBC.** `VCPDU_lat`/`lon` are `m/s2` despite reading like g's, and that exact mistake reached production here — case2 and case3 gated segmentation at an effective 0.031 g instead of 0.3 g, understating accel pitch by up to 32%.
- **Check its update rate in firmware** (`grep periodic.*Hz_CLK`). It bounds any usable cutoff: shock pots and the IMU are 100 Hz (Nyquist 50), but steering angle is 10 Hz (Nyquist 5), so filtering it above 5 Hz is meaningless.

## Adding a new case

The four cases share a deliberate shape. To add `case5_<thing>.py`:

1. **Reuse `case_common`** — `lowpass`, `elapsed_seconds`, `trim_window`, `find_steady_segments`, `top_k_peaks`, `baseline_corner_displacements`, `to_wheel_travel`, `find_step_glitches`, `find_braking_windows`. Don't redefine constants; if a pattern would be duplicated across cases, it belongs in `case_common` instead.
2. **Declare `REQUIRED_SIGNALS`** and skip files that lack them.
3. **Verify every threshold against real data before committing to it** — measure the noise floor in stopped-car windows to pick a peak prominence, and confirm your event windows exist and have the durations you assume. Every constant in the existing cases has its measurement recorded in a comment; match that.
4. **Convert to wheel travel before any axle arithmetic** if you touch the shock pots, because the front and rear motion ratios differ.
5. **Have your `report_*` function return a summary dict** as well as printing. That's what lets `case_summary.py` include the case without duplicating logic.
6. **Register it in `case_summary.py`** — add a `collect_caseN()` mirroring the others, and a column in `build_rows()`.
7. **Write plots to `plots/case5_<thing>/<event>/`**, plus one headline chart.
8. **Document the methodology in this README**, including anything you rejected and why. The reasoning is the expensive part to reconstruct — `case4` exists in its current form only because `√(roll² + pitch²)` was tried, measured, and found to reproduce `case2` to three decimals.

## Vehicle constants

| constant | value |
|---|---|
| Front track | 1219.2 mm |
| Rear track | 1168.4 mm |
| Wheelbase | **1543 mm** (1545 in `corner-model/Forces/car_data.py` is a known error on another branch) |
| Motion ratio, front | **1.15** (wheel ÷ spring) |
| Motion ratio, rear | **1.038** |

Front and rear motion ratios differ, which dictates *where* the conversion happens: every corner is converted to wheel travel **before** any roll, pitch or modal arithmetic. Differencing axles on raw shock-pot mm and applying one ratio afterwards is only valid when the ratios match, and they don't.

## Shared foundation

Inherited by every case; none of them redefine these.

| | |
|---|---|
| **Filter** | 4th-order Butterworth, zero-phase (`filtfilt`). **2.0 Hz** skidpad, **5.0 Hz** everything else |
| **Units** | `G = 9.80665`. `VCPDU_lat`/`lon` are **m/s²** in the DBC and are divided by G |
| **Time** | The InfluxDB union grid is **not uniformly sampled**. Every duration is real elapsed `t[e]−t[s]`, never `sample_count × dt` — that errs by 3–5×. Scalar `dt` is used *only* for filter design |
| **Baselining** | Each corner is zeroed against its own stopped-car window (speed <0.5 m/s, ≥2s real, trimmed 0.5s/end; prefers file start → end → longest anywhere, which catches an endurance driver change). Mandatory: each pot carries its own zero offset, and differencing without removing it counts the offset as suspension movement |
| **Glitch rejection** | Per-sensor-update jumps >8mm are masked ±1s — see *Known data problems* |
| **Peak detection** | `find_peaks` by **prominence only** — no index-based `distance`, because a fixed sample count spans different real time in different parts of a file. Spacing is enforced afterwards against elapsed time: tallest candidate first, reject any peak within 1.0s of an accepted one. Top 5 |

Two signals are deliberately **not** used:

- **Steering angle** — unusable, see below.
- **Speed derivative** — `dv/dt` from `VCFRONT_vehicleSpeed` reaches 89–127 m/s² (9–13 g) and *stays* there at the 99th percentile; low-passing to 0.2 Hz still leaves 5–6 g. The cause is the grid, not the sensor: speed is quantised at 0.01 m/s while grid intervals are sub-millisecond, so one quantisation step is already ~12 m/s². Use `VCPDU_lon` for acceleration (it peaks at a sensible 0.99 g on accel runs); speed is for coarse gating only.

---

## Case 1 — Max G's

**Events:** skidpad, autocross, endurance. **Signals:** `VCPDU_lat`, `VCPDU_lon`.

- **Skidpad** — steady segments found from the sign and magnitude of filtered lateral G (>0.3 g, ≥2.0s real duration), keeping the **2 longest runs per direction**, trimmed 0.5s each end. Reports the **median** over the trimmed middle, not a peak — matching how FSAE itself scores skidpad (average over the steady lap). Run-to-run spread also reported.
- **Autocross / endurance** — whole-file peak detection on lateral, longitudinal and combined `√(lat²+lon²)`, prominence **0.3 g**, top 5 pooled + single highest. Each peak reports the *simultaneous* lat/lon pair (the actual g-g point) and `alpha`, that point's angle.

Steering-rate gating was tried and abandoned; the absolute steering value was never used because the sensor is miscalibrated.

## Case 2 — Max Roll

**Events:** skidpad, autocross, endurance.

```
roll_front = wheel FR − wheel FL   → atan(mm / 1219.2)
roll_rear  = wheel RR − wheel RL   → atan(mm / 1168.4)
roll_avg   = (front + rear) / 2    → atan(mm / avg track)
```

- **Skidpad** — reuses case1's exact lateral-G segments; median front/rear/avg per run.
- **Autocross / endurance** — whole-file peaks on `|roll_front|`, `|roll_rear|` and `|roll_avg|` separately, prominence **2.0mm**, reporting front *and* rear at the same instant.

Prominence justification: roll noise std ~0.12mm during stopped windows, and sweeping 0.5→10mm left the top-5 and single peak completely unchanged.

## Case 3 — Max Pitch

**Events:** all five. `pitch = avg(wheel FL, FR) − avg(wheel RL, RR)` → `atan(mm / 1543)`.

**Sign convention — verified empirically against vehicle speed, not assumed:**

```
pitch > 0   squat      (acceleration)
pitch < 0   dive       (braking)
```

A *higher* mm reading is more **extension** on this car's calibration — the opposite of what the formula alone suggests. Called out because it is easy to misread.

Methodology differs per event because the data genuinely differs:

- **Skidpad** (2 Hz) — lateral-G segments, median pitch. Expected near zero; a sanity check.
- **Accel** (5 Hz) — longitudinal-G steady segments restricted to the **accelerating** (negative lon G) branch, so the braking phase at the end of accel files is excluded. Median over the trimmed window. Verified as one continuous ~4s pull, not a series of spikes.
- **Brake** (5 Hz) — windows from **front brake pressure >100 psi AND speed >3 m/s**, minimum 0.3s. *Both* gates are required: pressure alone produced a single 30.3-second "braking window" (the driver holding the pedal at a standstill) and several windows whose pitch was *positive* — squat, impossible under braking. With the speed gate, every surviving window dives correctly, which is independent evidence the detection is right. Within each window the single worst `|pitch|` instant is taken — a window-local peak, not a blind whole-file search. Pooled across files, top 5 averaged + single hardest.
- **Autocross / endurance** (5 Hz) — whole-file peaks on `|pitch|`, prominence **3.0mm** (pitch noise std 0.13–0.55mm during stopped windows).

## Case 4 — Combined Roll + Pitch

**Events:** all five. Reports **worst per-corner wheel travel**, where `travel < 0` = compression (bump), `> 0` = extension (droop). Both extremes are reported, since both have a mechanical limit.

### Why not `√(roll² + pitch²)`

That was the original plan. It was built, measured against real data, and **rejected**:

1. **Roll and pitch peaks never coincide** — measured gaps between each file's worst-roll and worst-pitch instant: endurance 869s, autocross 20–53s. These are independent events.
2. **Roll is 2–4× larger than pitch** on this car, so a root-sum-square is captured almost entirely by roll. On endurance it returned 1.450° at an instant where pitch was +0.034° — identical to case2's max-roll answer to three decimals. It measured nothing new.

Per-corner travel is where roll and pitch physically superpose, needs no arbitrary "both axes elevated" threshold, and is the quantity that decides whether a spring or damper runs out of travel.

### Modal decomposition

At the worst instant, the travel is decomposed **exactly** — an algebraic identity, asserted at runtime, not a fit:

```
heave = (FL + FR + RL + RR) / 4      FL = heave − roll + pitch + warp
roll  = ((FR + RR) − (FL + RL)) / 4  FR = heave + roll + pitch − warp
pitch = ((FL + FR) − (RL + RR)) / 4  RL = heave − roll − pitch − warp
warp  = ((FL + RR) − (FR + RL)) / 4  RR = heave + roll − pitch + warp
```

So the report states precisely how many mm came from roll vs pitch vs heave vs **warp** — diagonal chassis twist, visible here and in neither case2 nor case3.

### Other outputs

- Peak detection on the **4-corner envelope** `max(|FL|,|FR|,|RL|,|RR|)`, prominence 2.0mm, top 5 + single worst.
- **Skidpad and accel also get a sustained number** (median over steady segments) alongside the peak, being quasi-steady events.
- Per-corner signed extremes, with the outer 2% of each file excluded (`filtfilt` overshoots at array boundaries — a file ending mid-event produced a fake 17.36mm peak against a 16.33mm raw peak) plus glitch masking.
- Per-event roll-vs-pitch scatter with a convex hull, showing which *combinations* the car actually reaches.

**Scope caveat:** case4 runs all five events, but only **autocross (17–29% of samples) and endurance (20%)** genuinely load both axes at once. Skidpad is 2.6%, accel 0–0.9%, braketest1 0%. The other three are effectively sanity checks, not real combined cases.

---

## Known data problems

Read this before trusting any number.

### 1. Shock-pot step glitches — handled automatically

Twelve instantaneous step discontinuities exist across four files: FL and FR jump *together* by ~13mm and ~22mm, then hold at the new level. Suspension cannot step and then sit still, so these are sensor/electrical faults.

| file | time(s) |
|---|---|
| `accel_corinne1` | 118.84 |
| `autocross_andrew1` | 76.99 |
| `autocross_josh1` | 84.56 |
| `braketest2` | 46.23, 46.33, 147.95 |

They are **larger than any real event**, so an unprotected peak search reports them as the worst case — before rejection they held the top spot in three of case4's five events, including its overall design-driving case.

The 8mm threshold is not a judgement call. Over 7.6 million real sensor updates, legitimate per-update jumps have p99.9 = 1.19mm, p99.99 = 1.78mm, and the largest in any clean file is 4.38mm. The glitches are 20.35–23.32mm. **Nothing falls between 4.4mm and 20.3mm.**

### 2. `VCFRONT_steeringAngle` is unusable

Two separate problems, both traced to `firmware/components/vc/front/src/steeringAngle.c`:

- **Zero calibration was never run.** The map is ±0.78 V → ∓90°, i.e. −115.3846 °/V applied to `(voltage − steeringCalibration_data.zero)`. That zero is still 0 V, so a ~1.5 V resting sensor gives −115.3846 × 1.5 = **−173.077°** — exactly the −173.0 seen in all 11 files. This is *not* a DBC rail and *not* an electrical fault: lines 108–111 set `angle = 0.0f` when faulted, so a faulted sensor would read 0°, and the implied voltages (0.589–1.499 V) sit inside the 0.25/2.75 V fault window.
- **Only one steering direction registers.** Voltage only ever moves down from its 1.4993 V rest, where it sits for 73% of a file across just 69 distinct values. Re-zeroing recovers the offset but not the missing half of travel.

Its *rate of change* is not a safe fallback either: while the signal sits at rest its derivative is identically zero, which any "is the driver holding a steady line?" test reads as steady from a flat-lined sensor.

### 3. `FL` shock pot is suspect

On skidpad, FL sweeps **18.4mm** while FR sweeps **34.3mm**, and FL's static baseline ranges **42.4–66.9mm** across sessions, 13–22mm away from FR. This is likely the "one of the sensors might be broken" noted in the original project brief.

### 4. Front and rear roll disagree — unexplained

A rigid chassis has exactly *one* roll angle, so front and rear derived roll should match. They don't: **rear reads 7–27% more**, same sign every event. Worse, the **rear shows 16–22% left/right asymmetry that the front does not** (1.1–3.3% front), and it appears on skidpad, which is symmetric by construction.

A pure *gain* error on a rear pot cannot cause this — in roll, one pot compresses while the other extends, so `RR − RL` sums the two gains and gives equal magnitude either direction. Direction-dependent asymmetry requires genuinely asymmetric rear roll stiffness or a **non-linearity** (a pot near its stroke limit, or something binding). Candidate explanations for the front/rear gap remain chassis torsional flex, a motion-ratio error, or pot calibration — currently unresolved, so the rear roll number is the less trustworthy of the two.

Related: **FR is the worst-loaded corner in 8 of 11 files**, too consistent to be noise.

### 5. `braketest2.csv` is unreliable

Three independent red flags: shock-pot noise 10–20× every other file (0.394/0.667mm vs a 0.031mm median), elevated combined-angle noise, and filter overshoot stuck at 106% across all cutoffs. It also holds 6 of the 12 step glitches. Don't let it drive a design conclusion.

### 6. `endurance_full.csv` brake pressure saturates

Its front pressure p99 is exactly 2000 psi, the top of the DBC range `[0|2000]`. Pressure-derived peaks there are floors, not maxima.

### 7. IMU attitude signals

`VCPDU_angleRoll` / `anglePitch` read ±20–36° against ±1.3° derived from the shock pots — consistent with an uncalibrated gravity-vector tilt rather than chassis attitude (the DBC carries `IMU_UNCALIBRATED` and `IMU_YAW_CALIBRATION_FAILED` warnings). Not used. The raw *rates* (`VCPDU_roll`/`pitch`, deg/s) are a separate question and have not been validated.

---

## Open questions

- **Low-pass cutoff for accel/brake.** No cutoff was ever chosen for these two events — they inherit `AUTOX_END_CUTOFF_HZ` (5 Hz), a constant validated for autocross/endurance transients. It matters: peak pitch moves ~12% across 2→10 Hz. Complicating it, there is a real **6–8 Hz mode carrying 5.88mm** of travel, and both 5 and 8 Hz sit *on* that resonance, which makes the reported peak hypersensitive to the exact value. The choice is really whether that mode belongs in the answer: below it (~3 Hz) reports body attitude, above it (~15 Hz) reports true wheel travel. Affects case4's travel far more than case1–3's angles.
- **Motion ratio** is a single value per axle. If it varies meaningfully with travel, a curve would be more accurate.
- **Case 7 from the original brief (max yaw timing)** is deliberately not implemented.

## `filter_compare.py`

Compares low-pass cutoffs across **9 signals** — lateral/longitudinal/combined G, roll, pitch, vehicle speed, front/rear brake pressure, and steering angle (flagged unusable). Roll and pitch are included because those are what the case scripts actually report on; picking a cutoff from the G traces alone leaves the shock-pot cutoff unvalidated.

```powershell
uv run filter_compare.py comp2026_data/accel_*.csv --freqs 5 8 --zoom-on-peak
uv run filter_compare.py comp2026_data/braketest1.csv --freqs 2 5 10 --zoom-at 100
```

- Prints a **peak-attenuation table** — how much of each signal's peak survives each cutoff. The numerical version of what the plots show by eye.
- `--zoom-on-peak` centres each zoom on that signal's own largest moment (the fixed 600s window lands on arbitrary quiet track for short accel/brake events). `--zoom-at <seconds>` overrides it — useful because the automatic peak sometimes lands on a step glitch.
- Peak stats exclude the outer 2% of each file, since `filtfilt` overshoots at boundaries.

**Source sample rates** (from firmware — these bound which cutoffs mean anything):

| signal | rate | Nyquist |
|---|---|---|
| Shock pots (`shockpot.c`, `periodic100Hz_CLK`) | 100 Hz | 50 Hz |
| IMU lat/lon (`imu.c`, `periodic100Hz_CLK`) | 100 Hz | 50 Hz |
| Steering angle (`steeringAngle.c`, `periodic10Hz_CLK`) | 10 Hz | 5 Hz |

The ~1200 Hz "sampling frequency" the tool prints is union-grid density, not a real sample rate. It is the correct `fs` to design the filter against, but it is not evidence any signal is sampled that fast.

Also note the IMU's own firmware low-pass (`imu.c:47`) is set to a 100 Hz cutoff at a 100 Hz sample rate — above Nyquist, so it is effectively a pass-through and the offline filtering does all the real work.

## Shock-pot displacement vs voltage

`disp` is a single global linear transform of `volt`: **−25.510 mm/V**, identical on all four corners and all 11 files. So the voltage channels carry no extra information — but there is also **no per-corner calibration**, meaning unit-to-unit gain and zero variation is unaccounted for. That is a plausible contributor to problems 3 and 4 above.
