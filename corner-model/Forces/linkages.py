import numpy as np
from typing import Literal

try:
    from ..kinematics.hardpoints import HP
except ImportError:  # pragma: no cover - fallback for direct execution
    from kinematics.hardpoints import HP


def calculate_linkage_unit_vectors(axle: Literal["front", "rear"] = "front") -> dict[str, np.ndarray]:
    """
    Calculates the unit vectors of the suspension linkages.

    Args:
        axle: Selects the front or rear axle hardpoint set.

    Returns:
        A dictionary where keys are the linkage names and values are their
        corresponding unit vectors.
    """
    if axle not in {"front", "rear"}:
        raise ValueError("axle must be either 'front' or 'rear'")

    prefix = "rear" if axle == "rear" else ""
    unit_vectors = {}

    def get_point(point_name: str) -> np.ndarray:
        key = f"{prefix}_{point_name}" if prefix and f"{prefix}_{point_name}" in HP else point_name
        return HP[key]

    # Lower A-arm fore
    p1 = get_point("LAA_front_inboard")
    p2 = get_point("LAA_outboard")
    unit_vectors["lower_aarm_fore"] = (p2 - p1) / np.linalg.norm(p2 - p1)

    # Lower A-arm aft
    p1 = get_point("LAA_rear_inboard")
    p2 = get_point("LAA_outboard")
    unit_vectors["lower_aarm_aft"] = (p2 - p1) / np.linalg.norm(p2 - p1)

    # Upper A-arm fore
    p1 = get_point("UAA_front_inboard")
    p2 = get_point("UAA_outboard")
    unit_vectors["upper_aarm_fore"] = (p2 - p1) / np.linalg.norm(p2 - p1)

    # Upper A-arm aft
    p1 = get_point("UAA_rear_inboard")
    p2 = get_point("UAA_outboard")
    unit_vectors["upper_aarm_aft"] = (p2 - p1) / np.linalg.norm(p2 - p1)

    # Pushrod
    p1 = get_point("pushrod_outboard")
    p2 = get_point("pushrod_inboard")
    unit_vectors["pushrod"] = (p2 - p1) / np.linalg.norm(p2 - p1)

    # Tie rod
    p1 = get_point("tie_rod_inboard")
    p2 = get_point("tie_rod_outboard")
    unit_vectors["tierod"] = (p2 - p1) / np.linalg.norm(p2 - p1)

    return unit_vectors


