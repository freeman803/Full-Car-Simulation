"""
suspension.py — Double-wishbone solver, wheel travel sweep, and static report.
"""

import numpy as np
import pandas as pd

from .geometry import (
    camber_angle,
    caster_angle,
    kpi_angle,
    toe_angle,
    scrub_radius,
    mechanical_trail,
)

# Default travel range used by run_travel_sweep
DEFAULT_TRAVEL = np.linspace(-40.0, 40.0, 81)  # mm


def solve_double_wishbone(
    z_travel: float,
    hp: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    """
    Solve the double-wishbone constraint at a given wheel travel (mm).

    Model assumptions (planar arm rotation):
      - Each A-arm rotates in its own YZ plane about its inboard midpoint pivot.
      - Arm lengths are preserved exactly.
      - The tie rod outboard point moves with the upright (Z follows wheel travel).
      - The contact patch stays on the ground plane (Z = 0).

    Parameters
    ----------
    z_travel : float
        Wheel travel in mm. Positive = bump, negative = droop.
    hp : dict
        Hardpoint dictionary (from hardpoints.py or a modified copy for sweeps).

    Returns
    -------
    dict with updated positions for:
        upper_BJ, lower_BJ, tie_rod_inboard, tie_rod_outboard,
        wheel_center, contact_patch
    """
    UAA_mid = 0.5 * (hp["UAA_front_inboard"] + hp["UAA_rear_inboard"])
    LAA_mid = 0.5 * (hp["LAA_front_inboard"] + hp["LAA_rear_inboard"])

    r_upper = np.linalg.norm(hp["upper_BJ"] - UAA_mid)
    r_lower = np.linalg.norm(hp["lower_BJ"] - LAA_mid)

    def _arm_bj(pivot: np.ndarray, static_bj: np.ndarray, r: float) -> np.ndarray:
        """Find new outboard BJ position after wheel travels z_travel mm."""
        target_z = static_bj[2] + z_travel
        dz = target_z - pivot[2]
        dy = np.sqrt(max(r**2 - dz**2, 0.0))  # clamp at jounce/droop limit
        return np.array([static_bj[0], pivot[1] + dy, target_z])

    new_ubj = _arm_bj(UAA_mid, hp["upper_BJ"], r_upper)
    new_lbj = _arm_bj(LAA_mid, hp["lower_BJ"], r_lower)

    # Tie rod: inboard rack end is fixed; outboard knuckle rises with the upright
    tr_len   = np.linalg.norm(hp["tie_rod_outboard"] - hp["tie_rod_inboard"])
    tr_tgt_z = hp["tie_rod_outboard"][2] + z_travel
    dz_tr    = tr_tgt_z - hp["tie_rod_inboard"][2]
    dx_tr    = hp["tie_rod_outboard"][0] - hp["tie_rod_inboard"][0]
    dy_tr    = np.sqrt(max(tr_len**2 - dz_tr**2 - dx_tr**2, 0.0))
    new_tro  = np.array([hp["tie_rod_outboard"][0], hp["tie_rod_inboard"][1] + dy_tr, tr_tgt_z])

    # Wheel centre and contact patch follow lower BJ laterally
    new_wc    = hp["wheel_center"].copy()
    new_wc[1] = new_lbj[1] + (hp["wheel_center"][1] - hp["lower_BJ"][1])
    new_wc[2] = hp["wheel_center"][2] + z_travel
    new_cp    = np.array([new_wc[0], new_wc[1], 0.0])

    # Spindle (wheel spin) axis: the upright is a rigid body carrying the upper
    # BJ, lower BJ and tie-rod outboard. Find the rigid rotation that maps the
    # static upright triangle to its new position, and apply it to the static
    # spindle axis. This yields camber gain and bump steer through travel.
    new_spindle = _rotate_spindle(hp, new_ubj, new_lbj, new_tro)

    return {
        "upper_BJ":           new_ubj,
        "lower_BJ":           new_lbj,
        "tie_rod_inboard":    hp["tie_rod_inboard"].copy(),
        "tie_rod_outboard":   new_tro,
        "wheel_center":       new_wc,
        "contact_patch":      new_cp,
        "spindle_axis":       new_spindle,
    }


def _rotate_spindle(
    hp: dict[str, np.ndarray],
    new_ubj: np.ndarray,
    new_lbj: np.ndarray,
    new_tro: np.ndarray,
) -> np.ndarray:
    """
    Rotate the static spindle axis by the upright's rigid-body rotation.

    Uses a Kabsch (SVD) fit of the static upright triangle
    {upper_BJ, lower_BJ, tie_rod_outboard} onto its new positions to recover the
    rotation matrix, then applies it to hp['spindle_axis'].
    Falls back to the static spindle axis if it isn't defined.
    """
    spindle0 = hp.get("spindle_axis")
    if spindle0 is None:
        # No wheel orientation defined; return a straight-ahead vertical wheel.
        return np.array([0.0, 1.0, 0.0])

    P0 = np.array([hp["upper_BJ"], hp["lower_BJ"], hp["tie_rod_outboard"]])
    P1 = np.array([new_ubj,        new_lbj,        new_tro])
    c0, c1 = P0.mean(axis=0), P1.mean(axis=0)
    H = (P0 - c0).T @ (P1 - c1)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return R @ spindle0


def run_travel_sweep(
    hp: dict[str, np.ndarray],
    travel: np.ndarray = DEFAULT_TRAVEL,
) -> pd.DataFrame:
    """
    Run a bump/droop sweep over `travel` mm and return all kinematic metrics.

    Parameters
    ----------
    hp : dict
        Hardpoint dictionary.
    travel : np.ndarray
        Array of wheel travel positions (mm) to evaluate.

    Returns
    -------
    pd.DataFrame with columns:
        travel_mm, camber_deg, caster_deg, kpi_deg, toe_deg,
        scrub_mm, trail_mm, track_change_mm, camber_gain
    """
    wc0   = hp["wheel_center"][1]   # baseline lateral wheel centre position
    rows  = []

    for z in travel:
        s  = solve_double_wishbone(z, hp)
        ub = s["upper_BJ"]
        lb = s["lower_BJ"]
        cp = s["contact_patch"]

        sp = s["spindle_axis"]
        rows.append({
            "travel_mm":       float(z),
            "camber_deg":      camber_angle(sp),
            "caster_deg":      caster_angle(ub, lb),
            "kpi_deg":         kpi_angle(ub, lb),
            "toe_deg":         toe_angle(sp),
            "scrub_mm":        scrub_radius(ub, lb, cp) or 0.0,
            "trail_mm":        mechanical_trail(ub, lb, cp) or 0.0,
            "track_change_mm": 2.0 * (s["wheel_center"][1] - wc0),
        })

    df = pd.DataFrame(rows)
    df["camber_gain"] = np.gradient(df["camber_deg"].values, df["travel_mm"].values)
    return df


def static_report(hp: dict[str, np.ndarray], print_output: bool = True) -> dict:
    """
    Compute and optionally print all static geometry values at design ride height.

    Returns a dict of all computed values for programmatic use.
    """
    ubj = hp["upper_BJ"]
    lbj = hp["lower_BJ"]
    tri = hp["tie_rod_inboard"]
    tro = hp["tie_rod_outboard"]
    wc  = hp["wheel_center"]
    cp  = hp["contact_patch"]

    uaa_mid = 0.5 * (hp["UAA_front_inboard"] + hp["UAA_rear_inboard"])
    laa_mid = 0.5 * (hp["LAA_front_inboard"] + hp["LAA_rear_inboard"])

    spindle = hp.get("spindle_axis", np.array([0.0, 1.0, 0.0]))

    vals = {
        "camber_deg":     camber_angle(spindle),
        "caster_deg":     caster_angle(ubj, lbj),
        "kpi_deg":        kpi_angle(ubj, lbj),
        "toe_deg":        toe_angle(spindle),
        "scrub_mm":       scrub_radius(ubj, lbj, cp) or 0.0,
        "trail_mm":       mechanical_trail(ubj, lbj, cp) or 0.0,
        "arm_length_upper_mm": float(np.linalg.norm(ubj - uaa_mid)),
        "arm_length_lower_mm": float(np.linalg.norm(lbj - laa_mid)),
    }
    vals["included_angle_deg"] = vals["kpi_deg"] + vals["camber_deg"]
    vals["arm_ratio"]          = vals["arm_length_upper_mm"] / vals["arm_length_lower_mm"]

    if print_output:
        sep = "─" * 50
        print(sep)
        print("  FSAE CORNER — STATIC GEOMETRY REPORT")
        print(sep)
        print(f"  Camber angle           : {vals['camber_deg']:+.3f}°")
        print(f"  Caster angle           : {vals['caster_deg']:+.3f}°")
        print(f"  King Pin Inclination   : {vals['kpi_deg']:+.3f}°")
        print(f"  Included angle (KPI+C) : {vals['included_angle_deg']:.3f}°")
        print(f"  Static toe             : {vals['toe_deg']:+.3f}°  "
              f"({'toe-in' if vals['toe_deg'] > 0 else 'toe-out'})")
        print(f"  Scrub radius           : {vals['scrub_mm']:+.2f} mm  "
              f"({'positive' if vals['scrub_mm'] > 0 else 'negative'})")
        print(f"  Mechanical trail       : {vals['trail_mm']:+.2f} mm")
        print(sep)
        print(f"  Upper arm length       : {vals['arm_length_upper_mm']:.2f} mm")
        print(f"  Lower arm length       : {vals['arm_length_lower_mm']:.2f} mm")
        print(f"  Arm ratio (U/L)        : {vals['arm_ratio']:.4f}")
        print(sep)

        # FSAE range checks
        checks = {
            "Camber  (−2° to 0°)":     (-2.0 <= vals["camber_deg"] <= 0.0),
            "Caster  (3° to 8°)":      ( 3.0 <= vals["caster_deg"] <= 8.0),
            "KPI     (8° to 14°)":     ( 8.0 <= vals["kpi_deg"]    <= 14.0),
            "Toe     (−0.5° to 0.5°)": (-0.5 <= vals["toe_deg"]    <= 0.5),
            "Scrub   (0 to 25 mm)":    ( 0.0 <= vals["scrub_mm"]   <= 25.0),
            "Trail   (10 to 40 mm)":   (10.0 <= vals["trail_mm"]   <= 40.0),
        }
        print("\n  FSAE TYPICAL RANGE CHECK:")
        for label, ok in checks.items():
            print(f"  {'✅ OK ' if ok else '⚠️  OUT'}  {label}")

    return vals