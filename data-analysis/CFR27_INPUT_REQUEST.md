# CFR27 chassis stiffness — inputs needed

For the chassis torsional stiffness target. Model is written and waiting; these
eight numbers are all that's missing.

| # | Parameter | Units | Ask | CFR26 was |
|---|-----------|-------|-----|-----------|
| 1 | **ARB settings reachable, front** | N·m/deg at the axle | Suspension | 0 — none fitted |
| 2 | **ARB settings reachable, rear** | N·m/deg at the axle | Suspension | 0 — none fitted |
| 3 | Motion ratio, front | wheel ÷ spring | Suspension kinematics | 1.188 measured |
| 4 | Motion ratio, rear | wheel ÷ spring | Suspension kinematics | 1.038 measured |
| 5 | Track, front | mm | Suspension / CAD | 1219.2 |
| 6 | Track, rear | mm | Suspension / CAD | 1168.4 |
| 7 | Tyre vertical rate | lbf/in at running pressure | Suspension / tyre choice | 700 (Hoosier 43075, 300 lb, 10 psi) |
| 8 | Front mass fraction | 0–1 | Vehicle integration | 0.507 measured |

Already confirmed: spring rates **150 / 175 / 200 / 225 / 250 lbf/in**, same set
both ends, unchanged from CFR26.

## Notes when answering

**ARBs (1–2)** — every setting *reachable*, not a nominal rate. Blade-adjustable
means the discrete steps; if the bar can be removed, include 0. This drives the
answer more than anything else on the list.

**Motion ratio (3–4)** — please say whether each is **measured or from CAD**. It
enters stiffness as MR², so a 5 % error becomes 10 % in the target. CFR26's was
corrected twice before it settled.

**Tyre rate (7)** — at the *running* pressure and load, not a catalogue default.
If the tyre or pressure changes for CFR27 this must change with it.

## Not needed

Sprung mass, sprung CG height, roll centre heights. They cancel out of the
target — only the front/rear mass split matters. (They *are* needed to report
roll angles in deg/g, which is a different question.)
