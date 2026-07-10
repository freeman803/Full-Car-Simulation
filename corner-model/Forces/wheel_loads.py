from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Forces.car_data import CarData


def calculate_total_wheel_load(
    lateral_g: float,
    long_g: float,
    axle: Literal["front", "rear"],
    mass_kg: float | None = None,
    cg_height_mm: float | None = None,
    wheelbase_mm: float | None = None,
    front_track_mm: float | None = None,
    rear_track_mm: float | None = None,
    total_downforce_N: float | None = None,
    center_of_mass: float | None = None,
    center_of_pressure: float | None = None,
) -> float:
    """
    Calculate the total load on one wheel for a given axle under lateral and
    longitudinal acceleration.

    The result is the load on the loaded wheel side for positive lateral and
    longitudinal G values.
    """
    mass_kg = mass_kg if mass_kg is not None else CarData.MASS_KG
    cg_height_mm = cg_height_mm if cg_height_mm is not None else CarData.CG_HEIGHT_MM
    wheelbase_mm = wheelbase_mm if wheelbase_mm is not None else CarData.WHEELBASE_MM
    front_track_mm = front_track_mm if front_track_mm is not None else CarData.FRONT_TRACK_MM
    rear_track_mm = rear_track_mm if rear_track_mm is not None else CarData.REAR_TRACK_MM
    total_downforce_N = total_downforce_N if total_downforce_N is not None else CarData.TOTAL_DOWNFORCE_N
    center_of_mass = center_of_mass if center_of_mass is not None else getattr(CarData, "CENTER_OF_MASS", 0.5)
    center_of_pressure = center_of_pressure if center_of_pressure is not None else getattr(CarData, "CENTER_OF_PRESSURE", 0.3801)

    if axle not in {"front", "rear"}:
        raise ValueError("axle must be either 'front' or 'rear'")

    g = 9.81

    if axle == "front":
        axle_mass_fraction = center_of_mass
        axle_track_mm = front_track_mm
        aero_axle_fraction = 1.0 - center_of_pressure
    else:
        axle_mass_fraction = 1.0 - center_of_mass
        axle_track_mm = rear_track_mm
        aero_axle_fraction = center_of_pressure

    static_load_on_one_wheel_n = mass_kg * g * axle_mass_fraction / 2.0
    longitudinal_load_transfer_n = (
        mass_kg * long_g * g * cg_height_mm / wheelbase_mm * axle_mass_fraction
    )
    lateral_load_transfer_n = (
        mass_kg * lateral_g * g * cg_height_mm / axle_track_mm * 0.5
    )
    aero_downforce_on_axle_n = total_downforce_N * aero_axle_fraction

    total_wheel_load_n = (
        static_load_on_one_wheel_n
        + longitudinal_load_transfer_n
        + lateral_load_transfer_n
        + aero_downforce_on_axle_n
    )

    return float(total_wheel_load_n)


if __name__ == "__main__":
    example_load = calculate_total_wheel_load(
        lateral_g=1.0,
        long_g=0.2,
        axle="front",
    )
    print(f"Example front wheel load: {example_load:.2f} N")
