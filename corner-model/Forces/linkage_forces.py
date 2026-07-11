from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Forces.wheel_loads import calculate_total_wheel_load
from Forces.linkages import LINKAGE_POINTS, resolve_hardpoint, resolve_contact_patch
from Forces.tire_model import PacejkaTireModel, DEFAULT_TIR_PATH

LINKAGE_NAMES = list(LINKAGE_POINTS.keys())


def calculate_linkage_forces(
    lateral_g: float,
    long_g: float,
    axle: Literal["front", "rear"],
    wheel_force_n: float | None = None,
    slip_angle_rad: float | None = None,
    slip_ratio: float | None = None,
    pressure_pa: float | None = None,
) -> dict[str, dict[str, float]]:
    """
    Solve the linkage force balance for a single corner.

    Each of the six linkages (upper/lower A-arm fore & aft, pushrod, tie rod)
    is treated as a two-force member connecting a chassis (inboard) point to
    an upright (outboard) point. The upright/wheel assembly is treated as a
    single rigid body in equilibrium under those six reactions plus the
    external tire wrench (force and moment) applied at the contact patch. Six
    unknown member forces and six independent equilibrium equations (3 force
    + 3 moment, taken about the contact patch) make this statically
    determinate — no least-squares approximation involved.

    A positive force means tension (the member pulling its inboard and
    outboard ends together); negative means compression.

    The vertical tire force always comes from the load-transfer estimate. If
    slip_angle_rad, slip_ratio, and pressure_pa are all supplied, the lateral
    and longitudinal tire forces and the tire's own moments (from the Pacejka
    model) are included too, so cornering/braking g's change the direction
    (and rotational loading) of the applied wrench, not just its magnitude.

    Known simplification: the pushrod's outboard point is physically on the
    lower A-arm rather than the upright (see hardpoints.py). This model
    treats it as if it reacts directly against the upright/wheel assembly,
    avoiding a full multi-body solve of the A-arm itself.
    """
    if wheel_force_n is None:
        wheel_force_n = calculate_total_wheel_load(
            lateral_g=lateral_g,
            long_g=long_g,
            axle=axle,
        )

    longitudinal_force_n = 0.0
    lateral_force_n = 0.0
    moment_x_nm = 0.0
    moment_y_nm = 0.0
    moment_z_nm = 0.0
    if slip_angle_rad is not None and slip_ratio is not None and pressure_pa is not None:
        tire_model = PacejkaTireModel.from_tir(DEFAULT_TIR_PATH)
        tire_response = tire_model.calculate_tire_response(
            vertical_force_n=wheel_force_n,
            slip_angle_rad=slip_angle_rad,
            slip_ratio=slip_ratio,
            pressure_pa=pressure_pa,
        )
        longitudinal_force_n = tire_response["longitudinal_force_N"]
        lateral_force_n = tire_response["lateral_force_N"]
        moment_x_nm = tire_response["moment_x_Nm"]
        moment_y_nm = tire_response["moment_y_Nm"]
        moment_z_nm = tire_response["moment_z_Nm"]

    # Force and moment applied TO the wheel/upright assembly BY the ground,
    # at the contact patch (SAE convention: +Z is the normal load supporting
    # the corner's weight).
    tire_force = np.array([longitudinal_force_n, lateral_force_n, wheel_force_n], dtype=float)
    tire_moment = np.array([moment_x_nm, moment_y_nm, moment_z_nm], dtype=float)
    contact_patch = resolve_contact_patch(axle)

    # Build the 6x6 equilibrium system. Column i = [u_i; r_i x u_i], where
    # u_i is linkage i's inboard->outboard unit vector and r_i is the moment
    # arm from the contact patch to its outboard (upright) attachment point.
    columns = []
    for name in LINKAGE_NAMES:
        inboard_name, outboard_name = LINKAGE_POINTS[name]
        inboard = resolve_hardpoint(inboard_name, axle)
        outboard = resolve_hardpoint(outboard_name, axle)
        u = (outboard - inboard) / np.linalg.norm(outboard - inboard)
        r = outboard - contact_patch
        columns.append(np.concatenate([u, np.cross(r, u)]))

    A = np.column_stack(columns)
    b = np.concatenate([tire_force, tire_moment])
    forces = np.linalg.solve(A, b)

    return {
        name: {
            "force_N": float(force),
            "sense": "tension" if float(force) >= 0.0 else "compression",
            "sign": 1.0 if float(force) >= 0.0 else -1.0,
        }
        for name, force in zip(LINKAGE_NAMES, forces)
    }


if __name__ == "__main__":
    forces = calculate_linkage_forces(
        lateral_g=1.0,
        long_g=0.2,
        axle="front",
        slip_angle_rad=0.08,
        slip_ratio=0.1,
        pressure_pa=100000.0,
    )
    print("Linkage forces:")
    for name, payload in forces.items():
        print(f"- {name}: {payload['force_N']:.3f} N ({payload['sense']})")
