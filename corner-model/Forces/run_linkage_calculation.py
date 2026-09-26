from __future__ import annotations

import csv
import math
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Forces.linkage_forces import calculate_corner_forces

PSI_TO_PA = 6894.757293168

TIRE_LABELS = {
    "vertical_force_N": ("Fz (vertical)", "N"),
    "lateral_force_N": ("Fy (lateral)", "N"),
    "longitudinal_force_N": ("Fx (longitudinal)", "N"),
    "moment_x_Nm": ("Mx (overturning)", "N*m"),
    "moment_y_Nm": ("My (rolling resistance)", "N*m"),
    "moment_z_Nm": ("Mz (aligning)", "N*m"),
}


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


def prompt_path(prompt: str, default: Path) -> Path:
    value = input(f"{prompt} [{default}]: ").strip()
    return Path(value) if value else default


def write_csv(path: Path, inputs: dict[str, float | str], result: dict[str, dict]) -> None:
    """Write inputs, tire wrench, and member forces as one long-format table."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["category", "name", "value", "units", "sense"])

        for name, (value, units) in inputs.items():
            writer.writerow(["input", name, value, units, ""])

        for key, value in result["tire"].items():
            label, units = TIRE_LABELS[key]
            writer.writerow(["tire", label, f"{value:.6f}", units, ""])

        for name, payload in result["linkages"].items():
            writer.writerow(
                ["linkage", name, f"{payload['force_N']:.6f}", "N", payload["sense"]]
            )


def main() -> None:
    print("Linkage force calculator")
    axle = prompt_choice("Axle", ["front", "rear"])
    long_g = prompt_float("Longitudinal G: ")
    lat_g = prompt_float("Lateral G: ")
    slip_angle_deg = prompt_float("Slip angle (degrees): ")
    slip_ratio = prompt_float("Slip ratio: ")
    tire_pressure_psi = prompt_float("Tire pressure (psi): ")

    result = calculate_corner_forces(
        lateral_g=lat_g,
        long_g=long_g,
        axle=axle,
        slip_angle_rad=math.radians(slip_angle_deg),
        slip_ratio=slip_ratio,
        pressure_pa=tire_pressure_psi * PSI_TO_PA,
    )

    print("\nTire forces at the contact patch:")
    for key, value in result["tire"].items():
        label, units = TIRE_LABELS[key]
        print(f"- {label}: {value:.3f} {units}")

    print("\nLinkage forces:")
    for name, payload in result["linkages"].items():
        print(f"- {name}: {payload['force_N']:.3f} N ({payload['sense']})")

    inputs = {
        "axle": (axle, ""),
        "longitudinal_g": (long_g, "g"),
        "lateral_g": (lat_g, "g"),
        "slip_angle": (slip_angle_deg, "deg"),
        "slip_ratio": (slip_ratio, ""),
        "tire_pressure": (tire_pressure_psi, "psi"),
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_path = Path.cwd() / f"linkage_forces_{axle}_{timestamp}.csv"
    csv_path = prompt_path("\nCSV output path", default_path)
    write_csv(csv_path, inputs, result)
    print(f"Wrote {csv_path.resolve()}")


if __name__ == "__main__":
    main()
