"""
case_report.py — turn each case's console output and scattered plot files
into one self-contained web page.

Why: the results of a case currently live in two places that do not meet.
The numbers scroll past in a terminal and are gone; the plots sit as loose
HTML files under plots/<case>/<event>/ that you have to know about and open
one at a time. Neither is something you can hand to someone.

This produces plots/<case>/report.html — headline numbers, the full console
report, and every plot that case generated, in reading order.

DESIGN NOTE — the console text is TEE'd, not replaced. Everything still
prints exactly as before, so piping and grepping keep working and nothing
that depended on stdout breaks. The page is an addition, not a redirection.

Plots are embedded as lazy iframes pointing at the files the case already
wrote, rather than being regenerated or inlined. That keeps this decoupled:
a case can change how it builds a figure without this file knowing, and the
individual plot files stay usable on their own.

Usage in a case script:

    from case_report import report_page

    def main():
        with report_page("case2_max_roll", "Case 2 — Max Roll",
                         PLOTS_ROOT) as page:
            ...existing body, unchanged...
            page.summary = summaries_by_event
"""

import os
import io
import sys
import glob
import html
import datetime
import contextlib


STYLE = """
:root {
  color-scheme: light dark;
  --surface: #fcfcfb; --card: #ffffff; --border: #e4e3df;
  --text: #0b0b0b; --muted: #52514e; --accent: #2a78d6;
}
@media (prefers-color-scheme: dark) {
  :root {
    --surface: #1a1a19; --card: #232322; --border: #383835;
    --text: #ffffff; --muted: #c3c2b7; --accent: #3987e5;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 2rem 1.5rem 5rem; background: var(--surface);
  color: var(--text);
  font: 15px/1.6 ui-sans-serif, system-ui, -apple-system, sans-serif;
}
.wrap { max-width: 1200px; margin: 0 auto; }
h1 { font-size: 1.7rem; margin: 0 0 .25rem; }
h2 {
  font-size: 1.15rem; margin: 2.5rem 0 .75rem;
  padding-top: 1.25rem; border-top: 1px solid var(--border);
}
.sub { color: var(--muted); margin: 0 0 2rem; font-size: .9rem; }
.cards { display: flex; flex-wrap: wrap; gap: .75rem; margin: 1.5rem 0; }
/* Each event's headline numbers as one labelled band. A bare <h2> over a
   loose flex row held up at three events and fell apart at five: case5's
   32 cards and case6's 17 read as one undifferentiated wall of numbers.
   The rule under the event name is what makes the boundary survive a group
   whose cards wrap onto several lines. */
section.cardgroup { margin: 1.75rem 0 0; }
section.cardgroup > h2 {
  font-size: .78rem; text-transform: uppercase; letter-spacing: .08em;
  color: var(--muted); font-weight: 600;
  margin: 0; padding: 0 0 .45rem;
  border-top: none; border-bottom: 1px solid var(--border);
}
section.cardgroup > .cards { margin: .75rem 0 0; }
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 10px; padding: .85rem 1.1rem; min-width: 150px;
}
.card .label {
  color: var(--muted); font-size: .72rem; text-transform: uppercase;
  letter-spacing: .05em;
}
.card .value { font-size: 1.45rem; font-weight: 600; margin-top: .2rem; }
.card .unit { font-size: .85rem; color: var(--muted); font-weight: 400; }
/* The suspension-referenced figure, under the ground-referenced headline.
   Deliberately not a card of its own: two same-sized cards reading "1.73°"
   and "1.41°" for the same quantity is exactly the ambiguity that got the
   wrong number quoted for months. */
.card .alt {
  color: var(--muted); font-size: .72rem; margin-top: .3rem;
  border-top: 1px solid var(--border); padding-top: .3rem;
}
pre.console {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 10px; padding: 1.1rem 1.3rem; overflow-x: auto;
  font: 12.5px/1.55 ui-monospace, "Cascadia Code", Consolas, monospace;
  white-space: pre; color: var(--text);
}
figure { margin: 1.25rem 0 0; }
figcaption {
  color: var(--muted); font-size: .78rem; margin-bottom: .4rem;
  text-transform: uppercase; letter-spacing: .04em;
  display: flex; align-items: baseline; gap: .6rem; flex-wrap: wrap;
}
/* Reset the caption's uppercase/tracking — this is a control, not a label,
   and it has to read as clickable at a glance. */
a.popout {
  color: var(--accent); text-transform: none; letter-spacing: 0;
  font-weight: 600; font-size: .8rem; text-decoration: none;
  white-space: nowrap; margin-left: auto;
}
a.popout:hover { text-decoration: underline; }
iframe.plot {
  width: 100%; height: 520px; border: 1px solid var(--border);
  border-radius: 8px; background: #fff; display: block;
}
nav { margin-bottom: 2rem; font-size: .9rem; }
nav a { color: var(--accent); margin-right: 1rem; }
.empty { color: var(--muted); font-style: italic; }

/* Sticky bar: on a page this long, scrolling back to a link at the top to
   reach a sibling report is the main navigation cost. */
.bar {
  position: sticky; top: 0; z-index: 20; margin: -2rem -1.5rem 1.5rem;
  padding: .6rem 1.5rem; background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex; flex-wrap: wrap; gap: .4rem; align-items: center;
  font-size: .82rem;
}
.bar a {
  color: var(--muted); text-decoration: none; padding: .25rem .6rem;
  border: 1px solid var(--border); border-radius: 999px; white-space: nowrap;
}
.bar a:hover { color: var(--text); border-color: var(--accent); }
.bar a.home { color: var(--accent); border-color: var(--accent); }
.bar a.current {
  color: var(--text); font-weight: 600; background: var(--card);
  border-color: var(--muted);
}
.bar .spacer { flex: 1; }

/* Collapsed by default = the page opens on the numbers, not on 40 iframes.
   It also means nothing below a section has to be scrolled past to reach. */
details.section {
  border: 1px solid var(--border); border-radius: 10px;
  background: var(--card); margin: 1rem 0; overflow: hidden;
}
details.section > summary {
  cursor: pointer; padding: .8rem 1.1rem; font-weight: 600;
  list-style: none; display: flex; align-items: center; gap: .6rem;
}
details.section > summary::-webkit-details-marker { display: none; }
details.section > summary::before {
  content: "▸"; color: var(--muted); font-size: .85em;
  transition: transform .15s;
}
details.section[open] > summary::before { transform: rotate(90deg); }
details.section > summary:hover { color: var(--accent); }
details.section > summary .count {
  color: var(--muted); font-weight: 400; font-size: .8rem;
}
details.section > summary .note {
  color: var(--muted); font-weight: 400; font-size: .8rem; font-style: italic;
}
details.section .body { padding: 0 1.1rem 1.1rem; }
details.section h2 { margin-top: 1.5rem; }
details.section h2:first-child { border-top: none; padding-top: 0; margin-top: .5rem; }

/* Per-file heading inside an event section. */
h2.file {
  font-size: .95rem; font-family: ui-monospace, monospace;
  display: flex; align-items: center; gap: .5rem; flex-wrap: wrap;
}

.badge {
  font-size: .68rem; font-weight: 600; padding: .15rem .5rem;
  border-radius: 999px; letter-spacing: .03em; text-transform: uppercase;
  font-family: ui-sans-serif, system-ui, sans-serif;
}
.badge.error { background: #fdecec; color: #a3231f; }
.badge.warn  { background: #fdf3e2; color: #8a5a06; }
.badge.info  { background: #eaf1fb; color: #23558f; }
@media (prefers-color-scheme: dark) {
  .badge.error { background: #3a1f1e; color: #ff9a97; }
  .badge.warn  { background: #38301c; color: #f0c069; }
  .badge.info  { background: #1e2b3d; color: #8fbaf0; }
}

/* Known data problems, shown next to the files they apply to. */
.warn {
  border-left: 3px solid; border-radius: 6px; padding: .6rem .85rem;
  margin: .6rem 0; font-size: .85rem; line-height: 1.5;
}
.warn .who {
  display: block; font-family: ui-monospace, monospace; font-weight: 600;
  font-size: .78rem; margin-bottom: .2rem;
}
.warn.error { border-color: #d0342c; background: rgba(208, 52, 44, .07); }
.warn.warn  { background: rgba(214, 154, 42, .09); border-color: #d69a2a; }
.warn.info  { background: rgba(42, 120, 214, .07); border-color: var(--accent); }

table.instants { border-collapse: collapse; width: 100%; font-size: .85rem; }
table.instants th, table.instants td {
  border-bottom: 1px solid var(--border); padding: .45rem .6rem;
  text-align: left; vertical-align: top;
}
table.instants th {
  font-size: .72rem; text-transform: uppercase; letter-spacing: .04em;
  color: var(--muted); font-weight: 600;
}
table.instants .mono { font-family: ui-monospace, monospace; white-space: nowrap; }
table.instants .muted { color: var(--muted); }
table.instants .links a {
  color: var(--accent); margin-right: .7rem; white-space: nowrap;
}
.scroll { overflow-x: auto; }

ul.conv { margin: .3rem 0; padding-left: 1.2rem; font-size: .88rem; }
ul.conv li { margin: .35rem 0; }
ul.conv code {
  font-family: ui-monospace, monospace; font-size: .85em;
  background: var(--surface); padding: .1rem .3rem; border-radius: 4px;
}
"""


def _details(summary_html, body_html, open_by_default=False):
    return (f"<details class='section'{' open' if open_by_default else ''}>"
            f"<summary>{summary_html}</summary>"
            f"<div class='body'>{body_html}</div></details>")


class _Tee:
    """Write to the real stdout AND a buffer.

    Tee rather than capture, so the console behaves exactly as it always
    did — anything piping or grepping a case's output keeps working.
    """

    def __init__(self, stream, buffer):
        self._stream = stream
        self._buffer = buffer

    def write(self, text):
        self._stream.write(text)
        self._buffer.write(text)
        return len(text)

    def flush(self):
        self._stream.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)


class _Page:
    def __init__(self, case, title, plots_root):
        self.case = case
        self.title = title
        self.plots_root = plots_root
        self.summary = None
        # Unit for summary keys that don't carry one in their name. Left ""
        # for the cases whose keys end in _deg / _mm / _g and so speak for
        # themselves; see _label_and_unit.
        self.default_unit = ""
        self.buffer = io.StringIO()
        self.instants = []
        self.conventions = []

    def add_instant(self, event, csv_path, t_s, label, detail=""):
        """Record a moment worth being able to jump to.

        The console text has always said "worst at 116.59s" and nothing took
        you there — finding 116.59s by hand on an 1800-second interactive
        trace is genuinely tedious. These become a table of deep links that
        open the relevant plot already zoomed to that instant (see
        case_common's _DEEP_LINK_SCRIPT).

        DEDUPLICATED on (event, file, time-as-displayed). Different measures
        legitimately peak at the SAME sample — case1's autocross combined-G
        peak is its lateral-G peak, because lon was +0.03 g there — and that
        rendered as two table rows with the same time, same file and the
        same 1.763 g, which reads as a bug in the table. It is not: it is
        one instant that is the answer to two questions, so it becomes one
        row carrying both labels. The key rounds to the 0.01s the table
        prints, so rows a reader cannot tell apart never appear twice; a
        genuinely different instant one sample away (case2's 46.56 vs 46.57s
        avg/rear roll) still gets its own row.
        """
        stem = os.path.splitext(os.path.basename(csv_path))[0]
        key = (event, stem, round(float(t_s), 2))
        for existing in self.instants:
            if (existing["event"], existing["stem"],
                    round(existing["t"], 2)) == key:
                if label not in existing["label"].split(" · "):
                    existing["label"] += f" · {label}"
                # Same sample, so the context is the same reading; keep
                # whichever arrived with one rather than appending twice.
                if detail and not existing["detail"]:
                    existing["detail"] = detail
                return
        self.instants.append({
            "event": event,
            "stem": stem,
            "t": float(t_s),
            "label": label,
            "detail": detail,
        })

    def add_convention(self, text):
        """A sign/unit convention this case's readers need. Rendered in a
        fixed block on the page, because 'negative = compression' currently
        lives in one axis title on one plot."""
        self.conventions.append(text)


# Unit carried by a summary key's suffix. Longest match wins, so
# "peak_yaw_deg_s" reads °/s rather than seconds and "worst_travel_mm"
# reads mm rather than metres — case6's keys ALL missed the old three-way
# check, so every card on that page rendered as a bare number.
_UNIT_SUFFIXES = sorted(
    [("_deg_s", "°/s"), ("_deg", "°"), ("_mm", "mm"), ("_ms", "m/s"),
     ("_m", "m"), ("_g2", "g²"), ("_g", "g"), ("_s", "s"),
     ("_hz", "Hz"), ("_pct", "%")],
    key=lambda kv: -len(kv[0]),
)

# Stripped BEFORE the unit match and re-appended to the label, so
# "sustained_lat_g_min" is a g and not a unitless "sustained lat g min".
_QUALIFIER_SUFFIXES = ("_min", "_max", "_avg", "_median")

# Mirrors case_common.SUSP_SUFFIX. Duplicated for the same reason
# EVENT_DISPLAY_ORDER below is: this layer is stdlib-only at import time and
# does not drag numpy/scipy in for a five-character string.
SUSP_SUFFIX = "_susp"


def _label_and_unit(key, default_unit=""):
    """Display label and unit for a summary key.

    The unit token comes OUT of the label — "peak yaw 78.7 °/s" reads as a
    measurement, "peak yaw deg s 78.7" reads as a wall of words.

    `default_unit` covers a case whose keys do not carry their unit in the
    name. case5's are "roll_avg" / "pitch" / "steady_roll_front" — the event
    and the quantity, no unit token — so every card on that page rendered as
    a bare number. Renaming the keys was the alternative and is worse: they
    are parsed by case_summary.collect_case5 and pinned in the regression
    snapshot, so the whole page's unit would ride on a string nothing else
    should depend on.
    """
    qualifier = ""
    for suffix in _QUALIFIER_SUFFIXES:
        if key.endswith(suffix):
            key, qualifier = key[:-len(suffix)], suffix[1:]
            break

    unit = default_unit
    for suffix, symbol in _UNIT_SUFFIXES:
        if key.endswith(suffix):
            key, unit = key[:-len(suffix)], symbol
            break

    label = " ".join(p for p in (key.replace("_", " "), qualifier) if p)
    return label, unit


def _group_flat_summary(flat):
    """Split a FLAT {key: value} summary into {event: {metric: value}}.

    case5 returns its numbers flat because the keys already carry the event
    ("skidpad_roll_front"), which meant the whole page rendered as ONE
    undivided block of 32 cards under a "RESULTS" heading — the same
    numbers the other case pages break out per event. The prefix is right
    there in every key, so split on it and the page groups like the rest.
    Anything without a recognised event prefix stays together at the end.
    """
    grouped, leftover = {}, {}
    for key, value in flat.items():
        for event in EVENT_DISPLAY_ORDER:
            if key.startswith(f"{event}_"):
                grouped.setdefault(event, {})[key[len(event) + 1:]] = value
                break
        else:
            leftover[key] = value
    if leftover:
        grouped["results"] = leftover
    return grouped


def _cards(summary, default_unit=""):
    """Headline numbers, if the case handed us its summary dicts.

    Deliberately shallow: only scalar values one level under each event, so
    this shows the numbers a case actually headlines rather than every
    nested mode and intermediate.
    """
    if not summary:
        return ""

    # Two shapes in the wild, and silently rendering nothing for one of them
    # is worse than either. case1-case4 return {event: {key: value}};
    # case5 returns a FLAT {key: value} whose keys carry the event.
    flat = {k: v for k, v in summary.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)}

    grouped = {k: v for k, v in summary.items() if isinstance(v, dict)}

    if flat and not grouped:
        grouped = _group_flat_summary(flat)

    out = []
    # Same order as the plot sections and the results text — the cards used
    # to follow whatever order the case happened to build its dict in, so
    # case6 led with SKIDPAD, ACCEL, BRAKE while its plots below led with
    # SKIDPAD, AUTOCROSS, ENDURANCE.
    for event in sorted(grouped, key=_event_sort_key):
        values = grouped[event]
        if not isinstance(values, dict):
            continue

        scalars = [(k, v) for k, v in values.items()
                   if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if not scalars:
            continue

        # A "<key>_susp" scalar is the suspension-referenced twin of "<key>",
        # not a measurement in its own right, so it is folded into that
        # card's sub-line instead of getting a card. See SUSP_SUFFIX in
        # case_common for why ground-referenced is the headline.
        susp = {k[:-len(SUSP_SUFFIX)]: v for k, v in scalars
                if k.endswith(SUSP_SUFFIX)}

        out.append(f"<section class='cardgroup'>"
                   f"<h2>{html.escape(event.upper())}</h2><div class='cards'>")
        for key, value in scalars:
            if key.endswith(SUSP_SUFFIX):
                continue
            label, unit = _label_and_unit(key, default_unit)
            alt = ""
            if key in susp:
                shown = " ".join(x for x in (f"{susp[key]:.4g}",
                                             html.escape(unit)) if x)
                alt = f"<div class='alt'>{shown} suspension-ref</div>"
            out.append(
                f"<div class='card'><div class='label'>"
                f"{html.escape(label)}</div>"
                f"<div class='value'>{value:.4g} "
                f"<span class='unit'>{html.escape(unit)}</span></div>"
                f"{alt}</div>"
            )
        out.append("</div></section>")

    return "".join(out)


# Plots whose subject is the FILTER rather than the car. They answer "did
# the cutoff distort this?", which is a methodology question you check once
# and then stop looking at — so they belong at the bottom of the page, and
# behind a click, rather than between you and the g-g diagram.
FILTER_DIAGNOSTIC_SUFFIXES = ("_before_after",)


def _is_filter_diagnostic(rel):
    stem = os.path.splitext(os.path.basename(rel))[0]
    return any(stem.endswith(suffix) for suffix in FILTER_DIAGNOSTIC_SUFFIXES)


def _figure(rel):
    """One embedded plot, plus an explicit full-width escape hatch.

    The iframe is capped at the report column width, which is where these
    plots are hardest to work with — a g-g diagram or a 4-panel raw-vs-
    filtered trace wants the whole browser. Opening the plot file directly
    gives it the full viewport, and Plotly's own zoom/pan works there
    without fighting the page scroll.

    This link used to be a bare "↗" appended to the caption, which is the
    same affordance but effectively invisible. It is spelled out for the
    same reason build_cutoff_review.py spells it out.
    """
    label = os.path.splitext(os.path.basename(rel))[0].replace("_", " ")
    src = html.escape(rel.replace(os.sep, "/"))
    return (
        f"<figure><figcaption>{html.escape(label)}"
        f"<a class='popout' href='{src}' target='_blank' rel='noopener' "
        f"title='Open this plot in its own tab, at full browser width'>"
        f"open full width ↗</a></figcaption>"
        f"<iframe class='plot' loading='lazy' src='{src}'></iframe></figure>"
    )


def _warnings_block(stems):
    """Known data problems for these files, rendered where the files are.

    These were all already written up in the README, which is exactly the
    problem — a reader looking at four autocross runs presented identically
    has no way to know two of them have half the front roll signal missing.
    """
    from case_common import FILE_WARNINGS

    seen, rows = set(), []
    for stem in stems:
        for level, message in FILE_WARNINGS.get(stem, []):
            key = (stem, message)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                f"<div class='warn {level}'>"
                f"<span class='who'>{html.escape(stem)}</span>"
                f"{html.escape(message)}</div>"
            )
    return "".join(rows)


def _file_badges(stem):
    """Inline severity badge next to a file's name in the plot list."""
    from case_common import FILE_WARNINGS

    levels = {level for level, _ in FILE_WARNINGS.get(stem, [])}
    if "error" in levels:
        return "<span class='badge error'>known bad data</span>"
    if "warn" in levels:
        return "<span class='badge warn'>caveat</span>"
    if "info" in levels:
        return "<span class='badge info'>note</span>"
    return ""


# Per-file plots are named '<csv stem><suffix>'. Everything else in an
# event directory is a per-EVENT chart (roll_diagram, gg_diagram,
# roll_pitch_envelope) that pools all the files and has no single source.
#
# Longest first, so '_roll_before_after' is stripped whole rather than
# leaving a stray '_roll' behind after '_before_after' matches.
PER_FILE_SUFFIXES = tuple(sorted([
    "_roll_before_after",
    "_pitch_before_after",
    "_before_after",
    "_corner_travel",
], key=len, reverse=True))


def _stem_of(rel):
    """Source-CSV stem for a plot file, or "" if it isn't per-file."""
    base = os.path.splitext(os.path.basename(rel))[0]
    for suffix in PER_FILE_SUFFIXES:
        if base.endswith(suffix):
            return base[:-len(suffix)]
    return ""


def _instants_block(instants, plots_root):
    """Deep-link table: every instant the report quotes, one click away.

    Each row links to every plot belonging to that file, with '#t=<sec>' —
    the plots carry a small script that reads it and zooms there.
    """
    if not instants:
        return ""

    rows = []
    for item in instants:
        event_dir = os.path.join(plots_root, item["event"])
        links = []
        if os.path.isdir(event_dir):
            for name in sorted(os.listdir(event_dir)):
                if not name.endswith(".html") or not name.startswith(item["stem"]):
                    continue
                rel = f"{item['event']}/{name}"
                what = os.path.splitext(name)[0][len(item["stem"]):].strip("_")
                links.append(
                    f"<a href='{html.escape(rel)}#t={item['t']:.2f}' "
                    f"target='_blank'>{html.escape(what.replace('_', ' ') or 'plot')} ↗</a>"
                )

        rows.append(
            f"<tr><td class='mono'>{item['t']:.2f}s</td>"
            f"<td>{html.escape(item['label'])}</td>"
            f"<td class='mono'>{html.escape(item['stem'])}</td>"
            f"<td class='muted'>{html.escape(item['detail'])}</td>"
            f"<td class='links'>{' '.join(links) or '—'}</td></tr>"
        )

    return _details(
        f"Key instants <span class='count'>({len(instants)})</span> "
        f"<span class='note'>click to open a plot zoomed to that moment</span>",
        "<div class='scroll'><table class='instants'>"
        "<tr><th>time</th><th>what</th><th>file</th><th>context</th>"
        "<th>open at this instant</th></tr>"
        + "".join(rows) + "</table></div>",
        open_by_default=True,
    )


def _conventions_block(conventions):
    if not conventions:
        return ""
    items = "".join(f"<li>{c}</li>" for c in conventions)
    return _details(
        "Units and sign conventions "
        "<span class='note'>read before interpreting any number here</span>",
        f"<ul class='conv'>{items}</ul>",
        open_by_default=True,
    )


# ── Event display order ──────────────────────────────────────────────────
#
# Plot sections were ordered alphabetically, which buried SKIDPAD under
# ACCEL/AUTOCROSS/BRAKE/ENDURANCE even though it is the event these reports
# exist to answer. This is the same order as case_common.EVENT_KEYWORDS and
# CASE_EVENTS, so the plot sections now match the order the results text is
# already printed in. Duplicated rather than imported on purpose:
# case_report is stdlib-only and importing case_common would drag
# numpy/scipy into the reporting layer.
EVENT_DISPLAY_ORDER = ["skidpad", "autocross", "endurance", "brake", "accel"]


def _event_sort_key(group):
    """Sort key putting 'summary' first, then EVENT_DISPLAY_ORDER, then any
    unrecognised group alphabetically after those."""
    if group == "summary":
        return (0, 0, "")
    if group in EVENT_DISPLAY_ORDER:
        return (1, EVENT_DISPLAY_ORDER.index(group), "")
    return (2, 0, group)


def _plots(plots_root):
    """Every plot the case wrote, grouped by its event subdirectory.

    Returns (results_html, diagnostics_html, anchors). Results come first
    in reading order — headline chart, then per-event detail. The raw-vs-
    filtered plots are pulled out into `diagnostics_html` for the caller to
    place last: they are one per FILE, so on endurance and autocross they
    outnumber every other plot on the page and pushed the actual findings
    off the bottom of the scroll.
    """
    if not os.path.isdir(plots_root):
        return "<p class='empty'>No plots found.</p>", "", []

    paths = sorted(
        p for p in glob.glob(os.path.join(plots_root, "**", "*.html"),
                             recursive=True)
        if os.path.basename(p) != "report.html"
    )

    if not paths:
        return "<p class='empty'>No plots found.</p>", "", []

    groups, diagnostics, stems_by_event = {}, {}, {}
    for path in paths:
        rel = os.path.relpath(path, plots_root)
        group = os.path.dirname(rel) or "summary"
        target = diagnostics if _is_filter_diagnostic(rel) else groups
        target.setdefault(group, []).append(rel)
        # Which SOURCE FILES an event touches, from every plot in it — the
        # results and the diagnostics both. Warnings are keyed on the file,
        # and case2's only per-file plots are its diagnostics, so deriving
        # this from the results alone hid every warning it has.
        stem = _stem_of(rel)
        if stem:
            stems_by_event.setdefault(group, set()).add(stem)

    def _per_file(rels):
        """Plots grouped under their source file, per-event charts first.

        The "" key holds the per-event charts (roll_diagram, gg_diagram,
        …) — they pool every file, so they get no file heading and belong
        above the per-file detail rather than filed under one run.
        """
        by_stem = {}
        for rel in rels:
            by_stem.setdefault(_stem_of(rel), []).append(rel)

        chunks = [_figure(rel) for rel in by_stem.pop("", [])]
        for stem in sorted(by_stem):
            chunks.append(f"<h2 class='file'>{html.escape(stem)}"
                          f"{_file_badges(stem)}</h2>")
            chunks.extend(_figure(rel) for rel in by_stem[stem])
        return "".join(chunks)

    def _flag_badge(group):
        flagged = sum(1 for stem in stems_by_event.get(group, ())
                      if _file_badges(stem))
        return (f"<span class='badge error'>{flagged} file"
                f"{'s' if flagged != 1 else ''} flagged</span>"
                if flagged else "")

    ordered = sorted(groups, key=_event_sort_key)

    out, anchors = [], []
    for group in ordered:
        anchor = f"plots-{group}"
        anchors.append((group, anchor))

        # The banner lists every warning for the event, whichever section
        # the affected file's plots ended up in.
        banner = _warnings_block(sorted(stems_by_event.get(group, ())))

        out.append(
            f"<div id='{html.escape(anchor)}'>" +
            _details(
                f"{html.escape(group.upper())} — plots "
                f"<span class='count'>({len(groups[group])})</span>"
                f"{_flag_badge(group)}",
                banner + _per_file(groups[group]),
                # Results plots — the g-g diagram, the roll/pitch envelope,
                # the travel distributions — open by default. These ARE the
                # findings, and having to click into every event to see them
                # made the page open on nothing but headings. The raw-vs-
                # filtered diagnostics below stay closed: they answer "did
                # the cutoff distort this?", which you check once. The
                # iframes are lazy, so an open section costs nothing until
                # it is actually scrolled into view.
                open_by_default=True,
            ) + "</div>"
        )

    diag_html = ""
    if diagnostics:
        inner = []
        for group in sorted(diagnostics, key=_event_sort_key):
            inner.append(f"<h2>{html.escape(group.upper())}"
                         f"{_flag_badge(group)}</h2>")
            inner.append(_warnings_block(sorted(stems_by_event.get(group, ()))))
            inner.append(_per_file(diagnostics[group]))
        n = sum(len(v) for v in diagnostics.values())
        diag_html = (
            "<div id='filtering'>" +
            _details(
                f"Raw vs. filtered — filtering check "
                f"<span class='count'>({n})</span> "
                f"<span class='note'>methodology, not results</span>",
                "<p class='sub'>Grey is the raw sensor trace, colour is what "
                "the filter kept, and the right-hand panel is the difference — "
                "exactly what the cutoff discarded. A formless residual means "
                "the cutoff is safe; visibly coherent oscillation in it means "
                "real motion is being deleted.</p>" + "".join(inner),
            ) + "</div>"
        )

    return "".join(out), diag_html, anchors


@contextlib.contextmanager
def report_page(case, title, plots_root):
    """Tee this case's console output and write plots_root/report.html."""
    page = _Page(case, title, plots_root)

    real_stdout = sys.stdout
    sys.stdout = _Tee(real_stdout, page.buffer)

    try:
        yield page
    finally:
        sys.stdout = real_stdout

        os.makedirs(plots_root, exist_ok=True)
        out_path = os.path.join(plots_root, "report.html")

        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        results_html, diagnostics_html, anchors = _plots(plots_root)

        # Sibling reports, so you can move between cases without going via
        # the index. Built from what is on disk rather than hardcoded, so a
        # new case script appears here automatically.
        siblings = []
        parent = os.path.dirname(os.path.abspath(plots_root))
        listing = sorted(os.listdir(parent)) if os.path.isdir(parent) else []

        for other in listing:
            # THIS page counts even though its report.html is written a few
            # lines below and so does not exist yet — without the special
            # case, every report omitted itself from its own nav, which read
            # as "case4 doesn't exist" on the case4 page.
            if other != case and not os.path.exists(
                    os.path.join(parent, other, "report.html")):
                continue
            if not os.path.isdir(os.path.join(parent, other)):
                continue
            label = other.split("_")[0]
            current = " class='current'" if other == case else ""
            siblings.append(
                f"<a href='../{html.escape(other)}/report.html'{current}>"
                f"{html.escape(label)}</a>"
            )

        jump = ""
        if page.instants:
            jump += "<a href='#instants'>key instants</a>"
        jump += "".join(
            f"<a href='#{html.escape(a)}'>{html.escape(g)}</a>"
            for g, a in anchors
        )
        if diagnostics_html:
            jump += "<a href='#filtering'>filtering</a>"

        # Per-case method notes (docs/case2.md, docs/case4.md, …), linked from
        # the results rather than left in a file a reader may never open — the
        # same reason FILE_WARNINGS renders next to the plots. Keyed on the
        # "caseN" prefix, and only linked when the file actually exists, so
        # cases without notes are unaffected.
        doc_link = ""
        doc_name = f"{case.split('_')[0]}.md"
        doc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "docs", doc_name)
        if os.path.exists(doc_path):
            doc_link = (f"<a href='../../docs/{html.escape(doc_name)}'>"
                        f"calculations &amp; sources</a>")

        bar = (
            "<div class='bar'>"
            "<a class='home' href='../index.html'>&#8962; all reports</a>"
            "<a href='../case_summary.html'>summary table</a>"
            + "".join(siblings)
            + doc_link
            + "<span class='spacer'></span>"
            + jump
            + "</div>"
        )

        console = _details(
            "Console report <span class='note'>full numeric output</span>",
            f"<pre class='console'>{html.escape(page.buffer.getvalue())}</pre>",
        )

        body = (
            bar
            + f"<h1>{html.escape(title)}</h1>"
            + f"<p class='sub'>{html.escape(case)} &middot; generated {stamp}</p>"
            + _conventions_block(page.conventions)
            + _cards(page.summary, page.default_unit)
            + f"<div id='instants'>{_instants_block(page.instants, plots_root)}</div>"
            + console
            + results_html
            + diagnostics_html
        )

        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(
                f"<!doctype html><html><head><meta charset='utf-8'>"
                f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
                f"<title>{html.escape(title)}</title><style>{STYLE}</style>"
                f"</head><body><div class='wrap'>{body}</div></body></html>"
            )

        print(f"\nReport: {out_path}")


# One line saying what each case actually answers. A bare list of directory
# names ("case4_combined_roll_pitch") tells you nothing about which page to
# open, and this index is the entry point to all of it.
CASE_BLURBS = {
    "case1_max_gs": ("Max G's",
                     "How hard the car cornered and braked — sustained and peak, "
                     "with the g-g envelope."),
    "case2_max_roll": ("Max roll",
                       "Body roll angle, front and rear separately, plus the "
                       "front-vs-rear disagreement."),
    "case3_max_pitch": ("Max pitch",
                        "Body pitch angle under braking and acceleration, with "
                        "braking windows detected from brake pressure."),
    "case4_combined_roll_pitch": ("Combined loading",
                                  "Worst per-corner wheel travel, decomposed "
                                  "exactly into roll, pitch, heave and warp."),
    "case5_gradients": ("Roll &amp; pitch gradient",
                        "The headline suspension metric — degrees per g, a "
                        "property of the car rather than of the run."),
    "case6_max_yaw": ("Max yaw rate",
                      "How fast the car rotates about its vertical axis, plus "
                      "the corner radius the driver actually followed."),
}


def write_index(plots_dir="plots"):
    """One page linking every case report that exists."""
    os.makedirs(plots_dir, exist_ok=True)
    out_path = os.path.join(plots_dir, "index.html")

    top = ""
    if os.path.exists(os.path.join(plots_dir, "case_summary.html")):
        top = (
            "<a class='entry lead' href='case_summary.html'>"
            "<div class='name'>Summary table — every case, one row per event</div>"
            "<div class='blurb'>Start here. Nine columns across five case "
            "scripts, with each column block linking back to the case that "
            "produced it.</div></a>"
        )

    entries = []
    for path in sorted(glob.glob(os.path.join(plots_dir, "*", "report.html"))):
        case = os.path.basename(os.path.dirname(path))
        rel = os.path.relpath(path, plots_dir).replace(os.sep, "/")
        name, blurb = CASE_BLURBS.get(case, (case.replace("_", " "), ""))
        entries.append(
            f"<a class='entry' href='{html.escape(rel)}'>"
            f"<div class='name'>{name}</div>"
            f"<div class='blurb'>{blurb}</div>"
            f"<div class='src'>{html.escape(case)}.py</div></a>"
        )

    body = top + ("<div class='grid'>" + "".join(entries) + "</div>"
                  if entries else "<p class='empty'>No reports generated yet.</p>")

    index_style = """
.grid { display: grid; gap: .75rem; margin-top: 1rem;
        grid-template-columns: repeat(auto-fill, minmax(270px, 1fr)); }
.entry {
  display: block; text-decoration: none; color: inherit;
  background: var(--card); border: 1px solid var(--border);
  border-radius: 10px; padding: 1rem 1.15rem;
}
.entry:hover { border-color: var(--accent); }
.entry.lead { display: block; margin-top: 1rem; }
.entry .name { font-weight: 600; color: var(--accent); margin-bottom: .3rem; }
.entry .blurb { color: var(--muted); font-size: .87rem; }
.entry .src {
  color: var(--muted); font-size: .72rem; margin-top: .6rem;
  font-family: ui-monospace, monospace;
}
"""

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(
            f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>CFR26 telemetry analysis</title>"
            f"<style>{STYLE}{index_style}</style>"
            f"</head><body><div class='wrap'>"
            f"<h1>CFR26 telemetry analysis</h1>"
            f"<p class='sub'>Measured envelope from the 2026 competition "
            f"telemetry. Each page is regenerated by running its case script; "
            f"see <code>data-analysis/README.md</code> for methodology and the "
            f"known data problems that qualify these numbers.</p>"
            f"{body}</div></body></html>"
        )

    return out_path
