# References

Sources for the vehicle-dynamics calculations in the case scripts. Per-case
mapping of *which* source backs *which* line of maths is in `docs/case2.md` and
`docs/case4.md` — this file is just the bibliography.

**Verified** = the PDF was downloaded and read, and quotes in `docs/` are exact.
**Listing only** = the work is real and the cited section titles come from a
publisher or catalogue listing, but the text itself was not read. Do not quote
equations from a listing-only source without opening it first.

| Key | Reference | Status |
|---|---|---|
| `ROUELLE-06` | Rouelle, C. "Suspension stiffness", *Racecar Engineering*, June 2020, pp.53-54. [PDF](https://optimumg.com/wp-content/uploads/2021/10/racecar-2020_06.pdf) | Verified |
| `ROUELLE-11` | Rouelle, C. "Of springs and dampers", *Racecar Engineering*, November 2020, pp.50-51. [PDF](https://optimumg.com/wp-content/uploads/2021/10/racecar-2020_11.pdf) | Verified |
| `OG-TT1` | Giaraffa, M. "Tech Tip: Springs & Dampers, Part One — The Phantom Knowledge", OptimumG. [PDF](https://optimumg.com/wp-content/uploads/2020/01/SpringsDampers_Tech_Tip_1.pdf) | Verified |
| `OG-TT2` | Giaraffa, M. "Tech Tip: Springs & Dampers, Part Two — Attack of the Units", OptimumG. [PDF](https://optimumg.com/wp-content/uploads/2020/01/SpringsDampers_Tech_Tip_2.pdf) | Verified |
| `SEGERS` | Segers, J. *Analysis Techniques for Racecar Data Acquisition*, 2nd ed., SAE International, 2014. ISBN 9780768064599 | Listing only |
| `RCVD` | Milliken, W.F. & Milliken, D.L. *Race Car Vehicle Dynamics*, SAE R-146, 1995. [Chapter list](https://www.millikenresearch.com/rcvdbak.pdf) | Listing only |
| `ZS-2010` | Zhang, N. & Smith, W.A. "Hydraulically interconnected vehicle suspension: background and modelling", *Vehicle System Dynamics* 48(1), 2010. [Link](https://www.tandfonline.com/doi/full/10.1080/00423110903243182) | Listing only |
| `J670` | SAE J670, *Vehicle Dynamics Terminology*. [Link](https://saemobilus.sae.org/standards/j670_202206-vehicle-dynamics-terminology) | Listing only |
| `HPA` | HP Academy, "Roll gradients different front and rear", Professional Motorsport Data Analysis forum. [Link](https://www.hpacademy.com/forum/professional-motorsport-data-analysis/show/roll-gradients-different-front-and-rear/) | Verified — but a forum. Practitioner consensus, not peer-reviewed |

## Why these

`ROUELLE-*` and `OG-TT*` are OptimumG material — Claude Rouelle judges FSAE
design, so this is the vocabulary the event is judged in. `SEGERS` is the
standard SAE text for deriving vehicle dynamics from logged channels and has
named sections for most of what cases 2, 3 and 5 do; it is the one book worth
opening if you can get it. `RCVD` is the reference the others cite.

## Derived, not quoted

Two formulas here are not lifted from any source. Both are *derivations from
cited premises* rather than local inventions, and both are checked numerically —
say "derived from" when presenting them, not "per Milliken".

- **The `÷4` in case4's modal transform** is forced, not chosen. `ROUELLE-06`
  fixes the sign pattern; that matrix is Hadamard (`HᵀH = 4I`), so once you also
  require each corner to be the plain unweighted sum of its four modes, `1/4` is
  the only scalar that reconstructs. Derivation in [`docs/case4.md`](docs/case4.md).
- **The `1 + k_wheel/k_tyre` ground-referencing multiplier** follows in two lines
  from `ROUELLE-11` (wheel rate in series with tyre rate) and `OG-TT2` (spring
  roll equations exclude tyre roll). Matches first principles to six decimals.
  Derivation in [`docs/case2.md`](docs/case2.md).
