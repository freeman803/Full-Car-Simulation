# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "pytest"]
# ///
"""
test_torsional_stiffness.py — physics checks on the Deakin model.

Deliberately NOT part of test_regression.py's pinning harness: that one
drives the case scripts and needs comp2026_data, whereas this model is pure
and needs no telemetry at all. These are correctness properties (limits,
invariances, monotonicity), not pinned values, so they should hold for CFR27
inputs too -- only test_cfr26_matches_case5 is car-specific.

    uv run --with pytest pytest test_torsional_stiffness.py -q
"""

import numpy as np
import pytest

import case_common as cc
import torsional_stiffness as ts


def test_suspension_referenced_matches_case5():
    """case5_gradients derives 749 N*m/deg from the springs alone, no tyre."""
    kf, kr = ts.cfr26_axle_stiffness_susp()
    assert kf + kr == pytest.approx(749.0, abs=1.0)


def test_ground_referenced_matches_the_design_sheet():
    """
    The load-transfer model runs ground-referenced (ride rates), which is what
    the CFR26 design sheet reports. Getting this wrong inflates every axle
    stiffness by the GROUND_MULT factors, ~23-27%.
    """
    kf, kr = ts.cfr26_axle_stiffness()
    assert kf == pytest.approx(295.0, abs=0.5)
    assert kr == pytest.approx(306.1, abs=0.5)
    assert 100 * kf / (kf + kr) == pytest.approx(49.1, abs=0.2)


def test_the_two_references_differ_by_the_ground_multipliers():
    (sf, sr), (gf, gr) = ts.cfr26_axle_stiffness_susp(), ts.cfr26_axle_stiffness()
    assert sf / gf == pytest.approx(cc.GROUND_MULT_ROLL_FRONT, rel=1e-9)
    assert sr / gr == pytest.approx(cc.GROUND_MULT_ROLL_REAR, rel=1e-9)


def test_arb_adds_in_parallel_at_the_spring():
    """The ARB sums with the road springs, upstream of the tyre."""
    bare = ts.spring_roll_stiffness(cc.WHEEL_RATE_FRONT_N_MM, cc.FRONT_TRACK_MM)
    with_bar = ts.spring_roll_stiffness(cc.WHEEL_RATE_FRONT_N_MM, cc.FRONT_TRACK_MM, 100.0)
    assert with_bar == pytest.approx(bare + 100.0)
    # but downstream of the tyre it cannot add linearly
    axle = ts.cfr26_axle_stiffness(arb_front=100.0)[0]
    assert axle < ts.cfr26_axle_stiffness()[0] + 100.0


def test_rigid_limit_splits_by_roll_stiffness():
    """K_ch -> inf: both ends roll together, so load transfer follows K only."""
    kf, kr = 400.0, 400.0
    phi_f, phi_r = ts.solve_roll_angles(kf, kr, ts.RIGID, 600.0, 200.0)
    assert phi_f == pytest.approx(phi_r, rel=1e-6)


def test_floppy_limit_decouples_the_axles():
    """K_ch -> 0: each axle rolls on its own moment over its own stiffness."""
    kf, kr, m_f, m_r = 400.0, 300.0, 600.0, 200.0
    phi_f, phi_r = ts.solve_roll_angles(kf, kr, 1e-9, m_f, m_r)
    assert phi_f == pytest.approx(m_f / kf, rel=1e-5)
    assert phi_r == pytest.approx(m_r / kr, rel=1e-5)


def test_lltd_invariant_to_roll_moment_scale():
    """
    The 1.167x design-vs-measured gap lives in the absolute roll moment.
    The model is linear, so it cancels out of the LLTD ratio entirely --
    this is why that open question does not block setting a target.
    """
    kf, kr = ts.cfr26_axle_stiffness()
    a = ts.lltd(kf, kr, 1100.0, roll_moment=785.2)
    b = ts.lltd(kf, kr, 1100.0, roll_moment=673.0)
    assert a == pytest.approx(b, rel=1e-12)


def test_matched_distribution_needs_no_chassis():
    """
    When roll stiffness distribution matches the mass split, M_f/K_f = M_r/K_r,
    the chassis carries zero torque and its stiffness is irrelevant. This is
    the mechanism behind CFR26's near-insensitivity.
    """
    frac = 0.5
    kf = kr = 375.0
    soft = ts.lltd(kf, kr, 1.0, front_mass_fraction=frac)
    stiff = ts.lltd(kf, kr, ts.RIGID, front_mass_fraction=frac)
    assert soft == pytest.approx(stiff, rel=1e-9)


def test_delivered_fraction_is_monotonic_and_approaches_one():
    kt = 749.4
    base, cmd = (kt * 0.40, kt * 0.60), (kt * 0.60, kt * 0.40)
    ks = [100, 300, 700, 1500, 4000, 20000]
    fracs = [ts.delivered_fraction(k, base, cmd) for k in ks]
    assert all(b > a for a, b in zip(fracs, fracs[1:]))
    assert fracs[-1] == pytest.approx(1.0, abs=0.02)
    assert ts.delivered_fraction(ts.RIGID, base, cmd) == pytest.approx(1.0, rel=1e-6)


def test_stiffness_for_criterion_actually_hits_the_threshold():
    kt = 749.4
    base, cmd = (kt * 0.40, kt * 0.60), (kt * 0.60, kt * 0.40)
    k = ts.stiffness_for_criterion(base, cmd, threshold=0.80)
    assert ts.delivered_fraction(k, base, cmd) == pytest.approx(0.80, abs=1e-4)


def test_cfr26_target_lands_near_total_roll_stiffness():
    """Deakin's floor for CFR26: order of 1x total roll stiffness, not 4x."""
    kf, kr = ts.cfr26_axle_stiffness()
    k = ts.stiffness_for_range(kf + kr, [40.0, 60.0])
    assert 0.85 * (kf + kr) < k < 1.05 * (kf + kr)


def test_series_chain_is_dominated_by_the_softest_link():
    assert ts.series_stiffness(1e9, 500.0) == pytest.approx(500.0, rel=1e-6)
    assert ts.series_stiffness(1000.0, 1000.0) == pytest.approx(500.0)


def test_linear_to_torsional_matches_hand_calc():
    """K_T = K_L * L^2, with the deg/rad and mm/m conversions."""
    k_wheel, half_track = cc.WHEEL_RATE_FRONT_N_MM, cc.FRONT_TRACK_MM / 2.0
    got = ts.linear_to_torsional(k_wheel, half_track)
    want = k_wheel * half_track ** 2 * (np.pi / 180.0) / 1000.0
    assert got == pytest.approx(want)
    # an axle is two springs at half-track: K_roll = 2 * K_L * (t/2)^2.
    # Compare against the SUSPENSION-referenced figure -- no tyre in either.
    sf, _ = ts.cfr26_axle_stiffness_susp()
    assert 2 * got == pytest.approx(sf, rel=1e-9)


# --- installation stiffness / Riley & George chain ---------------------------

def test_rigid_installation_is_a_no_op():
    for kw, t in [(cc.WHEEL_RATE_FRONT_N_MM, cc.FRONT_TRACK_MM),
                  (cc.WHEEL_RATE_REAR_N_MM, cc.REAR_TRACK_MM)]:
        assert ts.delivered_axle_stiffness(kw, t, 0.0, np.inf) == pytest.approx(
            ts.axle_roll_stiffness(kw, t, 0.0))


def test_installation_always_costs_even_with_nothing_commanded():
    """
    The asymmetry against frame stiffness: a soft frame is free when you
    command nothing, a soft installation never is.
    """
    totals = []
    for ki in [50, 100, 200, 400, 800, np.inf]:
        a, b = ts.cfr26_delivered(k_install_n_mm=ki)
        totals.append(a + b)
    assert all(y > x for x, y in zip(totals, totals[1:]))     # monotonic
    assert totals[0] < 0.7 * totals[-1]                        # 50 N/mm costs >30%


def test_arb_authority_saturates_at_the_installation_stiffness():
    """An infinite bar cannot reach 100% front through a finite installation."""
    for ki in [50, 100, 200]:
        ceiling = ts.reachable_distribution(ki, 1e7)
        assert ceiling < 99.0
    # and a softer installation caps it lower
    assert ts.reachable_distribution(50, 1e7) < ts.reachable_distribution(400, 1e7)


def test_the_tyre_itself_caps_arb_authority():
    """
    Even with perfectly rigid mounts the tyre is still a series element, so an
    infinite bar cannot reach 100% front. The tyre is the last soft link.
    """
    ceiling = ts.reachable_distribution(np.inf, 1e9)
    tyre_f = ts.tyre_roll_stiffness(cc.FRONT_TRACK_MM)
    _, kr = ts.cfr26_axle_stiffness()
    assert ceiling == pytest.approx(100 * tyre_f / (tyre_f + kr), abs=0.2)
    assert ceiling < 90.0


def test_infer_installation_round_trips_spindle_to_spindle():
    frame, ki_f, ki_r = 1100.0, 3000.0, 4000.0
    meas = ts.spindle_to_spindle(frame, ki_f, ki_r)
    assert meas < min(frame, ki_f, ki_r)                       # series is softest
    assert ts.infer_installation(meas, frame) == pytest.approx(
        ts.series_stiffness(ki_f, ki_r))


def test_infer_installation_flags_a_measurement_that_beats_the_frame():
    assert ts.infer_installation(1200.0, 1100.0) == np.inf


def test_split_budget_hits_the_target():
    target = 863.0
    per = ts.split_budget(target, n_elements=2)
    assert ts.series_stiffness(per, per) == pytest.approx(target)
    per3 = ts.split_budget(target, n_elements=3)
    assert ts.series_stiffness(per3, per3, per3) == pytest.approx(target)


if __name__ == "__main__":
    # So `uv run test_torsional_stiffness.py` works like the other scripts here,
    # rather than importing the module and silently doing nothing.
    raise SystemExit(pytest.main([__file__, "-q"]))


# --- spring box -------------------------------------------------------------

def test_spring_box_reproduces_the_as_run_setup():
    """225/200 out of the box must equal the as-built axle stiffnesses."""
    setups = ts.spring_box_setups((225.0,), (200.0,))
    assert len(setups) == 1
    kf, kr, _ = setups[0]
    assert (kf, kr) == pytest.approx(ts.cfr26_axle_stiffness())


def test_spring_box_enumerates_every_combination():
    assert len(ts.spring_box_setups((200, 225, 250), (175, 200, 225))) == 9
    assert len(ts.spring_box_setups((225,), (200,), arb_front=(0.0, 100.0))) == 2


def test_degenerate_pairs_are_filtered_out():
    """
    Deakin's criterion is a FRACTION, so it blows up as the commanded change
    goes to zero. Without the filter the answer is set by the most pointless
    swap in the box -- 1233 N*m/deg off a 0.17-point change.
    """
    setups = ts.spring_box_setups((200, 225, 250), (175, 200, 225))
    unfiltered, _, _ = ts.stiffness_for_setups(setups, min_change_pts=0.0)
    filtered, _, change = ts.stiffness_for_setups(setups)
    assert unfiltered > 1200
    assert filtered < 800
    assert change >= ts.MIN_MEANINGFUL_LLTD_CHANGE_PTS


def test_a_stiffer_box_demands_a_stiffer_chassis():
    """
    Required stiffness scales with total roll stiffness, so owning stiffer
    springs raises the target -- the reason to size off the box, not the
    as-run setup.
    """
    soft, _, _ = ts.stiffness_for_setups(ts.spring_box_setups((175, 200), (150, 175)))
    stiff, _, _ = ts.stiffness_for_setups(ts.spring_box_setups((275, 300), (250, 275)))
    assert stiff > soft


def test_criterion_is_the_dominant_lever():
    """
    Deakin's 80% is the weakest defensible criterion, and the gap between it
    and 90% is most of the gap to what teams actually build. If this stops
    being true the headline's whole argument needs revisiting.
    """
    kf, kr = ts.cfr26_axle_stiffness()
    kt = kf + kr
    k80 = ts.stiffness_for_range(kt, [40.0, 60.0], threshold=0.80)
    k90 = ts.stiffness_for_range(kt, [40.0, 60.0], threshold=0.90)
    assert k90 > 2 * k80
    assert 1200 < k90 * 1.2 < 1800          # lands in the band teams build to


def test_requirement_scales_with_total_roll_stiffness():
    """Why a car with an ARB needs a stiffer frame than CFR26 does."""
    ratios = []
    for tot in (601.0, 800.0, 1000.0, 1200.0):
        ratios.append(ts.stiffness_for_range(tot, [40.0, 60.0]) / tot)
    assert max(ratios) - min(ratios) < 0.01   # near-constant multiple


def test_motion_share_round_trips():
    for pct in (2.5, 5.0, 10.0, 25.0):
        k = ts.stiffness_for_motion_share(pct)
        assert ts.chassis_motion_share(k) == pytest.approx(pct)


def test_pooles_rule_is_self_inconsistent():
    """
    "Allow ~5% of motion through the chassis" and "roughly 3:1" are not the
    same rule. 5% implies 19:1; 3:1 implies 25% of motion. Documented so the
    discrepancy is not rediscovered as a bug in this model.
    """
    kf, kr = ts.cfr26_axle_stiffness()
    # "the suspension" in a SERIES comparison is the series-equivalent, not
    # the parallel roll stiffness -- they differ by ~4x on this car.
    k_series = ts.series_stiffness(kf, kr)          # 150.2
    k_parallel = kf + kr                            # 601.1
    assert k_parallel / k_series == pytest.approx(4.0, rel=0.02)
    assert ts.stiffness_for_motion_share(5.0) / k_series == pytest.approx(19.0, rel=0.02)
    assert ts.chassis_motion_share(3.0 * k_series) == pytest.approx(25.0, rel=0.02)
    # so his "3:1" reads as 450 against the series value but 1803 against the
    # parallel one, and only the latter matches the 1200-1500 he also quoted
    assert 3.0 * k_series == pytest.approx(450, abs=10)
    assert 3.0 * k_parallel == pytest.approx(1803, abs=10)


def test_full_delivery_is_unreachable():
    """100% is the rigid-chassis asymptote, so it must report inf, not nan."""
    kf, kr = ts.cfr26_axle_stiffness()
    k = ts.stiffness_for_range(kf + kr, [40.0, 60.0], threshold=1.0)
    assert k == np.inf
    assert np.isfinite(ts.stiffness_for_range(kf + kr, [40.0, 60.0], threshold=0.99))


# --- CFR27 scaffold ---------------------------------------------------------

def test_cfr27_scaffold_reports_missing_parameters():
    import cfr27_target as c27
    assert len(c27.missing()) == 10          # nothing filled in yet
    assert c27.check() is False


def test_cfr27_scaffold_reproduces_cfr26_when_fed_cfr26():
    """
    Smoke test for the plumbing: feed the CFR27 script CFR26's parameters and
    it must land on CFR26's axle stiffnesses. Catches a parameter collected in
    P but never actually passed through to the model -- which is exactly what
    happened to tyre rate on the first cut.
    """
    import cfr27_target as c27
    saved = dict(c27.P)
    try:
        c27.P.update({
            "spring_rates_front_lbf_in": (225.0,),
            "spring_rates_rear_lbf_in": (200.0,),
            "motion_ratio_front": cc.MOTION_RATIO_FRONT,
            "motion_ratio_rear": cc.MOTION_RATIO_REAR,
            "track_front_mm": cc.FRONT_TRACK_MM,
            "track_rear_mm": cc.REAR_TRACK_MM,
            "tyre_rate_lbf_in": cc.TYRE_RATE_LBF_IN,
            "arb_settings_front_nm_deg": (0.0,),
            "arb_settings_rear_nm_deg": (0.0,),
            "front_mass_fraction": 0.507,
        })
        assert c27.missing() == []
        (kf, kr, _), = c27.setups()
        assert (kf, kr) == pytest.approx(ts.cfr26_axle_stiffness())
    finally:
        c27.P.clear(); c27.P.update(saved)


def test_tyre_rate_is_actually_used():
    """A softer tyre must lower the axle roll stiffness."""
    soft = ts.axle_from_spring(225.0, 1.188, 1219.2, tyre_rate_n_mm=60.0)
    stiff = ts.axle_from_spring(225.0, 1.188, 1219.2, tyre_rate_n_mm=300.0)
    assert soft < stiff


def test_build_margin_is_a_parameter_not_a_hardcode():
    """--margin must actually move the answer; it was hardcoded as 1.2 once."""
    kf, kr = ts.cfr26_axle_stiffness()
    floor = ts.stiffness_for_range(kf + kr, [40.0, 60.0], threshold=0.90)
    assert ts.BUILD_MARGIN == 1.20
    assert floor * 1.05 < floor * ts.BUILD_MARGIN
    # the frame falls short of the 90% target at every margin in the range
    for m in (1.05, 1.10, 1.20):
        assert ts.CFR26_FEA_NM_DEG < floor * m
