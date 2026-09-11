# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy"]
# ///
"""
cfr27_target.py — chassis torsional stiffness target for CFR27.

STATUS: WAITING ON SUSPENSION. Every parameter below is a placeholder. Fill
them in, run it, and it prints the target the same way torsional_stiffness.py
does for CFR26. Run it now and it tells you exactly what is still missing.

    uv run cfr27_target.py

The model, the criterion and the derivation all live in torsional_stiffness.py
and are not duplicated here -- this file is only the CFR27 parameter set plus
the run. Read that module's docstring first if you want to know why any of
this is the way it is.

WHAT CHANGED FROM CFR26, AND WHY IT MATTERS:

  1. CFR27 IS EXPECTED TO HAVE ANTI-ROLL BARS. CFR26 did not, so its roll
     stiffness distribution was welded to whichever four springs were fitted
     -- 44.8% front, against a 50.7% mass split. A bar is what lets you push
     that split around deliberately, and so it is what CREATES the demand the
     frame has to carry. CFR27's target will not be a small correction to
     CFR26's -- expect it to move a lot.

  2. THE TARGET SCALES WITH TOTAL ROLL STIFFNESS, near enough proportionally.
     If CFR27 is stiffer in roll than CFR26's 658.6 N*m/deg, the frame target
     rises in step. Do not carry CFR26's number across.

  3. SIZE OFF THE HARDWARE, not the setup you expect to run -- and off the
     FULL REACHABLE RANGE, not every pair of setups. This file uses
     stiffness_for_box(), the same routine as CFR26. Do not switch it to
     stiffness_for_setups(): that is the all-pairs variant, it is degenerate
     on a real box, and on CFR26's own hardware it returns 2772 against the
     box method's 1207. Read its docstring before touching this.
"""

import numpy as np

import torsional_stiffness as ts

# ===========================================================================
# PARAMETERS TO GET FROM SUSPENSION  --  all placeholders, none are real
# ===========================================================================
# Set a value and delete the None. `check()` lists whatever is still missing.

P = {
    # --- springs -----------------------------------------------------------
    # EVERY rate you would actually run, not just the expected pair. A spring
    # you own but would never fit is not a requirement, it is a distraction.
    # CONFIRMED 2026-09-01: CFR27 inherits CFR26's box unchanged.
    "spring_rates_front_lbf_in": ts.CFR26_SPRING_BOX,
    "spring_rates_rear_lbf_in":  ts.CFR26_SPRING_BOX,

    # --- motion ratio ------------------------------------------------------
    # Defined as WHEEL travel / SPRING travel, so > 1 for CFR26. Enters
    # stiffness as MR^2, making it the single most error-sensitive input here.
    # Say whether each is MEASURED or from CAD -- CFR26's was corrected twice.
    "motion_ratio_front": None,             # CFR26: 1.188 measured
    "motion_ratio_rear":  None,             # CFR26: 1.038 measured

    # --- geometry ----------------------------------------------------------
    "track_front_mm": None,                 # CFR26: 1219.2, centre-to-centre
    "track_rear_mm":  None,                 # CFR26: 1168.4

    # --- tyre --------------------------------------------------------------
    # Vertical rate at the RUNNING pressure and load, not a catalogue default.
    # CONFIRMED 2026-09-01: same COMPOUND as CFR26 -- Hoosier 43075, and 700
    # lbf/in is the 300 lb / 10 psi figure from Hoosier's published table.
    #
    # COMPOUND ALONE DOES NOT FIX THE RATE. The same tyre reads 652-859 lbf/in
    # across Hoosier's table depending on pressure and load (10-14 psi,
    # 200-400 lb). CFR26 carried 520 for a while, which was a rate for the
    # WRONG COMPOUND, and correcting it moved every ground-referenced angle by
    # 6-7%. So if CFR27 runs a different PRESSURE, this number changes even
    # though the compound has not. Worth re-checking once running pressures
    # are set.
    "tyre_rate_lbf_in": 700.0,

    # --- anti-roll bars  << THE BIG ONE FOR CFR27 >> ------------------------
    # Every setting reachable, in N*m/deg at the AXLE. If the bar is blade-
    # adjustable give the range as discrete steps; if it can be removed,
    # include 0. This is what creates the balance demand the frame must carry,
    # so it drives the answer more than anything else in this file.
    "arb_settings_front_nm_deg": None,      # e.g. (0, 100, 200, 300)
    "arb_settings_rear_nm_deg":  None,      # e.g. (0, 80, 160)

    # --- mass --------------------------------------------------------------
    # SUPPLIED 2026-09-01 as a DESIGN TARGET of 50/50, not a measurement.
    # CFR26's 0.507 was measured on competition scales; this is intent.
    #
    # Treat it as provisional and replace it with corner weights as soon as
    # CFR27 is on scales -- the as-built number will not be exactly 0.500 and
    # the direction of the miss matters (see below).
    #
    # WHY 50/50 IS AN INTERESTING CHOICE HERE. The chassis carries torque only
    # when roll stiffness distribution differs from roll MOMENT distribution.
    # At a 50/50 mass split the no-torque condition lands at a 50/50 roll
    # stiffness split, which is close to what several spring pairs give. So a
    # car built exactly to this target could be nearly insensitive to chassis
    # flex in its NEUTRAL setup -- the frame would only start working once the
    # ARB is used to move away from it. That does not lower the target (the
    # target comes from the widest adjustment, not the neutral one), but it
    # does mean a chassis-stiffness problem could be invisible until you tune.
    #
    # CFR26 was thought to be in exactly that position, on a 49.1% stiffness
    # split. The corrected rear spring (2026-09-11) put it at 44.8% and it is
    # not. Do not assume the neutral setup is the benign one -- check it.
    "front_mass_fraction": 0.500,

    # --- team decision, NOT a suspension input -----------------------------
    # What fraction of a commanded balance change must reach the tyres.
    # 0.80 is Deakin's published floor and is too weak to design to; 0.90 is
    # where the MRacing paper, Cardiff, Milliken's 3-5x rule and common team
    # practice all agree. See torsional_stiffness.headline() for the sweep.
    "criterion": 0.90,

    # Build LOSS, as a fraction -- how much softer the built car comes out
    # than its FEA. Applied as 1/(1-loss), NOT as x(1+loss): a 20% loss needs
    # x1.25, and x1.20 only covers 16.7%. That error was made once on CFR26
    # and fixed; do not reintroduce it here by typing a multiplier.
    #
    # 0.10 matches CFR26 and the Elsevier "up to 10% is acceptable" figure.
    # It is ASSUMED, not measured -- nobody has twist-tested a Concordia car.
    # Replace it the day CFR26 comes off a rig.
    "build_loss": 0.10,
}

# NOT NEEDED for the target, so do not chase them for this: sprung mass,
# sprung CG height, roll centre heights. The model is linear and the absolute
# roll moment cancels out of the load-transfer ratio -- only the front/rear
# mass SPLIT matters. They are needed to report roll angles in deg/g, which is
# a different question. (Pinned by test_lltd_invariant_to_roll_moment_scale.)

# label, units, who owns it, CFR26 value for reference
_LABELS = {
    "spring_rates_front_lbf_in": ("front spring rates available", "lbf/in tuple",
                                  "suspension", "150/175/200/225/250"),
    "spring_rates_rear_lbf_in":  ("rear spring rates available", "lbf/in tuple",
                                  "suspension", "150/175/200/225/250"),
    "motion_ratio_front":        ("front motion ratio", "wheel/spring",
                                  "suspension kinematics", "1.188 measured"),
    "motion_ratio_rear":         ("rear motion ratio", "wheel/spring",
                                  "suspension kinematics", "1.038 measured"),
    "track_front_mm":            ("front track", "mm", "suspension / CAD", "1219.2"),
    "track_rear_mm":             ("rear track", "mm", "suspension / CAD", "1168.4"),
    "tyre_rate_lbf_in":          ("tyre vertical rate", "lbf/in @ running psi",
                                  "suspension / tyre choice", "700 Hoosier 43075"),
    "arb_settings_front_nm_deg": ("front ARB settings reachable", "N*m/deg tuple",
                                  "suspension", "0, none fitted"),
    "arb_settings_rear_nm_deg":  ("rear ARB settings reachable", "N*m/deg tuple",
                                  "suspension", "0, none fitted"),
    "front_mass_fraction":       ("front mass fraction", "0-1",
                                  "vehicle integration", "0.507 measured"),

}


def missing():
    """Parameter keys still unset."""
    return [k for k in _LABELS if P.get(k) is None]


def check():
    """Print the shopping list. Returns True when everything is present."""
    gaps = missing()
    print("=" * 70)
    print("CFR27 TARGET — PARAMETERS NEEDED FROM SUSPENSION")
    print("=" * 70)
    if not gaps:
        print("\n  All present.\n")
        return True
    print(f"\n  {len(gaps)} of {len(_LABELS)} still missing.\n")
    print(f"  {'':4}{'parameter':<31} {'units':<22} {'ask':<24} {'CFR26 was'}")
    print("  " + "-" * 100)
    for k, (lab, unit, who, was) in _LABELS.items():
        mark = "[ ]" if k in gaps else "[x]"
        print(f"  {mark} {lab:<31} {unit:<22} {who:<24} {was}")
    print("\n  Fill these into P at the top of this file, then re-run.")
    print("  Not needed: sprung mass, sprung CG height, roll centre heights —")
    print("  they cancel out of the target. See the note in this file.\n")
    return False


def geometry():
    return {"mr_front": P["motion_ratio_front"], "mr_rear": P["motion_ratio_rear"],
            "track_front_mm": P["track_front_mm"], "track_rear_mm": P["track_rear_mm"],
            "tyre_rate_n_mm": P["tyre_rate_lbf_in"] * ts.cc.LBF_IN_TO_N_MM}


def setups():
    """Every reachable spring x ARB combination."""
    return ts.spring_box_setups(
        P["spring_rates_front_lbf_in"], P["spring_rates_rear_lbf_in"],
        arb_front=P["arb_settings_front_nm_deg"],
        arb_rear=P["arb_settings_rear_nm_deg"],
        geometry=geometry())


def target():
    """
    (target, floor, soft label, stiff label, commanded pts) once parameters
    are in. Same method as CFR26: the criterion applied to the FULL reachable
    range, then divided by (1 - build loss).
    """
    s = setups()
    floor, soft, stiff, change = ts.stiffness_for_box(
        s, threshold=P["criterion"],
        front_mass_fraction=P["front_mass_fraction"])
    return floor * ts.build_multiplier(P["build_loss"]), floor, soft, stiff, change


def report():
    s = setups()
    tot = [(kf + kr, 100 * kf / (kf + kr), lab) for kf, kr, lab in s]
    tgt, floor, soft, stiff, change = target()
    loss = P["build_loss"]
    mult = ts.build_multiplier(loss)
    print("=" * 70)
    print("CFR27 CHASSIS TORSIONAL STIFFNESS TARGET")
    print("=" * 70)
    print(f"\n  >>  DESIGN TO  {tgt:>6.0f} N*m/deg  <<"
          f"   ({100*P['criterion']:.0f}% criterion,"
          f" {100*loss:.0f}% build loss, x{mult:.3f})\n")
    print(f"  reachable setups          {len(s)}")
    print(f"  total roll stiffness      {min(t[0] for t in tot):.0f}"
          f" - {max(t[0] for t in tot):.0f} N*m/deg")
    print(f"  balance range reachable   {min(t[1] for t in tot):.1f}"
          f" - {max(t[1] for t in tot):.1f} % front")
    print(f"  sized off the full range  {soft} <-> {stiff}"
          f"   ({change:.2f} pts commanded)")
    print(f"  floor before build loss   {floor:.0f} N*m/deg")
    print()
    print("  THE CRITERION IS THE DOMINANT CHOICE -- it moved CFR26's answer by")
    print("  a factor of five. Do not accept the default without arguing it.")
    for th in (0.80, 0.85, 0.90, 0.95):
        k = ts.stiffness_for_box(s, threshold=th,
                                 front_mass_fraction=P["front_mass_fraction"])[0]
        mark = "  <--" if abs(th - P["criterion"]) < 1e-9 else "     "
        print(f"    {100*th:>3.0f}%  {k:>6.0f} floor  ->  {k*mult:>7.0f} target{mark}")
    print(f"\n  For comparison, CFR26 (no ARB): 658.6 N*m/deg roll stiffness,")
    print( "  44.8% front, target 1341 on the same criterion and build loss.")
    print( "  Expect CFR27 to differ a lot -- the ARB is what makes the frame")
    print( "  work for a living.\n")


def main():
    if check():
        print()
        report()


if __name__ == "__main__":
    main()
