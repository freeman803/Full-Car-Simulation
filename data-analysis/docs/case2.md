# Case 2 — Max Roll: calculations and sources

Citation keys resolve in [`../REFERENCES.md`](../REFERENCES.md).

## What is computed

Roll angle per axle, from the four shock-pot displacements. Every corner is
converted to **wheel** travel first, then differenced.

```
wheel_mm      = shockpot_mm * MR              MR = 1.188 front, 1.038 rear
roll_front_mm = wheel_FR - wheel_FL
roll_rear_mm  = wheel_RR - wheel_RL
roll_deg      = atan(roll_mm / track_mm) * 180/pi
```

Track 1219.2 mm front, 1168.4 mm rear. Wheelbase 1543 mm.

## Sources, claim by claim

| Claim | Source |
|---|---|
| Motion ratio is *wheel travel ÷ spring travel* (hence > 1, and you multiply) | `ROUELLE-11`: *"the ratio between wheel movement and spring movement"*; `OG-TT1`: *"MR = Motion ratio (Wheel/Spring travel)"* |
| Wheel rate = spring rate ÷ MR² | `ROUELLE-11`: *"The wheel rate, K, is the spring rate divided by the square of the motion ratio"*, with a conservation-of-energy derivation |
| Roll angle from suspension travel is a standard derived channel | `SEGERS`, §"Measuring Suspension Roll Angle" |
| Roll gradient is degrees of body roll per g of lateral acceleration | `OG-TT2`; `SEGERS`, §"The Roll Gradient" |
| Roll rate scales with track² | `OG-TT2`: `K_φF = π·t_f²·K_LF·K_RF / (180·(K_LF+K_RF))` |
| Ride/roll rate theory generally | `RCVD` Ch.16 "Ride and Roll Rates" |
| Axis and sign conventions | `J670`; `RCVD` Ch.4 "Vehicle Axis Systems" |

**MR is applied per corner, before any axle arithmetic.** Front and rear ratios
differ by 14%, so a single ratio applied after mixing axles is only valid if
they are equal. Follows directly from the per-corner definition in `OG-TT1`.

## Suspension- vs ground-referenced

Shock pots span chassis-to-upright, so they measure roll about the **wheel-centre
line**, not the ground. A design roll gradient normally includes tyre deflection.

- `OG-TT2` states the exclusion explicitly, right after its roll equations:
  *"The following equations do not take into account roll due to the tires."*
- `ROUELLE-11` supplies the missing element: *"Wheel rate will be in series with
  the tyre rate (or tyre stiffness if you prefer)."*

### Deriving the multiplier

Not quoted from anywhere — derived from those two statements in two lines. Under
a load increment `ΔF` at one corner, spring and tyre deflect in series:

```
suspension-referenced = ΔF/k_wheel                 chassis → wheel centre
ground-referenced     = ΔF/k_wheel + ΔF/k_tyre     chassis → ground
ratio                 = 1 + k_wheel/k_tyre
```

Sprung mass, CG height and weight distribution all cancel — tyre rate is the only
extra input. Pitch sums both axles' compliances, giving one multiplier rather
than a per-axle pair: `1 + (2/k_tyre) / (1/k_wf + 1/k_wr)`.

Checked against first principles (deflection per unit `ΔF`, suspension vs ground):

| | first principles | `case_common.py` |
|---|---|---|
| roll front | 1.306582 | 1.306582 |
| roll rear | 1.356970 | 1.356970 |
| pitch | 1.329863 | 1.329863 |

**Exact for load-transfer-driven roll and pitch**, since the same load increment
deflects spring and tyre. Approximate for transient peaks — a kerb strike does
not deflect the tyre proportionally. Gradients carry no such caveat.

The whole-car `avg` (1.332144) has one modelling choice on top: it is the ratio
of roll stiffness built on wheel rates to roll stiffness built on ride rates. The
`k·t²` weighting is `OG-TT2`'s `K_φ` formula; what is local is using one blended
multiplier instead of rebuilding from the two axles, because front/rear/avg peaks
land at three different instants and rebuilding would combine moments that never
coexisted (see the comment in `case_common.py`).

Say **"derived from"**, not "per Milliken".

Sanity check against published ranges (`OG-TT2`: 0.2–0.7 °/g stiff high-downforce,
1.0–1.8 °/g low-downforce): steady skidpad measures **0.898 °/g suspension-referenced,
1.196 °/g ground-referenced**. The ground-referenced figure lands in the published
band; the suspension-referenced one falls below it. Quote the ground-referenced
number to a judge, and say which reference it is in.

## The front/rear disagreement

Rear reads +9.5% of front consistently. `HPA` — practitioner discussion, not
peer-reviewed — attributes exactly this to chassis torsional deflection, bushing
and hardpoint compliance, difference in tyre loaded radius, calibration error,
and *"assumptions in kinematics (constant motion ratios etc)"*. The same thread
states the premise behind our front-vs-rear scatter plot: *"steady state roll
angles front and rear need to be in close agreement for a rigid chassis."*

Relevant here because our motion ratios are single measured values, not curves.

## Known approximation

The whole-car "avg" converts mean front/rear mm over mean track, rather than
averaging two separately converted angles. The two tracks differ by 4.3%, so the
error is 0.17–0.19% (1.6201° reported vs 1.6231° exact at the endurance peak).
Documented rather than fixed, so published numbers stay comparable.
