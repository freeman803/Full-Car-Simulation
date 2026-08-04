# Case 4 — Combined loading: calculations and sources

Citation keys resolve in [`../REFERENCES.md`](../REFERENCES.md).

## What is computed

Worst per-corner **wheel travel**, decomposed into the four suspension modes.
The decomposition is an algebraic identity, not a fit — reconstruction is
asserted at runtime.

```
heave = (FL + FR + RL + RR) / 4        FL = heave - roll + pitch + warp
roll  = ((FR + RR) - (FL + RL)) / 4    FR = heave + roll + pitch - warp
pitch = ((FL + FR) - (RL + RR)) / 4    RL = heave - roll - pitch - warp
warp  = ((FL + RR) - (FR + RL)) / 4    RR = heave + roll - pitch + warp
```

Sign convention: `travel < 0` = compression (bump), `> 0` = extension (droop).

## Sources, claim by claim

| Claim | Source |
|---|---|
| A conventional suspension has four DOF, so four coordinates uniquely fix all four wheels — which is *why* this is an identity | `ROUELLE-06`: *"A conventional suspension has four degrees of freedom so we need four independent coordinates to uniquely describe the position of all four wheels with respect to the vehicle body"* |
| The four modes, defined exactly as our sign table encodes them | `ROUELLE-06`: heave = all four equal; roll = side pairs equal and opposite; pitch = end pairs equal and opposite; *"Warp motion describes each pair of diagonal wheels moving an equal but opposite amount"* |
| Any single-wheel motion decomposes into all four modes | `ROUELLE-06`: *"When a single wheel moves up, it can be thought of as a combination of heave, roll, pitch and warp movement"* |
| Cause attribution per mode | `ROUELLE-06`: *"Heave is primarily due to vertical loading… Roll is primarily due to cornering. Pitch is primarily due to braking and accelerating. Warp is primarily due to road unevenness"* |
| Travel at a wheel is the design constraint, resolved by mode | `ROUELLE-06`, Key points: *"limit the movement to 5mm of travel at either wheel. Based on the load case that causes the most pitching, you can determine what your required pitch stiffness would need to be"* |
| Formal transformation-matrix treatment | `ZS-2010` |
| Motion ratio per corner, before modal arithmetic | `ROUELLE-11`, `OG-TT1` — see [`case2.md`](case2.md) |

`ROUELLE-06` is the load-bearing citation here: it supplies both the mode
definitions and the design workflow this case implements.

## Why `÷4` — it is forced, not chosen

`ROUELLE-06` fixes the **sign pattern** but not the scaling. Write that pattern
as a matrix `H` (rows heave/roll/pitch/warp, columns FL/FR/RL/RR) and it is a
**Hadamard matrix** — rows mutually orthogonal, entries ±1:

```
H Hᵀ = Hᵀ H = 4I
```

Case4's inverse is the plain unweighted sum, `FL = heave − roll + pitch + warp`,
with no coefficients. That pins the forward scalar:

```
x = Hᵀm  and  m = cHx   ⟹   x = c·HᵀH·x = 4c·x   ⟹   c = 1/4
```

Verified on real corner values: `c = 1/2` and `c = 1` both fail to reconstruct;
only `1/4` round-trips.

So the only *choice* is requiring each corner to be the plain sum of its four
modal contributions — and that choice is what puts every mode in **per-corner
millimetres**, which is why "roll contributed +5.95 mm to this corner" is a
sentence the report can say. State that convention when quoting mm; it is a
stated convention with a forced consequence, not an arbitrary scale factor.

## No benchmark for per-corner travel

The worst case (endurance, FR, −24.28 mm) is travel *used*. It becomes a margin
only once `BUMP_LIMIT_MM` / `DROOP_LIMIT_MM` are filled in from the car's own
hardware. Nothing published to compare it against.

## Why not sqrt(roll² + pitch²)

That was the original spec and it measures nothing new on this data: roll peaks
are 2–4× pitch peaks and the two never coincide (869 s apart on endurance), so
the root-sum-square is captured entirely by roll and reproduced case2's answer to
three decimals. Per-corner travel is where roll and pitch physically superpose,
needs no arbitrary "both axes elevated" threshold, and is the quantity that
decides whether a spring or damper runs out of travel — the criterion
`ROUELLE-06` frames the problem in.
