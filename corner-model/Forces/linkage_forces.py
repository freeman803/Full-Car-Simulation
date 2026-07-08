from __future__ import annotations

import numpy as np
from typing import Literal

from .wheel_loads import calculate_total_wheel_load
from .linkages import calculate_linkage_unit_vectors


def calculate_linkage_forces(
    lateral_g: float,
    long_g: float,
    axle: Literal["front", "rear"],
    wheel_force_n: float | None = None,
) -> dict[str, float]:
    """
    Solve a simplified linkage force balance for a single corner.

    The model uses the suspension linkage unit vectors and a single external
    wheel load vector to solve for the force in each linkage. The wheel load is
    represented as a vertical force acting at the contact patch, while the
    linkages provide the reaction forces needed to balance it.
    """
    if wheel_force_n is None:
        wheel_force_n = calculate_total_wheel_load(
            lateral_g=lateral_g,
            long_g=long_g,
            axle=axle,
        )

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
    wheel_force_vector = np.array([0.0, 0.0, -wheel_force_n], dtype=float)

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
    forces = calculate_linkage_forces(lateral_g=1.0, long_g=0.2, axle="front")
    print("Linkage forces:")
    for name, value in forces.items():
        print(f"- {name}: {value:.3f} N")
