# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pytest"]
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


def test_cfr26_matches_case5():
    """case5_gradients derives 749 N*m/deg from the springs independently."""
    kf, kr = ts.cfr26_axle_stiffness()
    assert kf + kr == pytest.approx(749.0, abs=1.0)


def test_arb_adds_in_parallel():
    kf_bare, _ = ts.cfr26_axle_stiffness()
    kf_arb, _ = ts.cfr26_axle_stiffness(arb_front=100.0)
    assert kf_arb == pytest.approx(kf_bare + 100.0)


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
    assert 600.0 < k < 900.0


def test_series_chain_is_dominated_by_the_softest_link():
    assert ts.series_stiffness(1e9, 500.0) == pytest.approx(500.0, rel=1e-6)
    assert ts.series_stiffness(1000.0, 1000.0) == pytest.approx(500.0)


def test_linear_to_torsional_matches_hand_calc():
    """K_T = K_L * L^2, with the deg/rad and mm/m conversions."""
    k_wheel, half_track = cc.WHEEL_RATE_FRONT_N_MM, cc.FRONT_TRACK_MM / 2.0
    got = ts.linear_to_torsional(k_wheel, half_track)
    want = k_wheel * half_track ** 2 * (np.pi / 180.0) / 1000.0
    assert got == pytest.approx(want)
    # an axle is two springs at half-track: K_roll = 2 * K_L * (t/2)^2
    kf, _ = ts.cfr26_axle_stiffness()
    assert 2 * got == pytest.approx(kf, rel=1e-9)
