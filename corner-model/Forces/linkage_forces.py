from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Forces.wheel_loads import calculate_total_wheel_load
from Forces.linkages import calculate_linkage_unit_vectors
from Forces.tire_model import PacejkaTireModel, DEFAULT_TIR_PATH


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
    Solve a simplified linkage force balance for a single corner.

    The model uses the suspension linkage unit vectors and a single external
    contact-patch force vector to solve for the force in each linkage. The
    vertical component always comes from the load-transfer estimate; if
    slip_angle_rad, slip_ratio, and pressure_pa are all supplied, the lateral
    and longitudinal tire forces (from the Pacejka model) are included too, so
    cornering/braking g's actually change the direction of the applied load
    rather than just its magnitude. The linkages provide the reaction forces
    needed to balance it.
    """
    if wheel_force_n is None:
        wheel_force_n = calculate_total_wheel_load(
            lateral_g=lateral_g,
            long_g=long_g,
            axle=axle,
        )

    longitudinal_force_n = 0.0
    lateral_force_n = 0.0
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

    unit_vectors = calculate_linkage_unit_vectors(axle=axle)

    # Use a small set of principal linkages and their directions.
    # We form a statics system where the unknown linkage forces are solved from
    # force equilibrium in the vertical direction.
    linkage_names = [
        "lower_aarm_fore",
        "lower_aarm_aft",
        "upper_aarm_fore",
        "upper_aarm_aft",
        "pushrod",
        "tierod",
    ]

    # Build a simple matrix with one equilibrium equation per active linkage
    # direction. For this initial implementation we solve for the force needed
    # in each linkage to support the wheel load in the vertical direction.
    directions = np.array([unit_vectors[name] for name in linkage_names], dtype=float)

    # Build an equilibrium matrix where each column is the direction vector of
    # one linkage. The unknowns are the scalar force magnitudes in each linkage.
    # The wheel load is expressed as an external force vector, and we solve for
    # the linkage forces that balance it.
    A = np.column_stack([unit_vectors[name].reshape(3, 1) for name in linkage_names])
    A = A.reshape(3, 6)
    wheel_force_vector = np.array(
        [-longitudinal_force_n, -lateral_force_n, -wheel_force_n], dtype=float
    )

    forces = np.linalg.pinv(A) @ wheel_force_vector
    forces = np.ravel(forces)

    return {
        name: {
            "force_N": float(force),
            "sense": "tension" if float(force) >= 0.0 else "compression",
            "sign": 1.0 if float(force) >= 0.0 else -1.0,
        }
        for name, force in zip(linkage_names, forces)
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
