import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go

# ============================================================
# USER INPUT — EDIT THESE ONLY
# ============================================================

# Path to the folder that contains your CSV file(s)
DATA_DIR = Path(r"C:\Users\austi\Downloads\CFR26_Data")

# Name of the CSV file that contains vertical acceleration data
VERT_FILE = "June_15_accel_skid_VCPDU_vert.csv"

# The channel name inside the file that holds vertical acceleration values
VERT_CHANNEL = "VCPDU_vert"

# Name of the HTML file that will be created with the plot (we will save it into results/)
OUTPUT_HTML = "ride_frequency_plot.html"

# ============================================================
# RESULTS FOLDER (created next to this script)
# ============================================================

# Determine the folder where this script lives. If __file__ is not defined (e.g., interactive REPL),
# fall back to the current working directory.
try:
    SCRIPT_DIR = Path(__file__).parent
except NameError:
    SCRIPT_DIR = Path.cwd()

# Create a "results" folder next to the script
RESULTS_DIR = SCRIPT_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)  # creates folder if it doesn't exist

# Full paths for outputs
OUTPUT_HTML_PATH = RESULTS_DIR / OUTPUT_HTML
OUTPUT_CSV_PATH = RESULTS_DIR / "processed_vert_downsampled.csv"

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
    Convert the raw table into a long format with columns: time, channel, value.
    Handles Influx-style and wide CAN-style formats.
    """
    # 1) Find which column looks like the time column
    time_col = None
    for c in time_candidates:
        if c in df.columns:
            time_col = c
            break
    if time_col is None:
        raise ValueError(f"No time column found in: {list(df.columns)}")

    # 2) If the file uses Influx-style columns, rename them to a common format
    if {"_time", "_value", "_field"}.issubset(set(df.columns)):
        out = df[["_time", "_field", "_value"]].rename(
            columns={"_time": "time", "_field": "channel", "_value": "value"}
        )
    else:
        # 3) Otherwise assume wide format and "melt" it into long format
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
    freq_ms: int = 5
) -> pd.DataFrame:
    """
    Extract one channel (sensor) and resample it to a uniform time grid.
    Steps:
      - Filter to the requested channel
      - Create a uniform time index from start to end at freq_ms intervals
      - Use nearest neighbor matching then interpolate missing values
      - Return a DataFrame with columns: time and new_name
    """

    # Keep only rows for the requested channel
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

# ============================================================
# LOAD RAW DATA
# ============================================================

# Read the CSV file into a DataFrame
df_vert_raw = load_csv(VERT_FILE)

# Normalize the raw table into a long time/channel/value format
df_vert_norm = normalize_timeseries(df_vert_raw)

# Extract the vertical acceleration channel and resample it uniformly
vert = extract_channel(df_vert_norm, VERT_CHANNEL, "Vert_mps2")

# If the requested channel wasn't found, stop the script
if vert is None:
    raise SystemExit("No vertical channel data found; exiting.")

# Convert acceleration from meters per second squared to g units
# 9.80665 is the standard gravity constant in m/s^2
vert["Vert_g"] = vert["Vert_mps2"].astype(float) / 9.80665
vert = vert.drop(columns=["Vert_mps2"])   # drop the original m/s^2 column

# Downsample every 2nd row to speed up processing and plotting
plot_df = vert.iloc[::2].reset_index(drop=True)
pdf = plot_df.copy()  # keep a copy for the FFT step

# Save the processed, downsampled time series to the results folder
# This gives you a CSV with the numeric data used for the FFT and plotting.
plot_df.to_csv(OUTPUT_CSV_PATH, index=False)
print(f"Saved processed time series to: {OUTPUT_CSV_PATH}")

# ============================================================
# COMPUTE RIDE FREQUENCY USING FFT
# ============================================================

# Ensure time has no timezone info so numeric math is safe
if pd.api.types.is_datetime64tz_dtype(pdf["time"].dtype):
    pdf["time"] = pdf["time"].dt.tz_convert(None)

# Convert time column to seconds relative to the first sample
t = pdf["time"]
t = (t - t.iloc[0]).dt.total_seconds().values

# Compute the average sample period dt and sample rate fs
dt = np.mean(np.diff(t))   # average time between samples in seconds
fs = 1.0 / dt              # sampling frequency in Hz

# Get the acceleration values as a numeric numpy array
acc = pdf["Vert_g"].astype(float).values
N = len(acc)               # number of samples

# Compute the real FFT and corresponding frequency bins
freqs = np.fft.rfftfreq(N, dt)      # frequencies for the FFT output
fft_vals = np.abs(np.fft.rfft(acc)) # magnitude of the FFT (power-like)

# Ignore very low frequencies below 0.5 Hz and find the dominant frequency
mask = freqs > 0.5
if mask.sum() == 0:
    dominant_freq = 0.0
else:
    dominant_freq = freqs[mask][np.argmax(fft_vals[mask])]

# Print the detected ride frequency in Hz
print(f"Ride Frequency = {dominant_freq:.2f} Hz")

# ============================================================
# PLOT PSD + MARKER FOR DOMINANT FREQUENCY
# ============================================================

fig = go.Figure()

# Add the FFT magnitude as a line plot (frequency vs magnitude)
fig.add_trace(go.Scatter(
    x=freqs,
    y=fft_vals,
    mode="lines",
    name="FFT Magnitude"
))

# Add a red marker at the dominant frequency for emphasis
if dominant_freq > 0:
    fig.add_trace(go.Scatter(
        x=[dominant_freq],
        y=[np.max(fft_vals[mask])],
        mode="markers",
        marker=dict(size=10, color="red"),
        name=f"Ride Frequency = {dominant_freq:.2f} Hz"
    ))

# Label the axes and title the plot
fig.update_layout(
    title="Ride Frequency (FFT of Vertical Acceleration)",
    xaxis=dict(title="Frequency (Hz)"),
    yaxis=dict(title="Magnitude"),
)

# Show the interactive plot in a browser window
fig.show()

# Save the interactive plot to the results folder so you can open it later
fig.write_html(OUTPUT_HTML_PATH)
print(f"Saved plot HTML to: {OUTPUT_HTML_PATH}")
