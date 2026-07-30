# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
case_summary.py — one consolidated "where the car is" table across all four
cases, so you don't have to read four separate console reports to answer
"what did the car actually do?".

HOW IT AVOIDS DRIFTING FROM THE CASES: it does not recompute anything. It
imports case1-case4 and calls their own analyse + report functions, taking
the summary dicts they already return, with their console output suppressed.
If a case changes its methodology or its definition of "typical", this table
changes with it automatically. Nothing about roll, pitch or G's is
reimplemented here — this file is presentation only.

Because it calls the real analysis, the numbers here are identical to the
ones the individual scripts print. It skips only their plotting, so it is
faster than running all four (and relies on parse_influx's cache).

Outputs:
- Console table.
- plots/case_summary.md    — same table in Markdown, for pasting into docs/PRs
- plots/case_summary.html  — same table as a styled standalone page

Run it:
    uv run case_summary.py --dir comp2026_data

See scripts/README.md for the methodology behind each number, and for the
known data problems that qualify them.
"""

import os
import io
import sys
import glob
import argparse
import contextlib

from case_common import group_by_event, SKIDPAD_CUTOFF_HZ, AUTOX_END_CUTOFF_HZ

import case1_max_gs as c1
import case2_max_roll as c2
import case3_max_pitch as c3
import case4_combined_roll_pitch as c4


# ── Collectors: mirror each case's own main() loop, minus the plotting ────
#
# Each one returns {event: summary_dict_or_None}, where the summary dict is
# EXACTLY what that case's report_* function returns. Console output from the
# underlying reports is swallowed — this script prints its own table.

def _quiet(fn, *args, **kwargs):
    """Call fn with stdout suppressed, returning its result."""
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


def collect_case1(grouped):
    out = {}
    for event in c1.CASE1_EVENTS:
        paths = grouped.get(event, [])
        if not paths:
            out[event] = None
            continue
        if event == "skidpad":
            results = [r for p in paths if (r := _quiet(c1.analyze_skidpad_file, p)) is not None]
            _, summary = _quiet(c1.report_skidpad, results)
        else:
            results = [r for p in paths if (r := _quiet(c1.analyze_transient_file, p, event)) is not None]
            _, summary = _quiet(c1.report_transient, event, results)
        out[event] = summary
    return out


def collect_case2(grouped):
    out = {}
    for event in c2.CASE2_EVENTS:
        paths = grouped.get(event, [])
        if not paths:
            out[event] = None
            continue
        if event == "skidpad":
            results = [r for p in paths if (r := _quiet(c2.analyze_skidpad_file, p)) is not None]
            _, summary = _quiet(c2.report_skidpad, results)
        else:
            results = [r for p in paths if (r := _quiet(c2.analyze_transient_file, p, event)) is not None]
            _, summary = _quiet(c2.report_transient, event, results)
        out[event] = summary
    return out


def collect_case3(grouped):
    out = {}
    for event in c3.CASE3_EVENTS:
        paths = grouped.get(event, [])
        if not paths:
            out[event] = None
            continue
        if event == "skidpad":
            results = [r for p in paths if (r := _quiet(c3.analyze_skidpad_file, p)) is not None]
            summary = _quiet(c3.report_steady, event, results)
        elif event == "accel":
            results = [r for p in paths if (r := _quiet(c3.analyze_accel_file, p)) is not None]
            summary = _quiet(c3.report_steady, event, results)
        elif event == "brake":
            results = [r for p in paths if (r := _quiet(c3.analyze_brake_file, p)) is not None]
            summary = _quiet(c3.report_brake, results)
        else:
            results = [r for p in paths if (r := _quiet(c3.analyze_transient_file, p, event)) is not None]
            summary = _quiet(c3.report_transient, event, results)
        out[event] = summary
    return out


def collect_case4(grouped):
    out = {}
    for event in c4.CASE4_EVENTS:
        paths = grouped.get(event, [])
        if not paths:
            out[event] = None
            continue
        cutoff = SKIDPAD_CUTOFF_HZ if event == "skidpad" else AUTOX_END_CUTOFF_HZ
        results = [r for p in paths if (r := _quiet(c4.analyze_worst_case, p, cutoff)) is not None]
        out[event] = _quiet(c4.report_event, event, results) if results else None
    return out


# ── Table assembly ───────────────────────────────────────────────────────

ALL_EVENTS = ["skidpad", "accel", "brake", "autocross", "endurance"]

HEADERS = [
    "Event",
    "Sustained lat G",
    "Peak lat G",
    "Peak lon G",
    "Roll (deg)",
    "Pitch (deg)",
    "Worst corner travel",
]


def _fmt(value, spec, dash="—"):
    return dash if value is None else format(value, spec)


def build_rows(s1, s2, s3, s4):
    """One row per event. A dash means that case does not cover this event, or
    the quantity does not exist for it (e.g. skidpad has no separate peak G —
    it is a sustained measurement by design)."""
    rows = []
    for event in ALL_EVENTS:
        a, b, c, d = s1.get(event), s2.get(event), s3.get(event), s4.get(event)

        sustained = peak_lat = peak_lon = None
        if a:
            lo, hi = a.get("sustained_lat_g_min"), a.get("sustained_lat_g_max")
            if lo is not None and hi is not None:
                sustained = f"{lo:.2f}–{hi:.2f} g" if abs(hi - lo) > 5e-3 else f"{lo:.2f} g"
            peak_lat, peak_lon = a.get("peak_lat_g"), a.get("peak_lon_g")

        # case2 reports front/rear/avg; the avg is the whole-car headline.
        roll = None
        if b:
            roll_val = b.get("avg_deg")
            if roll_val is not None:
                roll = f"{abs(roll_val):.2f}"

        # case3 reports typical (sustained or top-5 avg) and worst.
        pitch = None
        if c:
            typ, worst = c.get("typical_deg"), c.get("worst_deg")
            if worst is not None:
                pitch = f"{worst:.2f}"
            elif typ is not None:
                pitch = f"{typ:.2f}*"       # * = sustained, no separate peak

        travel = None
        if d:
            mm, corner = d.get("worst_travel_mm"), d.get("worst_corner")
            if mm is not None:
                travel = f"{mm:+.1f} mm ({corner})"

        rows.append([
            event.upper(),
            sustained or "—",
            _fmt(peak_lat, ".2f"),
            _fmt(peak_lon, ".2f"),
            roll or "—",
            pitch or "—",
            travel or "—",
        ])
    return rows


def print_console(rows):
    widths = [max(len(HEADERS[i]), max(len(r[i]) for r in rows)) for i in range(len(HEADERS))]
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(HEADERS))
    print("\n" + line)
    print("  ".join("-" * widths[i] for i in range(len(HEADERS))))
    for r in rows:
        print("  ".join(r[i].ljust(widths[i]) for i in range(len(HEADERS))))


def write_markdown(rows, path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# CFR26 — Measured Envelope Summary\n\n")
        fh.write("Generated by `scripts/case_summary.py`. Do not edit by hand — "
                 "rerun the script.\n\n")
        fh.write("| " + " | ".join(HEADERS) + " |\n")
        fh.write("|" + "|".join(["---"] * len(HEADERS)) + "|\n")
        for r in rows:
            fh.write("| " + " | ".join(r) + " |\n")
        fh.write(FOOTNOTES_MD)


FOOTNOTES_MD = """
`*` = sustained value (median over the steady window); that event has no
separate peak by design.

`—` = not covered by that case, or the quantity does not apply.

**Roll** is case2's whole-car average (front and rear averaged). **Pitch** is
case3's single worst instant where one exists, otherwise the sustained
median. **Worst corner travel** is case4's single worst per-corner WHEEL
displacement, negative = compression.

All angles scale linearly with the motion ratio (1.15 front / 1.038 rear).
See `scripts/README.md` for full methodology and for the known data problems
that qualify these numbers — in particular that `braketest2.csv` is
unreliable, the `FL` shock pot is suspect, and front/rear roll disagree by
7–27% for reasons not yet explained.
"""

HTML_HEAD = """<style>
 body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
      margin:2rem auto;max-width:60rem;padding:0 1rem;line-height:1.5}
 table{border-collapse:collapse;width:100%;margin:1.5rem 0}
 th,td{border:1px solid #d0d0d0;padding:.5rem .7rem;text-align:right}
 th{background:#f4f4f6;font-weight:600}
 td:first-child,th:first-child{text-align:left;font-weight:600}
 caption{caption-side:top;text-align:left;font-size:.9rem;color:#555;
         padding-bottom:.5rem}
 .notes{font-size:.9rem;color:#444;border-left:3px solid #ccc;padding-left:1rem}
 @media (prefers-color-scheme:dark){
   body{background:#15161a;color:#e6e6e8}
   th{background:#23242a}
   th,td{border-color:#3a3b42}
   .notes{color:#c8c8cc;border-color:#4a4b52}
 }
</style>
"""


def write_html(rows, path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("<!doctype html><meta charset='utf-8'>"
                 "<title>CFR26 Measured Envelope Summary</title>")
        fh.write(HTML_HEAD)
        fh.write("<h1>CFR26 — Measured Envelope Summary</h1>")
        fh.write("<table><caption>Generated by scripts/case_summary.py — "
                 "rerun the script rather than editing this file.</caption>")
        fh.write("<tr>" + "".join(f"<th>{h}</th>" for h in HEADERS) + "</tr>")
        for r in rows:
            fh.write("<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>")
        fh.write("</table>")
        fh.write("<div class='notes'>")
        for para in FOOTNOTES_MD.strip().split("\n\n"):
            fh.write(f"<p>{para}</p>")
        fh.write("</div>")


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Folder containing CSVs")
    args = parser.parse_args()

    csv_paths = sorted(glob.glob(os.path.join(args.dir, "*.csv")))
    if not csv_paths:
        print(f"No CSVs found in '{args.dir}'.")
        sys.exit(1)

    grouped = group_by_event(csv_paths)

    print("Collecting case1 (G's)...", flush=True)
    s1 = collect_case1(grouped)
    print("Collecting case2 (roll)...", flush=True)
    s2 = collect_case2(grouped)
    print("Collecting case3 (pitch)...", flush=True)
    s3 = collect_case3(grouped)
    print("Collecting case4 (combined / corner travel)...", flush=True)
    s4 = collect_case4(grouped)

    rows = build_rows(s1, s2, s3, s4)
    print_console(rows)

    out_root = os.path.join("plots")
    os.makedirs(out_root, exist_ok=True)
    md_path = os.path.join(out_root, "case_summary.md")
    html_path = os.path.join(out_root, "case_summary.html")
    write_markdown(rows, md_path)
    write_html(rows, html_path)

    print(f"\n  * = sustained value (no separate peak by design)")
    print(f"  Saved: {md_path}")
    print(f"  Saved: {html_path}")
    print("\nSee scripts/README.md for methodology and known data problems.")


if __name__ == "__main__":
    main()
