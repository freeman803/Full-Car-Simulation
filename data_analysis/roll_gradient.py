
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go

# ============================================================
# USER INPUT — EDIT THESE ONLY
# ============================================================

# Folder that contains your input CSV files
DATA_DIR = Path(r"C:\Users\austi\Downloads\CFR26_Data")

# Input CSV filenames
ROLL_FILE = "June 15 Austin Skidpad roll (after change).csv"
LATG_FILE = "June 15 Austin Skidpad lat g (after change).csv"

# Channel names inside the files to extract
ROLL_CHANNEL = "VCPDU_roll"        # e.g. "rollAngleDeg"
LATG_CHANNEL = "VCPDU_lat"         # e.g. "latAccel"

# Name of the HTML file to save (we will save it into results/)
OUTPUT_HTML = "roll_gradient_plot_austin_june_15_AC.html"

# ============================================================
# RESULTS FOLDER (created next to this script)
# ============================================================

# Determine the folder where this script lives. If running interactively (no __file__),
# fall back to the current working directory.
try:
    SCRIPT_DIR = Path(__file__).parent
except NameError:
    SCRIPT_DIR = Path.cwd()

# Create a "results" folder next to the script (if it doesn't already exist)
RESULTS_DIR = SCRIPT_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Full paths for outputs
OUTPUT_HTML_PATH = RESULTS_DIR / OUTPUT_HTML
OUTPUT_CSV_PATH = RESULTS_DIR / "processed_roll_latg_downsampled.csv"

# ============================================================
# LOADING + NORMALIZATION FUNCTIONS (pandas)
# ============================================================

def load_csv(filename: str) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.
    - skiprows=3 matches the original script which ignored the first 3 lines.
    - dtype=str reads everything as text first so we can parse safely later.
    """
    path = DATA_DIR / filename
    return pd.read_csv(path, skiprows=3, dtype=str, low_memory=False)


def normalize_timeseries(
    df: pd.DataFrame,
    time_candidates=("_time", "time", "timestamp")
) -> pd.DataFrame:
    """
    Convert a raw dataframe into a normalized long format with columns:
    ['time', 'channel', 'value'].
    Handles Influx-style (_time, _field, _value) and wide CAN-style.
    """

    # 1) Find which column looks like the time column
    time_col = None
    for c in time_candidates:
        if c in df.columns:
            time_col = c
            break
    if time_col is None:
        raise ValueError(f"No time column found in: {list(df.columns)}")

    # 2) Influx-style: rename to common columns
    if {"_time", "_value", "_field"}.issubset(set(df.columns)):
        out = df[["_time", "_field", "_value"]].rename(
            columns={"_time": "time", "_field": "channel", "_value": "value"}
        )
    else:
        # 3) Wide CAN-style: melt many sensor columns into channel/value pairs
        value_cols = [c for c in df.columns if c != time_col]
        out = df.melt(
            id_vars=[time_col],
            value_vars=value_cols,
            var_name="channel",
            value_name="value"
        ).rename(columns={time_col: "time"})

    # 4) Parse the time column into real datetime objects and sort by time
    out["time"] = pd.to_datetime(out["time"], errors="coerce")
    out = out.dropna(subset=["time"])          # drop rows where time couldn't be parsed
    out = out.sort_values("time").reset_index(drop=True)

    # Convert the value column to numeric where possible
    out["value"] = pd.to_numeric(out["value"], errors="coerce")

    return out


def extract_channel(
    df_norm: pd.DataFrame,
    channel_name: str,
    new_name: str,
    freq_ms: int = 10
) -> pd.DataFrame:
    """
    Extract a single channel and return a uniformly sampled DataFrame with columns:
    ['time', new_name]. Uses nearest merge_asof then time interpolation.
    """

    # Filter to the requested channel
    df = df_norm[df_norm["channel"] == channel_name].copy()
    if df.empty:
        print(f"Warning: no data for channel '{channel_name}'")
        return None

    # Determine the time range of the data
    t_min = df["time"].min()
    t_max = df["time"].max()

    # Create a uniform time index at the requested millisecond interval
    uniform_idx = pd.date_range(start=t_min, end=t_max, freq=f"{freq_ms}ms")
    uniform = pd.DataFrame({"time": uniform_idx})

    # Prepare the original channel data for merging (must be sorted)
    df_sorted = df[["time", "value"]].sort_values("time").reset_index(drop=True)

    # Merge the uniform times with the nearest original sample
    # tolerance ensures we only match if a sample is within freq_ms of the uniform time
    merged = pd.merge_asof(
        uniform,
        df_sorted,
        on="time",
        direction="nearest",
        tolerance=pd.Timedelta(f"{freq_ms}ms")
    )

    # If there are still missing values, interpolate them using time-based interpolation
    merged = merged.set_index("time")
    merged["value"] = merged["value"].interpolate(method="time", limit_direction="both")
    merged = merged.reset_index().rename(columns={"value": new_name})

    return merged


def merge_channels(dfs: list) -> pd.DataFrame:
    """
    Merge multiple uniformly-sampled channel DataFrames on the 'time' column using nearest-asof.
    Each DataFrame in dfs must have a 'time' column and one value column.
    """
    # Remove None entries (in case a channel was missing)
    dfs = [d for d in dfs if d is not None]
    if not dfs:
        return None

    out = dfs[0].sort_values("time").reset_index(drop=True)
    for d in dfs[1:]:
        d_sorted = d.sort_values("time").reset_index(drop=True)
        # merge_asof keeps the left (out) time index and finds nearest matches from d_sorted
        out = pd.merge_asof(out, d_sorted, on="time", direction="nearest")
    return out

# ============================================================
# LOAD RAW DATA
# ============================================================

# Read the CSV files into DataFrames
df_roll_raw = load_csv(ROLL_FILE)
df_latg_raw = load_csv(LATG_FILE)

# Normalize both files into long time/channel/value format
df_roll_norm = normalize_timeseries(df_roll_raw)
df_latg_norm = normalize_timeseries(df_latg_raw)

# Extract the requested channels and resample them uniformly
roll = extract_channel(df_roll_norm, ROLL_CHANNEL, "Roll", freq_ms=10)
latg = extract_channel(df_latg_norm, LATG_CHANNEL, "LatG_mps2", freq_ms=10)

# If latg exists, convert from m/s^2 to g and rename to "LatG"
if latg is not None:
    latg["LatG"] = latg["LatG_mps2"].astype(float) / 9.80665
    latg = latg.drop(columns=["LatG_mps2"])

# Merge the two channels into one DataFrame aligned by time
merged = merge_channels([roll, latg])
if merged is None:
    raise SystemExit("No channels available to merge; exiting.")

# Downsample for plotting (every 10th sample) to speed up plotting
plot_df = merged.iloc[::10].reset_index(drop=True)

# Save the processed, downsampled time series to the results folder
plot_df.to_csv(OUTPUT_CSV_PATH, index=False)
print(f"Saved processed time series to: {OUTPUT_CSV_PATH}")

# Convert to a pandas DataFrame (already pandas) and prepare for numeric ops
pdf = plot_df.copy()

# ============================================================
# COMPUTE ROLL GRADIENT (Fit Roll = k * LatG)
# ============================================================

# Create a mask to keep only rows where both Roll and LatG are finite numbers
mask = np.isfinite(pdf["Roll"]) & np.isfinite(pdf["LatG"])

# If there are enough valid points, fit a straight line: Roll = k * LatG
if mask.sum() < 2:
    print("Not enough valid data points to compute roll gradient.")
    k = np.nan
else:
    # np.polyfit returns [slope, intercept] for degree=1; we only need slope k
    k, _ = np.polyfit(pdf["LatG"][mask], pdf["Roll"][mask], 1)
    print(f"Roll Gradient = {k:.3f} deg/g")

# ============================================================
# PLOT — Roll vs Lateral G (Scatter + Fit Line)
# ============================================================

fig = go.Figure()

# Scatter plot of the data points (LatG on x-axis, Roll on y-axis)
fig.add_trace(go.Scatter(
    x=pdf["LatG"],
    y=pdf["Roll"],
    mode="markers",
    name="Data",
    marker=dict(size=4)
))

# If we computed a slope, draw the best-fit line across the LatG range
if np.isfinite(k):
    latg_min = np.nanmin(pdf["LatG"])
    latg_max = np.nanmax(pdf["LatG"])
    latg_range = np.linspace(latg_min, latg_max, 200)
    fig.add_trace(go.Scatter(
        x=latg_range,
        y=k * latg_range,
        mode="lines",
        name=f"Fit (Roll Gradient = {k:.2f} deg/g)"
    ))

# Add titles and axis labels so the plot is readable
fig.update_layout(
    title="Roll Gradient: Roll Angle vs Lateral Acceleration",
    xaxis=dict(title="Lateral Acceleration (g)"),
    yaxis=dict(title="Roll Angle (deg)"),
    legend=dict(x=0.01, y=0.99)
)

# Show the interactive plot in a browser window (if environment supports it)
fig.show()

# Save the interactive plot to the results folder so you can open it later
fig.write_html(OUTPUT_HTML_PATH)
print(f"Saved plot HTML to: {OUTPUT_HTML_PATH}")
