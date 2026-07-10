from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Forces.wheel_loads import calculate_total_wheel_load

DEFAULT_TIR_PATH = Path(__file__).with_name("16inx18in_R20 1.tir")


def _sign(value: float) -> float:
    return 1.0 if value >= 0.0 else -1.0


@dataclass
class PacejkaTireModel:
    tir_path: Path
    coefficients: dict[str, dict[str, float]]
    nominal_pressure_pa: float
    nominal_vertical_load_n: float

    @classmethod
    def from_tir(cls, tir_path: str | Path) -> "PacejkaTireModel":
        path = Path(tir_path)
        sections: dict[str, dict[str, float]] = {}
        current_section: str | None = None

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("$"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                sections[current_section] = {}
                continue
            if current_section is None or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            try:
                numeric_value = float(value)
            except ValueError:
                numeric_value = value
            sections[current_section][key] = numeric_value

        nominal_pressure_pa = float(sections["OPERATING_CONDITIONS"]["NOMPRES"])
        nominal_vertical_load_n = float(sections["VERTICAL"]["FNOMIN"])
        return cls(
            tir_path=path,
            coefficients=sections,
            nominal_pressure_pa=nominal_pressure_pa,
            nominal_vertical_load_n=nominal_vertical_load_n,
        )

    def _pressure_factor(self, pressure_pa: float) -> float:
        return max(0.5, pressure_pa / max(self.nominal_pressure_pa, 1.0))

    def calculate_tire_response(
        self,
        vertical_force_n: float,
        slip_angle_rad: float,
        slip_ratio: float,
        pressure_pa: float,
        inclination_angle_rad: float = 0.0,
    ) -> dict[str, float]:
        """
        Estimate tire force and moment outputs from a Pacejka-style coefficient set.

        The longitudinal force is now driven by the supplied slip ratio, while the
        lateral force remains driven by the slip angle.
        """
        lat_coeffs = self.coefficients["LATERAL_COEFFICIENTS"]
        long_coeffs = self.coefficients["LONGITUDINAL_COEFFICIENTS"]
        align_coeffs = self.coefficients["ALIGNING_COEFFICIENTS"]
        overturn_coeffs = self.coefficients["OVERTURNING_COEFFICIENTS"]
        rolling_coeffs = self.coefficients["ROLLING_COEFFICIENTS"]

        pressure_factor = self._pressure_factor(pressure_pa)
        dfz = (vertical_force_n - self.nominal_vertical_load_n) / self.nominal_vertical_load_n
        gamma = inclination_angle_rad

        # Lateral force (pure slip-angle form, MF2002-style).
        # Dy is a peak *force* (mu_y * Fz), so it must scale with the actual
        # vertical load in Newtons, not the dimensionless load ratio.
        cy = float(lat_coeffs["PCY1"])
        dy = (
            (float(lat_coeffs["PDY1"]) + float(lat_coeffs["PDY2"]) * dfz)
            * (1.0 - float(lat_coeffs["PDY3"]) * gamma**2)
            * vertical_force_n
        )
        kya = (
            float(lat_coeffs["PKY1"])
            * self.nominal_vertical_load_n
            * math.sin(2.0 * math.atan(vertical_force_n / (float(lat_coeffs["PKY2"]) * self.nominal_vertical_load_n)))
            * (1.0 - float(lat_coeffs["PKY3"]) * abs(gamma))
        )
        by = kya / max(cy * max(dy, 1e-6), 1e-6)
        ey = (float(lat_coeffs["PEY1"]) + float(lat_coeffs["PEY2"]) * dfz) * (
            1.0 - (float(lat_coeffs["PEY3"]) + float(lat_coeffs["PEY4"]) * gamma) * _sign(slip_angle_rad)
        )
        shy = float(lat_coeffs["PHY1"]) + float(lat_coeffs["PHY2"]) * dfz
        svy = vertical_force_n * (
            (float(lat_coeffs["PVY1"]) + float(lat_coeffs["PVY2"]) * dfz)
            + (float(lat_coeffs["PVY3"]) + float(lat_coeffs["PVY4"]) * dfz) * gamma
        )
        alpha = slip_angle_rad + shy
        lateral_force_n = dy * math.sin(
            cy * math.atan(by * alpha - ey * (by * alpha - math.atan(by * alpha)))
        )
        lateral_force_n += svy
        lateral_force_n *= pressure_factor

        # Longitudinal force (pure slip-ratio form, MF2002-style).
        cx = float(long_coeffs["PCX1"])
        dx = (
            (float(long_coeffs["PDX1"]) + float(long_coeffs["PDX2"]) * dfz)
            * (1.0 - float(long_coeffs["PDX3"]) * gamma**2)
            * vertical_force_n
        )
        kxk = (
            vertical_force_n
            * (float(long_coeffs["PKX1"]) + float(long_coeffs["PKX2"]) * dfz)
            * math.exp(float(long_coeffs["PKX3"]) * dfz)
        )
        bx = kxk / max(cx * max(dx, 1e-6), 1e-6)
        kappa = min(0.25, max(-0.25, slip_ratio))
        ex = (float(long_coeffs["PEX1"]) + float(long_coeffs["PEX2"]) * dfz + float(long_coeffs["PEX3"]) * dfz**2) * (
            1.0 - float(long_coeffs["PEX4"]) * _sign(kappa)
        )
        shx = float(long_coeffs["PHX1"]) + float(long_coeffs["PHX2"]) * dfz
        svx = vertical_force_n * (float(long_coeffs["PVX1"]) + float(long_coeffs["PVX2"]) * dfz)
        kappa_shifted = kappa + shx
        longitudinal_force_n = dx * math.sin(
            cx * math.atan(bx * kappa_shifted - ex * (bx * kappa_shifted - math.atan(bx * kappa_shifted)))
        )
        longitudinal_force_n += svx
        longitudinal_force_n *= pressure_factor

        # Aligning moment
        bz = float(align_coeffs["QBZ1"]) + float(align_coeffs["QBZ2"]) * dfz
        cz = float(align_coeffs["QCZ1"])
        dz = (
            (float(align_coeffs["QDZ1"]) + float(align_coeffs["QDZ2"]) * dfz)
            * vertical_force_n
        )
        ez = float(align_coeffs["QEZ1"]) + float(align_coeffs["QEZ2"]) * dfz + float(align_coeffs["QEZ3"]) * pressure_factor
        aligning_moment_nm = dz * math.sin(
            cz * math.atan(bz * slip_angle_rad - ez * (bz * slip_angle_rad - math.atan(bz * slip_angle_rad)))
        )
        aligning_moment_nm *= pressure_factor

        # Overturning moment
        overturning_moment_nm = (
            (float(overturn_coeffs["QSX1"]) + float(overturn_coeffs["QSX2"]) * dfz + float(overturn_coeffs["QSX3"]) * pressure_factor)
            * vertical_force_n
            * math.sin(slip_angle_rad)
        )

        # Rolling resistance moment
        rolling_moment_nm = (
            (float(rolling_coeffs["QSY1"]) + float(rolling_coeffs["QSY2"]) * dfz + float(rolling_coeffs["QSY3"]) * pressure_factor)
            * vertical_force_n
        )

        return {
            "lateral_force_N": float(lateral_force_n),
            "longitudinal_force_N": float(longitudinal_force_n),
            "moment_x_Nm": float(overturning_moment_nm),
            "moment_y_Nm": float(rolling_moment_nm),
            "moment_z_Nm": float(aligning_moment_nm),
        }


def calculate_tire_response_from_wheel_loads(
    lateral_g: float,
    long_g: float,
    axle: Literal["front", "rear"],
    slip_angle_rad: float,
    slip_ratio: float,
    pressure_pa: float,
    tir_path: str | Path | None = None,
) -> dict[str, float]:
    """Use the wheel-load helper to derive a vertical force and then evaluate the tire model."""
    wheel_load_n = calculate_total_wheel_load(
        lateral_g=lateral_g,
        long_g=long_g,
        axle=axle,
    )
    model = PacejkaTireModel.from_tir(tir_path or DEFAULT_TIR_PATH)
    return model.calculate_tire_response(
        vertical_force_n=wheel_load_n,
        slip_angle_rad=slip_angle_rad,
        slip_ratio=slip_ratio,
        pressure_pa=pressure_pa,
    )


if __name__ == "__main__":
    response = calculate_tire_response_from_wheel_loads(
        lateral_g=1.0,
        long_g=0.2,
        axle="front",
        slip_angle_rad=0.08,
        slip_ratio=0.1,
        pressure_pa=100000.0,
    )
    print("Tire response:")
    for key, value in response.items():
        print(f"- {key}: {value:.6f}")
