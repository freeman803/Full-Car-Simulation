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

  1. CFR27 IS EXPECTED TO HAVE ANTI-ROLL BARS. CFR26 did not, which is why its
     roll stiffness distribution sat on its mass split and the chassis was
     asked to carry almost no torque. A bar is what CREATES the demand the
     frame has to carry, so CFR27's target will not be a small correction to
     CFR26's -- expect it to move a lot.

  2. THE TARGET SCALES WITH TOTAL ROLL STIFFNESS, near enough proportionally.
     If CFR27 is stiffer in roll than CFR26's 601 N*m/deg, the frame target
     rises in step. Do not carry CFR26's number across.

  3. SIZE OFF THE SPRING BOX, not the setup you expect to run. See
     stiffness_for_setups() -- the binding case is usually the stiffest
     combination you own crossed with the widest bar setting.
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
    "spring_rates_front_lbf_in": None,      # e.g. (200, 225, 250)
    "spring_rates_rear_lbf_in":  None,      # e.g. (175, 200, 225)

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
    # CFR26 used 700 lbf/in (Hoosier 43075, 300 lb, 10 psi). If the tyre or
    # pressure changes for CFR27 this must change with it.
    "tyre_rate_lbf_in": None,               # CFR26: 700

    # --- anti-roll bars  << THE BIG ONE FOR CFR27 >> ------------------------
    # Every setting reachable, in N*m/deg at the AXLE. If the bar is blade-
    # adjustable give the range as discrete steps; if it can be removed,
    # include 0. This is what creates the balance demand the frame must carry,
    # so it drives the answer more than anything else in this file.
    "arb_settings_front_nm_deg": None,      # e.g. (0, 100, 200, 300)
    "arb_settings_rear_nm_deg":  None,      # e.g. (0, 80, 160)

    # --- mass --------------------------------------------------------------
    # Front fraction of total mass. Estimate from CAD until the car is on
    # scales, then replace with measured corner weights (CFR26: 0.507).
    "front_mass_fraction": None,

    # --- team decision, NOT a suspension input -----------------------------
    # What fraction of a commanded balance change must reach the tyres.
    # 0.80 is Deakin's published floor and is too weak to design to; 0.90 is
    # where the MRacing paper, Cardiff, Milliken's 3-5x rule and common team
    # practice all agree. See torsional_stiffness.headline() for the sweep.
    "criterion": 0.90,

    # Build margin. 1.20 is the MRacing paper's 10-20% designed-vs-built gap.
    # Replace with a Concordia figure once CFR26 has been on a twist rig.
    "build_margin": 1.20,
}

# NOT NEEDED for the target, so do not chase them for this: sprung mass,
# sprung CG height, roll centre heights. The model is linear and the absolute
# roll moment cancels out of the load-transfer ratio -- only the front/rear
# mass SPLIT matters. They are needed to report roll angles in deg/g, which is
# a different question. (Pinned by test_lltd_invariant_to_roll_moment_scale.)

_LABELS = {
    "spring_rates_front_lbf_in": "front spring rates available    lbf/in, tuple",
    "spring_rates_rear_lbf_in":  "rear spring rates available     lbf/in, tuple",
    "motion_ratio_front":        "front motion ratio              wheel/spring",
    "motion_ratio_rear":         "rear motion ratio               wheel/spring",
    "track_front_mm":            "front track                     mm",
    "track_rear_mm":             "rear track                      mm",
    "tyre_rate_lbf_in":          "tyre vertical rate              lbf/in at running psi",
    "arb_settings_front_nm_deg": "front ARB settings              N*m/deg, tuple",
    "arb_settings_rear_nm_deg":  "rear ARB settings               N*m/deg, tuple",
    "front_mass_fraction":       "front mass fraction             0-1",
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
    print(f"\n  {len(gaps)} of {len(_LABELS)} still missing:\n")
    for k in _LABELS:
        mark = "  [ ]" if k in gaps else "  [x]"
        print(f"{mark} {_LABELS[k]}")
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
    """(target, floor, worst pair, commanded change) once parameters are in."""
    s = setups()
    floor, pair, change = ts.stiffness_for_setups(
        s, threshold=P["criterion"],
        front_mass_fraction=P["front_mass_fraction"])
    return floor * P["build_margin"], floor, pair, change


def report():
    s = setups()
    tot = [(kf + kr, 100 * kf / (kf + kr), lab) for kf, kr, lab in s]
    tgt, floor, pair, change = target()
    print("=" * 70)
    print("CFR27 CHASSIS TORSIONAL STIFFNESS TARGET")
    print("=" * 70)
    print(f"\n  >>  DESIGN TO  {tgt:>6.0f} N*m/deg  <<"
          f"   ({100*P['criterion']:.0f}% criterion"
          f" + {100*(P['build_margin']-1):.0f}% build margin)\n")
    print(f"  reachable setups          {len(s)}")
    print(f"  total roll stiffness      {min(t[0] for t in tot):.0f}"
          f" - {max(t[0] for t in tot):.0f} N*m/deg")
    print(f"  balance range reachable   {min(t[1] for t in tot):.1f}"
          f" - {max(t[1] for t in tot):.1f} % front")
    print(f"  binding pair              {pair[0]} <-> {pair[1]}"
          f"   ({change:.2f} pts)")
    print(f"  floor before margin       {floor:.0f} N*m/deg")
    print(f"\n  For comparison, CFR26 (no ARB): 601 N*m/deg roll stiffness,")
    print( "  target 1557 on the same criterion. Expect CFR27 to differ a lot —")
    print( "  the ARB is what makes the frame work for a living.\n")


def main():
    if check():
        print()
        report()


if __name__ == "__main__":
    main()
