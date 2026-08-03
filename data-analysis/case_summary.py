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

See data-analysis/README.md for the methodology behind each number, and for the
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
import case5_gradients as c5
import case6_max_yaw as c6


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


def collect_case5(grouped):
    """Roll gradient per event, from case5's own main().

    case5 returns a FLAT dict keyed "<event>_roll_<which>" / "<event>_pitch",
    because a gradient is not per-event in the same way the other cases are —
    it is a property of the car measured on that event. Re-keyed to
    {event: {...}} here so it slots into the same table.
    """
    out = {}
    flat = _quiet(c5.summary_only, grouped)
    for key, value in (flat or {}).items():
        if value is None:
            continue
        # rsplit("_", 1) was correct while every key ended in front/rear/avg;
        # the "_ground" variants broke it, since all three then collapsed
        # onto the single key "ground". Strip the known prefix instead.
        if key.startswith("skidpad_steady_roll_"):
            which = key[len("skidpad_steady_roll_"):]
            out.setdefault("skidpad", {})[which] = value
        elif "_roll_" in key:
            event, which = key.split("_roll_")
            out.setdefault(event, {}).setdefault(which, value)
        elif key.endswith("_pitch_ground"):
            out.setdefault(key[:-len("_pitch_ground")], {})["pitch_ground"] = value
        elif key.endswith("_pitch"):
            out.setdefault(key[:-6], {})["pitch"] = value
    return out


def collect_case6(grouped):
    """Peak yaw rate per event, from case6's own analyse + report.

    Same shape as case1-case4: {event: summary_dict_or_None}. Nothing is
    recomputed — case6's report_event is what produces these numbers.
    """
    out = {}
    for event in c6.CASE6_EVENTS:
        paths = grouped.get(event, [])
        if not paths:
            out[event] = None
            continue
        cutoff = SKIDPAD_CUTOFF_HZ if event == "skidpad" else AUTOX_END_CUTOFF_HZ
        results = [r for p in paths
                   if (r := _quiet(c6.analyze_file, p, cutoff)) is not None]
        summary = _quiet(c6.report_event, event, results) if results else None
        if summary and event in c6.STEADY_EVENTS:
            _quiet(c6.report_sustained, event, results, summary)
        out[event] = summary
    return out


# ── Table assembly ───────────────────────────────────────────────────────

ALL_EVENTS = ["skidpad", "accel", "brake", "autocross", "endurance"]

HEADERS = [
    "Event",
    "Sustained lat G",
    "Peak lat G",
    "Peak lon G",
    "Roll (deg) sus→gnd",
    "Pitch (deg) sus→gnd",
    "Worst corner travel",
    "Roll grad sus→gnd",
    "Pitch grad sus→gnd",
    "Peak yaw (deg/s)",
]

# Which case produced each column, as (label, span, report_dir). Rendered as
# a header row above HEADERS.
#
# WHY: the table reads as one flat result, but the nine columns come from
# five different scripts with five different methodologies — a peak, a
# median over a steady window, and a fitted slope are not the same kind of
# number, and "why is skidpad's roll a dash in one column and a value in
# another" is only answerable if you know which case owns which column.
# The spans must sum to len(HEADERS).
COLUMN_GROUPS = [
    ("", 1, None),
    ("case1 — G's", 3, "case1_max_gs"),
    ("case2 — roll", 1, "case2_max_roll"),
    ("case3 — pitch", 1, "case3_max_pitch"),
    ("case4 — corner travel", 1, "case4_combined_roll_pitch"),
    ("case5 — gradients", 2, "case5_gradients"),
    ("case6 — yaw", 1, "case6_max_yaw"),
]

assert sum(span for _, span, _ in COLUMN_GROUPS) == len(HEADERS), \
    "COLUMN_GROUPS spans must cover exactly the HEADERS columns"


def _fmt(value, spec, dash="—"):
    return dash if value is None else format(value, spec)


def build_rows(s1, s2, s3, s4, s5=None, s6=None):
    """One row per event. A dash means that case does not cover this event, or
    the quantity does not exist for it (e.g. skidpad has no separate peak G —
    it is a sustained measurement by design)."""
    rows = []
    for event in ALL_EVENTS:
        a, b, c, d = s1.get(event), s2.get(event), s3.get(event), s4.get(event)
        e = (s5 or {}).get(event)
        f = (s6 or {}).get(event)

        sustained = peak_lat = peak_lon = None
        if a:
            lo, hi = a.get("sustained_lat_g_min"), a.get("sustained_lat_g_max")
            if lo is not None and hi is not None:
                sustained = f"{lo:.2f}–{hi:.2f} g" if abs(hi - lo) > 5e-3 else f"{lo:.2f} g"
            peak_lat, peak_lon = a.get("peak_lat_g"), a.get("peak_lon_g")

        # case2 reports front/rear/avg; the avg is the whole-car headline.
        roll = None
        if b:
            roll_val, roll_gnd = b.get("avg_deg"), b.get("avg_deg_ground")
            if roll_val is not None:
                roll = f"{abs(roll_val):.2f}"
                if roll_gnd is not None:
                    roll += f"→{abs(roll_gnd):.2f}"

        # case3 reports typical (sustained or top-5 avg) and worst.
        pitch = None
        if c:
            typ, worst = c.get("typical_deg"), c.get("worst_deg")
            if worst is not None:
                pitch = f"{worst:.2f}"
                if c.get("worst_deg_ground") is not None:
                    pitch += f"→{c['worst_deg_ground']:.2f}"
            elif typ is not None:
                pitch = f"{typ:.2f}"        # * = sustained, no separate peak
                if c.get("typical_deg_ground") is not None:
                    pitch += f"→{c['typical_deg_ground']:.2f}"
                pitch += "*"

        travel = None
        if d:
            mm, corner = d.get("worst_travel_mm"), d.get("worst_corner")
            if mm is not None:
                travel = f"{mm:+.1f} mm ({corner})"

        # Whole-car roll gradient. Skidpad's is the steady-segment fit,
        # which is the cleanest and the one to quote.
        #
        # The two gradients cover DIFFERENT events by design — roll needs
        # sustained lateral G (skidpad, autocross, endurance) and pitch needs
        # sustained longitudinal G (accel, brake, autocross, endurance). So
        # accel and brake have a pitch gradient and no roll gradient, and
        # skidpad the reverse. The dashes are meaningful, not missing data.
        gradient = None
        if e and e.get("avg") is not None:
            gradient = f"{abs(e['avg']):.3f}"
            if e.get("avg_ground") is not None:
                gradient += f"→{abs(e['avg_ground']):.3f}"

        pitch_gradient = None
        if e and e.get("pitch") is not None:
            pitch_gradient = f"{abs(e['pitch']):.3f}"
            if e.get("pitch_ground") is not None:
                pitch_gradient += f"→{abs(e['pitch_ground']):.3f}"

        rows.append([
            event.upper(),
            sustained or "—",
            _fmt(peak_lat, ".2f"),
            _fmt(peak_lon, ".2f"),
            roll or "—",
            pitch or "—",
            travel or "—",
            gradient or "—",
            pitch_gradient or "—",
            f"{abs(f['peak_yaw_deg_s']):.1f}" if f and f.get("peak_yaw_deg_s") else "—",
        ])
    return rows


def _group_row(widths, sep="  "):
    """The case-attribution row, centred over each group's own columns.

    Falls back to the bare case name where the full label doesn't fit, so a
    narrow group reads "case2" rather than the truncated "case2 — ro".
    """
    cells, col = [], 0
    for label, span, _ in COLUMN_GROUPS:
        width = sum(widths[col:col + span]) + len(sep) * (span - 1)
        text = label if len(label) <= width else label.split(" — ")[0]
        cells.append(text[:width].center(width))
        col += span
    return sep.join(cells)


def print_console(rows):
    widths = [max(len(HEADERS[i]), max(len(r[i]) for r in rows)) for i in range(len(HEADERS))]
    print("\n" + _group_row(widths))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(HEADERS))
    print(line)
    print("  ".join("-" * widths[i] for i in range(len(HEADERS))))
    for r in rows:
        print("  ".join(r[i].ljust(widths[i]) for i in range(len(HEADERS))))


def write_markdown(rows, path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# CFR26 — Measured Envelope Summary\n\n")
        fh.write("Generated by `data-analysis/case_summary.py`. Do not edit by hand — "
                 "rerun the script.\n\n")
        # Markdown has no colspan, so the case attribution is prefixed onto
        # each header cell instead of sitting in a row above it. Same
        # information, and it survives being pasted anywhere.
        labelled = []
        col = 0
        for label, span, _ in COLUMN_GROUPS:
            prefix = f"{label.split(' — ')[0]}: " if label else ""
            labelled.extend(prefix + HEADERS[col + i] for i in range(span))
            col += span

        fh.write("| " + " | ".join(labelled) + " |\n")
        fh.write("|" + "|".join(["---"] * len(HEADERS)) + "|\n")
        for r in rows:
            fh.write("| " + " | ".join(r) + " |\n")
        fh.write(FOOTNOTES_MD)


FOOTNOTES_MD = """
→ = ground-referenced (chassis roll/pitch relative to the ROAD, i.e. with
tyre deflection added). The first figure is suspension-referenced — what the
shock pots actually measure, and the primary number. Design targets are
usually ground-referenced; see the README before comparing against one.

`*` = sustained value (median over the steady window); that event has no
separate peak by design.

`—` = not covered by that case, or the quantity does not apply.

**Roll** is case2's whole-car average (front and rear averaged). **Pitch** is
case3's single worst instant where one exists, otherwise the sustained
median. **Worst corner travel** is case4's single worst per-corner WHEEL
displacement, negative = compression.

All angles scale linearly with the motion ratio (1.188 front / 1.038 rear).
See `data-analysis/README.md` for full methodology and for the known data problems
that qualify these numbers — in particular that the `FL` shock pot is
suspect, that two autocross runs have unusable FRONT shock-pot data, and
that front and rear roll disagree by 4–23% for reasons not yet explained.
(An earlier version of this note called `braketest2.csv` unreliable. That
verdict was wrong and is retracted — see the README.)
"""

HTML_HEAD = """<style>
 :root{--line:#d0d0d0;--head:#f4f4f6;--muted:#555;--accent:#2a78d6;
       --band:#fafafb}
 body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
      margin:2rem auto;max-width:72rem;padding:0 1rem;line-height:1.5}
 table{border-collapse:collapse;width:100%;margin:1.5rem 0;
       font-variant-numeric:tabular-nums}
 .scroll{overflow-x:auto}
 th,td{border:1px solid var(--line);padding:.5rem .7rem;text-align:right;
       white-space:nowrap}
 th{background:var(--head);font-weight:600}
 td:first-child,th:first-child{text-align:left;font-weight:600}
 tbody tr:nth-child(even) td{background:var(--band)}
 /* The case-attribution row. Each group gets its own top border so the
    column blocks read as blocks rather than as one undifferentiated run. */
 tr.groups th{font-size:.8rem;font-weight:600;letter-spacing:.02em;
              text-align:center;border-bottom:none;padding:.45rem .7rem}
 tr.groups th.g{border-top:3px solid var(--accent)}
 tr.groups th a{color:var(--accent);text-decoration:none}
 tr.groups th a:hover{text-decoration:underline}
 tr.groups th.blank{border:none;background:none}
 caption{caption-side:top;text-align:left;font-size:.9rem;color:var(--muted);
         padding-bottom:.5rem}
 nav{font-size:.9rem;margin:.5rem 0 0}
 nav a{color:var(--accent);margin-right:1rem}
 .notes{font-size:.9rem;color:#444;border-left:3px solid #ccc;padding-left:1rem}
 @media (prefers-color-scheme:dark){
   :root{--line:#3a3b42;--head:#23242a;--muted:#c8c8cc;--accent:#3987e5;
         --band:#1b1c21}
   body{background:#15161a;color:#e6e6e8}
   .notes{color:#c8c8cc;border-color:#4a4b52}
 }
</style>
"""


def write_html(rows, path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("<!doctype html><meta charset='utf-8'>"
                 "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                 "<title>CFR26 Measured Envelope Summary</title>")
        fh.write(HTML_HEAD)
        fh.write("<h1>CFR26 — Measured Envelope Summary</h1>")
        fh.write("<nav><a href='index.html'>&#8962; all reports</a></nav>")
        fh.write("<div class='scroll'>")
        fh.write("<table><caption>Generated by data-analysis/case_summary.py — "
                 "rerun the script rather than editing this file. "
                 "Each column block below is one case script; the header links "
                 "to that case's full report.</caption>")

        # Two-tier header: which case owns the columns, then the columns.
        fh.write("<tr class='groups'>")
        for label, span, report_dir in COLUMN_GROUPS:
            if not label:
                fh.write(f"<th class='blank' colspan='{span}'></th>")
                continue
            inner = (f"<a href='{report_dir}/report.html'>{label}</a>"
                     if report_dir else label)
            fh.write(f"<th class='g' colspan='{span}'>{inner}</th>")
        fh.write("</tr>")

        fh.write("<tr>" + "".join(f"<th>{h}</th>" for h in HEADERS) + "</tr>")
        for r in rows:
            fh.write("<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>")
        fh.write("</table></div>")
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

    print("Collecting case5 (gradients)...")
    s5 = collect_case5(grouped)
    print("Collecting case6 (yaw rate)...", flush=True)
    s6 = collect_case6(grouped)

    rows = build_rows(s1, s2, s3, s4, s5, s6)
    print_console(rows)

    out_root = os.path.join("plots")
    os.makedirs(out_root, exist_ok=True)
    md_path = os.path.join(out_root, "case_summary.md")
    html_path = os.path.join(out_root, "case_summary.html")
    write_markdown(rows, md_path)
    write_html(rows, html_path)

    print(f"\n  * = sustained value (no separate peak by design)")
    print(f"  → = ground-referenced (tyre deflection added); the first "
          f"figure is suspension-referenced and is the primary one")
    print(f"  Saved: {md_path}")
    print(f"  Saved: {html_path}")
    print("\nSee data-analysis/README.md for methodology and known data problems.")


if __name__ == "__main__":
    main()
