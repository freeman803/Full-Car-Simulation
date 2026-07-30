# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "pandas"]
# ///
"""Python port of parse_influx.m — read an InfluxDB CSV export into per-signal
time series on a shared (union) time grid, with an optional on-disk cache so the
big CSV is only parsed once.

Why the cache
-------------
MATLAB keeps `signals` in the workspace, so `if ~exist('signals','var')` skips the
reparse. Under uv, `uv run script.py` starts a FRESH process every time, so module
globals do not persist and uv's package cache does not cache parsed data. To get the
same "don't re-read the CSV" behaviour across runs, parse_influx pickles the parsed
result next to the CSV, keyed on the file's size + modified-time. If the CSV hasn't
changed, the next call reloads the pickle instead of re-parsing.

Run it (uv provisions numpy/pandas from the header above automatically):
    uv run parse_influx.py bms_thermalsFINAL.csv

Use it from code:
    from parse_influx import parse_influx
    signals = parse_influx('bms_thermalsFINAL.csv')     # parses + writes <name>.parsed.pkl
    signals = parse_influx('bms_thermalsFINAL.csv')     # 2nd call -> cache hit, near-instant

    t   = signals['BMSB_maxCellTemp'].time     # pandas DatetimeIndex (UTC)
    T   = signals['BMSB_maxCellTemp'].value    # np.ndarray on the union grid
    soc = signals.BMSB_packSOC.value           # dot access works too
    grid = signals.time                        # the shared union grid

MATLAB-style workspace guard (works in a persistent kernel: Jupyter / IPython /
Spyder, incl. `uv run --with jupyter jupyter lab`):
    if 'signals' not in globals():
        signals    = parse_influx('bms_thermalsFINAL.csv')
        signalsSOC = parse_influx('influx_exportBMSB_SOC.csv')

Each signal exposes the same fields as the MATLAB `entry`:
    .name .time_raw .value_raw .n .duration_s .time .value
"""

import os
import pickle

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _make_valid_name(name):
    """Light stand-in for matlab.lang.makeValidName: make a string usable as an
    attribute (invalid chars -> '_', prefix if it starts with a digit). Names
    like 'BMSB_packSOC' pass through unchanged."""
    valid = ''.join(ch if (ch.isalnum() or ch == '_') else '_' for ch in name)
    if valid and valid[0].isdigit():
        valid = 'x' + valid
    return valid or 'x'


def _zoh_previous(t_sig, v_sig, t_query):
    """Zero-order-hold resample, matching MATLAB interp1(t,v,tq,'previous',NaN).

    For each query time, return the value at the latest sample time <= query.
    Query points before the first sample or after the last sample -> NaN
    (no extrapolation), so signals that start late / end early carry leading /
    trailing NaNs on the union grid, exactly like the MATLAB code.
    """
    t_sig = np.asarray(t_sig, dtype=float)
    v_sig = np.asarray(v_sig, dtype=float)
    t_query = np.asarray(t_query, dtype=float)

    out = np.full(t_query.shape, np.nan)
    if t_sig.size == 0:
        return out

    idx = np.searchsorted(t_sig, t_query, side='right') - 1     # previous sample
    in_range = (idx >= 0) & (t_query <= t_sig[-1])
    out[in_range] = v_sig[idx[in_range]]
    return out


class Signal:
    """One InfluxDB field: raw samples plus a copy resampled onto the union grid."""

    __slots__ = ('name', 'time_raw', 'value_raw', 'n', 'duration_s', 'time', 'value')

    def __init__(self, name, time_raw, value_raw):
        self.name = name
        self.time_raw = time_raw            # pandas DatetimeIndex (UTC), sorted
        self.value_raw = value_raw          # np.ndarray
        self.n = int(value_raw.size)
        if self.n > 1:
            self.duration_s = (time_raw[-1] - time_raw[0]).total_seconds()
        else:
            self.duration_s = 0.0
        self.time = time_raw                # populated by the resampling step
        self.value = value_raw

    def __repr__(self):
        return f'Signal({self.name!r}, n={self.n}, duration_s={self.duration_s:.2f})'


class SignalSet(dict):
    """dict of {name: Signal} plus a `.time` attribute (the shared union grid).
    Supports both signals['name'] and signals.name access."""

    time = None

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)


# ---------------------------------------------------------------------------
# core parse (no caching) — faithful port of parse_influx.m
# ---------------------------------------------------------------------------
def _parse_influx_core(csv_path, verbose=True):
    if verbose:
        print(f'Reading {csv_path} ...')

    # 1. locate the header row.
    # InfluxDB annotated-CSV exports carry annotation lines before the header.
    # Usually those are '#'-prefixed (#group / #datatype / #default), but some
    # exports drop the '#' (leading 'TRUE,TRUE,FALSE,...' + 'dateTime:RFC3339,...'
    # + ',,,,' rows). Rather than trust the prefix, find the first line that
    # actually contains the columns we need — works for both dialects.
    required = ('_time', '_value', '_field')
    skip = None
    with open(csv_path, 'r') as fid:
        for i, line in enumerate(fid):
            cols = {c.strip() for c in line.rstrip('\r\n').split(',')}
            if all(r in cols for r in required):
                skip = i
                break
    if skip is None:
        raise ValueError(
            f"No header row containing {required} found in {csv_path}. "
            f"Is this an InfluxDB CSV export?")

    # 2. read CSV (the located row is the header)
    df = pd.read_csv(csv_path, skiprows=skip)

    for col in ('_time', '_value', '_field'):
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in {csv_path}. "
                             f"Columns: {list(df.columns)}")

    # 3. timestamps (handles 'T'/'Z' and fractional seconds)
    try:
        t = pd.to_datetime(df['_time'], utc=True, format='ISO8601')
    except (ValueError, TypeError):
        t = pd.to_datetime(df['_time'], utc=True)

    # 4. values / fields, keep only valid rows
    values = pd.to_numeric(df['_value'], errors='coerce').to_numpy()
    field = df['_field']
    valid = (field.notna()
             & (field.astype(str).str.len() > 0)
             & ~np.isnan(values)).to_numpy()

    t = pd.DatetimeIndex(t[valid])
    values = values[valid]
    field_names = field[valid].astype(str).to_numpy()

    # 5. per-signal series (sorted by time)
    signals = SignalSet()
    for sig in pd.unique(field_names):
        mask = field_names == sig
        t_sig = t[mask]
        v_sig = values[mask]

        order = np.argsort(t_sig.values, kind='stable')
        t_sig = t_sig[order]
        v_sig = v_sig[order]

        signals[_make_valid_name(sig)] = Signal(sig, t_sig, v_sig)

    if not signals:
        raise ValueError(f'No valid signals found in {csv_path}')

    # 6. safe union time grid across all signals
    all_times = np.concatenate([s.time_raw.asi8 for s in signals.values()])
    common_i8 = np.unique(all_times)                       # sorted, unique (int64 ns)
    common_time = pd.DatetimeIndex(common_i8).tz_localize('UTC')

    if verbose:
        span_s = (common_time[-1] - common_time[0]).total_seconds()
        print(f'Union grid: {len(common_time)} points ({span_s:.2f} s)')

    # 7. ZOH resampling onto the union grid
    t0 = common_time[0]
    t_num = (common_time - t0).total_seconds().to_numpy()
    for s in signals.values():
        t_sig_num = (s.time_raw - t0).total_seconds().to_numpy()
        s.value = _zoh_previous(t_sig_num, s.value_raw, t_num)
        s.time = common_time

    signals.time = common_time
    if verbose:
        print(f'Done. signals.time = {len(common_time)} points')
    return signals


# ---------------------------------------------------------------------------
# cache layer
# ---------------------------------------------------------------------------
_MEMO = {}   # in-process: abspath -> (stat_key, SignalSet)


def _stat_key(path):
    """Identity of the file's current contents: (size, mtime_ns). None if missing."""
    try:
        st = os.stat(path)
        return (st.st_size, st.st_mtime_ns)
    except OSError:
        return None


def _load_disk_cache(cache_path, key):
    if key is None or not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, 'rb') as f:
            blob = pickle.load(f)
        if isinstance(blob, dict) and blob.get('key') == key:
            return blob.get('signals')
    except Exception:
        return None    # stale / unreadable cache -> just reparse
    return None


def _save_disk_cache(cache_path, key, signals):
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump({'key': key, 'signals': signals}, f,
                        protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print(f'(warning: could not write cache {cache_path}: {e})')


def parse_influx(csv_path='influx_data.csv', cache=True, cache_path=None, verbose=True):
    """Parse an InfluxDB CSV export into a SignalSet.

    cache      : if True (default), reuse a pickled parse when the CSV is unchanged,
                 and write one after parsing. Set False to always reparse and skip
                 writing a cache file.
    cache_path : where the pickle lives (default: '<csv_path>.parsed.pkl').
    verbose    : print progress / cache-hit messages.

    Skips the reparse in two situations:
      * same process, same file already parsed  -> in-memory memo
      * new process (e.g. a fresh `uv run`)      -> on-disk pickle, if CSV unchanged
    """
    csv_path = os.fspath(csv_path)
    abspath = os.path.abspath(csv_path)
    key = _stat_key(csv_path)

    # in-process memo (repeat calls within one run are free)
    memo = _MEMO.get(abspath)
    if memo is not None and memo[0] == key:
        if verbose:
            print(f'{csv_path}: reusing in-memory parse.')
        return memo[1]

    # on-disk cache (survives fresh processes / `uv run`)
    cpath = cache_path or (csv_path + '.parsed.pkl')
    if cache:
        cached = _load_disk_cache(cpath, key)
        if cached is not None:
            if verbose:
                print(f'{csv_path}: loaded from cache {os.path.basename(cpath)} '
                      f'({len(cached.time)} grid points).')
            _MEMO[abspath] = (key, cached)
            return cached

    # parse for real
    signals = _parse_influx_core(csv_path, verbose=verbose)
    _MEMO[abspath] = (key, signals)
    if cache:
        _save_disk_cache(cpath, key, signals)
        if verbose:
            print(f'{csv_path}: cached to {os.path.basename(cpath)}.')
    return signals


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else 'influx_data.csv'
    sig = parse_influx(path)
    print(f'\n{len(sig)} signals:')
    for name in sorted(sig):
        s = sig[name]
        print(f'  {name:<28} n={s.n:>8}  dur={s.duration_s:8.1f}s')
