"""
visualize_linkage_forces.py — 3D suspension geometry colored by linkage force.

Draws the six force-carrying linkages (A-arms, pushrod, tie rod) at their real
hardpoint locations. Tension is green, compression is red; darker/more
saturated means more force. Each member is labeled with its force in Newtons.

Run directly for a demo plot, or import plot_linkage_forces_3d() to use your
own conditions.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kinematics.hardpoints import HP
from kinematics.plots import apply_style, ACCENT, GREY
from Forces.linkages import LINKAGE_POINTS, resolve_hardpoint
from Forces.linkage_forces import calculate_linkage_forces

RESULTS_DIR = _ROOT / "results"

TENSION_CMAP = LinearSegmentedColormap.from_list("tension", ["#b9f6c4", "#0f7a33"])
COMPRESSION_CMAP = LinearSegmentedColormap.from_list("compression", ["#f8b4b4", "#8a0f0f"])

DISPLAY_NAMES = {
    "lower_aarm_fore": "Lower A-arm (fore)",
    "lower_aarm_aft":  "Lower A-arm (aft)",
    "upper_aarm_fore": "Upper A-arm (fore)",
    "upper_aarm_aft":  "Upper A-arm (aft)",
    "pushrod":         "Pushrod",
    "tierod":          "Tie rod",
}


def _member_color(force_n: float, sense: str, max_abs_force: float) -> tuple:
    magnitude = abs(force_n) / max_abs_force if max_abs_force > 1e-9 else 0.0
    cmap = TENSION_CMAP if sense == "tension" else COMPRESSION_CMAP
    return cmap(0.15 + 0.85 * magnitude)


def plot_linkage_forces_3d(
    forces: dict[str, dict[str, float]],
    axle: Literal["front", "rear"] = "front",
    hp: dict[str, np.ndarray] | None = None,
    subtitle: str | None = None,
) -> plt.Figure:
    """3D suspension geometry with each linkage colored/labeled by its force."""
    hp = hp if hp is not None else HP

    fig = plt.figure(figsize=(13, 9))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#0f0f0f")

    max_abs_force = max(abs(payload["force_N"]) for payload in forces.values())

    for name, (p1_name, p2_name) in LINKAGE_POINTS.items():
        p1 = resolve_hardpoint(p1_name, axle)
        p2 = resolve_hardpoint(p2_name, axle)
        payload = forces[name]
        force_n = payload["force_N"]
        sense = payload["sense"]
        color = _member_color(force_n, sense, max_abs_force)
        linewidth = 2.5 + 3.5 * (abs(force_n) / max_abs_force if max_abs_force > 1e-9 else 0.0)

        ax.plot(
            [p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
            color=color, lw=linewidth, solid_capstyle="round",
        )
        ax.scatter(*p1, color="white", s=25, zorder=5)
        ax.scatter(*p2, color="white", s=25, zorder=5)

        mid = (p1 + p2) / 2.0
        ax.text(
            mid[0], mid[1], mid[2],
            f"{DISPLAY_NAMES[name]}\n{force_n:+.0f} N",
            color="white", fontsize=8, ha="center", va="center", zorder=10,
            bbox=dict(facecolor="#000000", alpha=0.55, edgecolor="none", pad=1.5),
        )

    # Non-force-carrying context geometry, drawn faint for spatial reference.
    upper_bj = resolve_hardpoint("UAA_outboard", axle)
    lower_bj = resolve_hardpoint("LAA_outboard", axle)
    ax.plot(
        [upper_bj[0], lower_bj[0]], [upper_bj[1], lower_bj[1]], [upper_bj[2], lower_bj[2]],
        color=GREY, lw=1.5, ls="--", label="Kingpin axis",
    )

    xs = [resolve_hardpoint(p, axle)[0] for pair in LINKAGE_POINTS.values() for p in pair]
    ys = [resolve_hardpoint(p, axle)[1] for pair in LINKAGE_POINTS.values() for p in pair]
    xx, yy = np.meshgrid([min(xs) - 100, max(xs) + 100], [min(ys) - 50, max(ys) + 50])
    ax.plot_surface(xx, yy, np.zeros_like(xx), alpha=0.05, color="white")

    ax.set_xlabel("X (fwd)", color="#aaa")
    ax.set_ylabel("Y (left)", color="#aaa")
    ax.set_zlabel("Z (up)", color="#aaa")
    ax.tick_params(colors="#666", labelsize=7)

    title = f"{axle.title()} Corner — Linkage Forces"
    if subtitle:
        title += f"\n{subtitle}"
    ax.set_title(title, color=ACCENT, fontsize=12)

    legend_handles = [
        Line2D([0], [0], color=TENSION_CMAP(0.9), lw=3, label="Tension (darker = more force)"),
        Line2D([0], [0], color=COMPRESSION_CMAP(0.9), lw=3, label="Compression (darker = more force)"),
        Line2D([0], [0], color=GREY, lw=1.5, ls="--", label="Kingpin axis (reference)"),
    ]
    ax.legend(handles=legend_handles, loc="upper left", fontsize=8)

    plt.tight_layout()
    return fig


def main() -> None:
    apply_style()

    axle: Literal["front", "rear"] = "front"
    lateral_g = 1.0
    long_g = 0.2
    slip_angle_rad = 0.08
    slip_ratio = 0.1
    pressure_pa = 100000.0

    forces = calculate_linkage_forces(
        lateral_g=lateral_g,
        long_g=long_g,
        axle=axle,
        slip_angle_rad=slip_angle_rad,
        slip_ratio=slip_ratio,
        pressure_pa=pressure_pa,
    )

    subtitle = f"lat {lateral_g:.2f}g, long {long_g:.2f}g, slip angle {np.degrees(slip_angle_rad):.1f}°"
    fig = plot_linkage_forces_3d(forces, axle=axle, subtitle=subtitle)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"linkage_forces_{axle}.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved -> {out_path}")

    print("\nLinkage forces:")
    for name, payload in forces.items():
        print(f"- {DISPLAY_NAMES[name]}: {payload['force_N']:+.1f} N ({payload['sense']})")

    plt.show()


if __name__ == "__main__":
    main()
