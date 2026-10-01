# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pandas", "scipy", "plotly"]
# ///
"""
cfr27_report.py — single-page HTML report combining everything from the
CFR27 chassis-stiffness sensitivity work: the headline target, the
criterion x build-loss grid, the ARB fitment comparison, a rules-of-thumb
cross-check, and Riley & George's vehicle-vs-frame-stiffness chart.

NOTHING IS RE-DERIVED HERE. Every number comes from cfr27_target.py,
torsional_stiffness.py and riley_vehicle_stiffness.py -- this script only
formats and assembles what those already compute.

    uv run cfr27_report.py

Writes plots/cfr27_report/report.html.
"""

import os

import cfr27_target as c27
import torsional_stiffness as ts
import riley_vehicle_stiffness as riley

OUTPUT_PATH = os.path.join("plots", "cfr27_report", "report.html")

# report styling, kept local (not imported from case_summary.py) to avoid
# pulling in its telemetry dependencies for a handful of CSS rules
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
 caption{caption-side:top;text-align:left;font-size:.9rem;color:var(--muted);
         padding-bottom:.5rem}
 .headline{font-size:1.4rem;font-weight:700;background:var(--head);
           border:1px solid var(--line);border-radius:.4rem;padding:1rem 1.2rem;
           margin:1rem 0}
 .notes{font-size:.9rem;color:#444;border-left:3px solid #ccc;padding-left:1rem}
 h2{margin-top:2.5rem;border-bottom:2px solid var(--accent);padding-bottom:.3rem}
 @media (prefers-color-scheme:dark){
   :root{--line:#3a3b42;--head:#23242a;--muted:#c8c8cc;--accent:#3987e5;
         --band:#1b1c21}
   body{background:#15161a;color:#e6e6e8}
   .notes{color:#c8c8cc;border-color:#4a4b52}
 }
</style>
"""


def _table(headers, rows, caption=None):
    out = ["<div class='scroll'><table>"]
    if caption:
        out.append(f"<caption>{caption}</caption>")
    out.append("<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>")
    for r in rows:
        out.append("<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>")
    out.append("</table></div>")
    return "\n".join(out)


def sensitivity_table():
    """Criterion x build-loss grid, ARB adjustable across its confirmed
    range at both ends -- same method as cfr27_target.report_sensitivity()."""
    s = c27.setups()
    criteria = (0.80, 0.85, 0.90, 0.95)
    losses = (0.0, 0.05, 0.10, 0.15)
    headers = ["criterion"] + [f"{100*l:.0f}% loss" for l in losses]
    rows = []
    for c in criteria:
        floor = ts.stiffness_for_box(s, threshold=c,
                                     front_mass_fraction=c27.P["front_mass_fraction"])[0]
        row = [f"{100*c:.0f}%"]
        for l in losses:
            tgt = floor * ts.build_multiplier(l)
            current = abs(c - c27.P["criterion"]) < 1e-9 and abs(l - c27.P["build_loss"]) < 1e-9
            row.append(f"{tgt:.0f}" + (" &larr;" if current else ""))
        rows.append(row)
    return headers, rows


def arb_table():
    """ARB fitment comparison -- same method as cfr27_target.report_arb_scenarios()."""
    headers = ["scenario", "target N&middot;m/deg", "floor", "swing, pts"]
    rows = []
    for label, tgt, floor, change in c27.arb_scenarios():
        mark = " (confirmed default)" if label.startswith("both, adjustable") else ""
        rows.append([label + mark, f"{tgt:.0f}", f"{floor:.0f}", f"{change:.2f}"])
    return headers, rows


def rules_of_thumb_table(tgt, k_total_lo, k_total_hi):
    headers = ["source", "N&middot;m/deg", "note"]
    rows = [
        ["CFR27 target (this work)", f"{tgt:.0f}",
         "90% criterion, 10% build loss, full box + ARB adjustable both ends"],
        ["CFR26 (no ARB), your own prior car", "1341", "same criterion and build loss"],
        ["Milliken/RCVD, 3-5x total roll stiffness", f"{3*k_total_lo:.0f}–{5*k_total_hi:.0f}",
         f"3x of softest reachable setup ({k_total_lo:.0f}) to 5x of stiffest ({k_total_hi:.0f})"],
        ["Cardiff, \"typical FSAE target\"", "1500", "paper-stated target"],
        ["MRacing paper, lap sim", "1550", "transient, comparable car"],
        ["Michigan, 30 yrs iteration", "2100", "MEASURED -- the strongest comparison point"],
        ["“what most FSAE teams build”", "1200–1500",
         "loose benchmark, mostly cars without a wide-range ARB"],
        ["Deakin, typical FSAE total roll stiffness", "500–1500",
         f"your achieved range: {k_total_lo:.0f}–{k_total_hi:.0f}"],
    ]
    return headers, rows


def main():
    tgt, floor, soft, stiff, change = c27.target()
    s = c27.setups()
    tot = [kf + kr for kf, kr, _ in s]
    k_total_lo, k_total_hi = min(tot), max(tot)

    k1, k2, k3, k4 = riley.cfr27_corner_rates()
    fig, springs_ceiling = riley.build_figure(k1, k2, k3, k4)
    riley_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

    norm_fig = riley.build_normalized_figure()
    zoom_fig = riley.build_normalized_figure(y_range=(0.85, 1.0), zoomed=True)
    riley_norm_html = (norm_fig.to_html(full_html=False, include_plotlyjs=False)
                       + zoom_fig.to_html(full_html=False, include_plotlyjs=False))

    sens_h, sens_r = sensitivity_table()
    arb_h, arb_r = arb_table()
    rot_h, rot_r = rules_of_thumb_table(tgt, k_total_lo, k_total_hi)

    html = []
    html.append("<!doctype html><meta charset='utf-8'>"
                "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                "<title>CFR27 Chassis Torsional Stiffness</title>")
    html.append(HTML_HEAD)
    html.append("<h1>CFR27 Chassis Torsional Stiffness</h1>")
    html.append("<p class='notes'>Generated by <code>data-analysis/cfr27_report.py</code>"
                " &mdash; rerun the script rather than editing this file. Model and"
                " derivation live in <code>torsional_stiffness.py</code> /"
                " <code>cfr27_target.py</code>; the chart's math is in"
                " <code>riley_vehicle_stiffness.py</code>.</p>")

    html.append(f"<div class='headline'>DESIGN TO {tgt:.0f} N&middot;m/deg &nbsp;&mdash;&nbsp; "
                f"{100*c27.P['criterion']:.0f}% criterion, {100*c27.P['build_loss']:.0f}%"
                f" build loss (floor {floor:.0f}, sized off {soft} &harr; {stiff},"
                f" {change:.2f} pts commanded)</div>")

    html.append("<h2>Criterion &times; build-loss sensitivity</h2>")
    html.append("<p class='notes'>Full owned spring box, ARB adjustable across its confirmed"
                " range at both ends (70mm/100mm lever) &mdash; not fixed to one setting.</p>")
    html.append(_table(sens_h, sens_r))

    html.append("<h2>ARB fitment comparison</h2>")
    html.append(f"<p class='notes'>Full spring box, {100*c27.P['criterion']:.0f}% criterion,"
                f" {100*c27.P['build_loss']:.0f}% build loss. “Confirmed default” is"
                " the scenario the headline target above uses.</p>")
    html.append("<p class='notes'><strong>Floor</strong>: the frame stiffness that meets the"
                " criterion before the build-loss uplift (target = floor &divide; (1 &minus;"
                " build loss)).</p>")
    html.append("<p class='notes'><strong>Swing, pts</strong>: the front/rear load-transfer"
                " swing, in percentage points, between the softest and stiffest reachable"
                " setups if the chassis were perfectly rigid &mdash; the commanded change the"
                " criterion has to protect.</p>")
    html.append(_table(arb_h, arb_r))

    html.append("<h2>Rules of thumb</h2>")
    html.append("<p class='notes'>Independent cross-checks, not the derivation &mdash; the"
                " headline number is sized off Deakin's criterion applied to the real"
                " hardware, not off any of these.</p>")
    html.append(_table(rot_h, rot_r))

    html.append("<h2>Riley &amp; George: vehicle vs. frame stiffness</h2>")
    html.append("<p class='notes'>One-wheel-bump series chain, springs left in circuit"
                " (not locked out, as a real twist test would). CFR27's four corner springs"
                f" alone cap this at {springs_ceiling:.1f} N&middot;m/deg regardless of frame"
                " or suspension-structure stiffness &mdash; a different question from the"
                " target above; see <code>torsional_stiffness.py</code>'s module docstring"
                " for the identity and the distinction.</p>")
    html.append(riley_html)

    html.append("<h2>Riley &amp; George: normalized by wheel rate</h2>")
    html.append("<p class='notes'>Riley's own convention (his Fig. 12/13) &mdash; frame"
                " stiffness and vehicle stiffness both divided by a single wheel rate, so it's"
                " generic rather than CFR27-specific (CFR27's front/rear corner rates differ"
                " ~46%, so there's no one wheel rate to normalize the chart above by). Dashed"
                " vertical lines mark the 80/85/90/95% criterion milestones for the"
                " 60&times;-wheel-rate curve. Second panel is the same curves zoomed to the"
                " 0.85&ndash;1.0 saturation region.</p>")
    html.append(riley_norm_html)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(html))
    print(f"report written to {os.path.abspath(OUTPUT_PATH)}")


if __name__ == "__main__":
    main()
