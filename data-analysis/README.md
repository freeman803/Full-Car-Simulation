# CFR26 Telemetry Analysis — `data-analysis/`

Analysis of the 2026 competition telemetry in `comp2026_data/`, answering: **what G's, roll and pitch did the car actually see, per event?** — so we know where we are before setting targets for the next suspension.

Everything here is **measurement-based**. Nothing imports from `corner-model/` or any other simulation model, deliberately.

## Getting the data

> ### ⚠️ TODO — pulling data from InfluxDB
>
> **Not written yet.** To fill this in, this section needs:
>
> - [ ] Where the InfluxDB instance lives (URL / host), and how to get access
> - [ ] The query used to export a session (bucket, measurement, time range)
> - [ ] Which export format/dialect to choose — the parser needs the **long format** with `_time`, `_field` and `_value` columns, not a pivoted wide table
> - [ ] Whether signals are selected at export time or everything is dumped
> - [ ] Where the shared CSVs are archived, so nobody re-exports unnecessarily
>
> Until then, ask whoever pulled the current set for a copy.

**The data is deliberately not in git.** `.gitignore` excludes `comp2026_data/`, `*.csv`, the `*.parsed.pkl` caches and all generated output.

Raw CSVs *can't* be committed regardless: the 11 files total 405 MB and `endurance_full.csv` alone is 235 MB, over GitHub's hard 100 MB per-file limit. But this is a deferred decision rather than a permanent rule — telemetry CSV compresses about 10×, which would put endurance at ~23 MB and the whole set at ~40 MB. If we revisit it, the options are Git LFS (preferred, keeps clones lean and scales to future seasons), or committing `.csv.gz` plus a one-time `gzip -d` — the latter needs a ~3-line change in `parse_influx.py`, which line-scans with plain `open()` and currently fails on gzip.

**Do not split `endurance_full.csv` to get under the limit.** Every chunk boundary becomes a `filtfilt` edge, and that is exactly what produced a fake 17.36mm pitch peak against a 16.33mm real one in `accel_corinne1` — splitting would manufacture that artifact at every seam, in the file holding the design-driving events. Mid-session chunks may also lack a stopped-car window to baseline against.

**Where to put your CSVs:** in `data-analysis/comp2026_data/`, or any folder you pass to `--dir`. Filenames matter — event type is detected from the name by case-insensitive substring match, first hit winning, in this order:

```
skidpad, autocross, endurance, brake, accel
```

So `braketest1.csv` → BRAKE, `accel_corinne1.csv` → ACCEL. A file matching none of them lands in an `unknown` group and gets skipped by the case scripts. Current naming for reference:

```
comp2026_data/
  accel_corinne1.csv  accel_corinne2.csv  accel_jamie_both.csv
  autocross_andrew1.csv  autocross_andrew2.csv
  autocross_josh1.csv    autocross_josh2.csv
  braketest1.csv  braketest2.csv
  endurance_full.csv
  skidpad_austin_both.csv
```

**First run is slower.** `parse_influx.py` writes a `<file>.csv.parsed.pkl` cache beside each CSV and reuses it while the CSV is unchanged, so subsequent runs are near-instant. Those caches are gitignored (369 MB for the current set).

**Sanity-check a new export before trusting it** — `--list-signals` costs about a second and needs no parse:

```powershell
uv run batch_signal_stats.py --dir comp2026_data --list-signals
```

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

## How much does the cutoff matter? — `cutoff_sweep.py`

Re-runs the whole case1–case4 pipeline at each of a list of frequencies and reports how much each headline number moves. The review pages show what a cutoff does to a **trace**; this shows what it does to the **number you report**.

```powershell
uv run cutoff_sweep.py --dir comp2026_data
uv run cutoff_sweep.py --dir comp2026_data --freqs 2 3 4 5 6 8 10 15 20
```

Cheap: a full pass over 11 files and 4 cases is ~20 s, so a seven-point sweep is a couple of minutes. It patches the cutoff constants on the case modules and calls `case_summary`'s collectors, so nothing is reimplemented and it cannot drift from what the cases really do. Both constants are set to the same value at each step — deliberately *not* production config — so each event shows its own sensitivity.

### Result: most numbers here are filter-dominated

Across 2–20 Hz, of 65 headline numbers: **6 move less than 2%**, and **35 move more than 10%**.

The split is clean and physical. **Skidpad steady-state numbers are nearly cutoff-independent**, because they report a *median over steady segments* — smooth low-frequency content a low-pass barely touches:

| quantity | 2 Hz → 20 Hz | spread |
|---|---|---|
| `case2.skidpad.front_deg` | 1.1017 → 1.1009 | **0.3%** |
| `case2.skidpad.rear_deg` | 1.2755 → 1.2730 | **0.3%** |
| `case2.skidpad.avg_deg` | 1.1810 → 1.1772 | **0.5%** |
| `case1.skidpad.sustained_lat_g_min` | 1.2593 → 1.2540 | **0.9%** |

**Transient peak numbers are dominated by it**, because a peak is exactly what a low-pass attenuates:

| quantity | 2 Hz → 20 Hz | spread |
|---|---|---|
| `case3.endurance.worst_deg` | 0.6016 → 0.9371 | **39%** |
| `case1.endurance.peak_lon_g` | 1.1960 → 1.7232 | **33%** |
| `case1.autocross.peak_lon_g` | 1.3749 → 1.7802 | **33%** |
| `case3.endurance.typical_deg` | 0.5683 → 0.8033 | **31%** |

**Every peak-based figure should be quoted with its cutoff attached.** "Peak longitudinal G was 1.65 g" is not a fact about the car without "at 5 Hz" beside it.

Two things the tool reports separately, both learned by getting them wrong first:

- **Sign flips.** Six quantities change sign across the sweep — `case4.skidpad.worst_travel_mm` reads +18.5 mm at 5 Hz and −19.8 mm at 8 Hz. That is not a 216% change in the physical answer; skidpad runs both directions, so the two candidate peaks are near-equal and the filter breaks the tie. Spread is measured on **magnitude** and the sign flip is flagged as its own fact. An earlier version differenced signed values and put seven such rows at the top of the table with 200%+ spreads.
- **Small bases.** `case4.*.worst_modes.warp` shows the largest spreads (49–231%), but warp is 0.5–1.7 mm — the percentage is large because the base is small, not because much is moving.

## Regression test — `test_regression.py`

Pins every headline number so a change that moves them has to be one someone **meant** to make.

```powershell
uv run test_regression.py --dir comp2026_data            # check
uv run test_regression.py --dir comp2026_data --update   # re-pin
```

Six real bugs were found and fixed here in quick succession — `VCPDU_lat`/`lon` read as g when the DBC says m/s², a hardcoded runs-per-direction cap that silently discarded data, step glitches winning the peak search, `filtfilt` edge artefacts, an inverted roll sign convention, and the `braketest2` misdiagnosis. Every fix moved published numbers, and nothing existed that would have caught any of them going the other way.

It pins the summary dicts from all four cases plus the **12-event step-glitch inventory**, and reports each difference with a percentage:

```
  cases.case4_combined_roll_pitch.endurance.worst_roll_deg
      pinned: -1.2569025802757943
      now:    -1.2498403951472068
      change: +0.562%
```

- **It is not a correctness test.** It cannot tell you a number is *right*, only that it is the *same*. That's the useful property while cutoff selection is in flight: when the per-signal cutoff table lands, every roll/pitch/travel figure will move, and the question is whether they moved where you expected.
- **It doesn't reimplement anything** — it calls `case_summary.py`'s collectors, which call each case's real analyse/report functions, so a methodology change is picked up rather than tested against a stale copy.
- **A failure is information, not an error to silence.** Read the diff, decide if the change was intended, then re-pin with `--update` and **commit `regression_expected.json`**. That commit is the record of what moved and why.

Verified end to end: changing `AUTOX_END_CUTOFF_HZ` from 5.0 to 6.0 was caught across every affected value with exit code 1.

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

All of these live in **`case_common.py`** and are imported by the case scripts. They used to be redefined in case2, case3 and case4 independently — the values agreed, but nothing enforced that, and `case_common.py` exists precisely because `case1` and `filter_compare` once drifted onto two different values of `G`.

| constant | value |
|---|---|
| Front track | 1219.2 mm (centre-to-centre) |
| Rear track | 1168.4 mm (centre-to-centre) |
| Wheelbase | **1543 mm** (1545 in `corner-model/Forces/car_data.py` is a known error on another branch) |
| Motion ratio, front | **1.15** (wheel ÷ spring) |
| Motion ratio, rear | **1.038** |

Front and rear motion ratios differ, which dictates *where* the conversion happens: every corner is converted to wheel travel **before** any roll, pitch or modal arithmetic. Differencing axles on raw shock-pot mm and applying one ratio afterwards is only valid when the ratios match, and they don't.

### mm → degrees

```
angle = atan(wheel_travel_mm / span_mm)      # span = track for roll, wheelbase for pitch
```

This is **exact, not a small-angle approximation** — `atan` is the exact relation for two vertical displacements separated by a horizontal span. The case2/case3/case4 docstrings described it as "small-angle" for a while, which was simply wrong; it never changed a number (linear and `atan` agree to 0.002% at 10 mm and 0.03% at 35 mm) but it implied a limitation that doesn't exist.

Pass **wheel** travel, not raw shock-pot mm.

### The one real approximation: whole-car "avg roll"

`AVG_TRACK_MM` converts a mean-mm over a mean-track rather than averaging two separately-converted angles. Because `atan` is non-linear and the two tracks differ by 50.8 mm, these are not the same: measured error is **0.17–0.19%** — 1.6201° the approximate way against 1.6231° exact.

Kept as-is deliberately so published numbers stay comparable with what's already been shared. Documented rather than silently corrected. Front and rear roll, reported separately, are each exact — it's only the combined figure that carries this.

## Shared foundation

Inherited by every case; none of them redefine these.

| | |
|---|---|
| **Filter** | 4th-order Butterworth, zero-phase (`filtfilt`). **2.0 Hz** skidpad, **5.0 Hz** everything else |
| **Units** | `G = 9.80665`. `VCPDU_lat`/`lon` are **m/s²** in the DBC and are divided by G |
| **Time** | The InfluxDB union grid is **not uniformly sampled**. Every duration is real elapsed `t[e]−t[s]`, never `sample_count × dt` — that errs by 3–5×. Scalar `dt` is used *only* for filter design |
| **Baselining** | Each corner is zeroed against its own stopped-car window (speed <0.5 m/s, ≥2s real, trimmed 0.5s/end; prefers file start → end → longest anywhere, which catches an endurance driver change). Mandatory: each pot carries its own zero offset, and differencing without removing it counts the offset as suspension movement. Step glitches are excluded from the window, and a **lockup guard** rejects candidate stops whose mean \|lon G\| ≥ 0.15 g |
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

## Case 5 — Roll and pitch gradient (°/g)

**Events:** roll on skidpad/autocross/endurance, pitch on accel/brake/autocross/endurance.

The headline suspension metric, and the one number the rest of the analysis was building toward. Cases 1–4 answer *"how much did the car roll?"* — a property of the **run**, since a driver who pushed harder gets a bigger number. Gradient answers *"how much does this car roll per unit of lateral acceleration"* — a property of the **car**, and the bridge to a roll stiffness in N·m/deg.

Nothing is reimplemented: roll comes from `case2_max_roll`'s loader and pitch from `case3_max_pitch`'s, so the angles behind these gradients are the exact numbers those cases report.

### The number

**Skidpad steady segments — the cleanest estimate, and the one to quote:**

| | gradient | R² |
|---|---|---|
| Front | **0.833 °/g** | 0.997 |
| Rear | **0.941 °/g** | 0.997 |
| Whole car | **0.886 °/g** | 0.998 |

`endurance_full` independently gives 0.812 / 0.918 / 0.864 °/g — a different event, different driver, 919k samples, agreeing to within 3%.

This lands squarely on the **0.83–0.94 °/g** hand-derived estimate. Two things are worth noting about that: the hand estimate's *range* turns out to have been the front-to-rear spread, and a completely independent check — dividing case2's skidpad roll angle by case1's sustained lateral G, neither of which computes a gradient — gives 0.814 / 0.943 / 0.873 °/g, within 2%.

**Pitch gradient** is 0.54 °/g, and accel (0.544) and brake (0.543) agree to three decimals despite being squat and dive respectively.

Intercepts are 0.002–0.101°, which is the baselining checking out: a level car at 0 g.

### Fitting choices

- **Intercept is fitted, not forced through zero.** The car is physically level at 0 g, so a large intercept is not a free parameter — it is evidence a baseline is off, and reporting it is the point.
- **Excluded:** step glitches, and samples below 2 m/s (a parked car is a dense cluster at the origin that inflates R² without informing the slope).
- **Transients are kept.** The scatter they produce is a result, not contamination — roll lags lateral G, so a corner entry and its matching exit trace different paths and the cloud opens into a loop. Steady-state skidpad gives R² = 0.997; autocross does not, and the width is the information. That is why the scatter plot is a deliverable and not just a diagnostic.
- **Signs are checked, not absolute-valued.** A positive raw slope would mean a convention flipped upstream, and is reported as an error rather than quietly hidden.

### Finding: two autocross runs have unusable front shock-pot data

The autocross files do not give one answer. Front gradient per file:

| file | front | rear | rear/front |
|---|---|---|---|
| `autocross_andrew2` | 0.780 | 0.884 | 1.13× |
| `autocross_josh1` | 0.794 | 0.895 | 1.13× |
| **`autocross_andrew1`** | **0.294** | 0.871 | **2.96×** |
| **`autocross_josh2`** | **0.311** | 0.905 | **2.91×** |

Per-corner travel per g isolates it completely — **both front corners drop by ~2.6× while both rears are untouched**:

| file | FL | FR | RL | RR |
|---|---|---|---|---|
| `autocross_andrew2` | 6.03 | −10.57 | 8.89 | −9.13 |
| `autocross_josh1` | 6.38 | −10.52 | 8.78 | −9.47 |
| `skidpad` | 6.56 | −11.04 | 9.13 | −9.95 |
| `endurance_full` | 6.36 | −10.93 | 9.37 | −9.34 |
| **`autocross_andrew1`** | **2.40** | **−3.86** | 8.55 | −9.21 |
| **`autocross_josh2`** | **2.50** | **−4.13** | 8.96 | −9.50 |

**This is a measurement problem, not the car.** Three things establish that:

**The runs are effectively identical.** In chronological order — `josh1` 18:38, `josh2` 18:47, `andrew1` 19:37, `andrew2` 19:39 — the pattern is normal, bad, bad, normal. Lateral-G content is the same in all four (\|lat\| p99 1.47–1.62 g, range 3.18–3.31 g), so it is not driving style. And `andrew1` → `andrew2` are **two minutes apart**, which rules out any physical change to the car. (There is also no anti-roll bar on the 2026 car, so an earlier ARB hypothesis in this file was wrong on the mechanism as well as the timing.)

**The decode is fine.** `disp ← volt` fits −25.495 to −25.511 mm/V in every file, against the documented global −25.510. Nothing is wrong with units or scaling.

**The front pots are sitting at the end of their range.** The raw voltage is what differs:

| file | FL volt median | FR volt median | front gradient |
|---|---|---|---|
| `josh1` | 0.816 | 1.241 | 0.794 |
| `josh2` | **0.332** | **0.550** | 0.311 |
| `andrew1` | **0.378** | **0.597** | 0.294 |
| `andrew2` | 0.855 | 1.340 | 0.780 |

Since `disp = −25.51·V + c`, low voltage is high extension. In the bad runs both front pots sit at roughly 0.2–0.8 V — the bottom of their electrical range and the maximum-extension end of their stroke — where they read 70.7 mm against the 63.6–66.7 mm every other file tops out at, and where travel compresses (`josh2` FL sweeps just **7.2 mm** against 22.4 mm in `josh1`).

This is the same phenomenon as *Known data problems #3* ("FL shock pot is suspect", static baseline wandering 42.4–66.9 mm across sessions) — but it affects **both front pots**, not just FL, and it now has a measured consequence: it more than halves the apparent front roll gradient.

**What to do with it.** Treat `autocross_josh2` and `autocross_andrew1` front data as unusable, and quote the front gradient from `josh1`, `andrew2`, skidpad and endurance, which agree at **0.78–0.83 °/g**. The rear is unaffected in all four files and needs no exclusion. The **pooled autocross figure of 0.542 °/g must not be quoted** — `case5_gradients.py` prints per-file gradients and warns when the front spread exceeds 1.5×, and its per-corner table is what separates a one-channel sensor fault from an axle-wide one.

The open question is *why* the front pots ended up at their extension limit for those two runs and not the neighbouring ones. A physical check of the front pot mounting and stroke range would settle it; the telemetry can localise the problem but not diagnose the hardware.

## What each file actually is — official results and run provenance

From the [FSAE Electric 2026 official results](https://www.fsaeonline.com/CompResources/2026/07af50d8-cbb6-4b9b-aaf8-5ff6a7e44057/FSAE_2026_MI6_results.pdf) plus team context. **Concordia is car #43, 19th overall, 475.1 points** (3rd in Cost at $25,197; car is 1 motor, 370 V, **215.5 kg** — the mass you need to turn a °/g gradient into N·m/deg).

This matters because a telemetry file is not self-describing. Knowing that one autocross run went off course, or that an endurance lap contains an unscheduled stop, changes how you read an anomaly in it.

### Autocross — Josh ran first, then Andrew

| official run | file | raw time | penalty | adjusted |
|---|---|---|---|---|
| 1 | `autocross_josh1` | 50.508 | **1 off course (+20 s)** | 70.508 |
| 2 | `autocross_josh2` | **49.541** | clean | 49.541 — best |
| 3 | `autocross_andrew1` | 54.514 | clean | 54.514 |
| 4 | `autocross_andrew2` | 51.687 | clean | 51.687 |

18th place, 81.81 points. Our own measurements corroborate the ordering: `andrew1` is the slowest official run *and* the slowest in telemetry (65.8 s moving, against 57–59 s), with the longest distance (804 m against 787–791 m).

### Endurance — Andrew first, then Josh. **DNF on the last lap.**

**1483.688 s, 21 laps completed**, DNF. Official lap times:

```
68.197  68.186  71.313  67.568  67.159  69.294  69.068
70.252  69.225  70.102  76.539  121.893  68.476  67.020
64.873  66.610  66.858  66.799  64.425  63.364  66.467
```

**Lap 12 is 121.893 s against a ~67 s norm.** That is the driver change plus a *momentary stop near the beginning of Josh's stint* — team-confirmed, not inferred. Lap 11 at 76.539 s is the run-in to it. The last seven laps (63–67 s) are the fastest of the event, so the car recovered fully.

Note `endurance_full.csv` spans 1740 s against the official 1483.7 s, so the file holds roughly four minutes beyond the scored run.

**This gives lap detection a ground truth.** Any lap detector can be validated against 21 known laps with known durations, rather than eyeballed.

### Skidpad — Austin only

15th, best 5.178 s. Austin ran first and **only his two runs were pulled**: 5.461/5.122 R/L (avg 5.291) and 5.297/5.061 (avg **5.178**, the counting run). The second driver DNF'd one run and was slower, so that data was deliberately not exported. `skidpad_austin_both.csv` is therefore both of Austin's runs and nothing else.

### Acceleration — Jamie first, then Corinne

20th, best 4.521 s. Runs were 4.569 / **4.521** (Jamie, both in `accel_jamie_both.csv`) then 4.604 / 4.601 (`accel_corinne1`, `accel_corinne2`). Remarkably consistent across drivers — 4.52–4.60 s.

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

### 5. `braketest2.csv` — earlier "unreliable" verdict was WRONG

This file was previously flagged as unreliable on three counts: shock-pot noise 10–20× every other file (0.394/0.667mm against a 0.031mm median), elevated combined-angle noise, and filter overshoot stuck at 106% across all cutoffs. **All three were the same artefact, and the file is fine.**

It holds step glitches at 46.23s and 46.33s, and `find_static_window` selects 0.5–50.2s as its stopped-car window — so **the glitches sit inside the baseline window**. The 10–20× "noise" was std computed across a step discontinuity, not sensor noise. Masking the glitch:

| corner | baseline median as-is | glitch-masked | std as-is | std masked |
|---|---|---|---|---|
| FL | 53.330 | **53.330** | 0.570 | **0.007** |
| FR | 38.380 | **38.380** | 0.964 | **0.024** |
| RR | 41.340 | **41.320** | | |

The glitch mask is now applied to baselining (`static_baseline(..., bad_mask=...)`). Across all 11 files this moves exactly **one** number: `braketest2`'s RR baseline, by **0.02 mm**. FL and FR are unchanged, as the table above says. That 0.02 mm propagates into six case4 brake figures by at most 0.72%. The mask is there for the *std* column, not the median one — see below.

Two conclusions. The **baseline was never damaged** — `static_baseline` uses a median, which is robust to the step, identical to three decimals. And with the glitch excluded the file's noise is **0.007–0.043mm**, making it one of the *cleanest* in the set rather than the worst.

The window is also genuinely stopped (mean longitudinal G +0.005 g), so it is not a lockup being mistaken for a standstill — a real risk in principle, since `VCFRONT_vehicleSpeed` comes from wheel speed and reads ~zero during a four-wheel lockup while the car is still moving.

**There is now a code guard for this**, not just a note. `find_static_window(..., lon_g=...)` rejects any candidate stop whose **mean** \|lon G\| reaches 0.15 g.

Two details matter. It is applied **per run, not per sample** — the per-sample version was tried first and is wrong: a genuine stop briefly touches 0.26–0.94 g as the car rolls to a halt, so sample-wise rejection fragments real stops, and measurably did (it moved `accel_jamie_both`'s window from 0.0–9.2 s to an entirely different 17.2–25.3 s, and trimmed nine others). A lockup is a *sustained* ~1 g deceleration, so the mean over the run is the right statistic. Every genuine stop in `comp2026_data` averages **0.008–0.031 g**, two orders of magnitude clear of the threshold.

The guard therefore changes **nothing** on the current data — all 11 windows are byte-identical with and without it. It was verified on a synthetic file instead: given a real standstill and a four-wheel lockup both reading speed ≈ 0, it picks the standstill; given only the lockup, it returns `None`, so `baselines_found=False` and the caller warns rather than silently baselining against a hard-braking car.

**Context that makes this the opposite of a throwaway file:** `braketest2` is the brake test that *passed* at competition — up to the required speed, braking at the mandated point, all four wheels locked. It is prime data.

The only genuine issue is the step glitches themselves, which `find_step_glitches()` now rejects automatically. One caution remains: any *std-based* measurement over a window containing a glitch will be inflated, so re-derive noise floors with the glitch mask applied.

### 6. IMU 2-sample spikes — visible in plots, harmless to the numbers

`VCPDU_lat` and `VCPDU_lon` carry isolated spikes that are **not vehicle motion**. This is the big downward spike visible in `accel_corinne1`'s longitudinal traces, and it is not unique to that file.

The signature is unmistakable and consistent across files:

| file | channel | value | samples |
|---|---|---|---|
| `accel_corinne1` | lon | −20.675 m/s² (**−2.108 g**) | 2 |
| `endurance_full` | lat | +27.591 m/s² (**+2.813 g**) | 2 |
| `autocross_josh1` | lon | +24.371 m/s² (**+2.485 g**) | 2 |
| `autocross_andrew2` | lat | −21.519 m/s² (**−2.194 g**) | 2 |

Three things mark these as artefacts rather than data:

- **Always exactly two consecutive samples, 10 ms apart**, holding a *bit-identical* value. A real accelerometer at a genuine peak does not produce the same float twice — noise alone would differ in the last bits.
- **Physically implausible.** 2.1–2.8 g where each file's own p99.9 is 0.9–1.9 g, reached in a single 10 ms step of 7–20 m/s².
- **Not a DBC rail** — the value differs per file, so this is not the brake-pressure-style saturation seen in `endurance_full`'s brake channel below.

**They do not affect any reported number.** Verified on `endurance_full`, whose spike is the largest at 2.813 g: the whole-file filtered maximum is **1.7798 g with the spike and 1.7798 g with it removed** — identical. The 5 Hz low-pass eliminates a 2-sample impulse, and the local filtered peak at the spike is only 1.09 g, well below the file's actual 1.78 g maximum elsewhere. Case 1's peak G figures stand.

**Where they do bite is the peak-attenuation table**, whose denominator is the raw *max*. A file whose raw max is a spike reads as if the filters were destroying signal (57–66% retained) when they are correctly rejecting an artefact. `filter_compare.py` prints a `raw p99.9` column beside the max and flags any cell where the two diverge by more than 1.3× — see its `spike_dominated` flag.

### 7. `endurance_full.csv` brake pressure saturates

Its front pressure p99 is exactly 2000 psi, the top of the DBC range `[0|2000]`. Pressure-derived peaks there are floors, not maxima.

### 8. IMU attitude signals

`VCPDU_angleRoll` / `anglePitch` read ±20–36° against ±1.3° derived from the shock pots — consistent with an uncalibrated gravity-vector tilt rather than chassis attitude (the DBC carries `IMU_UNCALIBRATED` and `IMU_YAW_CALIBRATION_FAILED` warnings). Not used. The raw *rates* (`VCPDU_roll`/`pitch`, deg/s) are a separate question and have not been validated.

---

## Open questions

- **Low-pass cutoff for accel/brake.** No cutoff was ever chosen for these two events — they inherit `AUTOX_END_CUTOFF_HZ` (5 Hz), a constant validated for autocross/endurance transients. It matters: peak pitch moves ~12% across 2→10 Hz. See *Spectral analysis* below — an earlier version of this entry said a real 6–8 Hz mode made the choice delicate, and that turned out not to be true, which makes the decision simpler than it looked.
- **Motion ratio** is a single value per axle. If it varies meaningfully with travel, a curve would be more accurate.
- **Case 7 from the original brief (max yaw timing)** is deliberately not implemented.

## `filter_compare.py`

Compares low-pass cutoffs across **9 signals** — lateral/longitudinal/combined G, roll, pitch, vehicle speed, front/rear brake pressure, and steering angle (flagged unusable). Roll and pitch are included because those are what the case scripts actually report on; picking a cutoff from the G traces alone leaves the shock-pot cutoff unvalidated.

```powershell
uv run filter_compare.py comp2026_data/accel_*.csv --freqs 5 8 --zoom-on-peak
uv run filter_compare.py comp2026_data/braketest1.csv --freqs 2 5 10 --zoom-at 100
```

### Three views per signal

A single overlay hid the data it was meant to show, and the cause is structural rather than cosmetic: **the higher the cutoff, the closer the filtered trace is to raw**, so the 15 and 20 Hz traces land almost exactly on the raw trace and — drawn last — paint over raw *and* every lower cutoff. Sweeping more frequencies makes it strictly worse, so no palette change fixes it. Each signal now produces:

| view | what it's for |
|---|---|
| `_panels` | **Primary.** Small multiples, one panel per cutoff, raw redrawn pale behind each. Nothing can be occluded because nothing competes |
| `_residual` | **What settles a borderline call.** `raw − filtered`, i.e. exactly what each cutoff *discards*, with RMS per panel. A formless residual means the cutoff is safe; coherent oscillation means real signal is being deleted |
| `_overlay` | All cutoffs on one axis — still the best view for judging *where* traces separate. Z-order is reversed (highest cutoff drawn first) so the lowest cutoff ends on top instead of buried |

Each cutoff gets a **distinct hue**, in fixed slot order by ascending frequency, so a given cutoff is the same colour on every signal and every file. A sequential single-hue ramp was tried first — cutoff is strictly an ordered magnitude, which argues for one — but seven steps of the same blue proved unreadable on a busy trace, and telling "the third blue" from "the fourth" is exactly what the overlay asks you to do. The palette is validated at 7 slots on the light surface (worst adjacent CVD ΔE 9.1, normal-vision ΔE 19.6); aqua, yellow and magenta fall below 3:1 contrast, so every view carries visible labels and never relies on colour alone. Past **8 cutoffs** the script raises rather than cycling hues — sweep fewer at a time.

Plots render at **220 dpi**, because the review pages scale them down to fit the column and the lightbox then blows them back up.

Prefer the `_zoom` views for choosing a cutoff. At full-file extent every cutoff collapses into the same smear and the views are context only.

- Prints a **peak-attenuation table** — how much of each signal's peak survives each cutoff. The numerical version of what the plots show by eye. Also written to `peak_attenuation.json` per file, which `build_cutoff_review.py` reads.
- **Read low percentages carefully.** The table's denominator is the raw *max*, which on some files is a 1–2 sample spike rather than the real peak of the manoeuvre — `endurance_full`'s raw lateral G maxes at **2.813 g** and holds 33 samples above 2.0 g, which is not physical for this car. A `raw p99.9` column sits beside the max and cells where the two diverge by >1.3× are flagged `spike_dominated`. In those cells a low "% retained" means the filter is *rejecting a glitch*, not destroying signal.
- `--skip-plots` refreshes `peak_attenuation.json` without regenerating the plots.

## Choosing cutoffs — `build_cutoff_review.py`

`case_common.py` currently carries exactly **two** cutoff constants and applies them to every signal regardless of content. Accel and brake have no chosen cutoff at all — they inherit the 5 Hz autocross value by accident of the `if/else` in each case script.

This tool lays out every decision that actually needs making — **29 cells**, as (quantity × event) rather than a mostly-N/A 9×5 grid — puts the relevant plots beside each one, and gives you somewhere to record the answer. It decides nothing itself.

```powershell
uv run build_cutoff_review.py
```

| output | |
|---|---|
| `review_cutoffs/<event>.html` | one scrollable page per event, plots inline in worklist order |
| `cutoff_decisions.yaml` | one block per cell with blank `chosen_hz:` / `why:` fields |

**Click any plot to zoom.** The pages carry a lightbox — scroll to zoom (about the cursor, so the detail under the pointer stays put), drag to pan, `fit` / `1:1` buttons, Esc to close. The inline images are scaled down to fit the column; the lightbox is where the 220 dpi detail actually becomes visible.

**"open interactive ↗" on the overlay** loads a Plotly version where each cutoff can be toggled from the legend — click to hide one, double-click to isolate it. That's the question a static overlay can't answer once you're down to two or three candidates ("what does this look like *without* 15 and 20 Hz?"). Box-zoom and pan come free. Generated at zoom extent only, and decimated to ~3000 points for display — the filtering still happens at full grid density, so it's the real filtered signal, just not every redundant sample of it.

Note the `_zoom` window is **10 s** by default, narrowed from 20 s because seven panels across 20 s left each cutoff too few pixels to judge. `--zoom-duration` overrides it.

Roll and pitch each appear **twice**, under different quantities. That is the point, not a duplication: `case2`/`case3` report them as body **angles** while `case4` reports physical wheel **travel**. High-frequency wheel motion is real travel but is not chassis attitude, so the travel answer can legitimately sit *higher* than the angle answer even though it is the same four sensors.

## Spectral analysis — `spectral_analysis.py`

Runs on a true 100 Hz grid (a Fourier transform of non-uniformly sampled data is undefined, and the union grid's zero-order-hold staircase would manufacture broadband energy that no sensor measured). Works in `case4`'s exact heave/roll/pitch/warp modal basis, because a PSD peak alone identifies nothing — what distinguishes a body mode from local wheel motion is **how the corners move relative to each other**.

```powershell
uv run spectral_analysis.py --dir comp2026_data
uv run spectral_analysis.py --dir comp2026_data --band 4 12
```

### Result: there is no 6–8 Hz mode

This README previously recorded "a real **6–8 Hz mode carrying 5.88mm** of travel" and treated it as the crux of every cutoff decision. **It is not supported by the data.**

| mode | verdict across 11 files |
|---|---|
| heave | 8/11 have a prominent peak, but at 1.1, 1.1, 3.4, 3.5, 3.9, 8.0, 8.8, 21.9 Hz — **no cluster** |
| roll | 9/11 prominent, at 1.1–21.8 Hz — **no cluster** |
| pitch | only 6/11 have a prominent peak at all |
| warp | 9/11 prominent, at 1.1–21.9 Hz — **no cluster** |

A resonance is a property of the structure, so it has to land at the *same* frequency file after file. These don't. Inter-corner coherence says the same thing independently — it never exceeds **0.41** in any band:

| band | FL–FR | RL–RR | FL–RL | FR–RR |
|---|---|---|---|---|
| 1–4 Hz | 0.22 | 0.24 | 0.27 | 0.21 |
| 4–9 Hz | 0.29 | 0.41 | 0.21 | 0.24 |
| 9–16 Hz | 0.13 | 0.14 | 0.12 | 0.12 |

Coherence that low means the corners are **not** moving together, so what the shock pots see above 1 Hz is largely uncorrelated per-corner content — road input and sensor noise — rather than coordinated body motion.

**This simplifies the cutoff decision.** There is no resonance to avoid sitting on, so 5 and 8 Hz are not special, and the choice is the plainer one of how much uncorrelated content belongs in each reported number.

Two cautions on the method. Local maxima on a falling spectrum are mostly ripple, so a peak must also stand above its local background — an earlier pass here reported the roll-off shoulder as a mode. And a peak count is not a mode: taking the median of scattered peak frequencies produced a confident "1.50 Hz mode" from frequencies spanning 1.12–21.88 Hz, which is why the clustering test exists.

Leaving a cell at its current value is a valid answer — but the `why` still gets filled in, so the next person knows it was decided rather than inherited.
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
