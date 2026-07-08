"""
steering.py — Steering kinematics: Ackermann, rack steer, toe curve.

NOTE: Steering here uses a tie-rod-vector approximation for the steer/toe angle
(the same first-order model the geometry module used to use). It is independent
of the spindle-axis toe used by the suspension travel sweep. Making the rack
model spindle-consistent (steer as a true rotation of the upright about the
kingpin axis) is a planned future refinement.
"""

import numpy as np
import pandas as pd

from .geometry import angle_between


def _tierod_steer_angle(
    tie_rod_inboard: np.ndarray,
    tie_rod_outboard: np.ndarray,
) -> float:
    """
    Steer/toe angle (deg) approximated from the tie-rod vector in the XY plane.
    Positive = toe-in direction for the left wheel.
    """
    tr_vec  = tie_rod_outboard - tie_rod_inboard
    tr_xy   = np.array([tr_vec[0], tr_vec[1], 0.0])
    angle   = angle_between(tr_xy, np.array([0.0, 1.0, 0.0]))
    sign    = -float(np.sign(tr_vec[0]))
    return sign * angle


def ackermann_ideal(
    steer_angle_outer_deg: float,
    wheelbase: float,
    track_width: float,
) -> float:
    """
    Ideal inner wheel steer angle for a given outer steer angle (Ackermann condition).

    Uses: cot(δ_outer) - cot(δ_inner) = track / wheelbase

    Parameters
    ----------
    steer_angle_outer_deg : float
        Outer wheel steer angle (degrees).
    wheelbase : float
        Car wheelbase (mm).
    track_width : float
        Front track width, centre-to-centre (mm).

    Returns
    -------
    float : ideal inner steer angle (degrees).
    """
    if abs(steer_angle_outer_deg) < 0.01:
        return 0.0
    outer_rad = np.radians(steer_angle_outer_deg)
    cot_outer = np.cos(outer_rad) / np.sin(outer_rad)
    cot_inner = cot_outer - track_width / wheelbase
    if abs(cot_inner) < 1e-10:
        return 90.0
    inner_rad = np.arctan(1.0 / cot_inner)
    return float(np.degrees(inner_rad))


def rack_steer_angle(
    rack_travel_mm: float,
    hp: dict[str, np.ndarray],
) -> float:
    """
    Compute wheel steer angle for a given rack lateral displacement.

    Moves the tie rod inboard (rack) end laterally and recomputes toe.

    Parameters
    ----------
    rack_travel_mm : float
        Rack displacement in mm. Positive = rack moves left.
    hp : dict
        Hardpoint dictionary.

    Returns
    -------
    float : steer angle at the wheel (degrees). Positive = toe-in direction.
    """
    new_tri = hp["tie_rod_inboard"].copy()
    new_tri[1] += rack_travel_mm
    return _tierod_steer_angle(new_tri, hp["tie_rod_outboard"])


def ackermann_sweep(
    hp: dict[str, np.ndarray],
    wheelbase: float,
    track_width: float,
    rack_range_mm: float = 50.0,
    n_points: int = 201,
) -> pd.DataFrame:
    """
    Sweep rack travel and compute Ackermann geometry across the steer range.

    Parameters
    ----------
    hp : dict
        Hardpoint dictionary.
    wheelbase : float
        Car wheelbase (mm).
    track_width : float
        Front track centre-to-centre (mm).
    rack_range_mm : float
        Full rack travel ± this value (mm).
    n_points : int
        Number of evaluation points.

    Returns
    -------
    pd.DataFrame with columns:
        rack_mm, steer_left_deg, steer_right_deg,
        ackermann_ideal_deg, ackermann_pct
    """
    rack_travels = np.linspace(-rack_range_mm, rack_range_mm, n_points)

    steer_left  = np.array([rack_steer_angle(rt, hp) for rt in rack_travels])
    # Right wheel sees the opposite rack movement (mirrored corner)
    steer_right = np.array([-rack_steer_angle(-rt, hp) for rt in rack_travels])

    # Ideal inner angle when left wheel is inner (left turn = positive rack)
    ackermann_inner = np.array([
        ackermann_ideal(abs(a), wheelbase, track_width) * np.sign(a)
        for a in steer_left
    ])

    # Ackermann percentage
    # 0% = parallel steer, 100% = perfect Ackermann
    eps = 1e-6
    ack_pct = np.where(
        np.abs(ackermann_inner - steer_left) > eps,
        (steer_right - steer_left) / (ackermann_inner - steer_left) * 100.0,
        100.0,
    )

    return pd.DataFrame({
        "rack_mm":            rack_travels,
        "steer_left_deg":     steer_left,
        "steer_right_deg":    steer_right,
        "ackermann_ideal_deg": ackermann_inner,
        "ackermann_pct":      ack_pct,
    })