import sys
from pathlib import Path
from typing import Literal

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kinematics.hardpoints import HP, WHEEL_RADIUS

# Each linkage as (inboard, outboard) base hardpoint names. Unit vectors and
# force signs throughout Forces/ assume this order consistently: positive
# force = tension = the member pulling its inboard and outboard ends
# together.
LINKAGE_POINTS: dict[str, tuple[str, str]] = {
    "lower_aarm_fore": ("LAA_front_inboard", "LAA_outboard"),
    "lower_aarm_aft":  ("LAA_rear_inboard",  "LAA_outboard"),
    "upper_aarm_fore": ("UAA_front_inboard", "UAA_outboard"),
    "upper_aarm_aft":  ("UAA_rear_inboard",  "UAA_outboard"),
    "pushrod":         ("pushrod_inboard",   "pushrod_outboard"),
    "tierod":          ("tie_rod_inboard",   "tie_rod_outboard"),
}


def resolve_hardpoint(point_name: str, axle: Literal["front", "rear"] = "front") -> np.ndarray:
    """Look up a hardpoint by its base (front-axle) name for the given axle."""
    if axle not in {"front", "rear"}:
        raise ValueError("axle must be either 'front' or 'rear'")

    if axle == "front":
        return HP[point_name]

    key = f"rear_{point_name}"
    if key not in HP:
        raise KeyError(
            f"Missing rear hardpoint '{key}' in HP (kinematics/hardpoints.py) — "
            f"add it rather than silently reusing the front-axle point."
        )
    return HP[key]


def resolve_contact_patch(axle: Literal["front", "rear"] = "front") -> np.ndarray:
    """
    Contact-patch position, used as the moment-balance reference point.

    The front axle has an explicit `contact_patch` hardpoint. The rear axle
    doesn't have one yet, so it's approximated as directly below
    `rear_wheel_center` by the nominal (unloaded) wheel radius — add a real
    `rear_contact_patch` hardpoint in kinematics/hardpoints.py for an exact
    rear-axle solve.
    """
    if axle == "front":
        return HP["contact_patch"]

    wheel_center = resolve_hardpoint("wheel_center", axle)
    return wheel_center - np.array([0.0, 0.0, WHEEL_RADIUS])


def calculate_linkage_unit_vectors(axle: Literal["front", "rear"] = "front") -> dict[str, np.ndarray]:
    """
    Calculates the unit vectors of the suspension linkages.

    Args:
        axle: Selects the front or rear axle hardpoint set.

    Returns:
        A dictionary where keys are the linkage names and values are their
        corresponding unit vectors.
    """
    unit_vectors = {}
    for name, (p1_name, p2_name) in LINKAGE_POINTS.items():
        p1 = resolve_hardpoint(p1_name, axle)
        p2 = resolve_hardpoint(p2_name, axle)
        unit_vectors[name] = (p2 - p1) / np.linalg.norm(p2 - p1)
    return unit_vectors


