# CFR26 Telemetry Analysis — detailed notes

Companion to [README.md](README.md), which covers setup and running. This file holds
the methodology, the reasoning behind each constant/threshold, and the data-quality
findings — the parts that are expensive to reconstruct if lost. If you're deciding
whether a number is trustworthy, or extending the analysis, start here.

## Getting the data — pulling from InfluxDB

> ### ⚠️ TODO — not written yet.
>
> To fill this in, this section needs:
>
> - [ ] Where the InfluxDB instance lives (URL / host), and how to get access
> - [ ] The query used to export a session (bucket, measurement, time range)
> - [ ] Which export format/dialect to choose — the parser needs the **long format** with `_time`, `_field` and `_value` columns, not a pivoted wide table
> - [ ] Whether signals are selected at export time or everything is dumped
> - [ ] Where the shared CSVs are archived, so nobody re-exports unnecessarily
>
> Until then, ask whoever pulled the current set for a copy.

**Why raw CSVs can't be committed even if we wanted to:** the 11 files total 405 MB
and `endurance_full.csv` alone is 235 MB, over GitHub's hard 100 MB per-file limit.
This is a deferred decision, not a permanent rule — telemetry CSV compresses about
10×, which would put endurance at ~23 MB and the whole set at ~40 MB. Options if
revisited: Git LFS (preferred — keeps clones lean, scales to future seasons), or
committing `.csv.gz` plus a one-time `gzip -d` (needs a ~3-line change in
`parse_influx.py`, which line-scans with plain `open()` and currently fails on gzip).

**Do not split `endurance_full.csv` to get under the limit.** Every chunk boundary
becomes a `filtfilt` edge, and that is exactly what produced a fake 17.36mm pitch
peak against a 16.33mm real one in `accel_corinne1` — splitting would manufacture
that artifact at every seam, in the file holding the design-driving events. Mid-session
chunks may also lack a stopped-car window to baseline against.

## Vehicle constants — full detail

All live in `case_common.py`, imported by every case script. They used to be
redefined independently in case2/3/4 — the values agreed, but nothing enforced
that, and `case_common.py` exists precisely because `case1` and `filter_compare`
once drifted onto two different values of `G`.

| constant | value |
|---|---|
| Front track | 1219.2 mm (centre-to-centre) |
| Rear track | 1168.4 mm (centre-to-centre) |
| Wheelbase | **1543 mm** (1545 in `corner-model/Forces/car_data.py` is a known error on another branch) |
| Motion ratio, front | **1.15** (wheel ÷ spring) |
| Motion ratio, rear | **1.038** |

Front and rear motion ratios differ, which dictates *where* the conversion
happens: every corner is converted to wheel travel **before** any roll, pitch
or modal arithmetic. Differencing axles on raw shock-pot mm and applying one
ratio afterwards is only valid when the ratios match, and they don't.

**mm → degrees:** `angle = atan(wheel_travel_mm / span_mm)` (span = track for
roll, wheelbase for pitch). This is **exact, not a small-angle approximation**
— `atan` is the exact relation for two vertical displacements separated by a
horizontal span. (Docstrings called it "small-angle" for a while; that was
simply wrong — it never changed a number, linear and `atan` agree to 0.002%
at 10 mm and 0.03% at 35 mm, but it implied a limitation that doesn't exist.)
Pass **wheel** travel, not raw shock-pot mm.

**The one real approximation — whole-car "avg roll":** `AVG_TRACK_MM` converts
a mean-mm over a mean-track rather than averaging two separately-converted
angles. Because `atan` is non-linear and the two tracks differ by 50.8 mm,
these are not the same: measured error is **0.17–0.19%** (1.6201° the
approximate way against 1.6231° exact). Kept as-is deliberately so published
numbers stay comparable with what's already been shared. Front and rear roll,
reported separately, are each exact — only the combined figure carries this.

## Shared foundation — full detail

Inherited by every case; none of them redefine these.

| | |
|---|---|
| **Filter** | 4th-order Butterworth, zero-phase (`filtfilt`). **10.0 Hz** for every event, **3.0 Hz** for front brake pressure. Chosen 2026-07-31 from `cutoff_sweep.py`, replacing an inherited 2.0/5.0 that nobody had validated — low cutoffs turned out to be the *unstable* region, and 5 Hz sat on the slope. Front brake pressure is Nyquist-forced: it is sampled at 10 Hz |
| **Units** | `G = 9.80665`. `VCPDU_lat`/`lon` are **m/s²** in the DBC and are divided by G |
| **Time** | The InfluxDB union grid is **not uniformly sampled** — median spacing 0.39 ms with gaps from 0.019 to 19.3 ms, a 1030× range within one file, built by zero-order hold. Every duration is real elapsed `t[e]−t[s]`, never `sample_count × dt`, which errs by 3–5×. Scalar `dt` is used *only* for filter design |
| **Sample rates** | Measured from raw per-signal timestamps: everything is **100 Hz** except `VCFRONT_brakePressure` at **10 Hz**. `case_common.uniform_resample()` resamples from RAW samples, never the ZOH union grid — a staircase's step edges carry broadband energy no sensor measured. Used by `filter_compare`, `spectral_analysis`, `lap_detection`; the case scripts still filter on the union grid (see `compare_resampling.py` for the ~1% delta) |
| **Baselining** | Each corner is zeroed against its own stopped-car window (speed <0.5 m/s, ≥2s real, trimmed 0.5s/end; prefers file start → end → longest anywhere, which catches an endurance driver change). Each pot carries its own zero offset; differencing without removing it counts the offset as suspension movement. Step glitches are excluded from the window, and a **lockup guard** rejects candidate stops whose mean \|lon G\| ≥ 0.15 g |
| **Glitch rejection** | Per-sensor-update jumps >8mm are masked ±1s — see *Known data problems* |
| **Peak detection** | `find_peaks` by **prominence only** — no index-based `distance`, because a fixed sample count spans different real time in different parts of a file. Spacing enforced afterwards against elapsed time: tallest candidate first, reject any peak within 1.0s of an accepted one. Top 5 |

Two signals deliberately **not** used:

- **Steering angle** — unusable, see *Known data problems #2*.
- **Speed derivative** — `dv/dt` from `VCFRONT_vehicleSpeed` reaches 89–127 m/s²
  (9–13 g) and *stays* there at the 99th percentile; low-passing to 0.2 Hz
  still leaves 5–6 g. The cause is the grid, not the sensor: speed is
  quantised at 0.01 m/s while grid intervals are sub-millisecond, so one
  quantisation step is already ~12 m/s². Use `VCPDU_lon` for acceleration
  (peaks at a sensible 0.99 g on accel runs); speed is for coarse gating only.

## Cutoff comparison table

The same headline table at the previous 2 Hz / 5 Hz cutoffs — skidpad roll and
pitch are **identical**, exactly as the sensitivity sweep predicted, and
everything that moved is a transient peak:

| Event | Peak lat G | Peak lon G | Roll | Pitch | Worst travel |
|---|---|---|---|---|---|
| SKIDPAD | — | — | 1.18 | 0.10* | +18.2 mm |
| BRAKE | — | — | — | 0.73 | −20.5 mm |
| AUTOCROSS | 1.73 | 1.34 | 1.44 | 0.91 | −27.8 mm |
| ENDURANCE | 1.78 | 1.65 | 1.57 | 0.89 | −23.9 mm |

The skidpad travel sign flip (+18.2 → −20.1 mm) is a near-equal-peak tie-break
(see *Sign flips* below), not a reversal of the physics — the magnitude went
18.2 → 20.1 mm.

### `cutoff_sweep.py` — how much does the cutoff matter?

Re-runs the whole case1–case4 pipeline at each of a list of frequencies and
reports how much each headline number moves.

```powershell
uv run cutoff_sweep.py --dir comp2026_data
uv run cutoff_sweep.py --dir comp2026_data --freqs 2 3 4 5 6 8 10 15 20
```

Cheap: a full pass over 11 files and 4 cases is ~20 s, so a seven-point sweep
is a couple of minutes. It patches the cutoff constants on the case modules
and calls `case_summary`'s collectors, so nothing is reimplemented. Both
constants are set to the same value at each step — deliberately *not*
production config — so each event shows its own sensitivity.

**Result: most numbers are filter-dominated.** Across 2–20 Hz, of 65 headline
numbers: **6 move less than 2%**, and **35 move more than 10%**. The split is
clean and physical:

**Skidpad steady-state numbers are nearly cutoff-independent**, because they
report a *median over steady segments* — smooth low-frequency content a
low-pass barely touches:

| quantity | 2 Hz → 20 Hz | spread |
|---|---|---|
| `case2.skidpad.front_deg` | 1.1017 → 1.1009 | **0.3%** |
| `case2.skidpad.rear_deg` | 1.2755 → 1.2730 | **0.3%** |
| `case2.skidpad.avg_deg` | 1.1810 → 1.1772 | **0.5%** |
| `case1.skidpad.sustained_lat_g_min` | 1.2593 → 1.2540 | **0.9%** |

**Transient peak numbers are dominated by it**, because a peak is exactly what
a low-pass attenuates:

| quantity | 2 Hz → 20 Hz | spread |
|---|---|---|
| `case3.endurance.worst_deg` | 0.6016 → 0.9371 | **39%** |
| `case1.endurance.peak_lon_g` | 1.1960 → 1.7232 | **33%** |
| `case1.autocross.peak_lon_g` | 1.3749 → 1.7802 | **33%** |
| `case3.endurance.typical_deg` | 0.5683 → 0.8033 | **31%** |

**Every peak-based figure should be quoted with its cutoff attached.** "Peak
longitudinal G was 1.65 g" is not a fact about the car without "at 5 Hz"
beside it.

Two things learned by getting them wrong first:

- **Sign flips.** Six quantities change sign across the sweep —
  `case4.skidpad.worst_travel_mm` reads +18.5 mm at 5 Hz and −19.8 mm at 8 Hz.
  Not a 216% change in the physical answer; skidpad runs both directions, so
  the two candidate peaks are near-equal and the filter breaks the tie.
  Spread is measured on **magnitude** and the sign flip is flagged
  separately. An earlier version differenced signed values and put seven such
  rows at the top of the table with 200%+ spreads.
- **Small bases.** `case4.*.worst_modes.warp` shows the largest spreads
  (49–231%), but warp is 0.5–1.7 mm — the percentage is large because the
  base is small, not because much is moving.

### `build_cutoff_review.py` — choosing cutoffs

**The cutoff decision has been made** — 10 Hz everywhere, 3 Hz for front brake
pressure, reasoning in `case_common.py`, evidence above. This tool is what
supported that decision and what to re-run if the data set changes or the
choice is revisited.

```powershell
uv run build_cutoff_review.py
```

Lays out every choice that genuinely needs making — **29 cells** (quantity ×
event, not a mostly-N/A 9×5 grid) — with the relevant plots beside each, and
somewhere to record the answer. It decides nothing itself.

| output | |
|---|---|
| `review_cutoffs/<event>.html` | one scrollable page per event, plots inline in worklist order |
| `cutoff_decisions.yaml` | one block per cell with blank `chosen_hz:` / `why:` fields |

Both are **generated on demand and not kept in the repo** — a blank worksheet
in version control would imply outstanding work that isn't outstanding; the
decision itself lives in `case_common.py`.

The worksheet carries the *which cells even matter* guidance from the
sensitivity sweep: all skidpad cells are insensitive (0.3–1.7%), front brake
pressure is Nyquist-forced, vehicle speed is coarse gating only — leaving the
autocross/endurance/brake peak cells, which move 24–39%.

Pages carry a lightbox (scroll to zoom about the cursor, drag to pan, `fit` /
`1:1`, Esc to close) and an "open interactive ↗" Plotly overlay per signal
where each cutoff can be toggled from the legend — the question a static
overlay can't answer once down to two or three candidates. `_zoom` window is
**10 s** by default (`--zoom-duration` overrides).

Roll and pitch each appear **twice**, under different quantities — not a
duplication: `case2`/`case3` report them as body **angles** while `case4`
reports physical wheel **travel**. High-frequency wheel motion is real travel
but not chassis attitude, so the travel answer can legitimately sit *higher*
than the angle answer even though it's the same four sensors.

## Regression test — `test_regression.py`, full detail

```powershell
uv run test_regression.py --dir comp2026_data            # check
uv run test_regression.py --dir comp2026_data --update   # re-pin
```

Six real bugs were found and fixed here in quick succession —
`VCPDU_lat`/`lon` read as g when the DBC says m/s², a hardcoded
runs-per-direction cap that silently discarded data, step glitches winning
the peak search, `filtfilt` edge artefacts, an inverted roll sign convention,
and the `braketest2` misdiagnosis. Every fix moved published numbers, and
nothing existed that would have caught any of them going the other way.

Pins the summary dicts from all four cases plus the **12-event step-glitch
inventory**, reporting each difference with a percentage:

```
  cases.case4_combined_roll_pitch.endurance.worst_roll_deg
      pinned: -1.2569025802757943
      now:    -1.2498403951472068
      change: +0.562%
```

- **Not a correctness test** — only tells you *same*, not *right*. Useful
  while cutoff selection is in flight: when a per-signal cutoff table lands,
  every roll/pitch/travel figure will move, and the question is whether they
  moved where expected.
- **Doesn't reimplement anything** — calls `case_summary.py`'s collectors, so
  a methodology change is picked up rather than tested against a stale copy.
- **A failure is information, not an error to silence.** Read the diff,
  decide if the change was intended, re-pin with `--update`, and **commit
  `regression_expected.json`** — that commit is the record of what moved and
  why.

Verified end to end: changing `AUTOX_END_CUTOFF_HZ` from 5.0 to 6.0 was caught
across every affected value with exit code 1.

## Union grid vs true 100 Hz — `compare_resampling.py`

Measures what would change if the case scripts filtered on a true 100 Hz grid
instead of the InfluxDB union grid.

```powershell
uv run compare_resampling.py --dir comp2026_data
```

**Decides nothing** — the case scripts still use the union grid.

| quantity | mean | range |
|---|---|---|
| roll | +0.84% | −2.76% to +5.53% |
| pitch | +0.88% | −5.77% to +4.60% |
| lateral G | +1.56% | **−7.51% to +9.60%** |

Not the "~1% systematic, one-directional" it was once assumed to be — it is
bidirectional and per-file up to ~10%, with `endurance_full`'s headline peak
lateral G moving 1.780 → 1.646 g. A real decision, not a free accuracy win,
which is why it's deferred rather than quietly applied.

Also prints the **residual inflation** the resampling removes — 40% on
skidpad to 485% on `autocross_andrew2` — which is why `filter_compare` *does*
resample: its residual view is what settles a borderline cutoff, and on the
union grid up to five sixths of the "discarded content" it showed was
zero-order-hold staircase rather than signal.

Deliberately not applied at the same time as the cutoff retune, so a
regression diff has one cause and stays attributable.

## `case_report.py`

Not run directly — each case imports it and wraps its `main()`, producing
`plots/<case>/report.html` and `plots/index.html`.

- **Console output is tee'd, not captured.** Everything still prints, so
  nothing that piped or grepped a case's output breaks. The page is an
  addition, not a redirection.
- **Plots are embedded as lazy iframes** pointing at the files each case
  already writes, not regenerated or inlined. A case can change how it builds
  a figure without this file knowing, and the individual plot files stay
  usable on their own.

## `batch_signal_stats.py` — full detail

```powershell
uv run batch_signal_stats.py --dir comp2026_data --list-signals   # cheap peek, no parse
uv run batch_signal_stats.py --dir comp2026_data                  # stats tables
uv run batch_signal_stats.py --dir comp2026_data --plot           # + time-series grids
uv run batch_signal_stats.py comp2026_data/skidpad_austin_both.csv   # single file
```

**`--list-signals` first, with unfamiliar data.** Reads only the
`_field`/`_value` columns — no pivot, no union grid, no pickle cache — and
reports `n`/`min`/`max` per signal. **1.0s on the 234 MB endurance file
against 3.8s for a cold full parse.**

It's also the *only* view showing each signal's true update rate, since the
stats tables count samples on the resampled union grid. That's real and easy
to miss: on skidpad, `VCFRONT_brakePressure` has **977 samples where the
shock pots have 9783** — roughly 10 Hz against 100 Hz.

`--plot` saves one PNG per event — a grid with a subplot per signal, a line
per file, x-axis in elapsed seconds. Lines >20,000 points are
stride-decimated for drawing only; stats always use full data. PNGs go to
`./plots` or `--plot-dir <folder>`.

**Plotting is selectable; stats are not.** A subplot grid stops being
readable well before the signal list does (19 signals is already a
2340×1820 image), but a text table costs nothing, and narrowing it would hide
the anomalies that make this tool diagnostic — you'd have to already suspect
`FL` to select `FL`.

```powershell
uv run batch_signal_stats.py --dir comp2026_data --plot --signals VCPDU_lat,VCPDU_lon
```

With `--plot` and no `--signals`, an interactive numbered prompt accepts
`all`, `1,4,7`, or ranges like `2-6,9`; bare Enter keeps everything. Skipped
when stdin isn't a TTY, so scripted/piped runs never block.

Files are grouped by event from the filename; all samples from all files of
an event are pooled into one table (every `accel_*.csv` becomes a single
ACCEL row set). A final ALL EVENTS table pools everything.

It's genuinely diagnostic. Reading the skidpad table alone surfaces three of
the known data problems: `steeringAngle` with a mean of −151° and max of
−69° (never positive), `shockpotdispFL` spanning 18.4mm against
`shockpotdispFR`'s 34.4mm, and `VCPDU_lat` reaching ±20 (confirming m/s², not g).

## Will it handle new signals?

Mostly yes, automatically.

| script | new signals? | why |
|---|---|---|
| `parse_influx.py` | ✅ automatic | Discovers signals from the CSV's own `_field` column. Never had a fixed list |
| `batch_signal_stats.py` | ✅ automatic | `discover_signals()` reports everything present, appends unrecognised names at the end, prints `[i] N signal(s) not in PREFERRED_SIGNAL_ORDER`. That constant only controls display order — not a filter |
| `filter_compare.py` | ⚠️ one-line edit | Add a tuple to `EXTRA_SIGNALS`: `(signal_name, plot_title, y_label, file_stem)`. Curated on purpose — you pick which signals to compare cutoffs on. Missing signals are skipped with a warning |
| `case_common.py` | ⚠️ explicit | `CORNER_SIGNAL_NAMES` and `BRAKE_PRESSURE_SIGNALS` name specific physical sensors; no generic meaning to substitute |
| `case1`–`case4` | ⚠️ explicit | Each declares `REQUIRED_SIGNALS` and refuses to run a file without them — correct by design, a case is a physics question, not a signal dump |

So a new channel appears in the survey with no code change, and only needs
wiring where a specific physical meaning is required.

**Two things to watch when adding a signal:**

- **Check its units in the DBC.** `VCPDU_lat`/`lon` are `m/s2` despite reading
  like g's, and that exact mistake reached production here — case2 and case3
  gated segmentation at an effective 0.031 g instead of 0.3 g, understating
  accel pitch by up to 32%.
- **Check its update rate in firmware** (`grep periodic.*Hz_CLK`). It bounds
  any usable cutoff: shock pots and the IMU are 100 Hz (Nyquist 50), but
  steering angle is 10 Hz (Nyquist 5), so filtering it above 5 Hz is meaningless.

## Adding a new case

The four cases share a deliberate shape. To add `case5_<thing>.py`:

1. **Reuse `case_common`** — `lowpass`, `elapsed_seconds`, `trim_window`,
   `find_steady_segments`, `top_k_peaks`, `baseline_corner_displacements`,
   `to_wheel_travel`, `find_step_glitches`, `find_braking_windows`. Don't
   redefine constants; if a pattern would be duplicated across cases, it
   belongs in `case_common` instead.
2. **Declare `REQUIRED_SIGNALS`** and skip files that lack them.
3. **Verify every threshold against real data before committing to it** —
   measure the noise floor in stopped-car windows to pick a peak prominence,
   confirm event windows exist with the durations you assume. Every constant
   in the existing cases has its measurement recorded in a comment; match that.
4. **Convert to wheel travel before any axle arithmetic** if touching shock
   pots, because front and rear motion ratios differ.
5. **Have your `report_*` function return a summary dict** as well as
   printing — that's what lets `case_summary.py` include it without
   duplicating logic.
6. **Register it in `case_summary.py`** — add a `collect_caseN()` mirroring
   the others, and a column in `build_rows()`.
7. **Write plots to `plots/case5_<thing>/<event>/`**, plus one headline chart.
8. **Document the methodology in the README**, including anything rejected
   and why — case4 exists in its current form only because
   `√(roll² + pitch²)` was tried, measured, and found to reproduce case2 to
   three decimals.

---

## Case 1 — Max G's, full methodology

**Events:** skidpad, autocross, endurance. **Signals:** `VCPDU_lat`, `VCPDU_lon`.

- **Skidpad** — steady segments from the sign and magnitude of filtered
  lateral G (>0.3 g, ≥2.0s real duration), keeping the **2 longest runs per
  direction**, trimmed 0.5s each end. Reports the **median** over the
  trimmed middle, not a peak — matching how FSAE itself scores skidpad
  (average over the steady lap). Run-to-run spread also reported.
- **Autocross / endurance** — whole-file peak detection on lateral,
  longitudinal and combined `√(lat²+lon²)`, prominence **0.3 g**, top 5
  pooled + single highest. Each peak reports the *simultaneous* lat/lon pair
  (the actual g-g point) and `alpha`, that point's angle.

Steering-rate gating was tried and abandoned; the absolute steering value was
never used because the sensor is miscalibrated.

## Case 2 — Max Roll, full methodology

**Events:** skidpad, autocross, endurance.

```
roll_front = wheel FR − wheel FL   → atan(mm / 1219.2)
roll_rear  = wheel RR − wheel RL   → atan(mm / 1168.4)
roll_avg   = (front + rear) / 2    → atan(mm / avg track)
```

- **Skidpad** — reuses case1's exact lateral-G segments; median front/rear/avg per run.
- **Autocross / endurance** — whole-file peaks on `|roll_front|`,
  `|roll_rear|` and `|roll_avg|` separately, prominence **2.0mm**, reporting
  front *and* rear at the same instant.

Prominence justification: roll noise std ~0.12mm during stopped windows, and
sweeping 0.5→10mm left the top-5 and single peak completely unchanged.

## Case 3 — Max Pitch, full methodology

**Events:** all five. `pitch = avg(wheel FL, FR) − avg(wheel RL, RR)` →
`atan(mm / 1543)`.

**Sign convention — verified empirically against vehicle speed, not assumed:**

```
pitch > 0   squat      (acceleration)
pitch < 0   dive       (braking)
```

A *higher* mm reading is more **extension** on this car's calibration — the
opposite of what the formula alone suggests.

Methodology differs per event because the data genuinely differs:

- **Skidpad** (2 Hz) — lateral-G segments, median pitch. Expected near zero;
  a sanity check.
- **Accel** (5 Hz) — longitudinal-G steady segments restricted to the
  **accelerating** (negative lon G) branch, excluding the braking phase at
  the end of accel files. Median over the trimmed window. Verified as one
  continuous ~4s pull, not a series of spikes.
- **Brake** (5 Hz) — windows from **front brake pressure >100 psi AND
  speed >3 m/s**, minimum 0.3s. *Both* gates required: pressure alone
  produced a single 30.3-second "braking window" (the driver holding the
  pedal at a standstill) and several windows whose pitch was *positive* —
  squat, impossible under braking. With the speed gate, every surviving
  window dives correctly — independent evidence the detection is right.
  Within each window the single worst `|pitch|` instant is taken. Pooled
  across files, top 5 averaged + single hardest.
- **Autocross / endurance** (5 Hz) — whole-file peaks on `|pitch|`,
  prominence **3.0mm** (pitch noise std 0.13–0.55mm during stopped windows).

## Case 4 — Combined Roll + Pitch, full methodology

**Events:** all five. Reports **worst per-corner wheel travel**, where
`travel < 0` = compression (bump), `> 0` = extension (droop). Both extremes
reported, since both have a mechanical limit.

### Why not `√(roll² + pitch²)`

Built, measured against real data, and **rejected**:

1. **Roll and pitch peaks never coincide** — measured gaps between each
   file's worst-roll and worst-pitch instant: endurance 869s, autocross
   20–53s. Independent events.
2. **Roll is 2–4× larger than pitch** on this car, so a root-sum-square is
   captured almost entirely by roll. On endurance it returned 1.450° at an
   instant where pitch was +0.034° — identical to case2's max-roll answer to
   three decimals. It measured nothing new.

Per-corner travel is where roll and pitch physically superpose, needs no
arbitrary "both axes elevated" threshold, and is the quantity that decides
whether a spring or damper runs out of travel.

### Modal decomposition

At the worst instant, travel is decomposed **exactly** — an algebraic
identity, asserted at runtime, not a fit:

```
heave = (FL + FR + RL + RR) / 4      FL = heave − roll + pitch + warp
roll  = ((FR + RR) − (FL + RL)) / 4  FR = heave + roll + pitch − warp
pitch = ((FL + FR) − (RL + RR)) / 4  RL = heave − roll − pitch − warp
warp  = ((FL + RR) − (FR + RL)) / 4  RR = heave + roll − pitch + warp
```

So the report states precisely how many mm came from roll vs pitch vs heave
vs **warp** — diagonal chassis twist, visible here and in neither case2 nor case3.

### Other outputs

- Peak detection on the **4-corner envelope** `max(|FL|,|FR|,|RL|,|RR|)`,
  prominence 2.0mm, top 5 + single worst.
- **Skidpad and accel also get a sustained number** (median over steady
  segments), being quasi-steady events.
- Per-corner signed extremes, with the outer 2% of each file excluded
  (`filtfilt` overshoots at array boundaries — a file ending mid-event
  produced a fake 17.36mm peak against a 16.33mm raw peak) plus glitch masking.
- Per-event roll-vs-pitch scatter with a convex hull, showing which
  *combinations* the car actually reaches.

**Scope caveat:** case4 runs all five events, but only **autocross (17–29% of
samples) and endurance (20%)** genuinely load both axes at once. Skidpad is
2.6%, accel 0–0.9%, braketest1 0%. The other three are effectively sanity
checks, not real combined cases.

---

## Case 5 — Roll and pitch gradient (°/g), full methodology

**Events:** roll on skidpad/autocross/endurance, pitch on
accel/brake/autocross/endurance.

The headline suspension metric, and the one number the rest of the analysis
was building toward. Cases 1–4 answer *"how much did the car roll?"* — a
property of the **run** (a driver who pushed harder gets a bigger number).
Gradient answers *"how much does this car roll per unit of lateral
acceleration"* — a property of the **car**, and the bridge to a roll
stiffness in N·m/deg.

Nothing is reimplemented: roll comes from `case2_max_roll`'s loader and pitch
from `case3_max_pitch`'s.

### The number

**Skidpad steady segments — the cleanest estimate, and the one to quote:**

| | gradient | R² |
|---|---|---|
| Front | **0.833 °/g** | 0.997 |
| Rear | **0.941 °/g** | 0.997 |
| Whole car | **0.886 °/g** | 0.998 |

`endurance_full` independently gives 0.812 / 0.918 / 0.864 °/g — a different
event, different driver, 919k samples, agreeing to within 3%.

This lands squarely on the **0.83–0.94 °/g** hand-derived estimate — that
range turns out to have been the front-to-rear spread. A completely
independent check — dividing case2's skidpad roll angle by case1's sustained
lateral G, neither of which computes a gradient — gives 0.814 / 0.943 / 0.873
°/g, within 2%.

**Pitch gradient** is 0.54 °/g; accel (0.544) and brake (0.543) agree to
three decimals despite being squat and dive respectively.

Intercepts are 0.002–0.101°, which is the baselining checking out: a level
car at 0 g.

### Fitting choices

- **Intercept is fitted, not forced through zero.** The car is physically
  level at 0 g, so a large intercept is not a free parameter — it's evidence
  a baseline is off, and reporting it is the point.
- **Excluded:** step glitches, and samples below 2 m/s (a parked car is a
  dense cluster at the origin that inflates R² without informing the slope).
- **Transients are kept.** The scatter they produce is a result, not
  contamination — roll lags lateral G, so a corner entry and its matching
  exit trace different paths and the cloud opens into a loop. Steady-state
  skidpad gives R² = 0.997; autocross does not, and the width is the
  information.
- **Signs are checked, not absolute-valued.** A positive raw slope would mean
  a convention flipped upstream, and is reported as an error rather than
  quietly hidden.

### Finding: two autocross runs have unusable front shock-pot data

Front gradient per file:

| file | front | rear | rear/front |
|---|---|---|---|
| `autocross_andrew2` | 0.780 | 0.884 | 1.13× |
| `autocross_josh1` | 0.794 | 0.895 | 1.13× |
| **`autocross_andrew1`** | **0.294** | 0.871 | **2.96×** |
| **`autocross_josh2`** | **0.311** | 0.905 | **2.91×** |

Per-corner travel per g isolates it completely — **both front corners drop by
~2.6× while both rears are untouched**:

| file | FL | FR | RL | RR |
|---|---|---|---|---|
| `autocross_andrew2` | 6.03 | −10.57 | 8.89 | −9.13 |
| `autocross_josh1` | 6.38 | −10.52 | 8.78 | −9.47 |
| `skidpad` | 6.56 | −11.04 | 9.13 | −9.95 |
| `endurance_full` | 6.36 | −10.93 | 9.37 | −9.34 |
| **`autocross_andrew1`** | **2.40** | **−3.86** | 8.55 | −9.21 |
| **`autocross_josh2`** | **2.50** | **−4.13** | 8.96 | −9.50 |

**This is a measurement problem, not the car:**

- **The runs are effectively identical.** Chronological order — `josh1`
  18:38, `josh2` 18:47, `andrew1` 19:37, `andrew2` 19:39 — pattern is normal,
  bad, bad, normal. Lateral-G content is the same in all four (\|lat\| p99
  1.47–1.62 g, range 3.18–3.31 g), so not driving style. `andrew1` →
  `andrew2` are **two minutes apart**, ruling out any physical change to the
  car. (There is also no anti-roll bar on the 2026 car, so an earlier ARB
  hypothesis was wrong on the mechanism as well as the timing.)
- **The decode is fine.** `disp ← volt` fits −25.495 to −25.511 mm/V in every
  file, against the documented global −25.510.
- **The front pots are sitting at the end of their range.** Raw voltage differs:

  | file | FL volt median | FR volt median | front gradient |
  |---|---|---|---|
  | `josh1` | 0.816 | 1.241 | 0.794 |
  | `josh2` | **0.332** | **0.550** | 0.311 |
  | `andrew1` | **0.378** | **0.597** | 0.294 |
  | `andrew2` | 0.855 | 1.340 | 0.780 |

  Since `disp = −25.51·V + c`, low voltage is high extension. In the bad runs
  both front pots sit at ~0.2–0.8 V — bottom of electrical range, maximum
  extension end of stroke — reading 70.7 mm against 63.6–66.7 mm elsewhere,
  where travel compresses (`josh2` FL sweeps just **7.2 mm** against 22.4 mm
  in `josh1`).

  Same phenomenon as *Known data problems #3* (FL baseline wandering
  42.4–66.9mm across sessions) — but affecting **both front pots**, not just
  FL, with a measured consequence: it more than halves the apparent front
  roll gradient.

**What to do with it.** Treat `autocross_josh2` and `autocross_andrew1` front
data as unusable; quote the front gradient from `josh1`, `andrew2`, skidpad
and endurance, which agree at **0.78–0.83 °/g**. Rear is unaffected in all
four files. The **pooled autocross figure of 0.542 °/g must not be quoted** —
`case5_gradients.py` prints per-file gradients and warns when the front
spread exceeds 1.5×.

**Confirmed independent of position around the lap** (via `lap_detection.py`,
common distance axis) — front/rear roll amplitude ratio per 79 m segment:

| segment | `josh1` | `josh2` | `andrew1` | `andrew2` |
|---|---|---|---|---|
| 0–79 m | 1.39 | **0.59** | **0.60** | 1.46 |
| 157–236 | 1.50 | **0.61** | **0.64** | 1.63 |
| 314–393 | 1.57 | **0.59** | **0.52** | 1.46 |
| 550–629 | 1.63 | **0.61** | **0.61** | 1.48 |
| 629–707 | 1.46 | **0.56** | **0.59** | 1.51 |

~1.5 on clean runs, ~0.6 on bad ones, **constant all the way round**. (Last
segment is the slowdown to the finish, roll tiny, ratio noise.) Rules out
driving style, a specific corner, and the Run 1 off-course excursion — a
run-long, position-independent factor of ~2.5 is a property of the
measurement, not of how the car was driven.

Open question: *why* the front pots ended up at their extension limit for
those two runs and not the neighbouring ones. Pattern is clean → bad → bad →
clean across a driver change and a 50-minute gap, with `andrew1`/`andrew2`
only two minutes apart, so nothing physical changed between the last two. A
check of the front pot mounting and usable stroke range would settle it —
telemetry can localise the problem but not diagnose the hardware.

---

## What each file actually is — official results and run provenance

From the [FSAE Electric 2026 official results](https://www.fsaeonline.com/CompResources/2026/07af50d8-cbb6-4b9b-aaf8-5ff6a7e44057/FSAE_2026_MI6_results.pdf)
plus team context. **Concordia is car #43, 19th overall, 475.1 points** (3rd
in Cost at $25,197; car is 1 motor, 370 V, **215.5 kg** — the mass needed to
turn a °/g gradient into N·m/deg).

A telemetry file is not self-describing — knowing that one autocross run went
off course, or that an endurance lap contains an unscheduled stop, changes
how an anomaly in it should be read.

### Autocross — Josh ran first, then Andrew

| official run | file | raw time | penalty | adjusted |
|---|---|---|---|---|
| 1 | `autocross_josh1` | 50.508 | **1 off course (+20 s)** | 70.508 |
| 2 | `autocross_josh2` | **49.541** | clean | 49.541 — best |
| 3 | `autocross_andrew1` | 54.514 | clean | 54.514 |
| 4 | `autocross_andrew2` | 51.687 | clean | 51.687 |

18th place, 81.81 points. Telemetry corroborates the ordering: `andrew1` is
the slowest official run *and* the slowest in telemetry (65.8 s moving,
against 57–59 s), with the longest distance (804 m against 787–791 m).

### Endurance — Andrew first, then Josh. **DNF on the last lap.**

**1483.688 s, 21 scored laps**, DNF. Two sources differ in a way worth
knowing: the [results portal](https://results.fsaeonline.com/MyResults.aspx?carnum=43&tab=endurance)
records **23 transponder passes** (first is init) and labels the count
*"Lap Count (Incl. Driver Chg & Black Flag): 22"*, while the official PDF
lists 21 and carries `DNF`. 23 passes − 1 init − 1 driver-change lap = 21
scored laps, so the two reconcile. Portal shows no explicit DNF text; PDF is
the official document, so DNF stands.

Lap times, with the portal's driver-change lap restored (PDF omits it,
shifting every subsequent lap number by one):

```
 1  68.197    7  69.067   13  121.893  ← momentary stop     19  66.800
 2  68.187    8  70.253   14   68.477                       20  64.423
 3  71.313    9  69.223   15   67.020                       21  63.363  ← best
 4  67.567   10  70.104   16   64.873                       22  66.470
 5  67.160   11  76.540   17   66.610
 6  69.293   12 168.890 ← DRIVER CHANGE   18  66.857
```

**Lap 12 (168.890 s, 16:07:08) is the driver change itself** — the portal
notes *"The Driver Change lap will appear below as a long lap."* **Lap 13
(121.893 s, 16:09:10) is the separate momentary stop near the start of
Josh's stint**, team-confirmed. Two distinct events, not one — an earlier
version of this section conflated them because the PDF's list omits the
driver-change lap entirely.

Lap 11 at 76.540 s is the run-in to the change. Last seven laps (63–67 s) are
the fastest of the event — the car recovered fully, best lap 63.363 s at lap 21.

Note `endurance_full.csv` spans 1740 s against the official 1483.7 s, so the
file holds roughly four minutes beyond the scored run.

This gives lap detection a strong ground truth: 22 laps with durations known
to the millisecond, two of which (12 and 13) are stationary events a detector
must handle rather than trip over. The portal also gives wall-clock
timestamps per lap for absolute-time checking.

### Skidpad — Austin only

15th, best 5.178 s. Austin ran first and **only his two runs were pulled**:
5.461/5.122 R/L (avg 5.291) and 5.297/5.061 (avg **5.178**, the counting
run). Second driver DNF'd one run and was slower, so that data was
deliberately not exported. `skidpad_austin_both.csv` is therefore both of
Austin's runs and nothing else.

### Brake test — `braketest2` is the valid run

Both runs achieved **full four-wheel lockup**. `braketest1` is invalid on
procedure only: driver braked **too early**, before the mandated point.
`braketest2` is the run that counted — up to the required speed, braking at
the right place, all four locked.

Procedure invalidates it for scoring, not for engineering: `braketest1` is
still real maximum-braking data and is used alongside `braketest2`.

Peak front pressures run counter to intuition:

| file | peak front pressure | status |
|---|---|---|
| `braketest1` | **1830 psi** | invalid — braked too early |
| `braketest2` | **1112 psi** | **the valid run** |

The *invalid* run used 65% more pressure for the same outcome — not a
contradiction, **past lockup, extra pressure does nothing**. Once all four
wheels are sliding, more pedal force cannot increase deceleration, so
pressure above the lock threshold only records how hard the driver pushed.
Peak brake pressure is a poor proxy for braking performance; lockup on this
car happens at or below ~1100 psi.

### Acceleration — Jamie first, then Corinne

20th, best 4.521 s. Runs were 4.569 / **4.521** (Jamie, both in
`accel_jamie_both.csv`) then 4.604 / 4.601 (`accel_corinne1`,
`accel_corinne2`). Remarkably consistent across drivers — 4.52–4.60 s.

## Known data problems

Read this before trusting any number.

### 1. Shock-pot step glitches — handled automatically

Twelve instantaneous step discontinuities across four files: FL and FR jump
*together* by ~13mm and ~22mm, then hold at the new level. Suspension cannot
step and then sit still, so these are sensor/electrical faults.

| file | time(s) |
|---|---|
| `accel_corinne1` | 118.84 |
| `autocross_andrew1` | 76.99 |
| `autocross_josh1` | 84.56 |
| `braketest2` | 46.23, 46.33, 147.95 |

They are **larger than any real event**, so an unprotected peak search
reports them as the worst case — before rejection they held the top spot in
three of case4's five events, including its overall design-driving case.

The 8mm threshold is not a judgement call. Over 7.6 million real sensor
updates, legitimate per-update jumps have p99.9 = 1.19mm, p99.99 = 1.78mm,
and the largest in any clean file is 4.38mm. The glitches are
20.35–23.32mm. **Nothing falls between 4.4mm and 20.3mm.**

### 2. `VCFRONT_steeringAngle` is unusable

Two separate problems, both traced to
`firmware/components/vc/front/src/steeringAngle.c`:

- **Zero calibration was never run.** The map is ±0.78 V → ∓90°, i.e.
  −115.3846 °/V applied to `(voltage − steeringCalibration_data.zero)`. That
  zero is still 0 V, so a ~1.5 V resting sensor gives −115.3846 × 1.5 =
  **−173.077°** — exactly the −173.0 seen in all 11 files. Not a DBC rail and
  not an electrical fault: lines 108–111 set `angle = 0.0f` when faulted, so
  a faulted sensor would read 0°, and the implied voltages (0.589–1.499 V)
  sit inside the 0.25/2.75 V fault window.
- **Only one steering direction registers.** Voltage only ever moves down
  from its 1.4993 V rest, where it sits for 73% of a file across just 69
  distinct values. Re-zeroing recovers the offset but not the missing half
  of travel.

Its *rate of change* is not a safe fallback either: while the signal sits at
rest its derivative is identically zero, which any "is the driver holding a
steady line?" test reads as steady from a flat-lined sensor.

### 3. `FL` shock pot is suspect

On skidpad, FL sweeps **18.4mm** while FR sweeps **34.3mm**, and FL's static
baseline ranges **42.4–66.9mm** across sessions, 13–22mm away from FR. Likely
the "one of the sensors might be broken" noted in the original project brief.

### 4. Front and rear roll disagree — unexplained

A rigid chassis has exactly *one* roll angle, so front and rear derived roll
should match. They don't: **rear reads 7–27% more**, same sign every event.
Worse, the **rear shows 16–22% left/right asymmetry that the front does not**
(1.1–3.3% front), appearing on skidpad, which is symmetric by construction.

A pure *gain* error on a rear pot cannot cause this — in roll, one pot
compresses while the other extends, so `RR − RL` sums the two gains and
gives equal magnitude either direction. Direction-dependent asymmetry
requires genuinely asymmetric rear roll stiffness or a **non-linearity** (a
pot near its stroke limit, or something binding). Candidate explanations
remain chassis torsional flex, a motion-ratio error, or pot calibration —
currently unresolved, so the rear roll number is the less trustworthy of the two.

Related: **FR is the worst-loaded corner in 8 of 11 files**, too consistent
to be noise.

### 5. `braketest2.csv` — earlier "unreliable" verdict was WRONG

Previously flagged as unreliable on three counts: shock-pot noise 10–20×
every other file (0.394/0.667mm against a 0.031mm median), elevated
combined-angle noise, and filter overshoot stuck at 106% across all cutoffs.
**All three were the same artefact, and the file is fine.**

It holds step glitches at 46.23s and 46.33s, and `find_static_window` selects
0.5–50.2s as its stopped-car window — so **the glitches sit inside the
baseline window**. The 10–20× "noise" was std computed across a step
discontinuity, not sensor noise. Masking the glitch:

| corner | baseline median as-is | glitch-masked | std as-is | std masked |
|---|---|---|---|---|
| FL | 53.330 | **53.330** | 0.570 | **0.007** |
| FR | 38.380 | **38.380** | 0.964 | **0.024** |
| RR | 41.340 | **41.320** | | |

The glitch mask is now applied to baselining (`static_baseline(...,
bad_mask=...)`). Across all 11 files this moves exactly **one** number:
`braketest2`'s RR baseline, by **0.02 mm**. FL and FR are unchanged. That
0.02 mm propagates into six case4 brake figures by at most 0.72%. The mask is
there for the *std* column, not the median one.

Two conclusions: the **baseline was never damaged** (`static_baseline` uses a
median, robust to the step, identical to three decimals), and with the
glitch excluded the file's noise is **0.007–0.043mm** — one of the *cleanest*
files, not the worst.

The window is also genuinely stopped (mean longitudinal G +0.005 g), so not a
lockup mistaken for a standstill — a real risk in principle, since
`VCFRONT_vehicleSpeed` comes from wheel speed and reads ~zero during a
four-wheel lockup while the car is still moving.

**There is now a code guard for this.** `find_static_window(..., lon_g=...)`
rejects any candidate stop whose **mean** \|lon G\| reaches 0.15 g. Applied
**per run, not per sample** — the per-sample version was tried first and is
wrong: a genuine stop briefly touches 0.26–0.94 g as the car rolls to a halt,
so sample-wise rejection fragments real stops (it moved
`accel_jamie_both`'s window from 0.0–9.2 s to an entirely different
17.2–25.3 s, and trimmed nine others). A lockup is a *sustained* ~1 g
deceleration, so the mean over the run is the right statistic. Every genuine
stop in `comp2026_data` averages **0.008–0.031 g**, two orders of magnitude
clear of the threshold.

The guard changes **nothing** on current data — all 11 windows are
byte-identical with and without it. Verified on a synthetic file instead:
given a real standstill and a four-wheel lockup both reading speed ≈ 0, it
picks the standstill; given only the lockup, returns `None`, so
`baselines_found=False` and the caller warns rather than silently baselining
against a hard-braking car.

**Context:** `braketest2` is the brake test that *passed* at competition —
up to the required speed, braking at the mandated point, all four wheels
locked. Prime data.

The only genuine issue is the step glitches themselves, now rejected
automatically by `find_step_glitches()`. One caution remains: any *std-based*
measurement over a window containing a glitch will be inflated, so re-derive
noise floors with the glitch mask applied.

### 6. IMU 2-sample spikes — visible in plots, harmless to the numbers

`VCPDU_lat` and `VCPDU_lon` carry isolated spikes that are **not vehicle
motion** — the big downward spike visible in `accel_corinne1`'s longitudinal
traces, not unique to that file.

| file | channel | value | samples |
|---|---|---|---|
| `accel_corinne1` | lon | −20.675 m/s² (**−2.108 g**) | 2 |
| `endurance_full` | lat | +27.591 m/s² (**+2.813 g**) | 2 |
| `autocross_josh1` | lon | +24.371 m/s² (**+2.485 g**) | 2 |
| `autocross_andrew2` | lat | −21.519 m/s² (**−2.194 g**) | 2 |

Marks of an artefact rather than data:

- **Always exactly two consecutive samples, 10 ms apart**, holding a
  *bit-identical* value — a real accelerometer at a genuine peak does not
  produce the same float twice.
- **Physically implausible.** 2.1–2.8 g where each file's own p99.9 is
  0.9–1.9 g, reached in a single 10 ms step of 7–20 m/s².
- **Not a DBC rail** — value differs per file, so not the brake-pressure-style
  saturation seen below.

**They do not affect any reported number.** Verified on `endurance_full`
(largest spike, 2.813 g): whole-file filtered maximum is **1.7798 g with the
spike and 1.7798 g without** — identical. The 5 Hz low-pass eliminates a
2-sample impulse; local filtered peak at the spike is only 1.09 g, well below
the file's actual 1.78 g maximum elsewhere. Case 1's peak G figures stand.

**Where they do bite:** the peak-attenuation table, whose denominator is the
raw *max*. A file whose raw max is a spike reads as if filters were
destroying signal (57–66% retained) when they're correctly rejecting an
artefact. `filter_compare.py` prints a `raw p99.9` column beside the max and
flags cells where the two diverge by >1.3× as `spike_dominated`.

### 7. `endurance_full.csv` brake pressure saturates — a firmware clamp

Front pressure reads exactly **2000 psi** at its maximum, p99.9 *and* p99.
That ceiling is not the sensor's or car's physical limit — it's an explicit
clamp in `brakePressure.c`:

```c
else if (brakePressure_data.voltage >= 4.5f)
    brakePressure_data.pressure = 2000.0f;      // hard clamp
else
    brakePressure_data.pressure = (voltage - 0.5f) * 500.0f;
```

Sensor is calibrated across 0.5–4.5 V → 0–2000 psi. **Any true pressure past
4.5 V reads exactly 2000**, so those samples are a *floor*, not a measurement.

Three things confirm genuine saturation rather than a coincidental real limit:

- **198 samples pinned at exactly 2000**, in only 5 episodes — a pile-up, the
  clipping signature. A real maximum is approached and rarely touched.
- **One episode runs 11.3 seconds continuously.** Braking pulses in this data
  are 0.31–2.43 s. Eleven seconds at maximum pressure is not a braking event.
- **Both brake tests achieved full four-wheel lockup at 1112 and 1830 psi.**
  Past lockup, extra pressure buys nothing, so 2000+ psi sustained for 11.3 s
  is far beyond anything braking requires.

All five episodes fall in a 30-second window (t = 1066–1096 s), oddly
clustered for racing. Whether that's a stationary period with someone
standing on the pedal or a sensor problem can't be told from this export —
the fault flag (`FM_FAULT_VCFRONT_BRAKEPRESSURESENSORFAULT`, set from the
same voltage) and the brake voltage channel would settle it, and neither was
pulled. **Worth adding both to the next export.**

Practical effect: pressure-derived peaks in `endurance_full` are floors, and
`find_braking_windows` may merge braking events there since a clamped signal
can't show the dip between two pulses.

### 8. `VCFRONT_brakePressure` is 10 Hz, not 100 Hz

Measured on all 11 files: front **10.0 Hz**, rear **100.0 Hz**, exactly.
Every other channel in the export is 100 Hz.

**The sensors are identical — the CAN messages are not.** Both modules
sample at 100 Hz (`brakePressure.c` has `brakePressure_periodic_100Hz`); the
difference is transmission rate:

| | message | `cycleTimeMs` | rate |
|---|---|---|---|
| Front | `VCFRONT_pedalInformation` (`0x51`) | 100 | **10 Hz** |
| Rear | `VCREAR_rearBrakePressure` (`0x453`) | 10 | **100 Hz** |

Front pressure rides on a **shared** 8-byte message alongside both APPS
voltages and the brake pot — only logged and displayed. Rear pressure has its
**own dedicated** message because `VCFRONT` subscribes to it: `torque.c` uses
it live to compute brake torque for torque allocation, so it has to be fast
and fresh.

Two consequences:

- **Nyquist is 5 Hz** for the front channel, so any cutoff at or above that
  is meaningless for it. Filtered at 3 Hz for exactly this reason.
- **`find_braking_windows` uses the front channel** — front and rear track
  each other and front is larger, but that happens to pick the 10× slower
  one, which can only place a window edge to within 100 ms against braking
  pulses of 0.31–2.43 s. Whether rear gives cleaner edges is worth checking.

The data **exists** at 100 Hz on the module and is simply not transmitted, so
front pressure at 100 Hz is a firmware change (raise `cycleTimeMs`, or give
it its own message), not new hardware — to be weighed against CAN bus load.

### 9. IMU attitude signals

`VCPDU_angleRoll` / `anglePitch` read ±20–36° against ±1.3° derived from the
shock pots — consistent with an uncalibrated gravity-vector tilt rather than
chassis attitude (the DBC carries `IMU_UNCALIBRATED` and
`IMU_YAW_CALIBRATION_FAILED` warnings). Not used.

`VCPDU_yaw` is partially characterised: dead-reckoning a path from yaw rate
and speed does **not close** — the integrated autocross course spans ~365 m
while start and end land 156–177 m apart. Consistent with the calibration
warning, and the reason there's no track map.

The raw *rates* (`VCPDU_roll`/`pitch`, deg/s) are a separate question and
have **not** been validated — different signals from the angle channels, may
fail for different reasons, or not at all. A proper write-up is outstanding.

## Open questions

- **Low-pass cutoff for accel/brake.** No cutoff was ever chosen for these
  two events — they inherit `AUTOX_END_CUTOFF_HZ` (5 Hz), a constant
  validated for autocross/endurance transients. It matters: peak pitch moves
  ~12% across 2→10 Hz. An earlier version of this entry claimed a real 6–8 Hz
  mode made the choice delicate — see *Spectral analysis* below; that turned
  out not to be true, simplifying the decision.
- **Motion ratio** is a single value per axle. If it varies meaningfully with
  travel, a curve would be more accurate.
- **Case 7 from the original brief (max yaw timing)** is deliberately not
  implemented.

## `filter_compare.py` — full detail

Compares low-pass cutoffs across **9 signals** — lateral/longitudinal/combined
G, roll, pitch, vehicle speed, front/rear brake pressure, and steering angle
(flagged unusable). Roll and pitch included because those are what the case
scripts actually report on — picking a cutoff from the G traces alone leaves
the shock-pot cutoff unvalidated.

```powershell
uv run filter_compare.py comp2026_data/accel_*.csv --freqs 5 8 --zoom-on-peak
uv run filter_compare.py comp2026_data/braketest1.csv --freqs 2 5 10 --zoom-at 100
```

### Three views per signal

A single overlay hid the data it was meant to show, structurally: **the
higher the cutoff, the closer the filtered trace is to raw**, so 15/20 Hz
traces land almost exactly on raw and — drawn last — paint over raw *and*
every lower cutoff. Sweeping more frequencies makes it strictly worse, so no
palette change fixes it. Each signal now produces:

| view | what it's for |
|---|---|
| `_panels` | **Primary.** Small multiples, one panel per cutoff, raw redrawn pale behind each. Nothing can be occluded because nothing competes |
| `_residual` | **What settles a borderline call.** `raw − filtered`, i.e. exactly what each cutoff *discards*, with RMS per panel. A formless residual means the cutoff is safe; coherent oscillation means real signal is being deleted |
| `_overlay` | All cutoffs on one axis — still the best view for judging *where* traces separate. Z-order reversed (highest cutoff drawn first) so the lowest cutoff ends on top |

Each cutoff gets a **distinct hue**, fixed slot order by ascending frequency,
so a given cutoff is the same colour on every signal and file. A sequential
single-hue ramp was tried first — cutoff is strictly ordered magnitude, which
argues for one — but seven steps of the same blue proved unreadable on a busy
trace. Palette validated at 7 slots on the light surface (worst adjacent CVD
ΔE 9.1, normal-vision ΔE 19.6); aqua, yellow and magenta fall below 3:1
contrast, so every view carries visible labels and never relies on colour
alone. Past **8 cutoffs** the script raises rather than cycling hues.

Plots render at **220 dpi**, because review pages scale them down to fit the
column and the lightbox blows them back up.

Prefer `_zoom` views for choosing a cutoff — at full-file extent every cutoff
collapses into the same smear and the views are context only.

- Prints a **peak-attenuation table** — how much of each signal's peak
  survives each cutoff. Also written to `peak_attenuation.json` per file,
  which `build_cutoff_review.py` reads.
- **Read low percentages carefully.** The table's denominator is the raw
  *max*, which on some files is a 1–2 sample spike rather than the real peak
  — `endurance_full`'s raw lateral G maxes at **2.813 g**, holding 33 samples
  above 2.0 g, not physical for this car. A `raw p99.9` column sits beside
  the max; cells diverging by >1.3× are flagged `spike_dominated`. There, a
  low "% retained" means the filter is *rejecting a glitch*, not destroying signal.
- `--skip-plots` refreshes `peak_attenuation.json` without regenerating plots.

## Spectral analysis — `spectral_analysis.py`, full detail

Runs on a true 100 Hz grid (a Fourier transform of non-uniformly sampled data
is undefined, and the union grid's zero-order-hold staircase would
manufacture broadband energy no sensor measured). Works in case4's exact
heave/roll/pitch/warp modal basis, because a PSD peak alone identifies
nothing — what distinguishes a body mode from local wheel motion is **how the
corners move relative to each other**.

```powershell
uv run spectral_analysis.py --dir comp2026_data
uv run spectral_analysis.py --dir comp2026_data --band 4 12
```

### Result: there is no 6–8 Hz mode

This README previously recorded "a real **6–8 Hz mode carrying 5.88mm** of
travel" and treated it as the crux of every cutoff decision. **It is not
supported by the data.**

| mode | verdict across 11 files |
|---|---|
| heave | 8/11 have a prominent peak, but at 1.1, 1.1, 3.4, 3.5, 3.9, 8.0, 8.8, 21.9 Hz — **no cluster** |
| roll | 9/11 prominent, at 1.1–21.8 Hz — **no cluster** |
| pitch | only 6/11 have a prominent peak at all |
| warp | 9/11 prominent, at 1.1–21.9 Hz — **no cluster** |

A resonance is a property of the structure, so it has to land at the *same*
frequency file after file. These don't. Inter-corner coherence says the same
thing independently — never exceeds **0.41** in any band:

| band | FL–FR | RL–RR | FL–RL | FR–RR |
|---|---|---|---|---|
| 1–4 Hz | 0.22 | 0.24 | 0.27 | 0.21 |
| 4–9 Hz | 0.29 | 0.41 | 0.21 | 0.24 |
| 9–16 Hz | 0.13 | 0.14 | 0.12 | 0.12 |

Coherence that low means the corners are **not** moving together, so what the
shock pots see above 1 Hz is largely uncorrelated per-corner content — road
input and sensor noise — rather than coordinated body motion.

**This simplifies the cutoff decision.** No resonance to avoid sitting on, so
5 and 8 Hz are not special — the choice is the plainer one of how much
uncorrelated content belongs in each reported number.

Two method cautions: local maxima on a falling spectrum are mostly ripple, so
a peak must also stand above its local background (an earlier pass reported
the roll-off shoulder as a mode); and a peak count is not a mode — taking the
median of scattered peak frequencies produced a confident "1.50 Hz mode" from
frequencies spanning 1.12–21.88 Hz, which is why the clustering test exists.

- `--zoom-on-peak` centres each zoom on that signal's own largest moment (the
  fixed 600s window lands on arbitrary quiet track for short accel/brake
  events). `--zoom-at <seconds>` overrides it — useful because the automatic
  peak sometimes lands on a step glitch.
- Peak stats exclude the outer 2% of each file, since `filtfilt` overshoots
  at boundaries.

**Source sample rates** (from firmware — these bound which cutoffs mean anything):

| signal | rate | Nyquist |
|---|---|---|
| Shock pots (`shockpot.c`, `periodic100Hz_CLK`) | 100 Hz | 50 Hz |
| IMU lat/lon (`imu.c`, `periodic100Hz_CLK`) | 100 Hz | 50 Hz |
| Steering angle (`steeringAngle.c`, `periodic10Hz_CLK`) | 10 Hz | 5 Hz |

**`filter_compare.py` resamples to a true 100 Hz grid before filtering**, so
100 Hz is the `fs` every filter there is designed against. The union-grid
density is still printed for context but is *not* a sample rate — it's how
often some signal happened to update, built by zero-order hold, and
designing a filter against it is what this used to do wrongly. A bug during
that change had `fs` still taken from the old union timestamps while the data
was already resampled, which would have made a nominal 5 Hz cutoff actually
0.57 Hz; the printed rate now names which is which so the two can't be
confused again.

Note the case scripts still filter on the union grid — see `compare_resampling.py`.

Also note the IMU's own firmware low-pass (`imu.c:47`) is set to a 100 Hz
cutoff at a 100 Hz sample rate — above Nyquist, so effectively a pass-through;
the offline filtering does all the real work.

## Lap detection — `lap_detection.py`, full detail

Finds laps and aligns runs corner-by-corner, **without any position signal**.

```powershell
uv run lap_detection.py --dir comp2026_data
uv run lap_detection.py --dir comp2026_data --file endurance_full
```

**There is no GPS in this data** — 19 signals across all 11 files, none
positional. `VCPDU_yaw` exists, but dead-reckoning a path from it does not
close: the integrated autocross course spans ~365 m while start and end land
**156–177 m apart**, consistent with the DBC's `IMU_YAW_CALIBRATION_FAILED`
warning. So there's no track map and no way to name a corner geometrically.

**Distance works instead.** Speed integrates cleanly even though it can't be
differentiated (the 9–13 g `dv/dt` is a differentiation artefact of the union
grid; integrating averages the same quantisation out). Cumulative distance is
lap-invariant — the same corner happens at the same distance every lap,
whatever the driver did. Laps come from resampling speed onto a uniform
**distance** grid and autocorrelating: a repeated course makes `v(d)`
periodic with period = lap length.

Working in distance rather than time is what makes stationary events
harmless. **A driver change adds ~170 s and zero metres**, so in the distance
domain it collapses to a point instead of looking like a lap boundary — the
case a time-based detector gets wrong.

### Validated against official lap times

| | |
|---|---|
| laps detected | **22** — exactly the official count |
| lap length | 970 m (autocorrelation +0.82) |
| interior laps | median error **0.65 s, 0.9% of lap time**; worst 3.28 s |

Three laps are inaccurate and all three are **edges, not failures**:

- **Lap 1** absorbs pre-race running — without a start line there's nothing
  to anchor it to.
- **Lap 12** is the driver change. All stopped time lands in whichever lap
  contains it, by design; the official boundary comes from a timing loop,
  this one from distance.
- **The last** is a partial remainder — total distance is not an exact
  multiple of a lap.

Autocross runs are correctly identified as **single laps** (too short to
autocorrelate a repeat) and get distance-aligned overlays instead, under
`plots/lap_detection/autocross_*_by_distance.html` for roll, lateral G and
speed. Those overlays are what confirmed the front shock-pot deficit is
uniform around the course.

**What it cannot do:** name a corner. Without position, "the same distance"
is the only handle on "the same corner", so overlays are read against
distance rather than a track map.

## Shock-pot displacement vs voltage

`disp` is a single global linear transform of `volt`: **−25.510 mm/V**,
identical on all four corners and all 11 files. So the voltage channels
carry no extra information — but there is also **no per-corner calibration**,
meaning unit-to-unit gain and zero variation is unaccounted for. Plausible
contributor to problems 3 and 4 above.
