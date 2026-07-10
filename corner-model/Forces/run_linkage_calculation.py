from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Forces.linkage_forces import calculate_linkage_forces


def prompt_float(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("Please enter a valid number.")


def prompt_choice(prompt: str, choices: list[str]) -> str:
    choice_str = "/".join(choices)
    while True:
        value = input(f"{prompt} ({choice_str}): ").strip().lower()
        if value in choices:
            return value
        print(f"Please choose one of: {choice_str}")


def main() -> None:
    print("Linkage force calculator")
    axle = prompt_choice("Axle", ["front", "rear"])
    long_g = prompt_float("Longitudinal G: ")
    lat_g = prompt_float("Lateral G: ")
    slip_angle = prompt_float("Slip angle (radians): ")
    slip_ratio = prompt_float("Slip ratio: ")
    tire_pressure = prompt_float("Tire pressure (Pa): ")

    forces = calculate_linkage_forces(
        lateral_g=lat_g,
        long_g=long_g,
        axle=axle,
        slip_angle_rad=slip_angle,
        slip_ratio=slip_ratio,
        pressure_pa=tire_pressure,
    )

    print("\nLinkage forces:")
    for name, payload in forces.items():
        force_n = payload["force_N"]
        sense = payload["sense"]
        print(f"- {name}: {force_n:.3f} N ({sense})")


if __name__ == "__main__":
    main()
