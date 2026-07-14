
"""
Pitch Gradient Analysis (IMU longitudinal accel vs pitch)

This script:
- Loads two CSV files exported from an IMU: longitudinal acceleration and pitch angle.
- Aligns them on a uniform timebase and interpolates missing samples.
- Converts longitudinal acceleration to g.
- Fits a linear model: pitch_angle = k * long_accel_g + intercept
  where k is the pitch gradient in degrees per g.
- Saves processed data, numeric results, and an interactive Plotly HTML plot
  into a "results" folder that lives next to this script (same folder used by your other scripts).

Edit the USER INPUT section below to point to your files and column names.
Requires: pandas, numpy, plotly
Install with: pip install pandas numpy plotly
"""

from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import sys

# ============================================================
# USER INPUT — EDIT THESE ONLY
# ============================================================

# Folder that contains your two CSV files (change to your folder)
DATA_DIR = Path(r"C:\Users\austi\Downloads\CFR26_Data")

# Filenames for the two CSVs (longitudinal accel and pitch angle)
LONG_FILE = "imu_longitudinal_accel.csv"   # longitudinal accel CSV (time + accel)
PITCH_FILE = "imu_pitch_angle.csv"         # pitch angle CSV (time + pitch)

# If your CSVs have specific column names for time and value, set them here.
# If left as None, the script will try to auto-detect a time column and use
# the first non-time numeric column as the value column.
LONG_TIME_COL = None   # e.g., "time" or "_time"
LONG_VAL_COL = None    # e.g., "accel_x" or "long_accel"

PITCH_TIME_COL = None  # e.g., "time" or "_time"
PITCH_VAL_COL = None   # e.g., "pitch_deg" or "pitch"

# Target uniform sample interval (milliseconds) used to align the two signals
RESAMPLE_MS = 10       # 10 ms is a common choice for IMU-derived signals

# Output filenames (will be saved into results/ next to this script)
OUTPUT_PLOT_HTML = "pitch_gradient_plot.html"
OUTPUT_PROCESSED_CSV = "processed_pitch_long_downsampled.csv"
OUTPUT_RESULTS_JSON = "pitch_gradient_results.json"

# ============================================================
# RESULTS FOLDER (created next to this script)
# ============================================================

# Determine the folder where this script lives. If __file__ is not defined
# (for example when running in an interactive REPL), fall back to the current working directory.
try:
    SCRIPT_DIR = Path(__file__).parent
except NameError:
    SCRIPT_DIR = Path.cwd()

# Create a "results" folder next to the script (if it doesn't already exist)
RESULTS_DIR = SCRIPT_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Full paths for outputs
OUTPUT_PLOT_PATH = RESULTS_DIR / OUTPUT_PLOT_HTML
OUTPUT_CSV_PATH = RESULTS_DIR / OUTPUT_PROCESSED_CSV
OUTPUT_JSON_PATH = RESULTS_DIR / OUTPUT_RESULTS_JSON

# ============================================================
# HELPER FUNCTIONS (with beginner-friendly comments)
# ============================================================

def resolve_and_check(path: Path) -> Path:
    """
    Resolve a Path to an absolute path and print existence info.
    This helps debug "file not found" issues by showing exactly what Python sees.
    """
    p = path.resolve()
    print(f"Resolved path: {p}")
    print(f"Exists: {p.exists()}  Is file: {p.is_file()}")
    return p

def load_csv_auto(path: Path, time_col: str | None = None, val_col: str | None = None) -> pd.DataFrame:
    """
    Load a CSV and try to find a time column and a numeric value column.
    Returns a DataFrame with columns ['time', 'value'].
    - If time_col is provided and exists, it will be used.
    - If val_col is provided and exists, it will be used.
    - Otherwise the function tries common names and heuristics.
    """
    df = pd.read_csv(path, low_memory=False)

    # 1) Find time column
    if time_col and time_col in df.columns:
        tcol = time_col
    else:
        candidates = ["_time", "time", "timestamp", "datetime", "DateTime", "date"]
        tcol = None
        for c in candidates:
            if c in df.columns:
                tcol = c
                break
        if tcol is None:
            # fallback: look for any column name containing 'time' or 'date'
            for c in df.columns:
                if "time" in c.lower() or "date" in c.lower():
                    tcol = c
                    break
    if tcol is None:
        # last resort: if file has exactly two columns, assume first is time
        if len(df.columns) == 2:
            tcol = df.columns[0]
        else:
            raise ValueError(f"Could not detect a time column in {path}. Columns: {list(df.columns)}")

    # 2) Parse time column to datetime
    df[tcol] = pd.to_datetime(df[tcol], errors="coerce")
    if df[tcol].isna().all():
        raise ValueError(f"Time column {tcol} could not be parsed as datetimes in {path}")

    # 3) Find value column
    if val_col and val_col in df.columns:
        vcol = val_col
    else:
        # choose the first numeric column that is not the time column
        numeric_cols = []
        for c in df.columns:
            if c == tcol:
                continue
            # test convertibility to numeric using a small sample
            try:
                pd.to_numeric(df[c].dropna().iloc[:10])
                numeric_cols.append(c)
            except Exception:
                continue
        if numeric_cols:
            vcol = numeric_cols[0]
        else:
            # fallback: if only two columns, pick the other one
            other_cols = [c for c in df.columns if c != tcol]
            if other_cols:
                vcol = other_cols[0]
            else:
                raise ValueError(f"No value column found in {path}")

    # 4) Keep only time and value, rename to standard names
    out = df[[tcol, vcol]].rename(columns={tcol: "time", vcol: "value"})
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    return out

def resample_to_uniform(df: pd.DataFrame, freq_ms: int) -> pd.DataFrame:
    """
    Given a DataFrame with columns ['time', 'value'], create a uniform time index
    at freq_ms milliseconds and interpolate the value column in time.
    Returns a DataFrame with columns ['time', 'value'] sampled uniformly.
    """
    tmin = df["time"].min()
    tmax = df["time"].max()
    # create uniform time index
    idx = pd.date_range(start=tmin, end=tmax, freq=f"{freq_ms}ms")
    uniform = pd.DataFrame({"time": idx})
    # merge_asof requires both sides sorted
    left = uniform
    right = df[["time", "value"]].sort_values("time").reset_index(drop=True)
    merged = pd.merge_asof(left, right, on="time", direction="nearest", tolerance=pd.Timedelta(f"{freq_ms}ms"))
    # interpolate any remaining NaNs using time-based interpolation
    merged = merged.set_index("time")
    merged["value"] = merged["value"].interpolate(method="time", limit_direction="both")
    merged = merged.reset_index()
    return merged

# ============================================================
# MAIN PROCESSING FLOW
# ============================================================

def main():
    # 1) Resolve and check input files
    long_path = resolve_and_check(DATA_DIR / LONG_FILE)
    pitch_path = resolve_and_check(DATA_DIR / PITCH_FILE)

    if not long_path.exists() or not pitch_path.exists():
        print("One or both input files are missing. Please check DATA_DIR and filenames.")
        sys.exit(1)

    # 2) Load CSVs and auto-detect columns
    print("Loading longitudinal acceleration CSV...")
    long_df = load_csv_auto(long_path, time_col=LONG_TIME_COL, val_col=LONG_VAL_COL)
    print(f"Loaded {len(long_df)} rows from {long_path.name}")

    print("Loading pitch angle CSV...")
    pitch_df = load_csv_auto(pitch_path, time_col=PITCH_TIME_COL, val_col=PITCH_VAL_COL)
    print(f"Loaded {len(pitch_df)} rows from {pitch_path.name}")

    # 3) Resample both to a common uniform timebase
    print(f"Resampling both signals to {RESAMPLE_MS} ms uniform grid for alignment...")
    long_uniform = resample_to_uniform(long_df, RESAMPLE_MS)
    pitch_uniform = resample_to_uniform(pitch_df, RESAMPLE_MS)

    # 4) Merge the two series on time (inner overlap via merge_asof)
    merged = pd.merge_asof(
        long_uniform.sort_values("time"),
        pitch_uniform.sort_values("time"),
        on="time",
        suffixes=("_long", "_pitch"),
        direction="nearest",
        tolerance=pd.Timedelta(f"{RESAMPLE_MS}ms")
    )

    # Rename columns to meaningful names and drop rows with missing values
    merged = merged.rename(columns={"value_long": "long_accel", "value_pitch": "pitch_deg"})
    merged = merged.dropna(subset=["long_accel", "pitch_deg"]).reset_index(drop=True)
    print(f"Merged series length (overlap): {len(merged)} samples")

    if len(merged) < 5:
        print("Warning: very few overlapping samples after alignment. Check timestamps and sampling.")

    # 5) Convert longitudinal acceleration to g (optional but common)
    merged["long_accel_g"] = merged["long_accel"].astype(float) / 9.80665

    # 6) Compute pitch gradient: fit pitch_deg = k * long_accel_g + intercept
    mask = np.isfinite(merged["pitch_deg"]) & np.isfinite(merged["long_accel_g"])
    if mask.sum() < 2:
        print("Not enough valid data to compute pitch gradient.")
        k = float("nan")
        intercept = float("nan")
    else:
        slope, intercept = np.polyfit(merged.loc[mask, "long_accel_g"], merged.loc[mask, "pitch_deg"], 1)
        k = slope
        print(f"Pitch Gradient = {k:.4f} deg/g (intercept = {intercept:.4f} deg)")

    # 7) Save processed merged data to CSV in results folder
    merged_to_save = merged.copy()
    merged_to_save.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"Saved processed merged data to: {OUTPUT_CSV_PATH}")

    # 8) Save numeric results (slope, intercept, sample count) to JSON
    results = {
        "pitch_gradient_deg_per_g": float(k) if np.isfinite(k) else None,
        "intercept_deg": float(intercept) if np.isfinite(intercept) else None,
        "num_samples": int(mask.sum()),
        "resample_ms": RESAMPLE_MS,
        "input_long_file": str(long_path),
        "input_pitch_file": str(pitch_path)
    }
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved numeric results to: {OUTPUT_JSON_PATH}")

    # 9) Create an interactive Plotly scatter plot with the fit line
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=merged["long_accel_g"],
        y=merged["pitch_deg"],
        mode="markers",
        marker=dict(size=4, opacity=0.6),
        name="Data (pitch vs long accel)"
    ))

    # Add fit line if slope is finite
    if np.isfinite(k):
        x_min = np.nanmin(merged["long_accel_g"])
        x_max = np.nanmax(merged["long_accel_g"])
        x_line = np.linspace(x_min, x_max, 200)
        y_line = k * x_line + intercept
        fig.add_trace(go.Scatter(
            x=x_line,
            y=y_line,
            mode="lines",
            line=dict(color="red"),
            name=f"Fit: pitch = {k:.3f} * accel_g + {intercept:.2f}"
        ))

    fig.update_layout(
        title="Pitch Angle vs Longitudinal Acceleration (g)",
        xaxis=dict(title="Longitudinal Acceleration (g)"),
        yaxis=dict(title="Pitch Angle (deg)"),
        legend=dict(x=0.01, y=0.99)
    )

    # Save interactive HTML plot to results folder
    fig.write_html(OUTPUT_PLOT_PATH)
    print(f"Saved interactive plot to: {OUTPUT_PLOT_PATH}")

    # Try to show the plot in interactive environments; if that fails, it's fine because we saved the HTML
    try:
        fig.show()
    except Exception:
        pass

if __name__ == "__main__":
    main()
