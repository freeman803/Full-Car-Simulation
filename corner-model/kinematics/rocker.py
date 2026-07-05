"""
rocker.py — Pushrod, bellcrank, and motion ratio kinematics.

Models the actuation chain:
    wheel travel → pushrod compression → bellcrank rotation → damper displacement

All lengths in mm, angles in degrees, forces in N.

Coordinate system: SAE J670  (X fwd, Y left, Z up)
"""

import numpy as np
import pandas as pd

from .suspension import solve_double_wishbone, DEFAULT_TRAVEL
from .geometry import normalize


# ─────────────────────────────────────────────────────────────────────────────
# Pushrod geometry
# ─────────────────────────────────────────────────────────────────────────────

def pushrod_length(hp: dict[str, np.ndarray]) -> float:
    """Static pushrod length (mm)."""
    return float(np.linalg.norm(hp["pushrod_inboard"] - hp["pushrod_outboard"]))


def pushrod_outboard_at_travel(
    z_travel: float,
    hp: dict[str, np.ndarray],
) -> np.ndarray:
    """
    Return the 3D position of the pushrod outboard pickup after wheel
    has travelled z_travel mm.  The pickup sits on the lower A-arm,
    so it moves with the lower BJ (same YZ rotation, fixed X offset).
    """
    s = solve_double_wishbone(z_travel, hp)
    # The pushrod outboard is offset from the lower BJ by a fixed vector
    # (measured at static). Apply the same arm rotation to it.
    lbj_static  = hp["lower_BJ"]
    lbj_new     = s["lower_BJ"]
    offset       = hp["pushrod_outboard"] - lbj_static
    # Scale offset Y to match new arm position (arm rotates, length preserved)
    dy_ratio = (lbj_new[1] - hp["LAA_front_inboard"][1]*0 - hp["LAA_rear_inboard"][1]*0)
    # Simple rigid-body: offset moves with the lower BJ translation
    return lbj_new + np.array([offset[0], offset[1] * (lbj_new[1] / max(lbj_static[1], 1e-6)), offset[2]])


def pushrod_compression(
    z_travel: float,
    hp: dict[str, np.ndarray],
) -> float:
    """
    Pushrod compression (mm) at a given wheel travel.
    Positive = pushrod shortens (pushes bellcrank in bump).
    The inboard end (bellcrank arm) is treated as fixed for this calculation;
    bellcrank rotation is solved separately in bellcrank_state().
    """
    static_len  = pushrod_length(hp)
    pb_new      = pushrod_outboard_at_travel(z_travel, hp)
    current_len = float(np.linalg.norm(hp["pushrod_inboard"] - pb_new))
    return static_len - current_len   # positive = shorter = compression


# ─────────────────────────────────────────────────────────────────────────────
# Bellcrank geometry
# ─────────────────────────────────────────────────────────────────────────────

def _bellcrank_arm_lengths(hp: dict[str, np.ndarray]) -> tuple[float, float]:
    """
    Return (pushrod_arm_length, damper_arm_length) — the moment arms
    of the bellcrank measured from its pivot.
    """
    pivot        = hp["bellcrank_pivot"]
    pushrod_arm  = float(np.linalg.norm(hp["bellcrank_pushrod_arm"] - pivot))
    damper_arm   = float(np.linalg.norm(hp["bellcrank_damper_arm"]  - pivot))
    return pushrod_arm, damper_arm


def bellcrank_state(
    z_travel: float,
    hp: dict[str, np.ndarray],
) -> dict:
    """
    Solve the bellcrank rotation and damper displacement for a given wheel travel.

    The bellcrank rotates about its pivot. The pushrod arm and damper arm
    are rigid levers. Rotation angle is solved from the pushrod compression
    using the law of cosines on the pushrod triangle.

    Returns
    -------
    dict with keys:
        rotation_deg     — bellcrank rotation (positive = bump direction)
        damper_disp_mm   — damper displacement (positive = compression)
        pushrod_arm_mm   — moment arm for pushrod
        damper_arm_mm    — moment arm for damper
        pushrod_comp_mm  — pushrod compression
    """
    pivot       = hp["bellcrank_pivot"]
    pa_len, da_len = _bellcrank_arm_lengths(hp)

    # Static pushrod length and current outboard position
    static_pr_len  = pushrod_length(hp)
    pb_new         = pushrod_outboard_at_travel(z_travel, hp)

    # Distance from pivot to pushrod outboard (forms a triangle with the pushrod)
    # pivot — pushrod_inboard is fixed arm (pa_len)
    # pivot — pb_new varies with travel
    pivot_to_pb    = float(np.linalg.norm(pb_new - pivot))

    # Law of cosines to find angle at pivot between pushrod arm and
    # line from pivot to new outboard position
    # c² = a² + b² - 2ab·cos(C)
    # c = distance outboard→inboard (= pushrod current length)
    pr_current = float(np.linalg.norm(hp["pushrod_inboard"] - pb_new))
    cos_angle  = np.clip(
        (pa_len**2 + pivot_to_pb**2 - pr_current**2) / (2 * pa_len * pivot_to_pb),
        -1.0, 1.0
    )
    # Bellcrank rotation relative to static
    static_pr_current = float(np.linalg.norm(hp["pushrod_inboard"] - hp["pushrod_outboard"]))
    pivot_to_pb_static = float(np.linalg.norm(hp["pushrod_outboard"] - pivot))
    cos_static = np.clip(
        (pa_len**2 + pivot_to_pb_static**2 - static_pr_current**2)
        / (2 * pa_len * pivot_to_pb_static),
        -1.0, 1.0
    )
    rotation_deg = float(np.degrees(np.arccos(cos_angle)) - np.degrees(np.arccos(cos_static)))

    # Damper displacement from bellcrank rotation (small angle on damper arm)
    rotation_rad = np.radians(rotation_deg)
    damper_disp  = da_len * np.sin(rotation_rad)   # positive = compression

    # Pushrod compression
    pr_comp = static_pr_current - pr_current

    return {
        "rotation_deg":    rotation_deg,
        "damper_disp_mm":  damper_disp,
        "pushrod_arm_mm":  pa_len,
        "damper_arm_mm":   da_len,
        "pushrod_comp_mm": pr_comp,
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
    Instantaneous motion ratio at a given wheel travel position.

    MR = d(damper_displacement) / d(wheel_travel)

    Computed numerically via central difference with step dz (mm).
    MR < 1 means the damper moves less than the wheel (mechanical advantage).
    """
    hi = bellcrank_state(z_travel + dz, hp)["damper_disp_mm"]
    lo = bellcrank_state(z_travel - dz, hp)["damper_disp_mm"]
    return (hi - lo) / (2.0 * dz)


def motion_ratio_sweep(
    hp: dict[str, np.ndarray],
    travel: np.ndarray = DEFAULT_TRAVEL,
) -> pd.DataFrame:
    """
    Sweep wheel travel and return motion ratio, damper displacement,
    bellcrank rotation, and derived wheel-rate at each position.

    Parameters
    ----------
    hp : dict
        Hardpoint dictionary (must include pushrod/bellcrank/damper points).
    travel : np.ndarray
        Wheel travel positions (mm).

    Returns
    -------
    pd.DataFrame with columns:
        travel_mm, motion_ratio, damper_disp_mm, bellcrank_rot_deg,
        pushrod_comp_mm, wheel_rate_N_mm
    """
    from .hardpoints import SPRING_RATE  # imported here to allow override

    rows = []
    for z in travel:
        bc   = bellcrank_state(z, hp)
        mr   = motion_ratio_at(z, hp)
        # Wheel rate = spring rate × MR²  (energy equivalence)
        wheel_rate = SPRING_RATE * mr**2

        rows.append({
            "travel_mm":        float(z),
            "motion_ratio":     mr,
            "damper_disp_mm":   bc["damper_disp_mm"],
            "bellcrank_rot_deg":bc["rotation_deg"],
            "pushrod_comp_mm":  bc["pushrod_comp_mm"],
            "wheel_rate_N_mm":  wheel_rate,
        })

    return pd.DataFrame(rows)


def effective_spring_rate(
    hp: dict[str, np.ndarray],
    spring_rate_N_mm: float,
    z_travel: float = 0.0,
) -> float:
    """
    Wheel-centre spring rate accounting for motion ratio.

    k_wheel = k_spring × MR²
    """
    mr = motion_ratio_at(z_travel, hp)
    return spring_rate_N_mm * mr**2


def effective_damper_rate(
    hp: dict[str, np.ndarray],
    damper_rate_Ns_mm: float,
    z_travel: float = 0.0,
) -> float:
    """
    Wheel-centre damping coefficient accounting for motion ratio.
 
    c_wheel = c_damper × MR²
    """
    mr = motion_ratio_at(z_travel, hp)
    return damper_rate_Ns_mm * mr**2


def motion_ratio_report(hp: dict[str, np.ndarray]) -> None:
    """Print a summary of bellcrank geometry and motion ratio at static ride height."""
    pa, da  = _bellcrank_arm_lengths(hp)
    mr      = motion_ratio_at(0.0, hp)
    bc      = bellcrank_state(0.0, hp)

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
