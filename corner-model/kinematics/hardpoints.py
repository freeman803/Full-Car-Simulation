"""
hardpoints.py — Left-front corner hardpoints at design (static) ride height.

THIS IS THE ONLY FILE YOU NEED TO EDIT WHEN UPDATING THE CAR.

Coordinate system: SAE J670
  X → forward  |  Y → left (driver's left)  |  Z → up
  Ground plane at Z = 0. All values in mm.

How to import from CAD:
  1. Export hardpoints in your CAD tool as XYZ coordinates.
  2. If your CAD origin is not at the contact patch, apply an offset so Z = 0
     sits at ground level. Only Z matters for scrub radius and trail calculations.
  3. Confirm Y is positive to the left (outboard points larger Y than chassis).
  4. Confirm X is positive forward (front of car).
"""

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# LEFT-FRONT CORNER HARDPOINTS  [X, Y, Z]  in mm
# ─────────────────────────────────────────────────────────────────────────────

HP: dict[str, np.ndarray] = {
    # Upper A-arm (UAA)
    "UAA_front_inboard": np.array([ 884.869,  247.493, 245.941]),   # chassis pickup (front)
    "UAA_rear_inboard":  np.array([ 617.550,  247.350, 259.202]),   # chassis pickup (rear)
    "UAA_outboard":      np.array([ 769.489, 542.608, 292.630]),   # upright upper ball joint

    # Lower A-arm (LAA)
    "LAA_front_inboard": np.array([ 926.852, 189.946,  87.317]),   # chassis pickup (front)
    "LAA_rear_inboard":  np.array([ 620.155, 189.937,  112.133]),   # chassis pickup (rear)
    "LAA_outboard":      np.array([ 777.991, 564.695,  113]),   # upright lower ball joint

    # Steering
    "tie_rod_inboard":   np.array([900.500, 208.360, 140.250]),   # rack end
    "tie_rod_outboard":  np.array([853.590, 550.000, 167.683]),   # upright steering knuckle

    # Wheel / contact patch
    "wheel_axis":        np.array([   771.5, 608.5, 203.2]),   # spindle point (on wheel axis)
    "wheel_center":      np.array([   771.5, 609.5, 203.2]),   # rim centre
    "contact_patch":     np.array([   771.5, 609.5,   0.0]),   # tyre contact (Z must be 0)

    # Rear corner hardpoints (Lotus sheet [x, y, z] -> [-x, y, z], same as front)
    "rear_UAA_front_inboard": np.array([-491.824, 283.290, 245.483]),
    "rear_UAA_rear_inboard":  np.array([-803.213, 283.475, 259.586]),
    "rear_UAA_outboard":      np.array([-794.356, 521.320, 292.0]),

    "rear_LAA_front_inboard": np.array([-514.431, 254.494, 104.239]),
    "rear_LAA_rear_inboard":  np.array([-769.457, 254.504, 103.012]),
    "rear_LAA_outboard":      np.array([-745.219, 536.571, 113.0]),

    "rear_pushrod_outboard":  np.array([-802.751,  483.811,  312.595]),
    "rear_pushrod_inboard":   np.array([-802.751,  342.604, 441.223]),

    "rear_tie_rod_outboard":  np.array([-795.219 , 536.573, 112.759]),
    "rear_tie_rod_inboard":   np.array([-795.182, 254.505, 102.888 ]),

    "rear_wheel_axis":        np.array([-771.5,   608.5,      203.2]),
    "rear_wheel_center":      np.array([-771.5,   609.5,      203.2]),
    "rear_contact_patch":     np.array([-771.5,   609.5,        0.0]),   # tyre contact (Z must be 0)

    "rear_bellcrank_pivot":   np.array([-802.751,  266.816, 366.308]),
    "rear_bellcrank_axis":    np.array([-803.751,  266.816, 366.308]),

    "rear_shock_chassis":     np.array([-802.751, 33.239,  362.805]),
    "rear_shock_bellcrank":   np.array([-802.751, 189.684, 445.585]),

    # Ball joint references — keep in sync with UAA_outboard / LAA_outboard
    "upper_BJ":          np.array([   735, 540, 292.63]),
    "lower_BJ":          np.array([  739.52, 559,  113]),
}

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CAR PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────

WHEEL_RADIUS  = 203    # mm  (16" OD tyre / 10" rim)
TRACK_WIDTH   = 1219.0   # mm  front track, centre-to-centre
WHEELBASE     = 1575.0   # mm
RACK_OFFSET_X = 86.64   # mm  rack centre relative to front axle (negative = behind axle)
CG_HEIGHT     = 313.0    # mm  centre of gravity height (used for anti-dive calculation)

# ─────────────────────────────────────────────────────────────────────────────
# PUSHROD  (lower A-arm outboard → bellcrank)
# ─────────────────────────────────────────────────────────────────────────────

HP["pushrod_outboard"] = np.array([  771.5, 507.788, 313.985])  # lower arm pickup
HP["pushrod_inboard"]  = np.array([  771.5, 261.864, 673.469])  # bellcrank input pivot

# ─────────────────────────────────────────────────────────────────────────────
# BELLCRANK / ROCKER
# ─────────────────────────────────────────────────────────────────────────────

HP["bellcrank_pivot"]       = np.array([  771.5, 218.464, 643.779])  # chassis bearing
HP["bellcrank_axis"]        = np.array([  770.5, 218.464, 643.779])  # 2nd rocker axis point
HP["bellcrank_pushrod_arm"] = np.array([  771.5, 261.864, 673.469])  # = pushrod_inboard
HP["bellcrank_damper_arm"]  = np.array([  771.5, 205.496, 690.132])  # spring-damper pickup

# ─────────────────────────────────────────────────────────────────────────────
# SPRING / DAMPER
# ─────────────────────────────────────────────────────────────────────────────

HP["damper_outboard"] = np.array([  771.5, 205.496, 690.132])  # bellcrank end
HP["damper_inboard"]  = np.array([  771.5, 39.856, 643.793])  # chassis top mount

# ─────────────────────────────────────────────────────────────────────────────
# SPRING / DAMPER RATES
# ─────────────────────────────────────────────────────────────────────────────

SPRING_RATE     = 39.403  # N/mm  spring rate at the damper
DAMPER_RATE     = 2.5    # N·s/mm  linear damping coefficient at the damper
UNSPRUNG_MASS   = 9.0    # kg    corner unsprung mass (wheel + upright + half-arms)
SPRUNG_MASS     = 53.75   # kg    corner sprung mass (quarter car)
TYRE_STIFFNESS  = 130.0  # N/mm  vertical tyre stiffness
