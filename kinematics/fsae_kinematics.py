# ------------------------------------------------------------
# Force GUI backend so plots appear in VS Code on Windows
# ------------------------------------------------------------
import matplotlib
matplotlib.use("TkAgg")

# ------------------------------------------------------------
# Imports
# ------------------------------------------------------------
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.optimize import fsolve
from mpl_toolkits.mplot3d import Axes3D

# ------------------------------------------------------------
# Plot styling
# ------------------------------------------------------------
plt.rcParams.update({
    'figure.facecolor': '#0f0f0f',
    'axes.facecolor':   '#1a1a1a',
    'axes.edgecolor':   '#444',
    'axes.labelcolor':  '#eee',
    'xtick.color':      '#aaa',
    'ytick.color':      '#aaa',
    'text.color':       '#eee',
    'grid.color':       '#333',
    'grid.linestyle':   '--',
    'grid.alpha':       0.5,
    'legend.facecolor': '#222',
    'legend.edgecolor': '#555',
    'font.family':      'monospace',
})

ACCENT = '#e8b84b'
BLUE   = '#4b9fe8'
GREEN  = '#4be87a'
RED    = '#e84b4b'

print("Environment ready — GUI backend active")

# ------------------------------------------------------------
# HARDPOINTS
# ------------------------------------------------------------
HP = {
    'UAA_front_inboard':  np.array([ 850.18,  246.48, 270.0]),
    'UAA_rear_inboard':   np.array([ 590.54,  246.48, 270.0]),
    'UAA_outboard':       np.array([ 735, 540, 292.63]),

    'LAA_front_inboard':  np.array([ 890.24,  192.24,  105.88]),
    'LAA_rear_inboard':   np.array([ 590.54,  192.24,  105.88]),
    'LAA_outboard':       np.array([   739.52, 559,  113]),

    'tie_rod_inboard':    np.array([830, 208.74, 154.64]),
    'tie_rod_outboard':   np.array([812.98, 553.25, 167.32]),

    'wheel_center':       np.array([   731, 609.5, 165.1]),
    'contact_patch':      np.array([   731, 609.5,   0.0]),

    'upper_BJ':           np.array([   735, 540, 292.63]),
    'lower_BJ':           np.array([  739.52, 559,  113]),
}

WHEELBASE = 1543
TRACK_WIDTH = 1219.0

# ------------------------------------------------------------
# Geometry utilities
# ------------------------------------------------------------
def normalize(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-10 else v

def angle_between(a, b, degrees=True):
    cos_theta = np.clip(np.dot(normalize(a), normalize(b)), -1, 1)
    angle = np.arccos(cos_theta)
    return np.degrees(angle) if degrees else angle

def camber_angle(upper_bj, lower_bj):
    kp = upper_bj - lower_bj
    kp_yz = np.array([0, kp[1], kp[2]])
    vertical = np.array([0, 0, 1])
    angle = angle_between(kp_yz, vertical)
    sign = np.sign(kp[1])
    return sign * angle

def caster_angle(upper_bj, lower_bj):
    kp = upper_bj - lower_bj
    kp_xz = np.array([kp[0], 0, kp[2]])
    vertical = np.array([0, 0, 1])
    angle = angle_between(kp_xz, vertical)
    sign = -np.sign(kp[0])
    return sign * angle

def kpi_angle(upper_bj, lower_bj):
    return abs(camber_angle(upper_bj, lower_bj))

def toe_angle(tie_rod_inboard, tie_rod_outboard, wheel_center):
    tr_vec = tie_rod_outboard - tie_rod_inboard
    tr_xy = np.array([tr_vec[0], tr_vec[1], 0])
    lateral = np.array([0, 1, 0])
    angle = angle_between(tr_xy, lateral)
    sign = -np.sign(tr_vec[0])
    return sign * angle

def scrub_radius(upper_bj, lower_bj, contact_patch, wheel_center):
    kp = upper_bj - lower_bj
    if abs(kp[2]) < 1e-10:
        return None
    t = -lower_bj[2] / kp[2]
    ground_intercept = lower_bj + t * kp
    return contact_patch[1] - ground_intercept[1]

def mechanical_trail(upper_bj, lower_bj, contact_patch):
    kp = upper_bj - lower_bj
    if abs(kp[2]) < 1e-10:
        return None
    t = -lower_bj[2] / kp[2]
    ground_intercept = lower_bj + t * kp
    return contact_patch[0] - ground_intercept[0]

# ------------------------------------------------------------
# Bump/droop solver
# ------------------------------------------------------------
def solve_double_wishbone(z_travel, hp):
    UAA_mid = 0.5 * (hp['UAA_front_inboard'] + hp['UAA_rear_inboard'])
    LAA_mid = 0.5 * (hp['LAA_front_inboard'] + hp['LAA_rear_inboard'])

    r_upper = np.linalg.norm(hp['upper_BJ'] - UAA_mid)
    r_lower = np.linalg.norm(hp['lower_BJ'] - LAA_mid)

    def arm_bj_position(pivot, static_bj, r_arm, z_offset):
        target_z = static_bj[2] + z_offset
        dz = target_z - pivot[2]
        dy_sq = r_arm**2 - dz**2
        dy = np.sqrt(max(dy_sq, 0))
        new_y = pivot[1] + dy
        return np.array([static_bj[0], new_y, target_z])

    new_UBJ = arm_bj_position(UAA_mid, hp['upper_BJ'], r_upper, z_travel)
    new_LBJ = arm_bj_position(LAA_mid, hp['lower_BJ'], r_lower, z_travel)

    tr_in = hp['tie_rod_inboard']
    tr_out = hp['tie_rod_outboard']
    tr_len = np.linalg.norm(tr_out - tr_in)
    tr_target_z = tr_out[2] + z_travel
    dz_tr = tr_target_z - tr_in[2]
    dy_tr_sq = tr_len**2 - dz_tr**2 - (tr_out[0] - tr_in[0])**2
    dy_tr = np.sqrt(max(dy_tr_sq, 0))
    new_TRO = np.array([tr_out[0], tr_in[1] + dy_tr, tr_target_z])

    new_WC = hp['wheel_center'].copy()
    new_WC[1] = new_LBJ[1] + (hp['wheel_center'][1] - hp['lower_BJ'][1])
    new_WC[2] = hp['wheel_center'][2] + z_travel
    new_CP = np.array([new_WC[0], new_WC[1], 0.0])

    return {
        'upper_BJ': new_UBJ,
        'lower_BJ': new_LBJ,
        'tie_rod_inboard': hp['tie_rod_inboard'],
        'tie_rod_outboard': new_TRO,
        'wheel_center': new_WC,
        'contact_patch': new_CP,
    }

# ------------------------------------------------------------
# Sweep
# ------------------------------------------------------------
travel_range = np.linspace(-40, 40, 81)
results = []

for z in travel_range:
    s = solve_double_wishbone(z, HP)
    ub, lb = s['upper_BJ'], s['lower_BJ']
    results.append({
        'travel_mm': z,
        'camber_deg': camber_angle(ub, lb),
        'caster_deg': caster_angle(ub, lb),
        'kpi_deg': kpi_angle(ub, lb),
        'toe_deg': toe_angle(s['tie_rod_inboard'], s['tie_rod_outboard'], s['wheel_center']),
        'scrub_mm': scrub_radius(ub, lb, s['contact_patch'], s['wheel_center']),
        'trail_mm': mechanical_trail(ub, lb, s['contact_patch']),
        'track_mm': 2 * s['wheel_center'][1],
    })

df = pd.DataFrame(results)
df['track_change_mm'] = df['track_mm'] - df.loc[df['travel_mm']==0, 'track_mm'].values[0]

# ------------------------------------------------------------
# Plot — Wheel Travel Kinematics
# ------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(16, 9))
fig.suptitle("FSAE Corner — Wheel Travel Kinematics", fontsize=14, color=ACCENT)

plots = [
    ('camber_deg', 'Camber (°)', ACCENT, axes[0,0]),
    ('caster_deg', 'Caster (°)', BLUE,   axes[0,1]),
    ('kpi_deg',    'KPI (°)',    GREEN,  axes[0,2]),
    ('toe_deg',    'Toe (°)',    RED,    axes[1,0]),
    ('scrub_mm',   'Scrub (mm)', ACCENT, axes[1,1]),
    ('track_change_mm', 'Track Change (mm)', BLUE, axes[1,2]),
]

for col, ylabel, color, ax in plots:
    ax.plot(df['travel_mm'], df[col], color=color, linewidth=2)
    ax.axhline(0, color='#555', linestyle='--')
    ax.axvline(0, color='#555', linestyle='--')
    ax.set_xlabel("Wheel Travel (mm)")
    ax.set_ylabel(ylabel)
    ax.set_title(ylabel, color=color)
    ax.grid(True)

plt.tight_layout()
plt.show()
