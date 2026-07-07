"""
geometry.py — Core kinematic geometry functions.

All functions are pure (no side effects, no global state).
Input / output in mm and degrees throughout.
"""

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Vector helpers
# ─────────────────────────────────────────────────────────────────────────────

def normalize(v: np.ndarray) -> np.ndarray:
    """Return unit vector of v. Returns v unchanged if near-zero length."""
    n = np.linalg.norm(v)
    return v / n if n > 1e-10 else v


def angle_between(a: np.ndarray, b: np.ndarray, degrees: bool = True) -> float:
    """Angle between two vectors. Returns degrees by default."""
    cos_theta = np.clip(np.dot(normalize(a), normalize(b)), -1.0, 1.0)
    angle = np.arccos(cos_theta)
    return float(np.degrees(angle)) if degrees else float(angle)


def rotation_matrix(axis: np.ndarray, angle_deg: float) -> np.ndarray:
    """Rodrigues rotation matrix: rotate around `axis` by `angle_deg` degrees."""
    axis = normalize(axis)
    a = np.radians(angle_deg)
    c, s = np.cos(a), np.sin(a)
    t = 1.0 - c
    x, y, z = axis
    return np.array([
        [t*x*x + c,   t*x*y - s*z, t*x*z + s*y],
        [t*x*y + s*z, t*y*y + c,   t*y*z - s*x],
        [t*x*z - s*y, t*y*z + s*x, t*z*z + c  ],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Suspension geometry primitives
# ─────────────────────────────────────────────────────────────────────────────

def kingpin_axis(upper_bj: np.ndarray, lower_bj: np.ndarray) -> np.ndarray:
    """Unit vector along the steering (kingpin) axis, from lower to upper BJ."""
    return normalize(upper_bj - lower_bj)


def camber_angle(upper_bj: np.ndarray, lower_bj: np.ndarray) -> float:
    """
    Camber angle in degrees.

    Defined as the angle of the kingpin axis projected onto the YZ plane,
    measured from the vertical (Z-axis).
      Negative = top of wheel tilted inboard  (desired for cornering)
      Positive = top of wheel tilted outboard
    """
    kp = upper_bj - lower_bj
    kp_yz = np.array([0.0, kp[1], kp[2]])
    angle = angle_between(kp_yz, np.array([0.0, 0.0, 1.0]))
    sign = float(np.sign(kp[1]))  # outboard tilt (positive Y) = positive camber
    return sign * angle


def caster_angle(upper_bj: np.ndarray, lower_bj: np.ndarray) -> float:
    """
    Caster angle in degrees.

    Defined as the angle of the kingpin axis projected onto the XZ plane,
    measured from the vertical.
      Positive = upper BJ tilted rearward of lower BJ (conventional positive caster)
    """
    kp = upper_bj - lower_bj
    kp_xz = np.array([kp[0], 0.0, kp[2]])
    angle = angle_between(kp_xz, np.array([0.0, 0.0, 1.0]))
    sign = -float(np.sign(kp[0]))  # rearward upper BJ (negative X) = positive caster
    return sign * angle


def kpi_angle(upper_bj: np.ndarray, lower_bj: np.ndarray) -> float:
    """
    King Pin Inclination (KPI) in degrees.

    Always positive. Inward tilt of the steering axis in the front view.
    Numerically equal to abs(camber_angle) for a symmetric suspension at zero steer.
    """
    return abs(camber_angle(upper_bj, lower_bj))


def toe_angle(
    tie_rod_inboard: np.ndarray,
    tie_rod_outboard: np.ndarray,
    wheel_center: np.ndarray,  # noqa: ARG001 — reserved for future 3D toe model
) -> float:
    """
    Static toe angle in degrees (simplified 2D XY-plane approximation).

    Positive = toe-in (front of wheel pointed inward toward centreline).
    The wheel plane direction is approximated by the tie rod vector.
    """
    tr_vec = tie_rod_outboard - tie_rod_inboard
    tr_xy = np.array([tr_vec[0], tr_vec[1], 0.0])
    lateral = np.array([0.0, 1.0, 0.0])
    angle = angle_between(tr_xy, lateral)
    sign = -float(np.sign(tr_vec[0]))  # rod angled forward = toe-in for left wheel
    return sign * angle


def scrub_radius(
    upper_bj: np.ndarray,
    lower_bj: np.ndarray,
    contact_patch: np.ndarray,
    wheel_center: np.ndarray = None,  # noqa: ARG001
) -> float | None:
    """
    Scrub radius in mm.

    Lateral (Y) distance at ground level between:
      - the KPI axis ground intercept
      - the tyre contact patch centreline
    Positive = intercept is inboard of contact patch (conventional positive scrub).
    Returns None if KPI axis is horizontal (degenerate case).
    """
    kp = upper_bj - lower_bj
    if abs(kp[2]) < 1e-10:
        return None
    t = -lower_bj[2] / kp[2]
    ground_intercept = lower_bj + t * kp
    return float(contact_patch[1] - ground_intercept[1])


def mechanical_trail(
    upper_bj: np.ndarray,
    lower_bj: np.ndarray,
    contact_patch: np.ndarray,
) -> float | None:
    """
    Mechanical (caster) trail in mm.

    Longitudinal (X) distance at ground level between:
      - the KPI axis ground intercept
      - the tyre contact patch
    Positive = contact patch is behind the intercept (self-centring trail).
    Returns None if KPI axis is horizontal (degenerate case).
    """
    kp = upper_bj - lower_bj
    if abs(kp[2]) < 1e-10:
        return None
    t = -lower_bj[2] / kp[2]
    ground_intercept = lower_bj + t * kp
    return float(contact_patch[0] - ground_intercept[0])
