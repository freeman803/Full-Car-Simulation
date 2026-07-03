"""
quarter_car.py — 2-DOF quarter car model with variable motion ratio.

State vector:  x = [z_s, dz_s, z_u, dz_u]
  z_s   — sprung mass displacement (m, positive up)
  dz_s  — sprung mass velocity (m/s)
  z_u   — unsprung mass displacement (m, positive up)
  dz_u  — unsprung mass velocity (m/s)

Road input z_r(t) acts on the tyre spring (k_t).

Equations of motion (in mm / N / s):
  m_s * z_s'' = -k_w(z_u) * (z_s - z_u) - c_w(z_u) * (z_s' - z_u')
  m_u * z_u'' =  k_w(z_u) * (z_s - z_u) + c_w(z_u) * (z_s' - z_u')
               - k_t * (z_u - z_r)

where k_w and c_w are the wheel-rate spring and damping (motion-ratio corrected).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from .hardpoints import (
    SPRING_RATE,
    DAMPER_RATE,
    SPRUNG_MASS,
    UNSPRUNG_MASS,
    TYRE_STIFFNESS,
    HP,
)
from .rocker import effective_spring_rate, effective_damper_rate, motion_ratio_at


# ─────────────────────────────────────────────────────────────────────────────
# Road inputs
# ─────────────────────────────────────────────────────────────────────────────

def road_step(
    t: float,
    amplitude_mm: float = 20.0,
    t_start: float = 0.1,
) -> float:
    """
    Step bump input: road rises instantly by `amplitude_mm` at t = t_start.
    Models hitting a kerb or pothole edge.
    """
    return amplitude_mm if t >= t_start else 0.0


def road_sine(
    t: float,
    amplitude_mm: float = 15.0,
    frequency_hz: float = 2.0,
) -> float:
    """
    Sinusoidal road input at `frequency_hz` Hz with peak `amplitude_mm`.
    Models a washboard road or steady-state frequency sweep.
    """
    return amplitude_mm * np.sin(2.0 * np.pi * frequency_hz * t)


def road_combined(
    t: float,
    step_amp_mm: float = 20.0,
    step_t: float = 0.5,
    sine_amp_mm: float = 10.0,
    sine_freq_hz: float = 3.0,
) -> float:
    """Step followed by sinusoidal input — tests transient + steady-state."""
    return road_step(t, step_amp_mm, step_t) + road_sine(t, sine_amp_mm, sine_freq_hz)


# ─────────────────────────────────────────────────────────────────────────────
# ODE right-hand side
# ─────────────────────────────────────────────────────────────────────────────

def _ode_rhs(
    t: float,
    x: np.ndarray,
    road_fn,
    hp: dict,
    spring_rate: float,
    damper_rate: float,
    sprung_mass: float,
    unsprung_mass: float,
    tyre_stiffness: float,
) -> np.ndarray:
    """
    Quarter-car equations of motion.

    All spring/damper rates here are at the wheel centre (motion-ratio corrected).
    Motion ratio is evaluated at the current unsprung displacement so the
    non-linear MR variation is captured during simulation.
    """
    z_s, dz_s, z_u, dz_u = x
    z_r = road_fn(t)

    # Current wheel travel (unsprung displacement minus road input)
    wheel_travel_mm = z_u - z_r

    # Motion-ratio-corrected rates at current wheel position
    k_w = effective_spring_rate(hp, spring_rate, wheel_travel_mm)
    c_w = effective_damper_rate(hp, damper_rate, wheel_travel_mm)
    k_t = tyre_stiffness

    # Suspension force (spring + damper between sprung and unsprung)
    f_susp = k_w * (z_u - z_s) + c_w * (dz_u - dz_s)

    # Tyre force (tyre spring between unsprung and road)
    f_tyre = k_t * (z_r - z_u)

    # Equations of motion (mm, N, s — consistent units)
    # Force in N, mass in kg, displacement in mm → acceleration in mm/s²
    # N = kg·m/s² = kg·(mm/s²)·1e-3 → multiply by 1e3 to stay in mm/s²
    ddz_s = ( f_susp) / sprung_mass    * 1e-3   # mm/s² → /1e3 for N/mm consistency
    ddz_u = (-f_susp + f_tyre) / unsprung_mass * 1e-3

    return np.array([dz_s, ddz_s, dz_u, ddz_u])


# ─────────────────────────────────────────────────────────────────────────────
# Simulation entry points
# ─────────────────────────────────────────────────────────────────────────────

def simulate(
    road_fn,
    t_span: tuple[float, float] = (0.0, 2.0),
    t_eval: np.ndarray | None = None,
    hp: dict | None = None,
    spring_rate: float | None = None,
    damper_rate: float | None = None,
    sprung_mass: float | None = None,
    unsprung_mass: float | None = None,
    tyre_stiffness: float | None = None,
) -> pd.DataFrame:
    """
    Simulate the quarter-car response to a given road input function.

    Parameters
    ----------
    road_fn : callable(t) -> float
        Road displacement in mm as a function of time.
    t_span : (t0, tf)
        Start and end time in seconds.
    t_eval : array-like, optional
        Times at which to record output. Defaults to 500 points over t_span.
    hp : dict, optional
        Hardpoint dict for motion ratio lookup. Defaults to HP from hardpoints.py.
    spring_rate : float, optional
        Damper spring rate (N/mm). Defaults to SPRING_RATE.
    damper_rate : float, optional
        Linear damping coefficient (N·s/mm). Defaults to DAMPER_RATE.
    sprung_mass : float, optional
        Quarter sprung mass (kg). Defaults to SPRUNG_MASS.
    unsprung_mass : float, optional
        Unsprung mass (kg). Defaults to UNSPRUNG_MASS.
    tyre_stiffness : float, optional
        Tyre vertical stiffness (N/mm). Defaults to TYRE_STIFFNESS.

    Returns
    -------
    pd.DataFrame with columns:
        time_s, road_mm, z_sprung_mm, z_unsprung_mm,
        vel_sprung_mm_s, vel_unsprung_mm_s,
        susp_travel_mm, accel_sprung_g, wheel_rate_N_mm, motion_ratio
    """
    # Resolve defaults
    _hp   = hp             if hp             is not None else HP
    _ks   = spring_rate    if spring_rate    is not None else SPRING_RATE
    _cs   = damper_rate    if damper_rate    is not None else DAMPER_RATE
    _ms   = sprung_mass    if sprung_mass    is not None else SPRUNG_MASS
    _mu   = unsprung_mass  if unsprung_mass  is not None else UNSPRUNG_MASS
    _kt   = tyre_stiffness if tyre_stiffness is not None else TYRE_STIFFNESS

    if t_eval is None:
        t_eval = np.linspace(t_span[0], t_span[1], 500)

    x0 = np.zeros(4)  # start at rest, equilibrium

    def rhs_wrapper(t, x):
        return _ode_rhs(t, x, road_fn, _hp, _ks, _cs, _ms, _mu, _kt)

    sol = solve_ivp(
        fun=rhs_wrapper,
        t_span=t_span,
        y0=x0,
        t_eval=t_eval,
        method="RK45",
        rtol=1e-6,
        atol=1e-8,
    )

    t    = sol.t
    z_s  = sol.y[0]
    dz_s = sol.y[1]
    z_u  = sol.y[2]

    road   = np.array([road_fn(ti) for ti in t])
    susp   = z_u - z_s
    ddz_s  = np.gradient(dz_s, t)          # sprung acceleration (mm/s²)
    accel_g = ddz_s / 9806.65              # convert to g

    mr_arr = np.array([motion_ratio_at(float(z_u[i] - road[i]), _hp) for i in range(len(t))])
    kw_arr = _ks * mr_arr**2

    return pd.DataFrame({
        "time_s":            t,
        "road_mm":           road,
        "z_sprung_mm":       z_s,
        "z_unsprung_mm":     z_u,
        "vel_sprung_mm_s":   dz_s,
        "vel_unsprung_mm_s": sol.y[3],
        "susp_travel_mm":    susp,
        "accel_sprung_g":    accel_g,
        "wheel_rate_N_mm":   kw_arr,
        "motion_ratio":      mr_arr,
    })


def simulate_step(
    amplitude_mm: float = 20.0,
    t_span: tuple[float, float] = (0.0, 2.5),
    **kwargs,
) -> pd.DataFrame:
    """Convenience wrapper: simulate a step bump input."""
    return simulate(
        road_fn=lambda t: road_step(t, amplitude_mm),
        t_span=t_span,
        **kwargs,
    )


def simulate_sine(
    amplitude_mm: float = 15.0,
    frequency_hz: float = 2.0,
    t_span: tuple[float, float] = (0.0, 3.0),
    **kwargs,
) -> pd.DataFrame:
    """Convenience wrapper: simulate a sinusoidal road input."""
    return simulate(
        road_fn=lambda t: road_sine(t, amplitude_mm, frequency_hz),
        t_span=t_span,
        **kwargs,
    )


def frequency_sweep(
    frequencies: np.ndarray | None = None,
    amplitude_mm: float = 5.0,
    settle_periods: int = 5,
    hp: dict | None = None,
    spring_rate: float | None = None,
    damper_rate: float | None = None,
    sprung_mass: float | None = None,
    unsprung_mass: float | None = None,
    tyre_stiffness: float | None = None,
) -> pd.DataFrame:
    """
    Frequency response sweep: run sinusoidal simulation at each frequency,
    extract steady-state amplitude ratio (transmissibility).

    Returns DataFrame with:
        freq_hz, transmissibility (z_s_amp / road_amp), phase_deg
    """
    if frequencies is None:
        frequencies = np.logspace(np.log10(0.5), np.log10(20.0), 40)

    rows = []
    for freq in frequencies:
        period   = 1.0 / freq
        t_total  = settle_periods * period
        t_eval   = np.linspace(0, t_total, max(int(t_total * 200), 300))

        df = simulate_sine(
            amplitude_mm=amplitude_mm,
            frequency_hz=freq,
            t_span=(0.0, t_total),
            t_eval=t_eval,
            hp=hp,
            spring_rate=spring_rate,
            damper_rate=damper_rate,
            sprung_mass=sprung_mass,
            unsprung_mass=unsprung_mass,
            tyre_stiffness=tyre_stiffness,
        )

        # Use last 2 periods as steady-state
        ss_mask  = df["time_s"] >= t_total - 2 * period
        ss       = df[ss_mask]
        amp_road = amplitude_mm
        amp_body = (ss["z_sprung_mm"].max() - ss["z_sprung_mm"].min()) / 2.0
        trans    = amp_body / amp_road if amp_road > 0 else 0.0

        # Phase: time of first body peak vs road peak in steady state
        road_ss   = ss["road_mm"].values
        body_ss   = ss["z_sprung_mm"].values
        t_ss      = ss["time_s"].values
        road_peak = t_ss[np.argmax(road_ss)]
        body_peak = t_ss[np.argmax(body_ss)]
        phase_deg = ((body_peak - road_peak) * freq * 360.0) % 360.0
        if phase_deg > 180:
            phase_deg -= 360.0

        rows.append({
            "freq_hz":          freq,
            "transmissibility": trans,
            "phase_deg":        phase_deg,
        })

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Natural frequency helpers
# ─────────────────────────────────────────────────────────────────────────────

def natural_frequencies(
    hp: dict | None = None,
    spring_rate: float | None = None,
    damper_rate: float | None = None,
    sprung_mass: float | None = None,
    unsprung_mass: float | None = None,
    tyre_stiffness: float | None = None,
) -> dict:
    """
    Compute undamped natural frequencies and damping ratios at static ride height.

    Uses linearised 2-DOF model at z_travel = 0.

    Returns dict with:
        f_ride_hz      — sprung mass (ride) frequency
        f_wheel_hz     — unsprung mass (wheel hop) frequency
        zeta_ride      — sprung mass damping ratio
        zeta_wheel     — unsprung mass damping ratio
        k_wheel_N_mm   — effective wheel rate
        c_wheel_Ns_mm  — effective wheel damping
    """
    _hp  = hp             if hp             is not None else HP
    _ks  = spring_rate    if spring_rate    is not None else SPRING_RATE
    _cs  = damper_rate    if damper_rate    is not None else DAMPER_RATE
    _ms  = sprung_mass    if sprung_mass    is not None else SPRUNG_MASS
    _mu  = unsprung_mass  if unsprung_mass  is not None else UNSPRUNG_MASS
    _kt  = tyre_stiffness if tyre_stiffness is not None else TYRE_STIFFNESS

    k_w  = effective_spring_rate(_hp, _ks, z_travel=0.0)
    c_w  = effective_damper_rate(_hp, _cs, z_travel=0.0)

    # Convert N/mm → N/m for frequency calculation
    k_w_si = k_w  * 1e3   # N/m
    c_w_si = c_w  * 1e3   # N·s/m
    k_t_si = _kt  * 1e3   # N/m

    # Ride (sprung) mode: simplified decoupled
    omega_ride  = np.sqrt(k_w_si / _ms)
    f_ride      = omega_ride / (2 * np.pi)
    zeta_ride   = c_w_si / (2 * np.sqrt(k_w_si * _ms))

    # Wheel hop (unsprung) mode: simplified decoupled
    omega_wheel = np.sqrt((k_w_si + k_t_si) / _mu)
    f_wheel     = omega_wheel / (2 * np.pi)
    zeta_wheel  = c_w_si / (2 * np.sqrt((k_w_si + k_t_si) * _mu))

    result = {
        "f_ride_hz":      f_ride,
        "f_wheel_hz":     f_wheel,
        "zeta_ride":      zeta_ride,
        "zeta_wheel":     zeta_wheel,
        "k_wheel_N_mm":   k_w,
        "c_wheel_Ns_mm":  c_w,
    }

    sep = "─" * 50
    print(sep)
    print("  QUARTER CAR — NATURAL FREQUENCIES")
    print(sep)
    print(f"  Wheel rate (at static) : {k_w:.3f} N/mm")
    print(f"  Wheel damping          : {c_w:.4f} N·s/mm")
    print(sep)
    print(f"  Ride frequency         : {f_ride:.2f} Hz")
    print(f"  Ride damping ratio ζ   : {zeta_ride:.3f}  "
          f"({'underdamped' if zeta_ride < 1 else 'overdamped'})")
    print(sep)
    print(f"  Wheel hop frequency    : {f_wheel:.2f} Hz")
    print(f"  Wheel damping ratio ζ  : {zeta_wheel:.3f}")
    print(sep)

    return result
