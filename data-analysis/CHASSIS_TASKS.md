# Chassis stiffness — task list

Working roadmap for the CFR27 chassis stiffness work. Written 2026-09-01.

**Where things stand.** CFR26's target is derived and defensible:
**1341 N·m/deg** — a 90 % delivery criterion across the balance range the real
spring box reaches, with a 10 % build loss allowed for. Unvalidated FEA puts
the frame near 1100, so it is **~18 % short**, and short at every criterion
from 85 % up and every build loss from 5 % to 20 %.

Closed already: the model and its tests (`torsional_stiffness.py`, 39 tests),
the criterion decision at 90 %, the build loss at 10 %, and the CFR26 spring
box (150/175/200/225/250 lbf/in, 25 setups, 36.6–57.0 % front).

Everything below either feeds CFR27's target or closes a gap the CFR26 work
exposed.

**The critical path is 1 → 5 → 6.** Nothing else unblocks a number.
**Do 8 first anyway** — it is cheap, and prior Concordia work may already
answer parts of 2, 4 and 5.

---

## 1. CFR27 target — parameters from suspension

**Script is ready and waiting.** `cfr27_target.py` holds the full parameter set
as placeholders; run it and it prints exactly what is still missing. Filling
`P` at the top of that file and re-running produces the target.

- [ ] **1a — Ask suspension for the ten inputs.** The list is in the script;
      `uv run cfr27_target.py` prints it as a checklist. Note these are
      **CFR27's** values — the CFR26 box is known and is not a substitute.
  - spring rates available, front and rear — **every rate we'd actually run**,
    not the expected pair. (CFR26's box is 150/175/200/225/250; ask whether
    CFR27 inherits it or changes.)
  - motion ratios front/rear (wheel ÷ spring), and **say whether measured or
    CAD** — this enters stiffness as MR², so it is the most error-sensitive
    input in the set. CFR26's was corrected twice.
  - track front/rear
  - tyre vertical rate at running pressure and load — not a catalogue default
  - **ARB settings reachable at each end** ← the one that matters most
  - front mass fraction (CAD estimate now, corner weights once it's on scales)
- [x] **1b — Criterion decided: 90 %.** Not a suspension input. Reasoning is
      on slide 9 — 80 % costs a fifth of the tuning authority, and the MRacing
      paper, Cardiff, common practice and Milliken's 3–5× rule all agree nearer
      90 %. Revisit only with a reason.
- [x] **1b′ — Build loss set at 10 %**, i.e. ÷0.90, not ×1.10. Assumed, not
      measured — see 6d, which is where it gets checked.
- [ ] **1c — Run it, sanity-check against CFR26**, and expect a materially
      different number. CFR26 had no ARB, so its frame was barely loaded; the
      bar is what makes the frame work for a living.

> **Do not chase** sprung mass, sprung CG height or roll centre heights for
> this. They cancel out of the target — only the front/rear mass split matters.
> Pinned by a test. They *are* needed to report roll angles in deg/g, which is
> a different question.

---

## 2. Hand calculations at suspension pickup points

Sizing and justification for the local structure where suspension loads enter
the frame. Judges probe this, and it is where installation stiffness is won or
lost.

- [ ] **2a — Loads at a node.** Resolve suspension link loads into the tubes
      meeting at each pickup. Establish the worst-case load set first (see 2d)
      and work from that, not from a nominal case.
- [ ] **2b — Loads *off* a node.** The case that actually needs the work: when
      a pickup does not land on a tube intersection, the tube sees **bending**
      rather than pure tension/compression, and a thin-wall tube is far weaker
      in bending. Quantify the penalty as a function of offset distance, and
      set a rule for the maximum offset we will accept before adding structure.
- [ ] **2c — Size the support tubes** at each suspension point from 2a/2b.
      Decide diameter and wall, and record *why* each was chosen. Cross-check
      against the rules for minimum tube sizes via the `fsae-rules` skill —
      never from memory, the numbers change between seasons.
- [ ] **2d — Agree the design load cases** before doing any of the above.
      DesignJudges' *Tube Frame Analysis* lists what they expect: torsion,
      max braking with max chain tension on the driven side, max acceleration
      with chain tension, max cornering with tyre and wing loads, one-wheel
      bump with simultaneous cornering, and a false-static 20 g front crash.
- [ ] **2e — Compare hand calcs against FEA** at the same points. Agreement is
      the evidence that both are right; disagreement is worth chasing before
      either number goes in a report.

---

## 3. Excel template for design iteration

One sheet where a proposed change goes in and torsional stiffness plus mass
come out, so options can be compared without re-deriving anything.

- [ ] **3a — Decide what the sheet is *for*.** Recording FEA runs (paste in
      results, track the trade) is a different sheet from predicting stiffness
      without FEA. The first is worth building; the second mostly is not,
      because tube-frame stiffness does not decompose neatly into a formula.
- [ ] **3b — Columns:** change description, date, tube changes made, mass Δ,
      torsional stiffness (and **which** — frame-only or wheel-to-wheel, they
      differ), stiffness/mass, and whether it clears the target.
- [ ] **3c — Make specific stiffness the headline** (N·m/deg per kg), not raw
      stiffness. Raw stiffness always improves by adding metal; the ratio is
      what shows whether a change was actually *good*.
- [ ] **3d — Keep the baseline row locked** so every change is measured against
      the same reference, and never delete old rows — the design-event value is
      in the evolution, not the final number.

---

## 4. Find the softest part of the chassis

The frame is a series of springs and the softest section dominates, so the
end-to-end number alone does not tell you where to spend mass.

- [ ] **4a — Plot twist distribution along the frame** from the torsion FEA:
      relative rotation of each cross-section against longitudinal position.
      The steep segments are the soft bays.
- [ ] **4b — Report sectional stiffness per bay**, not just the total. The
      Elsevier Formula Student paper does exactly this and localises the soft
      sections; Cardiff went 1446 → 2930 N·m/deg by fixing one bay their twist
      plot identified.
- [ ] **4c — Check the cockpit opening specifically.** It is the usual answer
      on a spaceframe, and if it *is* the limit then structure elsewhere —
      near the shocks, say — may be carrying no load and can come out.
- [ ] **4d — Feed the result back into 3.** "Which bay" is what makes the
      iteration sheet actionable rather than a log.

---

## 5. FEA setup and constraints

The 1100 N·m/deg figure is unvalidated and the setup behind it is unrecorded.
Until this is redone the target comparison rests on an unknown.

- [ ] **5a — Use the minimal constraint set.** From DesignJudges: rear fixed
      vertically both sides; longitudinal position and longitudinal-axis moment
      fixed one side; lateral position and lateral-axis moment fixed on the
      opposite side; equal and opposite vertical loads at the front damper /
      rocker mounts. Their warning: *"Lock down only the degrees of freedom
      that actually are either fixed or reacting the load beyond the frame"* —
      overconstraining makes the frame look stiffer than it is.
- [ ] **5b — Analyse wheel-to-wheel, not frame-only.** This is the big one.
      DesignJudges: *"I don't want to see just a fixed-bulkhead-to-fixed-
      bulkhead torsional load case on only the frame design."* They want it
      from the suspension pickups, or better *"from the wheelrim to the
      wheelrim through the outboard assemblies and links."* **Our 1100 is
      frame-only, which is exactly the number that article pushes back on.**
- [ ] **5c — Mesh.** Start at 5.1 mm second-order shells (five around a 1 in
      tube, so joint stress is visible); refine anywhere stress changes more
      than 40 % between adjacent elements. Record the sensitivity check.
- [ ] **5d — Include the ARB** in any CFR27 model. Leaving it out changed one
      published Formula Student result by ~17 %, and comparing a no-ARB model
      against an ARB-fitted test is not a comparison.
- [ ] **5e — Write down the setup** alongside the number. A stiffness figure
      without its boundary conditions is not a result.

---

## 6. Twist test CFR26

Closes three gaps at once and is the highest-value single thing on this list.

- [ ] **6a — Build or borrow a rig.** ASEE have a build paper; Cardiff's method
      (rigid suspension lockout bars, 3D motion capture) is in the library.
- [ ] **6b — Map the force–deflection curve**, do not take one load step. The
      curve is non-linear at low load and shows hysteresis — Riley & George.
- [ ] **6c — Back out installation stiffness** by comparing the measured
      wheel-to-wheel figure against frame-only FEA (`infer_installation()`).
      This number has never been measured on this car and is the one most
      likely to be limiting.
- [ ] **6d — Measure our own build loss** and replace the assumed 10 %. That
      10 % is a judgement call from published results (Cardiff hit 3.7 %,
      Elsevier call 10 % acceptable, MRacing measure 10–20 %) — **we have never
      run a twist test, so we have not earned it.** "Our designed-vs-built gap
      is X %" is a far stronger design-event answer than any borrowed number.
      If our real gap is worse than 10 %, the target rises.

---

## 7. Open modelling gaps

Not blocking anything, but each would sharpen the answer. Record them as known
limitations rather than discovering them in the tent.

- [ ] **7a — Transient.** Everything so far is steady-state. The MRacing paper
      ran a lap simulation and got a *higher* number, so the current target is
      a lower bound.
- [ ] **7b — Roll axis and unsprung terms.** Sampo (Surrey PhD) shows load
      transfer distribution has three terms and a spring change moves only one,
      so an elastic-only model overstates the tuning authority on offer. This
      makes the case for a tighter criterion, not a looser one.
- [ ] **7c — ARB load path.** Installation compliance is currently modelled in
      series with springs *and* bar together. If the bar has its own path to
      the frame, real saturation sits between that and none — resolving it
      needs the actual mounting geometry.
- [ ] **7d — Resolve the 1.167× roll gap.** Measured roll is ~17 % below the
      design sheet, and it sits between the roll moment (mass × CG height) and
      the roll stiffness. It does **not** affect the stiffness target — the
      scale cancels — but it is unexplained and worth closing.

---

## 8. Read the 2019 chassis capstone

Prior Concordia work on this exact subject. Cheap to read and it may already
cover parts of 2, 4 and 5 — worth doing before starting any of them, if only
to avoid redoing it.

- [ ] **8a — Find it and record where it lives.** Path not known; ask whoever
      has it. Add the location here once found so the next person doesn't
      have to hunt.
- [ ] **8b — Extract what is reusable:**
  - any torsional stiffness target they set, **and the justification** — a
    number without its reasoning is not evidence, but the reasoning may be
  - FEA setup: constraints, element type, mesh, and whether frame-only or
    wheel-to-wheel (§5)
  - whether a twist test was ever performed, and what it read (§6) — if the
    car was tested, we have a designed-vs-built gap already
  - hand calculations at suspension pickups, and tube sizing rationale (§2)
  - any stiffness distribution or soft-bay work (§4)
- [ ] **8c — Check what has since changed.** It is a 2019 document: the
      rulebook, the tyres, the packaging and the team's methods have all moved.
      Take the method, verify every number against current sources, and treat
      rules content as expired — check the `fsae-rules` skill instead.
- [ ] **8d — Record the delta.** Note what it got right, what we now do
      differently and why. That comparison is itself good design-event
      material: it shows the team's methods evolving rather than restarting.

---

## Reference

- Model, criterion and derivation: `torsional_stiffness.py`
  (`--detail`, `--sources`, `--criterion`, `--loss`)
- CFR27 scaffold: `cfr27_target.py`
- Reading library: `~/.claude/skills/chassis-design/references/papers.md`
- Rules, tube sizes, SES: the `fsae-rules` skill — never quote a rule from memory
