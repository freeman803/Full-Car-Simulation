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
    "UAA_front_inboard": np.array([ 850.18,  246.48, 270.0]),   # chassis pickup (front)
    "UAA_rear_inboard":  np.array([ 590.54,  246.48, 270.0]),   # chassis pickup (rear)
    "UAA_outboard":      np.array([ 735, 540, 292.63]),   # upright upper ball joint

    # Lower A-arm (LAA)
    "LAA_front_inboard": np.array([ 890.24,  192.24,  105.88]),   # chassis pickup (front)
    "LAA_rear_inboard":  np.array([ 590.54,  192.24,  105.88]),   # chassis pickup (rear)
    "LAA_outboard":      np.array([   739.52, 559,  113]),   # upright lower ball joint

    # Steering
    "tie_rod_inboard":   np.array([830, 208.74, 154.64]),   # rack end
    "tie_rod_outboard":  np.array([812.98, 553.25, 167.32]),   # upright steering knuckle

    # Wheel / contact patch
    "wheel_center":      np.array([   731, 609.5, 165.1]),   # rim centre
    "contact_patch":     np.array([   731, 609.5,   0.0]),   # tyre contact (Z must be 0)

    # Rear corner hardpoints
    "rear_LAA_front_inboard": np.array([ 256.8153, 487.7956, -277.8588]),
    "rear_LAA_rear_inboard":  np.array([ 256.8153, 832.5374, -277.8588]),
    "rear_LAA_outboard":      np.array([   292.00, 830.9, -510.41]),

    "rear_UAA_front_inboard": np.array([ 105.1149, 528.7743, -239.4689]),
    "rear_UAA_rear_inboard":  np.array([ 105.1149, 795.1525, -239.4689]),
    "rear_UAA_outboard":      np.array([   118.00, 783.1199, -523.2056]),

    "rear_pushrod_outboard":  np.array([ 302.015, 830.9, -484.315]),
    "rear_pushrod_inboard":   np.array([ 432.9636, 830.9, -351.75446]),

    "rear_tie_rod_outboard":  np.array([ 118.00, 832.4617, -522.95]),
    "rear_tie_rod_inboard":   np.array([ 105.1149, 832.4617, -239.4689]),

    "rear_wheel_axis":        np.array([ 203.2, 812.44, -585.2]),
    "rear_wheel_center":      np.array([ 203.2, 812.44, -584.2]),

    "rear_bellcrank_pivot":   np.array([ 380.32, 830.9, -299.7506]),
    "rear_bellcrank_axis":    np.array([ 380.32, 831.9, -299.7506]),

    "rear_shock_chassis":     np.array([ 370.2231, 830.9, -98.2623]),
    "rear_shock_bellcrank":   np.array([ 462.82355, 830.9, -249.10215]),

    # Ball joint references — keep in sync with UAA_outboard / LAA_outboard
    "upper_BJ":          np.array([   735, 540, 292.63]),
    "lower_BJ":          np.array([  739.52, 559,  113]),
}

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CAR PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────

WHEEL_RADIUS  = 203    # mm  (18" OD tyre / 10" rim)
TRACK_WIDTH   = 1219.0   # mm  front track, centre-to-centre
WHEELBASE     = 1543.0   # mm
RACK_OFFSET_X = 86.64   # mm  rack centre relative to front axle (negative = behind axle)
CG_HEIGHT     = 280.0    # mm  centre of gravity height (used for anti-dive calculation)

# ─────────────────────────────────────────────────────────────────────────────
# PUSHROD  (lower A-arm outboard → bellcrank)
# ─────────────────────────────────────────────────────────────────────────────

HP["pushrod_outboard"] = np.array([  743.36, 517.8, 139.34])  # lower arm pickup
HP["pushrod_inboard"]  = np.array([  743.36, 250, 687])  # bellcrank input pivot

# ─────────────────────────────────────────────────────────────────────────────
# BELLCRANK / ROCKER
# ─────────────────────────────────────────────────────────────────────────────

HP["bellcrank_pivot"]       = np.array([  743.36, 208.32, 653.19])  # chassis bearing
HP["bellcrank_pushrod_arm"] = np.array([  743.36, 250, 687])  # = pushrod_inboard
HP["bellcrank_damper_arm"]  = np.array([  743.36,  194.82, 706.77])  # spring-damper pickup

# ─────────────────────────────────────────────────────────────────────────────
# SPRING / DAMPER
# ─────────────────────────────────────────────────────────────────────────────

HP["damper_outboard"] = np.array([  743.36,  194.82, 706.77])  # bellcrank end
HP["damper_inboard"]  = np.array([  743.36,  25.78, 675])  # chassis top mount

# ─────────────────────────────────────────────────────────────────────────────
# SPRING / DAMPER RATES
# ─────────────────────────────────────────────────────────────────────────────

SPRING_RATE     = 39.403  # N/mm  spring rate at the damper
DAMPER_RATE     = 2.5    # N·s/mm  linear damping coefficient at the damper
UNSPRUNG_MASS   = 8.0    # kg    corner unsprung mass (wheel + upright + half-arms)
SPRUNG_MASS     = 53.75   # kg    corner sprung mass (quarter car)
TYRE_STIFFNESS  = 130.0  # N/mm  vertical tyre stiffness
