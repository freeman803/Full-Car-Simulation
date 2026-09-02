# CFR27 chassis stiffness — inputs still needed

For the chassis torsional stiffness target. Model is written and waiting; these
six numbers are all that's missing.

| # | Parameter | Units | Ask | CFR26 was |
|---|-----------|-------|-----|-----------|
| 1 | **ARB front — softest and stiffest** | N·m/deg **at the axle** | Suspension | 0 — none fitted |
| 2 | **ARB rear — softest and stiffest** | N·m/deg **at the axle** | Suspension | 0 — none fitted |
| 3 | Motion ratio, front | wheel ÷ spring | Suspension kinematics | 1.188 measured |
| 4 | Motion ratio, rear | wheel ÷ spring | Suspension kinematics | 1.038 measured |
| 5 | Track, front | mm | Suspension / CAD | 1219.2 |
| 6 | Track, rear | mm | Suspension / CAD | 1168.4 |


**Already answered** — spring rates **150/175/200/225/250 lbf/in**, same set both
ends · tyre **700 lbf/in**, same Hoosier 43075 at the same pressure · front mass
fraction **0.500**, a design *target*.

> The mass fraction is intent, not a measurement — CFR26's 0.507 came off
> competition scales. Replace it with corner weights as soon as CFR27 is
> weighed; the as-built number will not be exactly 0.500.

## Notes when answering

**ARBs (1–2) — a range is all I need.** Just the softest and stiffest setting at
each end. Intermediate detents change nothing: the criterion is applied to the
*widest* adjustment the car can make, so only the extremes enter. Checked — the
target is identical whether you give 2 settings or 41.

If the bar can be removed entirely, the soft end is 0.

**Please quote it at the AXLE, not at the bar.** A bar's own torsional stiffness
is not its roll stiffness at the axle — they differ by the ARB's motion ratio,
squared. If axle rate isn't to hand, send the bar rate *and* the ARB motion
ratio and I'll convert. Getting this wrong is the same trap as the road-spring
motion ratio, and it bites just as hard.

**Motion ratio (3–4)** — please say whether each is **measured or from CAD**. It
enters stiffness as MR², so a 5 % error becomes 10 % in the target. CFR26's was
corrected twice before it settled.

## Not needed

Sprung mass, sprung CG height, roll centre heights. They cancel out of the
target — only the front/rear mass split matters. (They *are* needed to report
roll angles in deg/g, which is a different question.)
