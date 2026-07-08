from __future__ import annotations

from pathlib import Path
import importlib.util
from typing import Literal

try:
    from .linkage_forces import calculate_linkage_forces
except ImportError:
    # Support running this script directly from the Forces folder.
    module_path = Path(__file__).with_name("linkage_forces.py")
    spec = importlib.util.spec_from_file_location("linkage_forces", module_path)
    if spec is None or spec.loader is None:
        raise ImportError("Could not import linkage_forces module")
    linkage_forces = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(linkage_forces)
    calculate_linkage_forces = linkage_forces.calculate_linkage_forces


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
    )

    print("\nLinkage forces:")
    for name, payload in forces.items():
        force_n = payload["force_N"]
        sense = payload["sense"]
        print(f"- {name}: {force_n:.3f} N ({sense})")

    print(
        "\nNote: slip angle, slip ratio, and tire pressure are accepted by the "
        "current interface but are not yet used in linkage force balance."
    )


if __name__ == "__main__":
    main()
