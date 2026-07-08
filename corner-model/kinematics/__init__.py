"""
FSAE Kinematics package.

Coordinate system: SAE J670
  X → forward
  Y → left (driver's left)
  Z → up
  Ground plane at Z = 0
  All units: mm and degrees
"""

from .hardpoints import HP, WHEEL_RADIUS, TRACK_WIDTH, WHEELBASE, RACK_OFFSET_X
from .geometry import (
    normalize,
    angle_between,
    rotation_matrix,
    camber_angle,
    caster_angle,
    kpi_angle,
    toe_angle,
    scrub_radius,
    mechanical_trail,
    kingpin_axis,
)
from .suspension import solve_double_wishbone, run_travel_sweep, static_report
from .steering import ackermann_ideal, rack_steer_angle, ackermann_sweep

__all__ = [
    "HP", "WHEEL_RADIUS", "TRACK_WIDTH", "WHEELBASE", "RACK_OFFSET_X",
    "normalize", "angle_between", "rotation_matrix",
    "camber_angle", "caster_angle", "kpi_angle", "toe_angle",
    "scrub_radius", "mechanical_trail", "kingpin_axis",
    "solve_double_wishbone", "run_travel_sweep", "static_report",
    "ackermann_ideal", "rack_steer_angle", "ackermann_sweep",
]
