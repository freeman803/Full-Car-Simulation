"""
run_linkage_from_excel.py — tire and linkage forces for every row of an Excel sheet.

Each input row gives one corner condition:

    axle               front / rear (or set one axle for every row with --axle)
    Fz_N               vertical tire load, N (used as-is; no load transfer is calculated)
    slip_angle_deg     slip angle, deg
    slip_ratio         slip ratio (+ = driving, - = braking)
    tire_pressure_psi  tire pressure, psi

Header matching ignores case, spaces and units, so "Fz", "FZ (N)", "Slip Angle"
and "Pressure" all work. Any other columns (time, run name, ...) are copied to
the output unchanged.

The output workbook has a "results" sheet with the inputs, the tire forces and
moments at the contact patch, and the six linkage forces (+ = tension), plus a
"conventions" sheet with the sign conventions.

Usage (from the repo root):
    uv run corner-model/Forces/run_linkage_from_excel.py inputs.xlsx
    uv run corner-model/Forces/run_linkage_from_excel.py inputs.xlsx -o results.xlsx --sheet Sheet2
    uv run corner-model/Forces/run_linkage_from_excel.py inputs.xlsx --axle front
    uv run corner-model/Forces/run_linkage_from_excel.py --template linkage_inputs.xlsx
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Forces.linkage_forces import calculate_corner_forces
from Forces.run_linkage_calculation import PSI_TO_PA

# Canonical input column -> accepted header spellings (after _normalize()).
INPUT_ALIASES: dict[str, set[str]] = {
    "axle": {"axle", "corner"},
    "Fz_N": {"fz", "fzn", "verticalload", "verticalloadn", "verticalforce", "verticalforcen", "wheelload", "wheelloadn"},
    "slip_angle_deg": {"slipangle", "slipangledeg", "alpha", "alphadeg"},
    "slip_ratio": {"slipratio", "kappa"},
    "tire_pressure_psi": {"tirepressure", "tirepressurepsi", "tyrepressure", "tyrepressurepsi", "pressure", "pressurepsi"},
}

TIRE_COLUMNS = {
    "longitudinal_force_N": "Fx_N",
    "lateral_force_N": "Fy_N",
    "moment_x_Nm": "Mx_Nm",
    "moment_y_Nm": "My_Nm",
    "moment_z_Nm": "Mz_Nm",
}

CONVENTIONS = [
    ("Axes", "SAE: X forward, Y left, Z up. Forces are ground-on-tire at the contact patch."),
    ("slip_ratio", "+ = driving (Fx forward), - = braking (Fx rearward)."),
    ("slip_angle_deg", "+ slip angle gives - Fy with this .tir file (PKY1 < 0)."),
    ("Fx", "Horizontal/vertical shifts (PHX, PVX) are ignored, so slip_ratio = 0 gives Fx = 0."),
    ("Linkage forces", "+ = tension, - = compression. Columns ending _N are newtons."),
    ("Tire moments", "Mx overturning, My rolling resistance, Mz aligning, N*m."),
]

TEMPLATE_ROWS = [
    {"axle": "front", "Fz_N": 1400.0, "slip_angle_deg": -4.0, "slip_ratio": 0.0, "tire_pressure_psi": 12.0},
    {"axle": "front", "Fz_N": 1100.0, "slip_angle_deg": 0.0, "slip_ratio": -0.05, "tire_pressure_psi": 12.0},
    {"axle": "rear", "Fz_N": 900.0, "slip_angle_deg": 0.0, "slip_ratio": 0.05, "tire_pressure_psi": 12.0},
]


def _normalize(header: str) -> str:
    """Lowercase and keep only letters, so 'Slip Angle (deg)' -> 'slipangledeg'."""
    return re.sub(r"[^a-z]", "", str(header).lower())


def find_input_columns(df: pd.DataFrame, need_axle: bool) -> dict[str, str]:
    """Map each canonical input name to the sheet's header for it."""
    by_normalized = {_normalize(col): col for col in df.columns}
    found: dict[str, str] = {}
    for canonical, aliases in INPUT_ALIASES.items():
        match = next((by_normalized[a] for a in aliases if a in by_normalized), None)
        if match is not None:
            found[canonical] = match

    required = [name for name in INPUT_ALIASES if name != "axle" or need_axle]
    missing = [name for name in required if name not in found]
    if missing:
        raise SystemExit(
            f"Missing input column(s): {', '.join(missing)}. "
            f"Found headers: {', '.join(map(str, df.columns))}. "
            "Run with --template to see the expected layout."
        )
    return found


def calculate_row(axle: str, fz_n: float, slip_angle_deg: float, slip_ratio: float, pressure_psi: float) -> dict[str, float]:
    result = calculate_corner_forces(
        lateral_g=0.0,
        long_g=0.0,
        axle=axle,
        wheel_force_n=fz_n,
        slip_angle_rad=math.radians(slip_angle_deg),
        slip_ratio=slip_ratio,
        pressure_pa=pressure_psi * PSI_TO_PA,
    )
    row = {column: result["tire"][key] for key, column in TIRE_COLUMNS.items()}
    for name, payload in result["linkages"].items():
        row[f"{name}_N"] = payload["force_N"]
    return row


def process(df: pd.DataFrame, default_axle: str | None) -> pd.DataFrame:
    columns = find_input_columns(df, need_axle=default_axle is None)
    df = df.dropna(how="all").reset_index(drop=True)

    outputs = []
    errors = []
    for i, src in df.iterrows():
        excel_row = i + 2  # header is row 1
        try:
            axle = default_axle or str(src[columns["axle"]]).strip().lower()
            if axle not in {"front", "rear"}:
                raise ValueError(f"axle must be front or rear, got {src[columns['axle']]!r}")
            values = [float(src[columns[name]]) for name in ("Fz_N", "slip_angle_deg", "slip_ratio", "tire_pressure_psi")]
            if any(math.isnan(v) for v in values):
                raise ValueError("blank input cell")
            outputs.append(calculate_row(axle, *values))
        except (ValueError, TypeError) as exc:
            errors.append(f"  row {excel_row}: {exc}")
            outputs.append({})

    if errors:
        print(f"{len(errors)} row(s) skipped (outputs left blank):")
        print("\n".join(errors))

    if default_axle is not None:
        df = df.assign(axle=default_axle)
    return pd.concat([df, pd.DataFrame(outputs, index=df.index)], axis=1)


def write_workbook(path: Path, results: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conventions = pd.DataFrame(CONVENTIONS, columns=["item", "convention"])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        results.to_excel(writer, sheet_name="results", index=False)
        conventions.to_excel(writer, sheet_name="conventions", index=False)
        for sheet_name, frame in (("results", results), ("conventions", conventions)):
            sheet = writer.sheets[sheet_name]
            sheet.freeze_panes = "A2"
            for idx, col in enumerate(frame.columns, start=1):
                width = max(len(str(col)), *(len(f"{v:.1f}" if isinstance(v, float) else str(v)) for v in frame[col])) if len(frame) else len(str(col))
                sheet.column_dimensions[sheet.cell(row=1, column=idx).column_letter].width = min(width + 2, 90)
        for row in writer.sheets["results"].iter_rows(min_row=2):
            for cell in row:
                if isinstance(cell.value, float):
                    cell.number_format = "0.000"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, nargs="?", help="Input .xlsx (or .csv) with one corner condition per row")
    parser.add_argument("-o", "--output", type=Path, help="Output .xlsx (default: <input>_linkage_forces.xlsx)")
    parser.add_argument("--sheet", default=0, help="Input sheet name or index (default: first sheet)")
    parser.add_argument("--axle", choices=["front", "rear"], help="Use this axle for every row instead of an axle column")
    parser.add_argument("--template", type=Path, metavar="PATH", help="Write an example input workbook to PATH and exit")
    args = parser.parse_args()

    if args.template:
        write_workbook(args.template, pd.DataFrame(TEMPLATE_ROWS))
        print(f"Wrote template -> {args.template.resolve()}")
        return
    if args.input is None:
        parser.error("give an input file, or --template PATH")

    sheet = int(args.sheet) if str(args.sheet).isdigit() else args.sheet
    if args.input.suffix.lower() == ".csv":
        df = pd.read_csv(args.input)
    else:
        df = pd.read_excel(args.input, sheet_name=sheet)

    results = process(df, args.axle)
    out_path = args.output or args.input.with_name(f"{args.input.stem}_linkage_forces.xlsx")
    write_workbook(out_path, results)
    print(f"{len(results)} row(s) -> {out_path.resolve()}")


if __name__ == "__main__":
    main()
