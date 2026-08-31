# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy"]
# ///
"""
torsional_stiffness.py — what chassis torsional stiffness the car actually
needs, and why.

THE QUESTION THIS ANSWERS. Not "how stiff can we make it" (the answer to
that is always "stiffer, for more mass") but Velie's question: how stiff
does it have to be before the car stops responding to the setup changes we
want to make? Stiffness past that point is pure mass.

THE MODEL is Deakin et al., SAE 2000-01-3554, "The Effect of Chassis
Stiffness on Race Car Handling Balance" (Leeds). The car is two point
masses joined by a torsional spring, with a roll spring at each end:

    [ K_f + K_ch      -K_ch     ] [ phi_f ]   [ M_f ]
    [   -K_ch      K_r + K_ch   ] [ phi_r ] = [ M_r ]

    phi_f, phi_r  front / rear suspension roll angle      deg
    K_f,   K_r    front / rear axle roll stiffness        N*m/deg
    K_ch          chassis torsional stiffness             N*m/deg
    M_f,   M_r    sprung roll moment, split front/rear    N*m
    chassis twist = phi_f - phi_r

Elastic lateral load transfer at each axle is then K*phi/track, and the
LLTD (front share of total load transfer) is what balance tuning actually
moves. Deakin's own equations 2-4 are the same system rearranged.

WHY IT MATTERS, in the two limits:

    K_ch -> inf   phi_f = phi_r. Load transfer splits by roll stiffness
                  ratio. Full tuning authority.
    K_ch -> 0     phi_f = M_f/K_f, phi_r = M_r/K_r. Each axle rolls on its
                  own, LLTD is fixed by the mass split, and springs and
                  ARBs do NOTHING to balance the car.

So the failure mode of a soft chassis is "the car will not respond to
setup changes", not "the car breaks".

THE CRITERION is Deakin's: a chassis is stiff enough when a commanded
change in roll stiffness distribution shows up as at least 80% of the
corresponding change in load transfer distribution. Implemented here as
delivered_fraction() — literally (LLTD change actually delivered) /
(LLTD change a rigid chassis would deliver).

THE RESULT IS INVARIANT TO THE ROLL MOMENT SCALE. The system is linear, so
scaling M_f and M_r together scales phi_f and phi_r together and cancels
out of the LLTD ratio. Only the front/rear SPLIT of the moment matters.
This is worth knowing here specifically: the open 1.167x design-vs-measured
roll gap (see case5_gradients and case_common) lives entirely in the
absolute roll moment, so IT DOES NOT AFFECT THE STIFFNESS TARGET AT ALL.
Verified numerically by main().

WHAT CFR26 CAN AND CANNOT TELL US. CFR26 ran no ARB, so its roll stiffness
distribution was welded to whatever the four springs gave: 48.3% front,
against a 50.7% front mass split. Those nearly match, which means the
chassis is asked to carry almost no torque and the model correctly reports
that chassis stiffness barely matters on the as-built car. That is a real
result, not a modelling failure -- but it means the as-built configuration
cannot set a target. A target has to be set against the range of
distributions you want to be able to REACH, which is what
stiffness_for_range() does.

INPUTS all come from case_common, which is where the validated CFR26
constants already live. Nothing is re-typed here.

NOT MODELLED: installation stiffness (Riley & George's series chain,
series_stiffness() below, is the hook for it), transient response (Deakin's
static model is steady-state; Velie used a lap sim and got a HIGHER number
than a quasi-static criterion gives), and tyre load sensitivity.
"""

import numpy as np

import case_common as cc

DEG = np.pi / 180.0

# ---------------------------------------------------------------------------
# Roll stiffness from the suspension
# ---------------------------------------------------------------------------

def axle_roll_stiffness(wheel_rate_n_mm, track_mm, arb_nm_deg=0.0):
    """
    Roll stiffness of one axle, N*m/deg, suspension-referenced.

        K_roll = 1/2 * k_wheel * track^2      [N*mm/rad]  -> N*m/deg

    Suspension-referenced means "chassis against the suspension", i.e. what
    the springs alone set, with no tyre deflection in it. That is the right
    reference for a load-transfer model: load transfer is set by the spring
    and ARB rates, and adding the tyre in series would double-count the
    tyre's own deflection, which does not feed back into elastic transfer.
    (case_common's GROUND_MULT_* exist for the different job of comparing a
    predicted chassis attitude against a measured one.)

    arb_nm_deg adds directly -- an ARB is a roll spring in parallel with the
    road springs, so its rate sums with theirs.
    """
    k = 0.5 * wheel_rate_n_mm * track_mm ** 2 * DEG / 1000.0
    return k + arb_nm_deg


def cfr26_axle_stiffness(arb_front=0.0, arb_rear=0.0):
    """CFR26's two axle roll stiffnesses, from the validated case_common constants."""
    return (
        axle_roll_stiffness(cc.WHEEL_RATE_FRONT_N_MM, cc.FRONT_TRACK_MM, arb_front),
        axle_roll_stiffness(cc.WHEEL_RATE_REAR_N_MM, cc.REAR_TRACK_MM, arb_rear),
    )


# ---------------------------------------------------------------------------
# The Deakin two-mass model
# ---------------------------------------------------------------------------

# Static front weight fraction, from competition corner weights (see
# fcs-cfr26-xlsx: the design sheet's typed 0.501 is slightly off; 0.507 is
# measured). Used as the sprung-mass split too, which is an approximation --
# unsprung mass is not distributed identically -- but LLTD is only weakly
# sensitive to it and nothing better is measured.
FRONT_MASS_FRACTION = 0.507

# Absolute roll moment per g, N*m/g, from the design sheet's sprung mass
# (243.5 kg incl. 68 kg driver) and sprung CG height above the roll axis
# (340.8 mm sprung CG, roll centres 10/14 mm). NEITHER IS MEASURED, and this
# number is the one implicated in the open 1.167x gap -- the measured roll
# gradient implies ~673 N*m/g against this 785. It is carried only so the
# model can report roll angles in deg/g; every LLTD and delivered-fraction
# result is invariant to it (see module docstring).
ROLL_MOMENT_NM_PER_G = 785.2


def solve_roll_angles(k_front, k_rear, k_chassis, m_front, m_rear):
    """Front and rear suspension roll angles, deg (per whatever unit M is in)."""
    k_chassis = max(float(k_chassis), 1e-9)   # a truly rigid chassis is the limit, not a case
    a = np.array([[k_front + k_chassis, -k_chassis],
                  [-k_chassis, k_rear + k_chassis]])
    return np.linalg.solve(a, np.array([m_front, m_rear], dtype=float))


def lltd(k_front, k_rear, k_chassis,
         front_mass_fraction=FRONT_MASS_FRACTION,
         roll_moment=ROLL_MOMENT_NM_PER_G):
    """
    Front share of total elastic lateral load transfer, as a percentage.

    This is the quantity balance tuning moves, and the quantity a soft
    chassis stops you from moving.
    """
    m_f = front_mass_fraction * roll_moment
    m_r = (1.0 - front_mass_fraction) * roll_moment
    phi_f, phi_r = solve_roll_angles(k_front, k_rear, k_chassis, m_f, m_r)
    d_w_f = k_front * phi_f / (cc.FRONT_TRACK_MM / 1000.0)
    d_w_r = k_rear * phi_r / (cc.REAR_TRACK_MM / 1000.0)
    return 100.0 * d_w_f / (d_w_f + d_w_r)


RIGID = 1e9   # stands in for an infinitely stiff chassis


def delivered_fraction(k_chassis, baseline, commanded, **kw):
    """
    Deakin's criterion, as a number.

    Both `baseline` and `commanded` are (k_front, k_rear) roll stiffness
    pairs -- the setup you start from and the setup you dial in. Returns the
    fraction of the LLTD change that actually reaches the tyres, where 1.0
    is what a rigid chassis would deliver. Deakin's threshold is 0.80.
    """
    got = lltd(*commanded, k_chassis, **kw) - lltd(*baseline, k_chassis, **kw)
    ideal = lltd(*commanded, RIGID, **kw) - lltd(*baseline, RIGID, **kw)
    if abs(ideal) < 1e-12:
        return 1.0      # nothing was commanded, so nothing can be lost
    return got / ideal


def stiffness_for_criterion(baseline, commanded, threshold=0.80,
                            lo=10.0, hi=1e6, **kw):
    """Smallest K_ch (N*m/deg) meeting `threshold`, by bisection."""
    if delivered_fraction(hi, baseline, commanded, **kw) < threshold:
        return float("nan")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if delivered_fraction(mid, baseline, commanded, **kw) < threshold:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def stiffness_for_range(k_total, distributions, threshold=0.80, **kw):
    """
    The design-time question: hold total roll stiffness fixed, require that
    ANY distribution in `distributions` (percent front) can be reached to
    `threshold`, and return the stiffness that satisfies the worst pair.

    This is the honest way to set a target before the car exists, because at
    design time you do not know where balance will land -- you size the
    chassis for the range you want to keep open.
    """
    pairs = [(k_total * d / 100.0, k_total * (1.0 - d / 100.0)) for d in distributions]
    worst = 0.0
    for i, base in enumerate(pairs):
        for cmd in pairs[i + 1:]:
            worst = max(worst, stiffness_for_criterion(base, cmd, threshold, **kw))
    return worst


# ---------------------------------------------------------------------------
# Riley & George series chain (SAE 2002-01-3300)
# ---------------------------------------------------------------------------

def series_stiffness(*stiffnesses):
    """1/K_total = sum(1/K_i). Springs in series: the softest link dominates."""
    return 1.0 / sum(1.0 / k for k in stiffnesses)


def linear_to_torsional(k_linear_n_mm, radius_mm):
    """K_T = K_L * L^2, small angle. N/mm and mm in, N*m/deg out."""
    return k_linear_n_mm * radius_mm ** 2 * DEG / 1000.0


# ---------------------------------------------------------------------------
# Installation stiffness — Riley & George's chain, applied to the roll model
# ---------------------------------------------------------------------------
#
# THE TWO COMPLIANCES FAIL DIFFERENTLY, and that is the whole reason to
# separate them. Both are "the chassis is not stiff enough", but they cost
# you tuning authority by different mechanisms and are found by different
# tests.
#
#   FRAME torsional stiffness sits BETWEEN the axles. It only costs you
#   anything when you command a distribution the mass split does not already
#   provide -- when M_f/K_f != M_r/K_r. Command nothing and a floppy frame is
#   free. This is why CFR26, with no ARB and its distribution sitting on its
#   mass split, is nearly insensitive to it.
#
#   INSTALLATION stiffness sits at EACH CORNER, in series with that corner's
#   wheel rate. It costs you on every corner, in every condition, whether or
#   not you commanded anything. Worse, it is downstream of the ARB: stiffen
#   the bar and you are pushing a stiffer spring through a fixed soft link,
#   so DELIVERED axle roll stiffness asymptotes to the installation stiffness
#   no matter how big the bar gets. That is Poole's "the soft elements
#   dominate all the motion and suspension adjustments have no effect", and
#   it is a saturation, not a gradual loss.
#
# So a frame number alone cannot tell you whether the car is tunable. A car
# can pass on torsional stiffness and still be untunable on installation
# stiffness -- Poole's own student car had a rocker mount about as soft as
# the tyre and ~400 N*m/deg as a result.
#
# THE SIMPLIFICATION, stated plainly because it matters: installation
# compliance is modelled as a single roll-mode spring in series with the
# axle's total roll stiffness (road springs AND anti-roll bar). In reality
# the ARB often has its own load path to the chassis, sharing only part of
# the rocker compliance, so the true saturation is somewhere between this
# and none. Resolving it needs the actual mounting geometry, not this model.
# This form is the conservative end and the right one for setting a target.

def install_roll_stiffness(k_install_n_mm, track_mm):
    """
    Corner installation stiffness (N/mm, referred to the WHEEL) expressed as
    an axle roll stiffness, N*m/deg. Same geometry as a wheel rate: two
    springs at half-track each.
    """
    if not np.isfinite(k_install_n_mm):
        return np.inf
    return 0.5 * k_install_n_mm * track_mm ** 2 * DEG / 1000.0


def delivered_axle_stiffness(wheel_rate_n_mm, track_mm, arb_nm_deg=0.0,
                             k_install_n_mm=np.inf):
    """
    Axle roll stiffness the TYRES actually see, N*m/deg.

    Springs and ARB act in parallel (both resist roll); installation
    compliance is in series with their sum, and caps it.
    """
    commanded = axle_roll_stiffness(wheel_rate_n_mm, track_mm, arb_nm_deg)
    k_inst = install_roll_stiffness(k_install_n_mm, track_mm)
    if not np.isfinite(k_inst):
        return commanded
    return series_stiffness(commanded, k_inst)


def cfr26_delivered(arb_front=0.0, arb_rear=0.0, k_install_n_mm=np.inf):
    """CFR26's two delivered axle roll stiffnesses, including installation."""
    return (
        delivered_axle_stiffness(cc.WHEEL_RATE_FRONT_N_MM, cc.FRONT_TRACK_MM,
                                 arb_front, k_install_n_mm),
        delivered_axle_stiffness(cc.WHEEL_RATE_REAR_N_MM, cc.REAR_TRACK_MM,
                                 arb_rear, k_install_n_mm),
    )


def spindle_to_spindle(k_frame, k_install_front, k_install_rear):
    """
    What a twist test measures, N*m/deg — Riley & George's series chain
    (SAE 2002-01-3300), with the suspension locked out so the road springs
    and tyres drop out of the chain and only structure remains.

    This is the bridge between the model and the rig: it is the number to
    predict BEFORE the test and to compare the test against afterwards.
    Installation stiffnesses are roll-mode (N*m/deg), i.e. already through
    install_roll_stiffness().
    """
    return series_stiffness(k_frame, k_install_front, k_install_rear)


def infer_installation(measured_s2s, k_frame):
    """
    Back the COMBINED installation stiffness out of a twist test, N*m/deg.

    Given a measured spindle-to-spindle number and a frame stiffness from
    FEA, whatever is missing is installation (plus any manufacturing
    shortfall in the frame -- the test cannot separate those two, which is
    exactly why Velie folds a 10-20% factor in rather than pretending it
    can). Returns inf if the measurement meets or beats the frame number,
    which means either the FEA is conservative or the test is wrong.
    """
    if measured_s2s >= k_frame:
        return np.inf
    return 1.0 / (1.0 / measured_s2s - 1.0 / k_frame)


def split_budget(target_s2s, n_elements=2):
    """
    Riley & George's structural-efficiency result: for elements of similar
    stiffness-to-weight, the lightest way to hit a series target is to make
    them EQUAL. n elements in series each need n * target.

    Returns the per-element stiffness. With n_elements=2 (frame vs. the
    combined installation path) this is just 2 * target.
    """
    return n_elements * target_s2s


def reachable_distribution(k_install_n_mm, arb_max_nm_deg, on="front"):
    """
    Percent-front roll stiffness distribution reachable with an ARB of rate
    `arb_max_nm_deg` fitted to one axle, given installation stiffness.

    This is the number that saturates. It is what the ARB is FOR, and a soft
    installation quietly takes it away.
    """
    arb_f = arb_max_nm_deg if on == "front" else 0.0
    arb_r = arb_max_nm_deg if on == "rear" else 0.0
    kf, kr = cfr26_delivered(arb_f, arb_r, k_install_n_mm)
    return 100.0 * kf / (kf + kr)



# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

# Unvalidated FEA estimate for the as-built CFR26 frame (Bianca, 2026-08-30).
# The design sheet's D93 = 1700 N*m/deg is an ASSUMPTION, not a measurement or
# an analysis result, and is deliberately not used here.
CFR26_FEA_NM_DEG = 1100.0



def report_installation():
    """Where the tuning authority actually goes: frame vs. installation."""
    kf, kr = ts_kf, ts_kr = cfr26_axle_stiffness()
    k_total = kf + kr

    print("\n" + "=" * 72)
    print("SPLITTING THE BUDGET: FRAME vs INSTALLATION STIFFNESS")
    print("=" * 72)
    print("  Installation stiffness is quoted at the WHEEL, N/mm. For scale,")
    print(f"  CFR26's wheel rates are {cc.WHEEL_RATE_FRONT_N_MM:.1f} / "
          f"{cc.WHEEL_RATE_REAR_N_MM:.1f} N/mm, so a 200 N/mm installation")
    print("  is about 7x the spring it sits behind.\n")

    print("  (a) INSTALLATION ALONE, no ARB commanded — it still costs you.")
    print(f"      {'k_inst N/mm':>12} | {'delivered K_f/K_r':>19} | {'total':>8} | {'lost':>6}")
    print("      " + "-" * 54)
    for ki in [50, 100, 200, 400, 800, np.inf]:
        a, b = cfr26_delivered(k_install_n_mm=ki)
        lab = "rigid" if not np.isfinite(ki) else f"{ki:.0f}"
        print(f"      {lab:>12} | {a:>8.1f} / {b:<8.1f} | {a+b:>8.1f} | "
              f"{100*(1-(a+b)/k_total):>5.1f}%")

    print("\n  (b) ARB AUTHORITY SATURATES. A front ARB is fitted and swept;")
    print("      the question is what roll stiffness distribution it can")
    print("      actually reach through a given installation stiffness.")
    arbs = [0, 100, 200, 400, 800]
    print(f"      {'k_inst N/mm':>12} | " + " | ".join(f"ARB{a:>4}" for a in arbs) + " |  ceiling")
    print("      " + "-" * 62)
    for ki in [50, 100, 200, 400, 800, np.inf]:
        row = [f"{reachable_distribution(ki, a):6.1f}%" for a in arbs]
        ceiling = reachable_distribution(ki, 1e7)
        lab = "rigid" if not np.isfinite(ki) else f"{ki:.0f}"
        print(f"      {lab:>12} | " + " | ".join(row) + f" |  {ceiling:5.1f}%")
    print("\n      The ceiling column is an INFINITE bar. A 100 N/mm installation")
    print("      caps distribution at that ceiling no matter what bar you fit —")
    print("      the authority is gone before the bar is sized.")

    print("\n  (c) BUDGET SPLIT for a spindle-to-spindle target.")
    target = stiffness_for_range(k_total, [40.0, 60.0]) * 1.2
    roll_to_wheel = 0.5 * cc.FRONT_TRACK_MM ** 2 * DEG / 1000.0   # N*m/deg per N/mm
    print(f"      Deakin floor for 40-60% front, +20% mfg: {target:.0f} N*m/deg")
    print(f"      spindle-to-spindle. Two elements in series get you there.\n")

    per = split_budget(target, n_elements=2)
    print(f"      Riley's EQUAL SPLIT — lightest, if frame and suspension have")
    print(f"      similar stiffness-to-weight:")
    print(f"        frame                            {per:>6.0f} N*m/deg")
    print(f"        installation, both axles         {per:>6.0f} N*m/deg")
    print(f"        = spindle-to-spindle             "
          f"{series_stiffness(per, per):>6.0f} N*m/deg  (target {target:.0f})")
    print(f"      Splitting that installation figure equally front/rear puts")
    print(f"      each axle at {2*per:.0f} N*m/deg = {2*per/roll_to_wheel:.0f} N/mm at the wheel.\n")

    print(f"      BUT THE FRAME IS NOT A FREE VARIABLE — the FEA says")
    print(f"      {CFR26_FEA_NM_DEG:.0f} N*m/deg, well under the {per:.0f} an equal split wants.")
    need = infer_installation(target, CFR26_FEA_NM_DEG)
    if np.isfinite(need):
        print(f"      Holding the frame at {CFR26_FEA_NM_DEG:.0f}, installation must reach")
        print(f"        {need:>6.0f} N*m/deg combined, i.e. {2*need:.0f} per axle")
        print(f"        = {2*need/roll_to_wheel:.0f} N/mm at the wheel, ~"
              f"{2*need/roll_to_wheel/cc.WHEEL_RATE_FRONT_N_MM:.0f}x the wheel rate.")
        print(f"      That is the binding constraint, and it is a demanding number.")
        print(f"      A stiffer frame buys it down fast: at {1.5*CFR26_FEA_NM_DEG:.0f} N*m/deg frame,")
        need2 = infer_installation(target, 1.5 * CFR26_FEA_NM_DEG)
        print(f"      installation only needs {2*need2/roll_to_wheel:.0f} N/mm.")
    else:
        print(f"      The frame alone already clears the target.")

    print("\n  (d) WHAT A TWIST TEST WOULD TELL YOU, given the 1100 FEA frame.")
    print(f"      {'measured s2s':>13} | {'implied installation':>21}")
    print("      " + "-" * 38)
    for meas in [500, 700, 900, 1000, 1050]:
        imp = infer_installation(meas, CFR26_FEA_NM_DEG)
        s = "beats FEA" if not np.isfinite(imp) else f"{imp:.0f} N*m/deg"
        print(f"      {meas:>10.0f}    | {s:>21}")
    print("      A test landing well under 1100 is not a bad frame -- it is")
    print("      the installation path showing up. The test cannot separate")
    print("      that from a manufacturing shortfall in the frame itself,")
    print("      which is why Velie folds in 10-20% rather than pretending it can.")

    print("\n  (e) CFR26 SPECIFICALLY: installation stiffness CANNOT be backed")
    print("      out of the roll data. Compliance can only ever ADD roll, and")
    print("      the measured roll gradient is already 1.167x BELOW prediction.")
    print("      So the telemetry bounds total compliance from above and says")
    print("      nothing about its size. It needs a twist test.")


def main():
    kf, kr = cfr26_axle_stiffness()
    k_total = kf + kr
    dist = 100.0 * kf / k_total

    print("=" * 72)
    print("CFR26 AS BUILT (no ARB)")
    print("=" * 72)
    print(f"  wheel rates            {cc.WHEEL_RATE_FRONT_N_MM:6.2f} / {cc.WHEEL_RATE_REAR_N_MM:5.2f} N/mm")
    print(f"  axle roll stiffness    {kf:6.1f} / {kr:5.1f} N*m/deg")
    print(f"  TOTAL roll stiffness   {k_total:6.1f} N*m/deg   (case5 cross-check: 749)")
    print(f"  roll stiffness distr   {dist:6.1f} % front")
    print(f"  static mass distr      {100*FRONT_MASS_FRACTION:6.1f} % front")
    print(f"  -> mismatch of only {abs(dist - 100*FRONT_MASS_FRACTION):.1f} points: the chassis is")
    print(f"     asked to carry almost no torque.\n")

    rigid = lltd(kf, kr, RIGID)
    floppy = lltd(kf, kr, 1e-9)
    print(f"  LLTD, rigid chassis    {rigid:6.2f} % front")
    print(f"  LLTD, K_ch -> 0        {floppy:6.2f} % front")
    print(f"  TOTAL authority at stake, even at zero stiffness: {floppy - rigid:.2f} points")
    print(f"  at the {CFR26_FEA_NM_DEG:.0f} N*m/deg FEA estimate: "
          f"{lltd(kf, kr, CFR26_FEA_NM_DEG) - rigid:.2f} points\n")

    print("  Invariance check -- LLTD vs the disputed roll moment scale:")
    for scale, label in [(785.2, "sheet 785 N*m/g"), (673.0, "measured 673 N*m/g")]:
        print(f"    {label:>22}:  LLTD @ {CFR26_FEA_NM_DEG:.0f} = "
              f"{lltd(kf, kr, CFR26_FEA_NM_DEG, roll_moment=scale):.4f} % front")
    print("    identical -> the open 1.167x gap does not touch the target.\n")

    print("=" * 72)
    print("WHAT THE CFR26 TARGET SHOULD HAVE BEEN")
    print("=" * 72)
    print("  Total roll stiffness is held at the as-built 749 N*m/deg; the")
    print("  question is how much DISTRIBUTION range the chassis must support.")
    print(f"\n  {'range kept open':>22} | {'K_ch for 80%':>12} | {'+20% mfg':>9}")
    print("  " + "-" * 50)
    for lo_d, hi_d in [(45, 55), (42.5, 57.5), (40, 60), (35, 65), (30, 70)]:
        k = stiffness_for_range(k_total, [lo_d, hi_d])
        print(f"  {f'{lo_d:g}-{hi_d:g} % front':>22} | {k:>9.0f} N*m/deg | {k*1.2:>6.0f}")
    print("\n  (+20% is Velie's manufacturing-error factor: MRacing measure a")
    print("   10-20% shortfall of built vs designed on spindle-to-spindle tests.)")

    print("\n" + "=" * 72)
    print("DELIVERED FRACTION vs CHASSIS STIFFNESS  (40-60 % front range)")
    print("=" * 72)
    base = (k_total * 0.40, k_total * 0.60)
    cmd = (k_total * 0.60, k_total * 0.40)
    print(f"  {'K_ch N*m/deg':>13} | {'delivered':>10}")
    print("  " + "-" * 27)
    for k_ch in [200, 400, 600, 800, 1000, 1100, 1500, 2000, 3000, 5000]:
        f = delivered_fraction(k_ch, base, cmd)
        mark = "  <-- 80%" if f >= 0.80 and delivered_fraction(k_ch - 1, base, cmd) < 0.80 else ""
        note = "   [FEA est]" if k_ch == CFR26_FEA_NM_DEG else ""
        print(f"  {k_ch:>13.0f} | {100*f:>9.1f}%{mark}{note}")

    report_installation()


if __name__ == "__main__":
    main()
