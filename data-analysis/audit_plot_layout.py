# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Flag generated plots whose header text can overlap or run off the figure.

    uv run audit_plot_layout.py plots

Run it after ANY change to how a plot is built. Header overlap is
invisible until someone opens the one chart, at the one window size,
where it shows — it reached 34 of 84 figures here before anyone noticed,
and a further 30 had title lines too long to fit (Plotly does not wrap
title text). Both classes are cheap to detect from the figure JSON that
Plotly embeds in each HTML file, and near-impossible to catch by eye.

Reads that JSON and checks the top-of-figure stack — title, legend, and
subplot-title annotations — against an INDEPENDENT pixel model. The
constants here deliberately differ from the ones `case_common.py` uses to
lay the header out: a checker that shares the code's assumptions can only
confirm them.
"""
import glob
import json
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "plots"

# Independent estimate of the rendered header height. Deliberately NOT the
# same constants the code uses, so this can disagree with it: a Plotly
# title line renders ~24px, a smaller <sub> line ~18px, plus the title's
# own top padding.
TITLE_PAD_PX = 12
TITLE_MAIN_PX = 24
TITLE_SUB_PX = 18
LEGEND_ROW_PX = 22


def title_height(n_lines):
    return TITLE_PAD_PX + TITLE_MAIN_PX + max(n_lines - 1, 0) * TITLE_SUB_PX


def figures(path):
    """Yield every Plotly figure spec embedded in an HTML file.

    Uses raw_decode rather than a regex: the layout contains nested
    objects, so a non-greedy {.*?} stops at the first inner brace and
    silently yields an empty layout — which is how the first version of
    this script reported a clean bill of health on a figure whose legend
    was visibly sitting on its title.
    """
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    decoder = json.JSONDecoder()
    for match in re.finditer(r'Plotly\.newPlot\(\s*"[^"]+",\s*', text):
        pos = match.end()
        try:
            data, end = decoder.raw_decode(text, pos)
            pos = end
            while pos < len(text) and text[pos] in ", \n\t":
                pos += 1
            layout, _ = decoder.raw_decode(text, pos)
        except (json.JSONDecodeError, ValueError):
            continue
        yield data, layout


def check(path, data, layout):
    problems = []

    height = layout.get("height") or 450
    margin_t = (layout.get("margin") or {}).get("t")
    title = layout.get("title") or {}
    legend = layout.get("legend") or {}
    annotations = layout.get("annotations") or []

    # Subplot titles are the annotations pinned at/above the top of a
    # subplot domain with yref=paper.
    subplot_titles = [
        a for a in annotations
        if a.get("yref") == "paper" and isinstance(a.get("y"), (int, float))
        and a["y"] >= 0.98 and a.get("text")
    ]

    title_text = title.get("text") or ""
    title_lines = title_text.count("<br>") + 1 if title_text else 0
    title_px = title_height(title_lines) if title_lines else 0

    # --- 1. Legend in paper coords above the plot area, with subplot
    # titles present. Paper y>1 is a fraction of the PLOT AREA, so the
    # pixel offset drifts with figure height and the two collide.
    legend_y = legend.get("y")
    legend_yref = legend.get("yref", "paper")
    if (subplot_titles and legend_yref == "paper"
            and isinstance(legend_y, (int, float)) and legend_y >= 1.0):
        problems.append(
            f"legend at paper y={legend_y} sits in the same band as "
            f"{len(subplot_titles)} subplot title(s)")

    # --- 2. Top margin too small for the header stack it has to hold.
    if margin_t is not None and title_px:
        n_visible = sum(
            1 for tr in data
            if tr.get("showlegend") is not False and tr.get("name"))
        if legend.get("orientation") == "h" and legend_yref in ("paper", "container"):
            rows = max(1, -(-n_visible // 3))
            needed = title_px + rows * LEGEND_ROW_PX + (30 if subplot_titles else 8)
        else:
            needed = title_px + (30 if subplot_titles else 8)
        if margin_t < needed:
            problems.append(
                f"margin.t={margin_t} but header stack needs ~{needed}px "
                f"(title {title_lines} line(s), {n_visible} legend items)")

    # --- 3. Title lines that will not fit the figure. Plotly does not wrap
    # title text, so an over-long line runs off the side and is clipped.
    for line in title_text.split("<br>"):
        visible = re.sub(r"<[^>]+>", "", line).replace("&nbsp;", " ")
        if len(visible) > 130:
            problems.append(
                f"title line of {len(visible)} visible chars will not wrap "
                f"(\"{visible[:48]}...\")")
            break

    # --- 4. Title and legend overlapping in container coords.
    if (legend_yref == "container" and isinstance(legend_y, (int, float))
            and title.get("yref") == "container"):
        legend_top_px = (1 - legend_y) * height
        if legend_top_px < title_px:
            problems.append(
                f"legend top at {legend_top_px:.0f}px overlaps a "
                f"{title_px}px title block")

    return problems


bad = 0
total = 0
for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)):
    if os.path.basename(path) in ("report.html", "index.html", "case_summary.html"):
        continue
    for data, layout in figures(path):
        total += 1
        problems = check(path, data, layout)
        if problems:
            bad += 1
            print(f"\n{os.path.relpath(path, ROOT)}")
            for problem in problems:
                print(f"    - {problem}")

print(f"\n{total} figures checked, {bad} with header-overlap risk")
