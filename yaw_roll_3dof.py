"""
3-DOF Yaw-Roll Bicycle Model with Lateral Load Transfer (FSAE)
================================================================
DOFs  : lateral, yaw, roll
States: x = [vy, r, phi, p]   (lat. velocity, yaw rate, roll angle, roll rate)
Tires : MF6.1 pure lateral (from 16inx18in_R20_2.tir), load-sensitive

The point of this model: lateral load transfer + tire load sensitivity
creates a REAL understeer gradient that responds to setup (roll stiffness
distribution), unlike the 2-DOF model where a=b & equal C gave Kus = 0.

Equations of motion (phi positive = roll toward outside of a left turn):
  m (vy_dot + Vx r) - ms hs phi_dd            = Fyf + Fyr
  Iz r_dot                                     = a Fyf - b Fyr
  Ixs phi_dd - ms hs (vy_dot + Vx r)           = (ms g hs - Kphi) phi - Cphi p

Per-side load transfer on axle i (outer gains, inner loses):
  dFz_i = (Kphi_i*phi + Cphi_i*p)/t_i  +  ms_i*ay*zRC_i/t_i
          \\_____ elastic (springs/ARB) ____/   \\__ geometric (roll center) __/
"""

import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace


# ------------------- Vehicle parameters -------------------
veh = SimpleNamespace()
veh.m = 296.0       # total mass [kg]
veh.Iz = 250.0       # yaw inertia [kg m^2]
veh.a = 0.7715      # CG to front axle [m]
veh.b = 0.7715      # CG to rear axle [m]
veh.L = veh.a + veh.b

# Roll model
veh.ms = 256.0        # sprung mass [kg] (unsprung folded in - simplification)
veh.Ixs = 120.0        # sprung roll inertia about roll axis [kg m^2]
veh.tf = 1.219       # front track [m]
veh.tr = 1.168       # rear track [m]
veh.hcg = 0.313       # CG height [m]
veh.zRCf = 0.01        # front roll center height [m]
veh.zRCr = 0.014       # rear roll center height [m]
veh.Kphi = 25000.0     # TOTAL roll stiffness [N m/rad] (~1.2 deg/g roll gradient)
veh.TLLTD = 0.55        # front share of roll stiffness (elastic LT distribution)
zeta_roll = 0.6         # roll mode damping ratio

# Derived roll quantities
veh.hs = veh.hcg - (veh.zRCf * veh.b + veh.zRCr * veh.a) / veh.L  # CG above roll axis
Kphi_eff = veh.Kphi - veh.ms * 9.81 * veh.hs                      # incl. gravity destiffening
veh.Cphi = 2 * zeta_roll * np.sqrt(Kphi_eff * veh.Ixs)            # roll damping [N m s/rad]

print(f'CG height above roll axis hs = {veh.hs:.3f} m')
print(f'Roll gradient = {(veh.ms*veh.hs*9.81/Kphi_eff)*180/np.pi:.2f} deg/g, '
      f'roll mode ~ {np.sqrt(Kphi_eff/veh.Ixs)/2/np.pi:.1f} Hz')


# ------------------- Tire model (MF6.1 lateral) -------------------
tire = SimpleNamespace()
tire.Fz0 = 667.0
tire.PCY1 = 1.5
tire.PDY1 = 2.4103
tire.PDY2 = -0.2076
tire.PEY1 = -0.0030776
tire.PEY2 = -0.0037438
tire.PEY3 = 11.8254
tire.PKY1 = -74.1177
tire.PKY2 = 3.8205
tire.PKY4 = 2.0
tire.PHY1 = 0.00020521
tire.PHY2 = 0.00037151
tire.PVY1 = 0.041439
tire.PVY2 = 0.014071
tire.LMUY = 0.65   # TTC belt -> asphalt friction scaling
tire.LKY = 1.0


def mf61_fy(alpha, Fz, tire):
    """MF6.1 pure lateral force (zero camber, nominal pressure), ISO sign
    convention as fitted (PKY1 < 0: positive slip -> negative Fy)."""
    Fz = max(Fz, 1.0)
    dfz = (Fz - tire.Fz0) / tire.Fz0
    SHy = tire.PHY1 + tire.PHY2 * dfz
    SVy = Fz * (tire.PVY1 + tire.PVY2 * dfz) * tire.LMUY
    aly = alpha + SHy
    Cy = tire.PCY1
    Dy = (tire.PDY1 + tire.PDY2 * dfz) * tire.LMUY * Fz
    Ey = min((tire.PEY1 + tire.PEY2 * dfz) * (1 - tire.PEY3 * np.sign(aly)), 1)
    By = (tire.PKY1 * tire.Fz0 * np.sin(tire.PKY4 * np.arctan(Fz / (tire.PKY2 * tire.Fz0)))
          * tire.LKY / (Cy * Dy))
    Fy = Dy * np.sin(Cy * np.arctan(By * aly - Ey * (By * aly - np.arctan(By * aly)))) + SVy
    return Fy


def mf61_kya(Fz, tire):
    """Cornering stiffness magnitude [N/rad per tire]"""
    return abs(tire.PKY1 * tire.Fz0 * np.sin(tire.PKY4 * np.arctan(Fz / (tire.PKY2 * tire.Fz0))) * tire.LKY)


Fz_st = veh.m * 9.81 / 4   # static per-tire load [N]
print(f'Static wheel load {Fz_st:.0f} N, axle stiffness {2*mf61_kya(Fz_st, tire):.0f} N/rad\n')


def fy_axle_lt(alpha, FzI, FzO, tire):
    """Axle lateral force, vehicle convention, inner + outer tire."""
    Fy = 0.0
    if FzI > 0:
        Fy += mf61_fy(-alpha, FzI, tire)
    Fy += mf61_fy(-alpha, FzO, tire)
    return Fy


def invert_axle_lt(F_req, FzI, FzO, tire):
    """Slip angle producing axle force F_req at loads (FzI, FzO).
    Returns None if F_req exceeds the axle peak."""
    gr = np.linspace(0, 0.35, 800)
    Fy = np.array([fy_axle_lt(al, FzI, FzO, tire) for al in gr])
    ipk = np.argmax(Fy)
    Fpk = Fy[ipk]
    if F_req > Fpk:
        return None
    lo, hi = 0.0, gr[ipk]
    for _ in range(55):
        mid = 0.5 * (lo + hi)
        if fy_axle_lt(mid, FzI, FzO, tire) < F_req:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def ss_corner(ay, R, TLLTD, veh, tire, Fz_st):
    """Steady-state cornering solution at lateral accel ay on radius R.
    Returns [delta, alpha_f, alpha_r, phi] or None if beyond grip limit."""
    g = 9.81
    Kphi_eff = veh.Kphi - veh.ms * g * veh.hs
    phi = veh.ms * veh.hs * ay / Kphi_eff
    Kf = TLLTD * veh.Kphi
    Kr = (1 - TLLTD) * veh.Kphi
    dFf = Kf * phi / veh.tf + veh.ms * (veh.b / veh.L) * ay * veh.zRCf / veh.tf
    dFr = Kr * phi / veh.tr + veh.ms * (veh.a / veh.L) * ay * veh.zRCr / veh.tr
    FzfI = max(Fz_st - dFf, 0)
    FzfO = 2 * Fz_st - FzfI
    FzrI = max(Fz_st - dFr, 0)
    FzrO = 2 * Fz_st - FzrI
    Ff_req = (veh.b / veh.L) * veh.m * ay
    Fr_req = (veh.a / veh.L) * veh.m * ay
    af = invert_axle_lt(Ff_req, FzfI, FzfO, tire)
    ar = invert_axle_lt(Fr_req, FzrI, FzrO, tire)
    if af is None or ar is None:
        return None
    Vx = np.sqrt(ay * R)
    r = Vx / R
    vy = veh.b * r - ar * Vx
    delta = af + (vy + veh.a * r) / Vx
    return np.array([delta, af, ar, phi])


def yawroll_deriv(x, delta, Vx, veh, tire, Fz_st, ay_prev):
    """State derivative of the 3-DOF yaw-roll model.
    x = [vy, r, phi, p, psi, X, Y]. ay_prev feeds the geometric load
    transfer term (explicit lag of one step; the term is small and smooth)."""
    g = 9.81
    vy, r, phi, p, psi = x[0], x[1], x[2], x[3], x[4]

    # Slip angles
    af = delta - (vy + veh.a * r) / Vx
    ar = -(vy - veh.b * r) / Vx

    # Load transfer (elastic from roll state, geometric from ay)
    Kf = veh.TLLTD * veh.Kphi
    Kr = (1 - veh.TLLTD) * veh.Kphi
    Cf = veh.TLLTD * veh.Cphi
    Cr = (1 - veh.TLLTD) * veh.Cphi
    dFf = (Kf * phi + Cf * p) / veh.tf + veh.ms * (veh.b / veh.L) * ay_prev * veh.zRCf / veh.tf
    dFr = (Kr * phi + Cr * p) / veh.tr + veh.ms * (veh.a / veh.L) * ay_prev * veh.zRCr / veh.tr

    # Axle forces with per-tire loads (sign-symmetric: use sign of slip angle)
    Fyf = fy_axle_lt(af, max(Fz_st - abs(dFf), 0), min(2 * Fz_st, Fz_st + abs(dFf)), tire)
    Fyr = fy_axle_lt(ar, max(Fz_st - abs(dFr), 0), min(2 * Fz_st, Fz_st + abs(dFr)), tire)

    # Mass matrix solve: unknowns [vy_dot; r_dot; phi_dd]
    M = np.array([
        [veh.m, 0, -veh.ms * veh.hs],
        [0, veh.Iz, 0],
        [-veh.ms * veh.hs, 0, veh.Ixs],
    ])
    rhs = np.array([
        Fyf + Fyr - veh.m * Vx * r,
        veh.a * Fyf - veh.b * Fyr,
        veh.ms * veh.hs * Vx * r + (veh.ms * g * veh.hs - veh.Kphi) * phi - veh.Cphi * p,
    ])
    sol = np.linalg.solve(M, rhs)

    ay = sol[0] + Vx * r
    xdot = np.array([
        sol[0], sol[1], p, sol[2], r,
        Vx * np.cos(psi) - vy * np.sin(psi),
        Vx * np.sin(psi) + vy * np.cos(psi),
    ])
    return xdot, ay, dFf, dFr


# ---------- TEST A: Constant radius, sweep roll stiffness split ----------
# Steady-state cornering on radius R. For each lateral g:
#   roll angle and load transfer follow directly from ay,
#   axle forces are fixed by statics (Fyf = b/L m ay, Fyr = a/L m ay),
#   invert the two-tire axle curve at transferred loads -> slip angles -> delta.
# Repeat for several TLLTD values to see the balance shift.

R = 9.125                                    # FSAE skidpad radius [m]
TLLTD_sweep = [0.40, 0.50, 0.55, 0.60, 0.70]
ay_g = np.linspace(0.1, 1.7, 80)             # lateral g candidates

fig1, ax1 = plt.subplots(num='Constant Radius - Roll Stiffness Split Sweep')
cols = plt.cm.tab10(np.linspace(0, 1, len(TLLTD_sweep)))
Kus_meas = np.full(len(TLLTD_sweep), np.nan)
aylim = np.full(len(TLLTD_sweep), np.nan)

for j, T in enumerate(TLLTD_sweep):
    d = np.full(ay_g.shape, np.nan)
    for i, ayg in enumerate(ay_g):
        out = ss_corner(ayg * 9.81, R, T, veh, tire, Fz_st)
        if out is None:
            aylim[j] = ayg
            break
        d[i] = out[0]
    ok = ~np.isnan(d)
    ax1.plot(ay_g[ok], d[ok] * 180 / np.pi, color=cols[j], linewidth=1.5,
              label=f'TLLTD = {T:.2f}')
    # gradient around 1.0 g
    d1 = ss_corner(0.9 * 9.81, R, T, veh, tire, Fz_st)
    d2 = ss_corner(1.1 * 9.81, R, T, veh, tire, Fz_st)
    if d1 is not None and d2 is not None:
        Kus_meas[j] = (d2[0] - d1[0]) / (0.2 * 9.81)

ax1.axhline(veh.L / R * 180 / np.pi, color='k', linestyle='--', label='_nolegend_')
ax1.text(ay_g[0], veh.L / R * 180 / np.pi, 'Ackermann', va='bottom')
ax1.grid(True)
ax1.set_xlabel('a_y [g]')
ax1.set_ylabel(r'$\delta$ [deg]')
ax1.set_title(f'Handling diagram vs roll stiffness distribution (R = {R:.3f} m)')
ax1.legend(loc='upper left')

fig2, ax2 = plt.subplots(num='Understeer Gradient vs TLLTD')
ax2.plot(TLLTD_sweep, Kus_meas * 9.81 * 180 / np.pi, 'bo-', linewidth=1.5)
ax2.axhline(0, color='k', linestyle='--')
ax2.grid(True)
ax2.set_xlabel('Front share of roll stiffness (TLLTD)')
ax2.set_ylabel(r'$K_{us}$ @ 1 g [deg/g]')
ax2.set_title(r'Balance tuning: roll stiffness split $\rightarrow$ understeer gradient')

for j, T in enumerate(TLLTD_sweep):
    print(f'TLLTD {T:.2f} : K_us = {Kus_meas[j]*9.81*180/np.pi:+6.3f} deg/g,  '
          f'grip limit ~ {aylim[j]:.2f} g')


# ---------- TEST B: Open-loop constant speed + constant steer ----------
# Time-domain 3-DOF simulation with nonlinear tires and dynamic load
# transfer. Constant Vx, constant delta, applied from straight running.

Vx_test = 10.0                    # [m/s]
delta_test = 6 * np.pi / 180      # [rad]
T_end, dt = 12.0, 0.001           # roll mode is ~5.5 Hz -> smaller dt than 2-DOF
t = np.arange(0, T_end + dt, dt)

x = np.zeros(7)                   # [vy; r; phi; p; psi; X; Y]
ay_prev = 0.0
log = np.zeros((len(t), 10))

for k in range(len(t)):
    xdot, ay, dFf, dFr = yawroll_deriv(x, delta_test, Vx_test, veh, tire, Fz_st, ay_prev)
    x = x + dt * xdot
    ay_prev = ay
    log[k, :] = [x[0], x[1], x[2], x[3], x[4], x[5], x[6], ay, dFf, dFr]

fig3, axes = plt.subplots(2, 3, num='3-DOF Open-Loop Constant Steer', figsize=(12, 7))

ax = axes[0, 0]
ax.plot(log[:, 5], log[:, 6], 'b')
ax.axis('equal')
ax.grid(True)
ax.set_xlabel('X [m]')
ax.set_ylabel('Y [m]')
ax.set_title('Path')

ax = axes[0, 1]
ax.plot(t, log[:, 1] * 180 / np.pi, 'b')
ax.grid(True)
ax.set_xlabel('t [s]')
ax.set_ylabel('r [deg/s]')
ax.set_title('Yaw rate')

ax = axes[0, 2]
ax.plot(t, log[:, 7] / 9.81, 'r')
ax.grid(True)
ax.set_xlabel('t [s]')
ax.set_ylabel('a_y [g]')
ax.set_title('Lateral acceleration')

ax = axes[1, 0]
ax.plot(t, log[:, 2] * 180 / np.pi, 'm')
ax.grid(True)
ax.set_xlabel('t [s]')
ax.set_ylabel(r'$\phi$ [deg]')
ax.set_title('Roll angle')

ax = axes[1, 1]
ax.plot(t, log[:, 8], 'b', label='front')
ax.plot(t, log[:, 9], 'r--', label='rear')
ax.grid(True)
ax.set_xlabel('t [s]')
ax.set_ylabel(r'$\Delta F_z$ per side [N]')
ax.set_title('Load transfer')
ax.legend(loc='lower right')

ax = axes[1, 2]
ax.plot(t, (Fz_st - log[:, 8]) / Fz_st * 100, 'b', label='front')
ax.plot(t, (Fz_st - log[:, 9]) / Fz_st * 100, 'r--', label='rear')
ax.grid(True)
ax.set_xlabel('t [s]')
ax.set_ylabel('Inner wheel load [% static]')
ax.set_title('Inner wheel loads (0% = wheel lift)')
ax.legend()

fig3.tight_layout()
plt.show()
