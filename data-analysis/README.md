# CFR26 Telemetry Analysis — `data-analysis/`

## What this is

Six analysis scripts that read the **2026 competition telemetry** (CFR26, the car that ran at FSAE Michigan) and answer one question: **what G's, roll and pitch did the car actually see, per event?** The point is that the next car's suspension — CFR27, which the rest of this repo models — gets designed against measurement instead of assumption.

Everything here is measurement-based. Nothing imports from `corner-model/` or any simulation, deliberately. It is a **separate, self-contained project inside this repo.**

**Three ways in, depending on why you're here:**

| you want | go to |
|---|---|
| **The answers.** The measured envelope, one table | [Results](#results--the-measured-envelope) below, or open `plots/case_summary.html` |
| **To trust the answers.** How each number is made, and what's wrong with the data | [How the numbers are made](#how-the-numbers-are-made) and [Known data problems](#known-data-problems) |
| **To run or extend it** | [Setup](#setup) and [Extending it](#extending-it) |

If you read nothing else, read [the three things to know](#results--the-measured-envelope) under the results table. Quoting a number from here without them is how this analysis has been misread before.

---

## Setup

**1. You need the telemetry, and it is not in this repo.** This is the blocker, so deal with it first — every script below does nothing without it. See [The data](#the-data). For the 2026 competition data csvs, download the `comp2026_data/` folder on the Capstone Teams in the Test Data Channel > raw data csvs.

**2. Install the environment.** From the **repo root**, following the root `README.md` prerequisites (Git + `uv`):

```bash
uv sync
```

**3. Run everything from inside `data-analysis/`.** All the commands below assume that working directory. They are plain `uv` invocations — nothing here is shell- or OS-specific, so PowerShell, cmd, bash and zsh all work.

```bash
cd data-analysis
```

## Quick start

```bash
uv run batch_signal_stats.py --dir comp2026_data --list-signals   # sanity-check an export (~30 s)
uv run case_summary.py --dir comp2026_data                        # one table, all six cases (~4 min)
uv run case1_max_gs.py --dir comp2026_data                        # ...and each case for detail
uv run test_regression.py --dir comp2026_data                     # after changing anything
```

`--dir` is the only option the case scripts take (default `comp2026_data`); `--help` confirms it. The tools have a few more — `test_regression.py --update`, for instance.

**What to expect.** With cached parses, `case_summary.py` takes ~4 minutes and prints almost nothing until it finishes — six `Collecting…` lines, then the table. The **first** run of anything is much slower, because each CSV is parsed and cached (see [The data](#the-data)); budget ~800 MB of disk for `comp2026_data/` once the `.parsed.pkl` caches are written beside the CSVs. If the data directory is missing or empty, scripts report no files and exit rather than erroring.

**Reports.** Each *case* script prints a console report and writes `plots/<case>/report.html` — headline numbers, the console output, and every plot it generated on one page. **The HTML is the thing to hand to someone; the console is for working.** Every embedded plot has an `open full width ↗` link, because the report column is too narrow to work in.

`case_summary.py` writes only `plots/case_summary.{html,md}` — it does **not** produce the per-case reports. To populate `plots/index.html`, which links them all, run all six case scripts.

| file | what it is |
|---|---|
| `case1_max_gs.py` | Max lateral / longitudinal / combined G |
| `case2_max_roll.py` | Max roll angle |
| `case3_max_pitch.py` | Max pitch angle |
| `case4_combined_roll_pitch.py` | Combined roll + pitch, as per-corner wheel travel |
| `case5_gradients.py` | Roll and pitch gradient (°/g) — a property of the **car**, not the run |
| `case6_max_yaw.py` | Max yaw rate (°/s) and the corner radius actually driven |
| `case_common.py` | Shared constants and helpers. Anything that must stay identical across cases lives here |
| `case_summary.py` | The consolidated table across all six cases |
| `case_report.py` | Builds the HTML reports. Not run directly |
| `parse_influx.py` | Andrew's InfluxDB CSV parser. **Do not modify** |
| `test_regression.py` | Pins every headline number |

Other tools are listed under [Tools](#tools).

## The data

**Not in git** — `comp2026_data/`, `*.csv` and the `*.parsed.pkl` caches are all gitignored. (Raw CSVs can't be committed anyway: 405 MB total, and `endurance_full.csv` alone is 235 MB against GitHub's 100 MB per-file limit.)


Put CSVs in `data-analysis/comp2026_data/` or pass `--dir`. **Event type is detected from the filename** by case-insensitive substring, first hit winning, in this order: `skidpad, autocross, endurance, brake, accel`. A file matching none lands in `unknown` and is skipped.

```
accel_corinne1.csv  accel_corinne2.csv  accel_jamie_both.csv
autocross_andrew1.csv  autocross_andrew2.csv  autocross_josh1.csv  autocross_josh2.csv
braketest1.csv  braketest2.csv  endurance_full.csv  skidpad_austin_both.csv
```

First run is slow; `parse_influx.py` caches a `.parsed.pkl` beside each CSV and reuses it while the CSV is unchanged.

**Never split `endurance_full.csv` to get under a size limit.** Every chunk boundary becomes a `filtfilt` edge, which manufactures fake peaks (a 17.36 mm pitch peak against a 16.33 mm real one, in `accel_corinne1`), and mid-session chunks may have no stopped-car window to baseline against.

---

## Results — the measured envelope

| Event | Sustained lat G | Peak lat G | Peak lon G | Roll ° | Pitch ° | Worst corner travel | Roll grad °/g | Pitch grad °/g | Peak yaw °/s |
|---|---|---|---|---|---|---|---|---|---|
| SKIDPAD | 1.26–1.33 g | — | — | 1.49 | 0.13* | −20.8 mm (FR) | **1.119** | — | 78.7 |
| ACCEL | — | — | — | — | 0.45* | +15.8 mm (RR) | — | 0.672 | 52.6 |
| BRAKE | — | — | — | — | 0.98 | −22.2 mm (FR) | — | 0.676 | 93.3 |
| AUTOCROSS | — | **1.76** | 1.39 | **1.88** | 0.80 | −21.5 mm (FR) | 1.056 | 0.681 | **105.1** |
| ENDURANCE | — | 1.60 | **1.72** | 1.82 | **1.18** | **−24.3 mm (FR)** | 1.091 | 0.727 | 99.3 |

**Reading the table.**

- `*` — a **sustained** value (median over the steady window), not a peak. That event has no separate peak by design.
- `—` — **that case does not cover that event.** It never means missing or failed data. Skidpad has no "Peak lat G" because case 1 reports a median there on purpose, not because a peak is unavailable.
- **Roll ° and Pitch ° are unsigned magnitudes.** The sign is in the case sections: brake pitch is dive (negative), accel pitch is squat (positive).
- **"Worst corner travel" is signed, and is the one column that is *not* ground-referenced.** Negative is compression. It is real suspension travel in millimetres at the wheel — **do not apply the ×1.25 ground-referencing multiplier to it.** That multiplier converts *angles*; travel is already the physical quantity a bump stop limits. See [case 4](#case-4--combined-roll--pitch).

**Three things to know before quoting any of these:**

1. **Every angle and gradient here is ground-referenced** — chassis attitude relative to the *road*, tyre deflection included. That is the reference the **Simplified Steady State Suspension Spreadsheet** predicts in and that published FSAE gradients use, so these compare against a target directly. The suspension-referenced figure the shock pots see is ~19–20% lower and sits beside each headline on the case report pages. See [Ground-referenced angles](#ground-referenced-angles).
2. **Every peak figure is filter-dependent.** Across the 2→20 Hz sweep (`cutoff_sweep.py`, re-run 2026-08-06), **46 of 82 headline numbers move more than 10%** and only 10 move less than 2%. `case3.endurance.worst_deg` spans 0.763→1.198° (37.0%) and `case1.endurance.peak_lon_g` spans 1.196→1.744 g (31.9%). (The percentages are reference-independent — a constant multiplier cannot change a spread — so the reference switch left every sensitivity figure here untouched.) *"Peak longitudinal G was 1.72 g"* is not a fact about the car without **"at 10 Hz"** beside it. Steady-state skidpad numbers are the exception: they move 0.3–0.9%, because a median over a steady window is not something a low-pass touches.
3. **The columns come from six different methodologies.** A peak, a median over a steady window, and a fitted slope are not the same kind of number; `plots/case_summary.html` carries a case-attribution header row for this reason.

`case_summary.py` **recomputes nothing.** It imports the cases and calls their own analyse/report functions with output suppressed, so the table cannot drift from what the individual scripts print.

---

## How the numbers are made

> **Sources.** [`REFERENCES.md`](REFERENCES.md) is the bibliography, including
> what is *not* sourced and must not be presented as if it were. Per-case
> derivations with citations are in [`docs/case2.md`](docs/case2.md) and
> [`docs/case4.md`](docs/case4.md), and are linked from each report page.

Every case follows the same pipeline, all of it in `case_common.py`:

```
parse → union time grid → per-corner static baseline → shock mm → WHEEL mm → filter → measure
```

### Vehicle constants

These are **as-built CFR26 values, not assumptions** — the suspension the team designed and the car that ran at competition.

| constant | value | where it comes from |
|---|---|---|
| Front track | 1219.2 mm (centre-to-centre) | as designed |
| Rear track | 1168.4 mm | as designed |
| Wheelbase | **1543 mm** | as designed |
| Motion ratio, front | **1.188** (wheel ÷ spring) | a **team design choice**, then **measured and validated on the CFR26 car** |
| Motion ratio, rear | **1.038** | same |
| Springs | 225 / 200 lbf/in front / rear = 39.40 / 35.03 N/mm | the rates the team **chose and ran at competition** |
| Wheel rates (`k_spring / MR²`) | 27.92 / 32.51 N/mm | derived from the two rows above |
| Tyre vertical rate | 122.59 N/mm (**700 lbf/in**), same front and rear | Simplified Steady State Suspension Spreadsheet |
| Anti-roll bar | **none on the 2026 car** — the four springs are the entire roll stiffness | as built |

Because they are measurements rather than free parameters, **do not retune a motion ratio to make something else agree.** That was tried once against the front/rear roll disagreement and is retracted: it only closes the gap by assuming the chassis is rigid *and* all four pots are correctly calibrated, and the measurement overrides both.

**Front and rear motion ratios differ, which dictates where the conversion happens:** every corner is converted to wheel travel *before* any roll, pitch or modal arithmetic. Differencing axles on raw shock-pot mm and applying one ratio afterwards is only valid when the ratios match, and they don't. All angles scale linearly with motion ratio.

The front wheel rate coming out **softer** than the rear (27.92 vs 32.51 N/mm) despite the stiffer front spring is not a transcription error — it is the MR² term, and 1.188² against 1.038² more than reverses the 225/200 spring split.

### mm → degrees

```
angle = atan(wheel_travel_mm / span_mm)      span = track for roll, wheelbase for pitch
```

**Exact, not a small-angle approximation** — `atan` is the exact relation for two vertical displacements separated by a horizontal span. Pass **wheel** travel, not raw shock-pot mm.

*The one real approximation:* whole-car "avg roll" converts a mean-mm over a mean-track rather than averaging two separately-converted angles. Because `atan` is non-linear and the tracks differ by 50.8 mm, these differ by **0.17–0.19%**. Kept deliberately, so published numbers stay comparable with what has already been shared. Front and rear roll, reported separately, are each exact.

### Ground-referenced angles

**Every angle these scripts report is ground-referenced** — chassis attitude relative to the **road**, with the tyre's own deflection included. Under load transfer the outside tyre squashes and the inside extends, tilting the wheel-centre line against the road, and camber relative to the road is what sets grip. That is why the design side works in this reference: the **Simplified Steady State Suspension Spreadsheet** builds roll stiffness from the **ride rate** (wheel rate and tyre rate in series), so its predicted roll and pitch gradients are ground-referenced, and so is essentially every published FSAE roll gradient.

**The raw measurement is not.** A shock pot is bolted between chassis and upright, so both its ends sit *above* the tyre — it can only see chassis roll relative to the line joining the two **wheel centres**. Call that suspension-referenced. It is carried beside every headline number (`[susp-ref …]` in the console, a sub-line under each report card) because the spring cross-check below validates *that* figure and you need it to audit the conversion. It is **not** the number to quote.

> **This reversed on 2026-08-06.** These reports used to lead with the suspension-referenced figure, which is how a completely correct measurement came to look ~20% too small against a ground-referenced design target — and, compounded with a stale motion ratio, is what produced the suspension team's *"at least 2× low"* report. Nothing about the measurement changed; the reference the reports lead with did. To convert an older number quoted from this repo, multiply by the table below.

The conversion is **exact** for load-transfer-driven roll and pitch, because the same load increment deflects spring and tyre in series:

```
suspension roll at an axle = 2·ΔF / (k_wheel · track)
tyre roll        at an axle = 2·ΔF / (k_tyre  · track)
⇒  ground roll = suspension roll × (1 + k_wheel / k_tyre)
```

Sprung mass, CG height and weight distribution all cancel — **tyre rate is the only input.**

| multiplier | value |
|---|---|
| Front roll | ×1.228 |
| Rear roll | ×1.265 |
| Whole-car roll | ×1.247 (stiffness-weighted) |
| Pitch | ×1.245 |

Since tyre rate is the only input, **these multipliers move with it** — a stiffer tyre deflects less, so less of the chassis's motion against the road is tyre, and every ground-referenced angle here shrinks. The spreadsheet's own predicted gradients move with it in the same direction, because its ride rate is wheel-in-series-with-tyre, so the **predicted-vs-measured gap is unchanged at any tyre rate**. See [the open questions](#open-questions).

**Two caveats.** Whole-car roll uses **one stiffness-weighted multiplier** rather than being rebuilt from the two axles — case2's front/rear/avg each come from their own peak search at different instants, so averaging converted peaks combines moments that never coexisted (~7% high on endurance). And the conversion holds for a peak driven by **load transfer**; a peak driven by a kerb strike is not deflecting the tyre proportionally.

**`case4` per-corner travel is deliberately not converted** — that is real suspension travel, and it is what bump-stop and droop margin are measured in.

### Filtering, baselining, peaks

| | |
|---|---|
| **Filter** | 4th-order Butterworth, zero-phase (`filtfilt`). **10.0 Hz on every event and every signal**, deliberately — one cutoff, so no number is the product of a per-event tuning choice. The single exception is **front brake pressure at 3.0 Hz**: that channel is sampled at 10 Hz, so its Nyquist limit is 5 Hz and 3 Hz keeps a margin below it rather than filtering right at the edge. Selected with `cutoff_sweep.py` and `filter_compare.py`, replacing an inherited 2/5 Hz that had never been checked — the low cutoffs turned out to be the *unstable* region and 5 Hz sat on the slope |
| **Units** | `G = 9.80665`. **`VCPDU_lat`/`lon` are m/s² in the DBC**, not g, and are divided by G. Reading them as g gated segmentation at an effective 0.031 g and understated accel pitch by up to 32% before it was caught |
| **Time** | The InfluxDB union grid is **not uniformly sampled** — median spacing 0.39 ms, gaps from 0.019 to 19.3 ms, built by zero-order hold. Every duration is real elapsed `t[e]−t[s]`, never `sample_count × dt`, which errs by 3–5×. Scalar `dt` is used *only* for filter design |
| **Sample rates** | Everything is 100 Hz except `VCFRONT_brakePressure` at **10 Hz** and `VCFRONT_steeringAngle` at 20 Hz frames (10 Hz useful bandwidth). `uniform_resample()` resamples from RAW samples, never the ZOH union grid — a staircase's step edges carry broadband energy no sensor measured |
| **Baselining** | Each corner is zeroed against its own stopped-car window (speed <0.5 m/s, ≥2 s real, trimmed 0.5 s/end). **Mandatory** — each pot carries its own zero offset, and differencing without removing it counts that offset as suspension movement. Files containing a shock-pot step are cut at the step and each segment gets its own local baseline (`segmented_baselines`); `baseline_is_reproducible()` cross-checks every stopped window in a file against a 4.0 mm threshold. A **lockup guard** rejects candidate stops whose mean \|lon G\| ≥ 0.15 g, so a four-wheel lockup (speed ≈ 0 from wheel-speed) is never mistaken for a standstill |
| **Glitch rejection** | Per-sensor-update jumps >8 mm are masked ±1 s. Not a judgement call: over 7.6M real updates, legitimate jumps have p99.99 = 1.78 mm and max 4.38 mm; the glitches are 20.35–23.32 mm, and **nothing falls in between** |
| **Peak detection** | `find_peaks` by **prominence only**. *Prominence* is how far a peak stands above the higher of the two valleys either side of it — how far you must descend before you can climb to anything taller. It filters on how much a peak **stands out from its own surroundings**, not on absolute height, so ripple riding on top of a large sustained value is rejected while a genuine excursion from a quiet baseline is kept. No index-based `distance` argument is used, since a fixed sample count spans different real time in different parts of a file; spacing is enforced afterwards against elapsed time — tallest first, reject anything within 1.0 s of an accepted peak. Top 5 per event, pooled across that event's files |
| **Edge trimming** | The outer 2% of each file is excluded from raw min/max — `filtfilt` overshoots at array boundaries, and a file ending mid-event produces a fake peak |
| **Plateau vs spike** | Every reported peak is one instantaneous sample. `peak_shape()` reports the mean over a 0.2 s window centred on it, as a % of the peak: **≥95% = plateau, <85% = SPIKE**. It changes nothing about how peaks are found; it tells you whether the peak was a sustained limit or one tall crest |

**Two signals are deliberately not used.** Steering angle (unusable — see below), and **the derivative of vehicle speed**: `dv/dt` reaches 89–127 m/s² and *stays* there at p99, because speed is quantised at 0.01 m/s while grid intervals are sub-millisecond, so one quantisation step is already ~12 m/s². Use `VCPDU_lon` for acceleration; speed is for coarse gating only.

---

## The cases

### Case 1 — Max G's

**Events:** skidpad, autocross, endurance. **Signals:** `VCPDU_lat`, `VCPDU_lon`.

- **Skidpad** — steady segments from the sign and magnitude of filtered lateral G (>0.3 g, ≥2.0 s real), trimmed 0.5 s each end. Reports the **median** over the trimmed middle, matching how FSAE scores skidpad. No peak, by design.

  Segment selection is **adaptive, not a fixed count**: per direction, keep every qualifying run at least **70%** as long as the longest run of that sign (`MIN_FRACTION_OF_LONGEST`). A hard cap exists (`runs_per_direction`) but only case3's brake path passes one. On the current skidpad file this happens to keep 2 runs per direction — the right answer by coincidence of the data, not because 2 is the rule.
- **Autocross / endurance** — whole-file peak detection on lateral, longitudinal and combined `√(lat²+lon²)`, prominence **0.3 g**. Each peak reports the *simultaneous* lat/lon pair — the actual g-g point — and its angle, `alpha`.

**`alpha` — where a peak sits on the friction circle.** Reported with every peak as `alpha = atan2(|lat|, |lon|)` in degrees:

| alpha | meaning |
|---|---|
| **90°** | pure cornering — no braking or acceleration |
| **45°** | equal parts of both — the combined-load corner of the circle you are trying to use |
| **0°** | pure straight-line braking or acceleration |

**Gotcha:** `alpha` is measured from the **longitudinal** axis, so on the g-g plot 90° lies along the horizontal (lateral) axis, not vertically.

**The friction envelope.** The g-g diagram carries a convex hull of the cloud and reports its **area in g²**, computed from the **full arrays**, never the thinned display set. Dotted circles mark whole-g radii, so the gap between hull and circle is the grip anisotropy.

### Case 2 — Max Roll

**Events:** skidpad, autocross, endurance.

```
roll_front = wheel FR − wheel FL   → atan(mm / 1219.2)
roll_rear  = wheel RR − wheel RL   → atan(mm / 1168.4)
roll_avg   = (front + rear) / 2    → atan(mm / avg track)
```

**Sign conventions — read this before the formula looks backwards.** Two separate conventions stack here, and each is stated where it applies:

| | |
|---|---|
| **The channel** | On this car's calibration a **higher mm reading means more extension** (droop), not more compression. This is a property of the shock-pot wiring, verified empirically against vehicle speed in [case 3](#case-3--max-pitch) — it is not something the formula tells you |
| **Derived roll** | **`roll > 0` means the LEFT side is compressed.** Follow it through: `roll_front = FR − FL` is positive when FR reads higher, higher means FR is more *extended*, and the right side extending is the left side compressing — i.e. a left-hand turn |

Nothing downstream depends on getting this the right way round by luck: case 5 checks the sign of every fitted slope and reports a flipped one as an error rather than silently taking the absolute value.

- **Skidpad** — reuses case1's exact lateral-G segments; median front/rear/avg per run.
- **Autocross / endurance** — whole-file peaks on `|roll_front|`, `|roll_rear|`, `|roll_avg|` separately, reporting front *and* rear at the same instant.

**Peaks are found on the wheel-travel difference in millimetres, and converted to degrees only when reported.** That is why the prominence threshold below is in mm and not in degrees — it is applied one step upstream of the `atan`. (At these angles the two are near-proportional anyway: 2.0 mm is 0.094° on the front track.)

Prominence threshold **2.0 mm**, justified against the noise floor: roll noise std in stopped windows is **0.021–0.126 mm, median 0.049** (22 measurements, 11 files × front/rear), so 2.0 mm is 16× the worst and 41× the median. Sweeping it 0.5→10 mm leaves the top-5 and the single peak **identical to four decimals**, so nothing here is sensitive to the exact value.

### Case 3 — Max Pitch

**Events:** all five. `pitch = avg(wheel FL, FR) − avg(wheel RL, RR)` → `atan(mm / 1543)`.

**Sign convention — verified empirically against vehicle speed, not assumed:**

```
pitch > 0   squat  (acceleration)
pitch < 0   dive   (braking)
```

This is where the channel's polarity was established: a *higher* mm reading is more **extension** on this car's calibration — the opposite of what the formula alone suggests. Case 2's roll sign follows from the same fact.

Method differs per event because the data genuinely differs:

- **Skidpad** — lateral-G segments, median pitch. Expected near zero; a sanity check.
- **Accel** — longitudinal-G steady segments restricted to the **accelerating** branch, so the braking phase at the end of accel files is excluded. Verified as one continuous ~4 s pull, not a series of spikes.
- **Brake** — windows from **front brake pressure >100 psi AND speed >3 m/s**, minimum 0.3 s. *Both* gates are required: pressure alone produced a 30.3-second "braking window" (the driver holding the pedal at a standstill) and several windows with *positive* pitch — squat, impossible under braking. With the speed gate every surviving window dives correctly, which is independent evidence the detection is right. Within each window the single worst `|pitch|` instant is taken.
- **Autocross / endurance** — whole-file peaks on `|pitch|`, prominence **3.0 mm** (pitch noise std 0.13–0.55 mm in stopped windows). As in case 2, the peak search runs on the mm signal and the `atan` to degrees happens at reporting.

### Case 4 — Combined Roll + Pitch

**Events:** all five. Reports **worst per-corner wheel travel**, where `travel < 0` = compression (bump), `> 0` = extension (droop). Both extremes are reported; both have a mechanical limit.

**Why not `√(roll² + pitch²)`** — it was built, measured and rejected: roll and pitch peaks never coincide, and roll is 2–4× larger, so the root-sum-square just reproduces case2. Per-corner travel is where the two physically superpose, needs no arbitrary "both axes elevated" threshold, and is what decides whether a spring or damper runs out of travel. Evidence in [`docs/case4.md`](docs/case4.md).

**Modal decomposition.** At the worst instant, travel is decomposed **exactly** — an algebraic identity asserted at runtime, not a fit:

```
heave = (FL + FR + RL + RR) / 4      FL = heave − roll + pitch + warp
roll  = ((FR + RR) − (FL + RL)) / 4  FR = heave + roll + pitch − warp
pitch = ((FL + FR) − (RL + RR)) / 4  RL = heave − roll − pitch − warp
warp  = ((FL + RR) − (FR + RL)) / 4  RR = heave + roll − pitch + warp
```

Any way four corners can move is exactly one combination of these four, and they are mutually independent — that is what makes it an identity. Each mode's mm is its contribution to **one** corner, so the four sum with the right signs to that corner's travel.

| mode | what moves | cause |
|---|---|---|
| **heave** | all four the same way | the car rising or settling flat — aero load, a crest or dip |
| **roll** | left pair vs right pair, opposite | cornering lean |
| **pitch** | front pair vs rear pair, opposite | dive under braking, squat under acceleration |
| **warp** | the diagonals opposite — FL+RR one way, FR+RL the other | the chassis being **twisted** along its length. A single-wheel bump or one-wheel kerb strike |

**Only case4 can see warp** — case2 and case3 average corners in pairs, which cancels it exactly. Warp is resisted by the springs like any other mode; what makes it worth reading is that chassis torsional compliance writes a warp-pattern signature into these same four channels, since the pots measure chassis-to-upright per corner.

**Other outputs.** Peak detection on the 4-corner envelope `max(|FL|,|FR|,|RL|,|RR|)`, prominence 2.0 mm. Skidpad and accel also get a **sustained** number, being quasi-steady. Per-event roll-vs-pitch scatter with a convex hull. And a **per-corner travel distribution** reporting p1/median/p99 alongside min/max — p1–p99 is where a corner actually *lives* when working hard, while an extreme is one instant and can be a kerb strike.

**Travel is also reported as a load, in newtons.** `ΔF = −travel × wheel rate` (27.92 N/mm front, 32.51 N/mm rear), signed so that **compression is a load increase** — the worst autocross instant, FR at −21.52 mm, is **+601 N onto that corner** relative to its stopped-car static load; endurance's −24.28 mm is **+678 N**. No tyre term enters: the pots measure the spring's own deflection once motion ratio is applied, and the tyre deflects in series *under* that same load rather than adding to it, which is the premise the [ground-referencing multiplier](#ground-referenced-angles) is derived from.

This is the only figure in the analysis directly comparable to a **design load-transfer prediction**, which is always quoted per corner in newtons and never in millimetres — so it is the bridge nothing else here crosses. It is reported in the case-4 console output and report page only, deliberately not in the summary table, which stays in millimetres.

> Those limits are **wheel** travel. Motion ratio is defined here as wheel ÷ spring (> 1), so **multiply** shock travel by it: `wheel_mm = shock_mm × MR`, e.g. 30 mm of front shock stroke is 30 × 1.188 = **35.6 mm** at the wheel. This is the same direction `to_wheel_travel()` applies, and getting it backwards is a factor of MR² ≈ 1.41 on the front.

**Scope caveat:** case4 runs all five events, but only **autocross (17–29% of samples) and endurance (20%)** genuinely load both axes at once. Skidpad is 2.6%, accel 0–0.9%, braketest1 0%. The other three are sanity checks, not real combined cases.

### Case 5 — Roll and pitch gradient (°/g)

**Events:** roll on skidpad/autocross/endurance, pitch on accel/brake/autocross/endurance.

Cases 1–4 answer *"how much did the car roll?"* — a property of the **run**, since a driver who pushed harder gets a bigger number. Gradient answers *"how much does this car roll per g"* — a property of the **car**, and the bridge to a roll stiffness in N·m/deg. Nothing is reimplemented: roll comes from case2's loader and pitch from case3's.

**Skidpad steady segments are the cleanest estimate and the one to quote:**

| | ground-ref (quote this) | suspension-ref | R² |
|---|---|---|---|
| Front | 1.053 °/g | 0.858 | 0.992 |
| Rear | 1.188 °/g | 0.939 | 0.993 |
| **Whole car** | **1.119 °/g** | **0.898** | 0.995 |

> ⚠️ **Every gradient in this section carries its frame inline — `(susp-ref)` or `(ground-ref)` — and none is ever written bare.** The diagnostics and the spring cross-check below work in the **suspension-referenced** frame, because that is the one the shock pots and the springs actually set. The results table at the top of this README is **ground-referenced**, so the same event legitimately appears as two numbers ~25% apart in two places — autocross whole-car roll is **0.846 °/g (susp-ref)** and **1.056 °/g (ground-ref)**. Convert with the [multipliers](#ground-referenced-angles) before comparing anything here against a design target. Quoting the wrong frame is what produced the "2× low" report, so if you find a bare number anywhere in this repo, treat it as a bug rather than guessing.

**Pitch gradient** pools both signs of longitudinal G into a single slope per event, so an event's figure is not separable into squat and dive.

**Cross-checked against the springs — the only check that doesn't route through the shock pots.** With no ARB, the four springs make the entire roll stiffness. Watch the units: the wheel rates are N/mm and the tracks are mm, so the bracket comes out in **N·mm/rad** and needs converting.

```
K_roll = (k_wf·T_f² + k_wr·T_r²) / 2
       = (27.92 × 1219.2² + 32.51 × 1168.4²) / 2
       = 4.294e7 N·mm/rad
       = 42 940 N·m/rad          ÷ 1000
       = 749 N·m/deg             × π/180
```

This is a check on the **suspension-referenced** slope, since springs alone set that one and no tyre term enters it. Motion ratio enters stiffness as **MR²**, so it is twice as sensitive to an MR error as the angles are — which is the point, because every other cross-check available here routes through the same pots and the same motion ratio, so those test repeatability rather than calibration.

> **What it does not establish.** 749 N·m/deg against the measured 0.898 °/g gives a roll moment of ~673 N·m per g, and going from there to a CG height needs a **sprung mass and a roll-axis height that nobody has measured on this car**. Those are not inputs to anything here — no script uses a mass, a CG height or a roll-axis height — so that step is deliberately not taken. For reference if you ever need it: the competition mass is **215.5 kg without driver**, so add a **68–70 kg driver** for the as-run total.

**Fitting choices.** Intercept is **fitted, not forced through zero** — the car is physically level at 0 g, so a large intercept is not a free parameter, it is evidence a baseline is off (measured: 0.002–0.101°, which is the baselining checking out). Step glitches and samples below 2 m/s are excluded. **Transients are kept**: roll lags lateral G, so corner entry and exit trace different paths and the cloud opens into a loop — the width is the information, which is why the scatter is a deliverable. Signs are checked rather than absolute-valued; a positive raw slope means a convention flipped upstream and is reported as an error.

**⚠️ Two autocross runs have unusable front data.** `autocross_andrew1` and `autocross_josh2` give a front gradient of **0.302 / 0.320 °/g (susp-ref)** against **0.801 / 0.818 °/g (susp-ref)** for the other two, while all four rears agree. Both front pots sit at 0.2–0.8 V — the maximum-extension end of their stroke — where travel is clipped to a third.

Pooling all four gives **0.557 °/g (susp-ref)**; the script **excludes them automatically** (`case_common.SUSPECT_CORNERS`) and reports **0.809 °/g (susp-ref)**, consistent with skidpad and endurance at **0.81–0.86 °/g (susp-ref)**. The per-file table still lists all four, marking the dropped ones; the front-spread warning fires at 1.5× **across the pooled files only**. The deficit is uniform around the lap (front/rear amplitude ratio ~0.6 on the bad runs against ~1.5 on the clean ones, constant every 79 m segment), so it is a property of the measurement, not of how the car was driven.

> **`SUSPECT_CORNERS` is read by case5 only — and that is correct, not an oversight.** Cases 2, 3 and 4 run on all four autocross files, including the two bad ones. It doesn't matter, because **the fault under-reads**: a pot clipped near its extension limit records *less* travel than really happened, so a suspect corner can never win a maximum search. It can, however, drag a least-squares slope regardless of magnitude, which is exactly why case5 has to drop it.
>
> Verified on the current data rather than assumed — every autocross headline comes from a **clean** file: case2's roll peaks (front 1.725°, rear 2.052°, avg 1.878°) are all `autocross_andrew2`, and case4's worst corner travel (−21.52 mm FR) is `autocross_josh1`, with the whole top-5 split between those two. If new data ever puts a suspect file on top of a peak search, that is a bug and this reasoning stops holding.

### Case 6 — Max yaw rate (°/s)

**Events:** all five. Cases 1–5 measure what the car does to itself under load; none measure **how fast it changes direction**.

| Event | Peak yaw | Radius **at that instant** |
|---|---|---|
| **AUTOCROSS** | **−105.1 °/s** | 6.0 m |
| ENDURANCE | +99.3 °/s | 5.0 m |
| BRAKE | −93.3 °/s | 6.2 m |
| SKIDPAD | +78.7 °/s | 7.6 m |
| ACCEL | −52.6 °/s | 9.5 m |

Radius is `R = v/ω`, the line the car actually followed — not the painted radius of the corner. Skidpad also gets a **sustained** number, 61.1 °/s, from four runs alternating direction.

> **Two different skidpad radii appear in this section, and both are correct.** The **7.6 m** above is `v/ω` at the single peak-yaw *instant* (26.32 s, 10.4 m/s) — a turn-in transient, not the steady line. The **9.65 m** in the geometry check below is the *median over the four steady-state runs* (9.8 / 9.3 / 9.9 / 9.5 m). Only the steady-state one is meaningful against the course geometry; a peak-yaw instant is by definition not steady-state. The same caveat applies to every radius in the table — they are instantaneous, so read them as "how tight was the tightest thing in this event", not as a corner spec.

**The channel is validated on every run, not trusted from a note.** A car in a corner satisfies `a_lat = v · ω`, an identity sharing **no sensor** with the gyro (lateral G from the IMU accelerometer, speed from the front wheels). Measured per file: r = +0.965…+0.993, slope 1.06–1.18. Slope above 1.0 is expected, not error — the identity assumes zero sideslip and `VCFRONT_vehicleSpeed` is front-wheel-derived, so it under-reads through a corner. Straight-line events report *inconclusive* rather than *fail*.

**Skidpad geometry check.** `R = v/ω` comes from two sensors that know nothing about the course, so where it lands against the rulebook is a calibration check on both. FSAE 2026 v1.0 **D.10.1.1** specifies inner circles 15.25 m diameter and outer circles 21.25 m, i.e. a legal driven line between **7.625 and 10.625 m** (lane centre 9.125 m); measured **9.65 m**, inside the band. Identical in the 2027 draft, but cite the 2026 rulebook — it is the authoritative one.

**What it deliberately does not do: dead-reckon a path.** A 7–18% scale error is harmless instantaneously and fatal once integrated — over 60 s it accumulates tens of degrees of heading error, which is why the autocross course integrates to ~365 m while start and end land 156–177 m apart. Every quantity in case6 is instantaneous or a ratio of two instantaneous values, **never an integral**.

---

## Known data problems

Read this before trusting any number.

| # | problem | status |
|---|---|---|
| 1 | Shock-pot step glitches — 12 across 4 files | **handled automatically** |
| 2 | Shock-pot steps corrupt whole-file baselines | **fixed** (`segmented_baselines`) |
| 3 | `VCFRONT_steeringAngle` unusable | **not used** |
| 4 | Front pots at extension limit on 2 autocross runs | **excluded from case5 fits only** (harmless to 2/3/4 — see case 5); hardware check needed |
| 5 | `FL` shock pot suspect | known, unresolved |
| 6 | Front and rear roll disagree — rear reads ~9.5% high | **unexplained** |
| 7 | IMU 2-sample spikes | harmless to reported numbers |
| 8 | `endurance_full` brake pressure saturates at 2000 psi | firmware clamp; peaks are floors |
| 9 | Front brake pressure is 10 Hz, not 100 | filtered at 3 Hz for this reason |
| 10 | `VCPDU_angleRoll`/`anglePitch` unusable; `VCPDU_roll`/`pitch` below resolution | **not used**; `VCPDU_yaw` is good |

**1–2. Shock-pot steps.** FL and FR jump *together* by ~13 mm and ~22 mm in a single sample, then hold — `accel_corinne1` @118.84 s, `autocross_andrew1` @76.99 s, `autocross_josh1` @84.56 s, `braketest2` @46.23/46.33/147.95 s. Suspension cannot step and then sit still, so **it is the sensor's zero that moves, not the car**: it happens in one 0.3 ms sample while the car is parked, it is in the raw voltage, nothing else in the file moves, and the magnitudes repeat across files. What fits is a **front shock-pot mount slipping between two seated positions** — a bolt in a slotted hole, a rod end backed off, or a loose bracket. It slips *both* directions, so nothing is permanently deformed. Rears never do it.

They are larger than any real event, so an unprotected peak search reports them as the worst case — they held the top spot in three of case4's five events before rejection. Worse, a step also corrupts the **baseline**: `−27.98 mm`, previously the largest corner travel in the data set and the quoted autocross design case, was almost entirely a wrong static baseline. The corner had moved 3.6 mm. Files are now cut at each step and each segment baselined locally.

> ⚠️ **Do not** "correct" a step by subtracting the reported jump. `find_step_glitches` returns a *magnitude*, not a direction; applying it signed-wrong made `andrew1`'s FR read −53 mm. The direction must come from the stopped-window medians either side.

**3. `VCFRONT_steeringAngle`.** Two separate faults, both in `firmware/components/vc/front/src/steeringAngle.c`. **Zero calibration was never run** — the map applies −115.3846 °/V to `(voltage − zero)` with `zero` still 0 V, so a ~1.5 V resting sensor reads −173.077°, exactly the −173.0 seen in all 11 files. (Not a DBC rail and not a fault: a faulted sensor is forced to 0°.) And **only one steering direction registers** — voltage only ever moves down from its 1.4993 V rest. Its *rate of change* is not a safe fallback either: at rest the derivative is identically zero, which any "holding a steady line?" test reads as steady from a flat-lined sensor.

**4–5. Front pots.** See case 5 above. On skidpad, FL sweeps 18.4 mm while FR sweeps 34.3 mm, and FL's static baseline ranges 42.4–66.9 mm across sessions. Likely the "one of the sensors might be broken" from the original brief. **What to check on the car:** stroke range and mount security on both front pots, and whether the pot bodies move by hand relative to their brackets.

**6. Front vs rear roll.** A rigid chassis has exactly *one* roll angle, so the two should match. They don't — the rear reads high. **Quote the gradient figure, not a peak ratio:**

| comparison | rear reads | why this one |
|---|---|---|
| **Skidpad roll gradient, suspension-referenced** (0.858 → 0.939 °/g) | **+9.5%** | **The number to use.** A whole-run fit over matched windows, no filter or reference-frame effects folded in |
| Skidpad roll gradient, ground-referenced (1.053 → 1.188 °/g) | +12.8% | Same data; larger only because the front and rear ground-referencing multipliers differ (×1.228 vs ×1.265) |
| Skidpad steady per-run peaks, across the four runs | +6.6% … +19.5% | Real spread, but four samples of a noisy ratio |
| Whole-file peak searches (case2 headline numbers) | **not comparable** | Front and rear peaks land at *different instants*, so this is not like-for-like — at the autocross front-peak instant the rear actually reads **lower** |

The last row is why earlier versions of this README and of `case2_max_roll.py` quoted ranges — "4–23%" and "7–27%" respectively — with "same sign every event" attached. Both mixed matched and unmatched comparisons, the two disagreed with each other because only one had been updated when the front motion ratio was corrected 1.15 → 1.188, and the "same sign" part is not true instant-by-instant. All of them now report the 9.5% above.

The rear also shows 16–22% left/right asymmetry the front does not — on skidpad, which is symmetric by construction. A pure *gain* error cannot cause that (in roll one pot compresses while the other extends, so `RR − RL` sums the gains either direction); it needs genuinely asymmetric rear roll stiffness or a **non-linearity** — a pot near its stroke limit, or something binding. A motion-ratio error is ruled out (both are validated measurements) and so is tyre deflection, which pushes the wrong way. **Currently unresolved, so the rear roll number is the less trustworthy of the two.**

**7. IMU spikes.** `VCPDU_lat`/`lon` carry isolated 2.1–2.8 g excursions that are **always exactly two consecutive samples holding a bit-identical value** — a real accelerometer does not produce the same float twice. They do not affect any reported number (endurance's filtered max is 1.7798 g with and without its spike); they bite only the peak-attenuation table, whose denominator is the raw max, which `filter_compare.py` flags as `spike_dominated`.

**8–9. Brake pressure.** `endurance_full`'s front pressure reads exactly 2000 psi at max, p99.9 *and* p99 — an explicit clamp in `brakePressure.c` at 4.5 V, so those samples are a **floor, not a measurement**. Front is transmitted at **10 Hz** (rear at 100 Hz) because front rides on a shared message while rear has its own — `VCFRONT` consumes it live for torque allocation. Nyquist 5 Hz, hence the 3 Hz filter. Switching braking-window detection to rear was measured and **changes nothing reported** — it does segmentation, not measurement, and 50 ms of window edge is immaterial inside a 0.5–1.1 s window. Rear *would* be needed for anything using the pressure trace itself: rise rate, pedal shape, ABS-style modulation.

**10. IMU attitude.** `VCPDU_yaw` is **good** — see case 6. `VCPDU_roll`/`pitch` are the *same chip* but sit at its resolution: the car yaws at ~50 °/s and rolls at ~0.8 °/s against a 0.45 °/s noise floor, i.e. SNR 1.8× against yaw's 136×, plus a firmware zero-clamp that reads exactly 0.0 for 27–65% of parked samples. `VCPDU_angleRoll`/`anglePitch` read ±22–33° against the shock pots' ±1.8°, **anti-correlated** (r = −0.33), don't match a gravity-vector tilt, are inconsistent with their own rate channel, and drift 3.7° between parked windows in one file. **The shock-pot derivation is the correct measurement and the dedicated attitude sensor is the broken one.**

**Also worth knowing:** `braketest2.csv` was once flagged unreliable on three counts. **All three were the same artefact and the verdict was wrong** — its step glitches fell inside the baseline window, and a std computed across a step discontinuity is not noise. Glitch-masked, the file is one of the *cleanest* in the set (0.007–0.043 mm), and it is the brake test that **passed** at competition. Use it.

**Shock-pot scale:** `disp` is a single global linear transform of `volt`, **−25.510 mm/V**, identical on all four corners and all 11 files. The voltage channels carry no extra information — but there is also **no per-corner calibration**, so unit-to-unit gain and zero variation is unaccounted for. A plausible contributor to problems 5 and 6.

---

## What each file actually is

**The names in the filenames are the drivers who ran that session at competition** — Andrew, Josh, Austin, Corinne and Jamie. They identify runs, nothing more.

From the [FSAE Electric 2026 official results](https://www.fsaeonline.com/CompResources/2026/07af50d8-cbb6-4b9b-aaf8-5ff6a7e44057/FSAE_2026_MI6_results.pdf). **Concordia is car #43, 19th overall, 475.1 points**, **215.5 kg without driver** (add 68–70 kg for the as-run total). A telemetry file is not self-describing, and knowing a run went off course changes how you read an anomaly in it.

> Note this is *not* enough to turn a °/g gradient into a roll moment — that needs **sprung** mass and CG height above the roll axis, neither of which has been measured on this car. See [case 5](#case-5--roll-and-pitch-gradient-g).

| event | files | result |
|---|---|---|
| **Autocross** | `josh1` (off course, +20 s), `josh2` (**best, 49.541 s**), `andrew1`, `andrew2` | 18th, 81.81 pts. `andrew1` is slowest officially *and* in telemetry — corroboration |
| **Endurance** | `endurance_full` — Andrew, then Josh | 1483.688 s, **21 scored laps, DNF on the last**. Lap 12 (168.9 s) is the driver change; lap 13 (121.9 s) is a separate momentary stop. Best 63.363 s at lap 21. The file spans 1740 s, ~4 min beyond the scored run |
| **Skidpad** | `skidpad_austin_both` | 15th, best 5.178 s. Austin's two runs only; the second driver's data was deliberately not exported |
| **Brake** | `braketest1`, `braketest2` | Both achieved **full four-wheel lockup**. `braketest2` is the valid run; `braketest1` is invalid **on procedure only** (braked before the mandated point) and is still real max-braking data |
| **Accel** | `accel_jamie_both`, `accel_corinne1`, `accel_corinne2` | 20th, best 4.521 s, spread 4.52–4.60 s |

**Do not use peak brake pressure as a performance metric.** Past lockup, extra pressure only records how hard the driver pushed — the invalid run used 1830 psi against the valid run's 1112 for the same outcome.

The endurance lap times give lap detection a millisecond-accurate ground truth, including two stationary events a detector must handle rather than trip over.

---

## Tools

| tool | what it's for |
|---|---|
| `batch_signal_stats.py` | **Start here with a new data set.** min/max/mean per signal, pooled per event. `--list-signals` is a 1 s peek with no parse — the only view showing each signal's *true* update rate, since the stats tables count samples on the resampled grid |
| `cutoff_sweep.py` | Re-runs the whole pipeline at each of a list of frequencies and reports how much each headline number moves. The review pages show what a cutoff does to a *trace*; this shows what it does to the *number you report* |
| `filter_compare.py` | Cutoff comparison across 9 signals, three views each (panels / residual / overlay) plus a peak-attenuation table. The full-rate instrument — the case plots are decimated for display |
| `build_cutoff_review.py` | Lays out the 29 (quantity × event) cells that genuinely need a cutoff decision, with plots beside each. **The decision is already made** (10 Hz); this is what supported it and what to re-run if the data changes |
| `spectral_analysis.py` | PSD in case4's modal basis, on a true 100 Hz grid. **Result: there is no 6–8 Hz mode** — an earlier README claimed one, but peak frequencies don't cluster across files and inter-corner coherence never exceeds 0.41, so what the pots see above 1 Hz is largely uncorrelated per-corner content |
| `lap_detection.py` | Finds laps **without any position signal** — there is no GPS in this data. Speed integrates cleanly into distance (even though it cannot be differentiated), and distance is lap-invariant. Detects **22 laps, exactly the official count**, median interior error 0.65 s. A driver change adds ~170 s and zero metres, so in the distance domain it collapses to a point |
| `compare_resampling.py` | Measures what would change if the cases filtered on a true 100 Hz grid instead of the union grid. **It decides nothing** — roll +0.84%, lat G +1.56% mean but −7.5%/+9.6% per file, so it is a real decision rather than a free accuracy win |
| `audit_plot_layout.py` | `uv run audit_plot_layout.py plots` — flags figures whose header text (title, legend, subplot titles) overlaps or runs off the chart. Checks the Plotly JSON embedded in each report against a **deliberately independent** pixel model, since a checker sharing `case_common.py`'s layout assumptions could only confirm them. Run it after **any** change to how a plot is built: this class of fault is invisible until someone opens the one chart at the one window size where it shows, and it had reached 34 of 84 figures before anyone noticed |
| `test_regression.py` | Pins every headline number. `--update` to re-pin |

**About the regression test.** It is **not a correctness test** — it cannot tell you a number is *right*, only that it is the *same*. Six real bugs were found and fixed in quick succession (lat/lon read as g, a hardcoded runs-per-direction cap, step glitches winning the peak search, `filtfilt` edge artefacts, an inverted roll sign, the `braketest2` misdiagnosis), every one of which moved published numbers with nothing watching. A failure is information: read the diff, decide whether the change was intended, re-pin, and **commit `regression_expected.json`** — that commit is the record of what moved and why.

---

## Open questions

- **The 10 Hz cutoff is a reviewed judgement, not an optimum.** It was chosen from `filter_compare.py`'s residual view across 2–20 Hz, with `cutoff_sweep.py` quantifying how far every headline number moves — deliberately reporting the sensitivity rather than asserting one frequency is correct. Re-running the sweep is how to revisit it if the data changes.
- **Motion ratio is a single value per axle.** If it varies meaningfully with travel, a curve would be more accurate.
- **Why measured pitch sits 1.34× below the design prediction.** In the **Simplified Steady State Suspension Spreadsheet**, **anti-squat/anti-lift** and **anti-dive** are both **0 — typed constants, not formulas**, so the spreadsheet derives them from no geometry and cannot confirm its own assumption. Team recollection is that 0 was the design intent, which is a normal FSAE choice. They are still *live* inputs: they feed the elastic load transfer and so the **predicted pitch gradient of 0.901 °/g** at 0% anti (after the tyre-rate correction, reproduced exactly from the spreadsheet). Two readings fit the telemetry, and the spreadsheet cannot distinguish them:
  - **Roll shows a 1.167× gap where no anti term exists anywhere in the chain**, so ~17% of the discrepancy is common to both axes and is *not* about anti geometry. Removing it leaves pitch-specific **1.147×**, which **~14% real anti-dive/anti-lift** would account for — plausible as as-built geometry even when 0 was drawn.
  - If the car genuinely has 0% anti, that 1.147× needs another cause.

  **The likely mechanism for a non-zero as-built anti is weld tab placement** (team, 2026-08-03): 0 was drawn, but the tabs went on by hand and are off by some amount. The sensitivity makes that easy to believe — anti is a ratio amplified by `L/h = 1543/325 = 4.75`, so:

  | anti | side-view angle | height error across a wishbone's two chassis pickups, 200 mm apart |
  |---|---|---|
  | 5% | 0.60° | 2.1 mm |
  | 10% | 1.21° | 4.2 mm |
  | **14.3%** | **1.73°** | **6.0 mm** |
  | 20% | 2.41° | 8.4 mm |

  So ~6 mm of *relative* height error between the front and rear pickup of one wishbone produces the 14% in question — ordinary for hand-welded tabs and invisible by eye. Two caveats: this is the same lumped model the spreadsheet uses (lateral load transfer × (1 − anti)) with **no brake-bias term**, and a proper front anti-dive formula includes front bias, which would require a *larger* angle for the same effective anti — so 6 mm is a **lower bound**, not an estimate. And it assumes the error is in the height *difference* across a wishbone; an error moving both pickups together changes roll centre, not anti.

  **Worth measuring all four corners, not just the fronts.** Hand-placed tabs are unlikely to be off symmetrically, and there are two unexplained left/right observations already on record — the rear's 16–22% roll asymmetry that the front does not show (problem 6), and `FR` being worst-loaded in 8 of 11 files. Different mechanism (anti is side-view, roll asymmetry is front-view), so this is a hypothesis rather than a finding, but one measurement session tests both.

  **Settling it needs as-built pickup coordinates measured against CAD**, not more telemetry. The common 1.167× factor across both axes is the bigger question and is unexplained.

  **Tyre rate is not the explanation, and this has been tested rather than assumed.** Changing it moves every ground-referenced number *and* the spreadsheet's own predicted gradients by the same amount in the same direction, leaving both ratios *identical to four decimals* (roll 1.167×, pitch 1.338×) — checked across a 520–859 lbf/in sweep. The tyre term cancels exactly: the spreadsheet builds roll stiffness from **ride** rates while the measurement's ground-referencing multiplies by wheel/ride. Look at wheel rates (spring rate or motion ratio), track, or the measured suspension-referenced slope instead.
- **Why the front pots sat at their extension limit** on two autocross runs and not the neighbouring ones — telemetry can localise it but not diagnose the hardware.
- **Front vs rear roll disagreement** (problem 6) — chassis torsional flex or front pot calibration, unresolved.
- **Data in the repo** is deferred, not refused. Telemetry compresses ~10× (405 MB → ~40 MB), so Git LFS is viable; the `.csv.gz` route needs a ~3-line change in `parse_influx.py`, which is Andrew's file — ask, don't edit.
- **Add to the next InfluxDB pull:** the IMU calibration flags and the brake fault flag. The DBC defines them; the current export does not include them, so claims about them are unverifiable.
- **Case 7 from the original brief (max yaw *timing*)** is deliberately not implemented. Case 6 covers yaw-rate magnitude only.

---

## Extending it

**Adding a signal.** `parse_influx.py` and `batch_signal_stats.py` pick up new signals automatically — a new channel appears in the survey with no code change. `filter_compare.py` needs one tuple in `EXTRA_SIGNALS`. `case_common.py` and the cases name specific physical sensors and must be edited explicitly; that is correct, since a case is a physics question, not a signal dump. **Always check the new signal's units in the DBC and its update rate in firmware** (`grep periodic.*Hz_CLK`) — the rate bounds any usable cutoff, and the `m/s²`-vs-`g` mistake reached production here.

**Adding a case.**

1. **Reuse `case_common`** — `lowpass`, `elapsed_seconds`, `trim_window`, `find_steady_segments`, `top_k_peaks`, `baseline_corner_displacements`, `to_wheel_travel`, `find_step_glitches`, `find_braking_windows`. Don't redefine constants. If a pattern would be duplicated across cases, it belongs in `case_common` — duplicated logic has cost real accuracy here twice.
2. **Declare `REQUIRED_SIGNALS`** and skip files that lack them.
3. **Verify every threshold against real data** before committing to it — measure the noise floor in stopped-car windows to pick a prominence. Every constant in the existing cases has its measurement recorded in a comment.
4. **Convert to wheel travel before any axle arithmetic** if you touch the shock pots.
5. **Return a summary dict** as well as printing — that is what lets `case_summary.py` include the case without duplicating logic. Hang presentation-only metadata off an underscore-prefixed key so the regression snapshot skips it.
6. **Register it** in `case_summary.py` (a `collect_caseN()` plus a column) and `test_regression.py`.
7. **Document the methodology here, including anything you rejected and why.** The reasoning is the expensive part to reconstruct — case4 exists in its current form only because `√(roll² + pitch²)` was tried, measured, and found to reproduce case2 to three decimals.
