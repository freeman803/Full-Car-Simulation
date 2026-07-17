"""
Interactive Magic Formula tire curve visualizer.

Loads a .tir coefficient file and evaluates the Magic Formula steady-state
equations (pure + combined slip, with inflation-pressure effects). Supports
both MF-Tyre 6.1/6.2 files (FITTYP 61/62, with NOMPRES and PP* pressure
terms) and the older PAC2002 format (PROPERTY_FILE_FORMAT='PAC2002', no
pressure model). The 6.x equation set is a strict superset that reduces to
PAC2002 once the format-specific defaults are supplied on load.

    inputs  : tire pressure, FZ, slip angle, slip ratio, camber
    outputs : FX, FY, MX, MY, MZ

The user picks ONE input to sweep over a range, fixes the remaining four
inputs, and picks ONE output to plot against it (either can go on either
axis). The outputs are computed by the model, so they can never be fixed.

Usage:
    python tire_visualizer.py [path/to/file.tir]

User-facing units: pressure in psi, slip angle and camber in degrees,
forces in N, moments in N*m. Internally the model runs in Pa / radians
as required by the .tir file.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PSI_TO_PA = 6894.757
EPS = 1e-10

DEFAULT_TIR = Path(__file__).with_name("16inx18in_R20 1.tir")


def parse_tir(path: Path) -> dict[str, float]:
    """Flatten a .tir file into {COEFFICIENT: value}. Non-numeric entries
    (units, tire side, ...) are skipped; MF coefficient names are unique
    across sections so a flat dict is safe."""
    coeffs: dict[str, float] = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("$")[0].strip()
        if not line or line.startswith("[") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        try:
            coeffs[key.strip()] = float(value.strip())
        except ValueError:
            continue
    return coeffs


def _safe(x, eps=EPS):
    """Keep a denominator away from zero while preserving its sign."""
    return np.where(x >= 0, np.maximum(x, eps), np.minimum(x, -eps))


# FITTYP numeric switch -> human label, for files that use the [MODEL] code
# instead of the PROPERTY_FILE_FORMAT string.
_FITTYP_LABELS = {5: "MF5.2", 6: "MF5.2", 21: "MF6.1", 61: "MF6.1", 62: "MF6.2"}


def detect_format(path: Path) -> str:
    """Best-effort Magic Formula variant label for a .tir file.

    Prefers the PROPERTY_FILE_FORMAT string (e.g. 'PAC2002'); falls back to
    the numeric FITTYP switch (61 -> MF6.1, 62 -> MF6.2). Returns 'MF6.x'
    when neither is present, since the evaluator is a 6.1/6.2 superset."""
    fittyp = None
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("$")[0].strip()
        if "=" not in line or line.startswith("["):
            continue
        key, _, val = line.partition("=")
        key = key.strip().upper()
        val = val.strip().strip("'\"").strip()
        if key == "PROPERTY_FILE_FORMAT" and val:
            return val.upper()
        if key == "FITTYP":
            try:
                fittyp = int(float(val))
            except ValueError:
                pass
    if fittyp is not None:
        return _FITTYP_LABELS.get(fittyp, f"FITTYP {fittyp}")
    return "MF6.x"


class MF62Tire:
    """Steady-state Magic Formula tire (MF-Tyre 6.1/6.2 and PAC2002).

    The 6.1/6.2 equations (Pacejka 2012 eqs. 4.E1-4.E78) are evaluated for
    every file; PAC2002 files are handled by the same code because that
    equation set is a strict superset — the loader supplies the defaults a
    PAC2002 file omits (PKY4=2, no inflation-pressure model, LFZ0 alias).

    All methods accept scalars or numpy arrays (broadcasting) for
    fz [N], alpha [rad], kappa [-], press [Pa], and camber gamma [rad].
    """

    def __init__(self, tir_path: Path):
        self.path = Path(tir_path)
        self.p = parse_tir(self.path)
        self.format = detect_format(self.path)
        # The nominal-load scaling factor is lambda-Fz0. MF-Tyre files write
        # it LFZO (letter O); many PAC2002 files write LFZ0 (digit zero).
        # Accept either so the value is never silently dropped.
        if "LFZO" not in self.p and "LFZ0" in self.p:
            self.p["LFZO"] = self.p["LFZ0"]
        # PAC2002 / MF5.2-era files predate the MF6.1 camber-stiffness
        # coefficients PKY6/PKY7. They instead carry the camber horizontal
        # shift in PHY3 and expect load-linear rolling resistance (QSY7=1), so
        # forces() must pick the right camber & My form. Trust the format label
        # when it is known; otherwise fall back to a capability check (a real
        # MF6.x file always ships PKY6/PKY7).
        if self.format in ("PAC2002", "MF5.2"):
            self.legacy = True
        elif self.format in ("MF6.1", "MF6.2"):
            self.legacy = False
        else:
            self.legacy = "PKY6" not in self.p and "PKY7" not in self.p
        self.FZ0 = self.p["FNOMIN"]
        # PAC2002 has no inflation-pressure model: no NOMPRES and no PP*
        # coefficients. When absent, pressure is inert (every PP* term is 0),
        # so we only need a nonzero reference pressure to avoid dividing by
        # zero when forming dpi = (p - P0)/P0.
        nompres = self.p.get("NOMPRES")
        self.pressure_dependent = nompres is not None and nompres > 0
        self.P0 = nompres if self.pressure_dependent else 101325.0
        r0 = self.p.get("UNLOADED_RADIUS", 0.2)
        # A radius in meters is < ~1; some files store centimeters
        # (e.g. 19.58 -> 0.1958 m, a 16 in OD tire).
        self.R0 = r0 / 100.0 if r0 > 2.0 else r0

    def c(self, name: str, default: float = 0.0) -> float:
        return self.p.get(name, default)

    def forces(self, fz, alpha, kappa, press, gamma=0.0) -> dict:
        p = self.c
        fz = np.maximum(np.asarray(fz, dtype=float), 1.0)
        alpha = np.asarray(alpha, dtype=float)
        kappa = np.asarray(kappa, dtype=float)
        press = np.asarray(press, dtype=float)
        gamma = np.asarray(gamma, dtype=float)

        FZ0p = p("LFZO", 1) * self.FZ0
        dfz = (fz - FZ0p) / FZ0p
        dpi = (press - self.P0) / self.P0
        g2 = gamma * gamma

        # ---------------- pure longitudinal Fx0 ----------------
        Cx = p("PCX1") * p("LCX", 1)
        mux = ((p("PDX1") + p("PDX2") * dfz)
               * (1 + p("PPX3") * dpi + p("PPX4") * dpi**2)
               * (1 - p("PDX3") * g2) * p("LMUX", 1))
        Dx = mux * fz
        Kxk = (fz * (p("PKX1") + p("PKX2") * dfz) * np.exp(p("PKX3") * dfz)
               * (1 + p("PPX1") * dpi + p("PPX2") * dpi**2) * p("LKX", 1))
        SHx = (p("PHX1") + p("PHX2") * dfz) * p("LHX", 1)
        SVx = fz * (p("PVX1") + p("PVX2") * dfz) * p("LVX", 1) * p("LMUX", 1)
        kx = kappa + SHx
        Ex = np.minimum((p("PEX1") + p("PEX2") * dfz + p("PEX3") * dfz**2)
                        * (1 - p("PEX4") * np.sign(kx)) * p("LEX", 1), 1.0)
        Bx = Kxk / _safe(Cx * Dx)
        Fx0 = Dx * np.sin(Cx * np.arctan(
            Bx * kx - Ex * (Bx * kx - np.arctan(Bx * kx)))) + SVx

        # combined-slip weighting Gxa(alpha)
        Bxa = (p("RBX1") + p("RBX3") * g2) * np.cos(np.arctan(p("RBX2") * kappa)) * p("LXAL", 1)
        Cxa = p("RCX1")
        Exa = np.minimum(p("REX1") + p("REX2") * dfz, 1.0)
        SHxa = p("RHX1")
        a_s = alpha + SHxa
        Gxa0 = np.cos(Cxa * np.arctan(
            Bxa * SHxa - Exa * (Bxa * SHxa - np.arctan(Bxa * SHxa))))
        Gxa = np.cos(Cxa * np.arctan(
            Bxa * a_s - Exa * (Bxa * a_s - np.arctan(Bxa * a_s)))) / _safe(Gxa0)
        Gxa = np.maximum(Gxa, 0.0)
        Fx = Gxa * Fx0

        # ---------------- pure lateral Fy0 ----------------
        Cy = p("PCY1") * p("LCY", 1)
        muy = ((p("PDY1") + p("PDY2") * dfz)
               * (1 + p("PPY3") * dpi + p("PPY4") * dpi**2)
               * (1 - p("PDY3") * g2) * p("LMUY", 1))
        Dy = muy * fz
        # PKY4 governs the shape of Kya vs load; its physical default is 2
        # (PAC2002 hardcodes this factor and omits the coefficient). Default
        # to 2.0 so an absent PKY4 does not zero out the cornering stiffness.
        Kya = (p("PKY1") * FZ0p * (1 + p("PPY1") * dpi) * (1 - p("PKY3") * abs(gamma))
               * np.sin(p("PKY4", 2.0) * np.arctan(
                   fz / FZ0p / ((p("PKY2") + p("PKY5") * g2) * (1 + p("PPY2") * dpi))))
               * p("LKY", 1))
        Kya = _safe(Kya)
        Kyg0 = fz * (p("PKY6") + p("PKY7") * dfz) * (1 + p("PPY5") * dpi) * p("LKYC", 1)
        SVyg = fz * (p("PVY3") + p("PVY4") * dfz) * gamma * p("LKYC", 1) * p("LMUY", 1)
        SVy = fz * (p("PVY1") + p("PVY2") * dfz) * p("LVY", 1) * p("LMUY", 1) + SVyg
        if self.legacy:
            # PAC2002/MF5.2 carry the camber horizontal shift directly in PHY3
            # and do not use the MF6.x Kyg0/SVyg reformulation (no PKY6/PKY7).
            SHy = (p("PHY1") + p("PHY2") * dfz) * p("LHY", 1) + p("PHY3") * gamma
        else:
            SHy = (p("PHY1") + p("PHY2") * dfz) * p("LHY", 1) + (Kyg0 * gamma - SVyg) / Kya
        ay = alpha + SHy
        Ey = np.minimum((p("PEY1") + p("PEY2") * dfz)
                        * (1 + p("PEY5") * g2 - (p("PEY3") + p("PEY4") * gamma) * np.sign(ay))
                        * p("LEY", 1), 1.0)
        By = Kya / _safe(Cy * Dy)
        Fy0 = Dy * np.sin(Cy * np.arctan(
            By * ay - Ey * (By * ay - np.arctan(By * ay)))) + SVy

        # combined-slip weighting Gyk(kappa)
        Byk = (p("RBY1") + p("RBY4") * g2) * np.cos(np.arctan(p("RBY2") * (alpha - p("RBY3")))) * p("LYKA", 1)
        Cyk = p("RCY1")
        Eyk = np.minimum(p("REY1") + p("REY2") * dfz, 1.0)
        SHyk = p("RHY1") + p("RHY2") * dfz
        ks = kappa + SHyk
        DVyk = (muy * fz * (p("RVY1") + p("RVY2") * dfz + p("RVY3") * gamma)
                * np.cos(np.arctan(p("RVY4") * alpha)))
        SVyk = DVyk * np.sin(p("RVY5") * np.arctan(p("RVY6") * kappa)) * p("LVYKA", 1)
        Gyk0 = np.cos(Cyk * np.arctan(
            Byk * SHyk - Eyk * (Byk * SHyk - np.arctan(Byk * SHyk))))
        Gyk = np.cos(Cyk * np.arctan(
            Byk * ks - Eyk * (Byk * ks - np.arctan(Byk * ks)))) / _safe(Gyk0)
        Gyk = np.maximum(Gyk, 0.0)
        Fy = Gyk * Fy0 + SVyk

        # ---------------- overturning moment Mx ----------------
        fzr = fz / self.FZ0
        fyr = Fy / self.FZ0
        Mx = (self.R0 * fz * p("LMX", 1) * (
                p("QSX1") * p("LVMX", 1)
                - p("QSX2") * gamma * (1 + p("PPMX1") * dpi)
                + p("QSX3") * fyr
                + p("QSX4") * np.cos(p("QSX5") * np.arctan((p("QSX6") * fzr) ** 2))
                * np.sin(p("QSX7") * gamma + p("QSX8") * np.arctan(p("QSX9") * fyr))
                + p("QSX10") * np.arctan(p("QSX11") * fzr) * gamma)
              + self.R0 * Fy * p("LMX", 1) * (p("QSX13") + p("QSX14") * abs(gamma))
              - self.R0 * fz * p("LMX", 1) * p("QSX12") * gamma * abs(gamma))

        # ---------------- rolling resistance My ----------------
        # Vx/V0 taken as 1 (steady state at reference speed).
        My = (-self.R0 * self.FZ0 * p("LMY", 1)
              * (p("QSY1") + p("QSY2") * Fx / self.FZ0 + p("QSY3") + p("QSY4")
                 + (p("QSY5") + p("QSY6") * fzr) * g2)
              # PAC2002 My is linear in load; an absent QSY7 must default to 1,
              # not 0 (fzr**0 would make My load-independent).
              * fzr ** p("QSY7", 1.0 if self.legacy else 0.0)
              * (press / self.P0) ** p("QSY8"))
        My = My * np.ones_like(Fx)

        # ---------------- aligning moment Mz ----------------
        # pneumatic trail t
        SHt = p("QHZ1") + p("QHZ2") * dfz + (p("QHZ3") + p("QHZ4") * dfz) * gamma
        at = alpha + SHt
        Bt = ((p("QBZ1") + p("QBZ2") * dfz + p("QBZ3") * dfz**2)
              * (1 + p("QBZ4") * gamma + p("QBZ5") * abs(gamma))
              * p("LKY", 1) / p("LMUY", 1))
        Ct = p("QCZ1")
        Dt = (fz * (self.R0 / FZ0p) * (p("QDZ1") + p("QDZ2") * dfz)
              * (1 - p("PPZ1") * dpi)
              * (1 + p("QDZ3") * abs(gamma) + p("QDZ4") * g2) * p("LTR", 1))
        # residual moment Mzr
        SHf = SHy + SVy / Kya
        ar = alpha + SHf
        Br = p("QBZ9") * p("LKY", 1) / p("LMUY", 1) + p("QBZ10") * By * Cy
        Dr = (fz * self.R0 * ((p("QDZ6") + p("QDZ7") * dfz) * p("LRES", 1)
                              + (p("QDZ8") + p("QDZ9") * dfz) * (1 + p("PPZ2") * dpi) * gamma * p("LKZC", 1)
                              + (p("QDZ10") + p("QDZ11") * dfz) * gamma * abs(gamma) * p("LKZC", 1))
              * p("LMUY", 1) * np.cos(alpha))
        # equivalent slip angles fold kappa into the trail/residual curves
        Kratio = Kxk / Kya
        at_eq = np.sqrt(at**2 + Kratio**2 * kappa**2) * np.sign(at)
        ar_eq = np.sqrt(ar**2 + Kratio**2 * kappa**2) * np.sign(ar)
        Et = np.minimum((p("QEZ1") + p("QEZ2") * dfz + p("QEZ3") * dfz**2)
                        * (1 + (p("QEZ4") + p("QEZ5") * gamma)
                           * (2 / np.pi) * np.arctan(Bt * Ct * at)), 1.0)
        t = Dt * np.cos(Ct * np.arctan(
            Bt * at_eq - Et * (Bt * at_eq - np.arctan(Bt * at_eq)))) * np.cos(alpha)
        Mzr = Dr * np.cos(np.arctan(Br * ar_eq))
        Fy_no_svk = Gyk * Fy0
        s = (self.R0 * (p("SSZ1") + p("SSZ2") * (Fy / FZ0p)
                        + (p("SSZ3") + p("SSZ4") * dfz) * gamma) * p("LS", 1))
        Mz = -t * Fy_no_svk + Mzr + s * Fx

        return {"fx": Fx, "fy": Fy, "mx": Mx, "my": My, "mz": Mz}


# ---------------------------------------------------------------------------
# Interactive CLI
# ---------------------------------------------------------------------------

# key, label, unit, kind
PARAMS = [
    ("pressure", "Tire pressure", "psi", "input"),
    ("fz", "FZ  (vertical load)", "N", "input"),
    ("sa", "Slip angle", "deg", "input"),
    ("sr", "Slip ratio", "-", "input"),
    ("camber", "Camber (inclination angle)", "deg", "input"),
    ("fx", "FX  (longitudinal force)", "N", "output"),
    ("fy", "FY  (lateral force)", "N", "output"),
    ("mx", "MX  (overturning moment)", "N*m", "output"),
    ("my", "MY  (rolling resistance moment)", "N*m", "output"),
    ("mz", "MZ  (aligning moment)", "N*m", "output"),
]
KEY_TO_PARAM = {key: (key, label, unit, kind) for key, label, unit, kind in PARAMS}
INPUT_KEYS = [k for k, _, _, kind in PARAMS if kind == "input"]
OUTPUT_KEYS = [k for k, _, _, kind in PARAMS if kind == "output"]

FIXED_DEFAULTS = {"pressure": None, "fz": None, "sa": 0.0, "sr": 0.0, "camber": 0.0}  # None -> from .tir
SWEEP_DEFAULTS = {
    "pressure": (8.0, 20.0),
    "fz": (100.0, 1500.0),
    "sa": (-12.0, 12.0),
    "sr": (-0.2, 0.2),
    "camber": (-4.0, 4.0),
}


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        print("\nNo more input - exiting.")
        sys.exit(1)


def ask_float(prompt: str, default: float) -> float:
    while True:
        raw = ask(f"{prompt} [{default:g}]: ")
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            print("  Please enter a number.")


def choose_key(keys: list[str], heading: str, prompt: str) -> str:
    """Show a numbered menu of parameter keys and return the chosen key."""
    print(f"\n{heading}")
    for i, key in enumerate(keys, start=1):
        _, label, unit, _ = KEY_TO_PARAM[key]
        print(f"  {i}. {label:<33} [{unit}]")
    while True:
        raw = ask(f"{prompt} (1-{len(keys)}): ")
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            return keys[int(raw) - 1]
        print(f"  Enter a number between 1 and {len(keys)}.")


def main() -> None:
    tir_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TIR
    if not tir_path.exists():
        print(f"Tire file not found: {tir_path}")
        sys.exit(1)

    tire = MF62Tire(tir_path)
    nompres_psi = tire.P0 / PSI_TO_PA

    print("=" * 68)
    print("Magic Formula tire curve visualizer")
    print(f"  Tire file       : {tir_path.name}")
    print(f"  Model format    : {tire.format}")
    print(f"  Nominal load    : {tire.FZ0:g} N")
    if tire.pressure_dependent:
        print(f"  Nominal pressure: {nompres_psi:.1f} psi ({tire.P0:g} Pa)")
    else:
        print("  Nominal pressure: n/a (no inflation-pressure model)")
    print(f"  Unloaded radius : {tire.R0:.4f} m")
    print("=" * 68)

    swept_key = choose_key(
        INPUT_KEYS,
        "Model inputs:",
        "Which input should be SWEPT along an axis? The other four get fixed values",
    )
    output_key = choose_key(
        OUTPUT_KEYS,
        "Model outputs (computed from the inputs):",
        "Which output should be plotted against it?",
    )

    print("\nEnter values for the fixed inputs (press Enter for the default):")
    values: dict[str, float] = {}
    for key in INPUT_KEYS:
        if key == swept_key:
            continue
        _, label, unit, _ = KEY_TO_PARAM[key]
        default = FIXED_DEFAULTS[key]
        if default is None:
            default = nompres_psi if key == "pressure" else tire.FZ0
        values[key] = ask_float(f"  {label} [{unit}]", default)

    # axis assignment
    k1, k2 = swept_key, output_key
    print(f"\nAxes: 1. {KEY_TO_PARAM[k1][1]}   2. {KEY_TO_PARAM[k2][1]}")
    while True:
        raw = ask("Which one goes on the X axis? (1/2) [1]: ") or "1"
        if raw in ("1", "2"):
            break
        print("  Enter 1 or 2.")
    x_key = k1 if raw == "1" else k2
    y_key = k2 if raw == "1" else k1

    if output_key == "my" and all(tire.c(f"QSY{i}") == 0.0 for i in range(1, 9)):
        print("\nWarning: every rolling-resistance coefficient (QSY1-QSY8) in this .tir")
        print("is zero, so MY will be identically 0 across the sweep.")

    # sweep range for the free input
    _, s_label, s_unit, _ = KEY_TO_PARAM[swept_key]
    lo_d, hi_d = SWEEP_DEFAULTS[swept_key]
    print(f"\nSweep range for {s_label} [{s_unit}]:")
    lo = ask_float("  min", lo_d)
    hi = ask_float("  max", hi_d)
    n = int(ask_float("  number of points", 300))
    sweep = np.linspace(lo, hi, max(n, 2))
    values[swept_key] = sweep

    # evaluate the model (convert UI units -> model units)
    out = tire.forces(
        fz=values["fz"],
        alpha=np.deg2rad(values["sa"]),
        kappa=values["sr"],
        press=values["pressure"] * PSI_TO_PA,
        gamma=np.deg2rad(values["camber"]),
    )

    axis_data = {swept_key: sweep, output_key: out[output_key]}
    x, y = axis_data[x_key], axis_data[y_key]

    _, x_label, x_unit, _ = KEY_TO_PARAM[x_key]
    _, y_label, y_unit, _ = KEY_TO_PARAM[y_key]
    fixed_inputs_desc = ", ".join(
        f"{KEY_TO_PARAM[k][1].split('(')[0].strip()} = {values[k]:g} {KEY_TO_PARAM[k][2]}"
        for k in INPUT_KEYS if k != swept_key
    )

    print(f"\nPlotting {y_label} vs {x_label}  ({fixed_inputs_desc})")
    yv = out[output_key]
    print(f"  {KEY_TO_PARAM[output_key][1]} range over sweep: "
          f"{yv.min():.2f} to {yv.max():.2f} {KEY_TO_PARAM[output_key][2]}")

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(x, y, lw=2, color="tab:blue")
    ax.set_xlabel(f"{x_label} [{x_unit}]")
    ax.set_ylabel(f"{y_label} [{y_unit}]")
    ax.set_title(f"{tir_path.stem}\n{y_label} vs {x_label}   |   {fixed_inputs_desc}",
                 fontsize=10)
    ax.grid(True, alpha=0.4)
    ax.axhline(0, color="gray", lw=0.8)
    ax.axvline(0, color="gray", lw=0.8)
    fig.tight_layout()

    out_png = tir_path.parent / f"plot_{y_key}_vs_{x_key}.png"
    fig.savefig(out_png, dpi=150)
    print(f"  Saved plot to {out_png}")
    plt.show()


if __name__ == "__main__":
    main()
