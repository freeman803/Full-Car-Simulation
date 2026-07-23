"""
rocker.py — Pushrod, bellcrank, and motion ratio kinematics.

Models the actuation chain:
    wheel travel → pushrod outboard motion → bellcrank rotation → damper displacement

CORRECTED MODEL (rigid pushrod)
───────────────────────────────
The pushrod is a RIGID link: its length is constant. Wheel travel moves the
pushrod outboard pickup (which rides on the lower A-arm). Because the rod length
is fixed, that motion forces the bellcrank to rotate about its pivot. We solve
for the rotation angle θ that keeps the pushrod length constant (a 1-D root
find), then apply the same rotation to the damper arm to get damper travel.

The bellcrank is planar: pivot, pushrod arm, damper arm and the damper axis all
lie in a single Y-Z plane (constant X), so the rotation is a 2-D rotation about
the car's X axis. This matches the hardpoints in hardpoints.py.

All lengths in mm, angles in degrees, forces in N.
Coordinate system: SAE J670  (X fwd, Y left, Z up)
"""

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from .suspension import solve_double_wishbone, DEFAULT_TRAVEL


# ─────────────────────────────────────────────────────────────────────────────
# Planar helpers (work in the bellcrank's Y-Z plane)
# ─────────────────────────────────────────────────────────────────────────────

def _yz(p: np.ndarray) -> np.ndarray:
    """Project a 3D point onto the bellcrank plane -> (Y, Z)."""
    return np.array([p[1], p[2]])


def _rot2(p: np.ndarray, centre: np.ndarray, ang_rad: float) -> np.ndarray:
    """Rotate 2D point p about centre by ang_rad."""
    s, c = np.sin(ang_rad), np.cos(ang_rad)
    d = p - centre
    return centre + np.array([c * d[0] - s * d[1], s * d[0] + c * d[1]])


# ─────────────────────────────────────────────────────────────────────────────
# Pushrod geometry
# ─────────────────────────────────────────────────────────────────────────────

def pushrod_length(hp: dict[str, np.ndarray]) -> float:
    """Static (and, being rigid, constant) pushrod length (mm)."""
    return float(np.linalg.norm(hp["pushrod_inboard"] - hp["pushrod_outboard"]))


def pushrod_outboard_at_travel(
    z_travel: float,
    hp: dict[str, np.ndarray],
) -> np.ndarray:
    """
    3D position of the pushrod outboard pickup after wheel travel z_travel mm.

    The pickup is rigidly attached to the lower A-arm, so it translates with the
    lower ball joint as the arm rotates. (Fixed offset from the lower BJ.)
    """
    s        = solve_double_wishbone(z_travel, hp)
    offset   = hp["pushrod_outboard"] - hp["lower_BJ"]
    return s["lower_BJ"] + offset


# ─────────────────────────────────────────────────────────────────────────────
# Bellcrank geometry
# ─────────────────────────────────────────────────────────────────────────────

def _bellcrank_arm_lengths(hp: dict[str, np.ndarray]) -> tuple[float, float]:
    """(pushrod_arm_length, damper_arm_length) measured from the pivot (mm)."""
    pivot       = hp["bellcrank_pivot"]
    pushrod_arm = float(np.linalg.norm(hp["bellcrank_pushrod_arm"] - pivot))
    damper_arm  = float(np.linalg.norm(hp["bellcrank_damper_arm"]  - pivot))
    return pushrod_arm, damper_arm


def bellcrank_state(
    z_travel: float,
    hp: dict[str, np.ndarray],
) -> dict:
    """
    Solve bellcrank rotation and damper displacement for a given wheel travel.

    Method (rigid pushrod, planar bellcrank):
      1. Move the pushrod outboard pickup to its position at z_travel.
      2. Find rotation θ about the pivot such that the distance from the rotated
         pushrod-arm tip to the (moved) outboard pickup equals the constant
         pushrod length.
      3. Rotate the damper-arm tip by θ; damper displacement is the change in
         length of the damper (arm tip → chassis mount).

    Returns
    -------
    dict with keys:
        rotation_deg     — bellcrank rotation (+ = droop side here; sign is a
                           convention, magnitude is what matters)
        damper_disp_mm   — damper displacement (+ = extension, − = compression)
        pushrod_arm_mm   — moment arm for pushrod
        damper_arm_mm    — moment arm for damper
        pushrod_comp_mm  — retained for API compatibility; ~0 for a rigid rod
    """
    pivot2   = _yz(hp["bellcrank_pivot"])
    pr_arm0  = _yz(hp["bellcrank_pushrod_arm"])   # pushrod arm tip (static)
    dm_arm0  = _yz(hp["bellcrank_damper_arm"])    # damper arm tip (static)
    dmp_in2  = _yz(hp["damper_inboard"])          # chassis damper mount (fixed)

    L_push   = pushrod_length(hp)
    dmp_len0 = float(np.linalg.norm(dm_arm0 - dmp_in2))

    p_out2   = _yz(pushrod_outboard_at_travel(z_travel, hp))

    def _resid(th: float) -> float:
        tip = _rot2(pr_arm0, pivot2, th)
        return float(np.linalg.norm(p_out2 - tip) - L_push)

    # Root-find the rotation. Bracket around 0 and widen until a sign change is
    # found (handles large travel where rotation approaches ±60°).
    theta = 0.0
    for hi_deg in (30, 45, 60, 80):
        hi = np.radians(hi_deg)
        if _resid(-hi) * _resid(hi) <= 0.0:
            theta = brentq(_resid, -hi, hi, xtol=1e-8)
            break
    else:
        # Degenerate / unreachable geometry: fall back to no rotation.
        theta = 0.0

    dm_tip   = _rot2(dm_arm0, pivot2, theta)
    dmp_len  = float(np.linalg.norm(dm_tip - dmp_in2))
    damper_disp = dmp_len - dmp_len0

    pa_len, da_len = _bellcrank_arm_lengths(hp)

    return {
        "rotation_deg":    float(np.degrees(theta)),
        "damper_disp_mm":  damper_disp,
        "pushrod_arm_mm":  pa_len,
        "damper_arm_mm":   da_len,
        "pushrod_comp_mm": 0.0,   # rigid rod: no compression (kept for API parity)
    }


# ─────────────────────────────────────────────────────────────────────────────
# Motion ratio
# ─────────────────────────────────────────────────────────────────────────────

def motion_ratio_at(
    z_travel: float,
    hp: dict[str, np.ndarray],
    dz: float = 0.5,
) -> float:
    """
    Instantaneous motion ratio |d(damper_disp) / d(wheel_travel)| at z_travel.

    Central difference with step dz (mm). Returned as a positive magnitude so
    that wheel_rate = spring_rate * MR**2 behaves correctly regardless of the
    rotation sign convention.
    """
    hi = bellcrank_state(z_travel + dz, hp)["damper_disp_mm"]
    lo = bellcrank_state(z_travel - dz, hp)["damper_disp_mm"]
    return abs((hi - lo) / (2.0 * dz))


def motion_ratio_sweep(
    hp: dict[str, np.ndarray],
    travel: np.ndarray = DEFAULT_TRAVEL,
) -> pd.DataFrame:
    """
    Sweep wheel travel and return motion ratio, damper displacement,
    bellcrank rotation, and derived wheel rate at each position.

    Returns
    -------
    pd.DataFrame with columns:
        travel_mm, motion_ratio, damper_disp_mm, bellcrank_rot_deg,
        pushrod_comp_mm, wheel_rate_N_mm
    """
    from .hardpoints import SPRING_RATE

    rows = []
    for z in travel:
        bc = bellcrank_state(z, hp)
        mr = motion_ratio_at(z, hp)
        rows.append({
            "travel_mm":        float(z),
            "motion_ratio":     mr,
            "damper_disp_mm":   bc["damper_disp_mm"],
            "bellcrank_rot_deg":bc["rotation_deg"],
            "pushrod_comp_mm":  bc["pushrod_comp_mm"],
            "wheel_rate_N_mm":  SPRING_RATE * mr**2,
        })

    return pd.DataFrame(rows)


def effective_spring_rate(
    hp: dict[str, np.ndarray],
    spring_rate_N_mm: float,
    z_travel: float = 0.0,
) -> float:
    """Wheel-centre spring rate: k_wheel = k_spring * MR**2."""
    mr = motion_ratio_at(z_travel, hp)
    return spring_rate_N_mm * mr**2


def effective_damper_rate(
    hp: dict[str, np.ndarray],
    damper_rate_Ns_mm: float,
    z_travel: float = 0.0,
) -> float:
    """Wheel-centre damping coefficient: c_wheel = c_damper * MR**2."""
    mr = motion_ratio_at(z_travel, hp)
    return damper_rate_Ns_mm * mr**2


def motion_ratio_report(hp: dict[str, np.ndarray]) -> None:
    """Print bellcrank geometry and motion ratio at static ride height."""
    pa, da = _bellcrank_arm_lengths(hp)
    mr     = motion_ratio_at(0.0, hp)

    from .hardpoints import SPRING_RATE, DAMPER_RATE

    sep = "─" * 50
    print(sep)
    print("  PUSHROD / BELLCRANK — STATIC REPORT")
    print(sep)
    print(f"  Pushrod length         : {pushrod_length(hp):.2f} mm")
    print(f"  Pushrod arm (pivot→rod): {pa:.2f} mm")
    print(f"  Damper arm  (pivot→dmp): {da:.2f} mm")
    print(f"  Arm ratio (dmp/rod)    : {da/pa:.4f}")
    print(sep)
    print(f"  Motion ratio (static)  : {mr:.4f}")
    print(f"  Wheel rate             : {SPRING_RATE * mr**2:.2f} N/mm")
    print(f"  Wheel damping          : {DAMPER_RATE * mr**2:.4f} N·s/mm")
    print(sep)