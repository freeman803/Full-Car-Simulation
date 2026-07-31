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
}
iframe.plot {
  width: 100%; height: 520px; border: 1px solid var(--border);
  border-radius: 8px; background: #fff; display: block;
}
nav { margin-bottom: 2rem; font-size: .9rem; }
nav a { color: var(--accent); margin-right: 1rem; }
.empty { color: var(--muted); font-style: italic; }
"""


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
        self.buffer = io.StringIO()


def _cards(summary):
    """Headline numbers, if the case handed us its summary dicts.

    Deliberately shallow: only scalar values one level under each event, so
    this shows the numbers a case actually headlines rather than every
    nested mode and intermediate.
    """
    if not summary:
        return ""

    # Two shapes in the wild, and silently rendering nothing for one of them
    # is worse than either. case1-case4 return {event: {key: value}};
    # case5 returns a FLAT {key: value} because its keys already carry the
    # event ("skidpad_roll_front"). Normalise rather than force one shape on
    # the cases, since the flat form reads better in case5's own report.
    flat = {k: v for k, v in summary.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)}

    grouped = {k: v for k, v in summary.items() if isinstance(v, dict)}

    if flat and not grouped:
        grouped = {"results": flat}

    out = []
    for event, values in grouped.items():
        if not isinstance(values, dict):
            continue

        scalars = [(k, v) for k, v in values.items()
                   if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if not scalars:
            continue

        out.append(f"<h2>{html.escape(event.upper())}</h2><div class='cards'>")
        for key, value in scalars:
            unit = ("deg" if key.endswith("_deg")
                    else "mm" if key.endswith("_mm")
                    else "g" if key.endswith("_g") else "")
            out.append(
                f"<div class='card'><div class='label'>"
                f"{html.escape(key.replace('_', ' '))}</div>"
                f"<div class='value'>{value:.4g} "
                f"<span class='unit'>{unit}</span></div></div>"
            )
        out.append("</div>")

    return "".join(out)


def _plots(plots_root):
    """Every plot the case wrote, grouped by its event subdirectory.

    Sorted so the per-event detail follows the headline chart that usually
    sits at the root of plots_root.
    """
    if not os.path.isdir(plots_root):
        return "<p class='empty'>No plots found.</p>"

    paths = sorted(
        p for p in glob.glob(os.path.join(plots_root, "**", "*.html"),
                             recursive=True)
        if os.path.basename(p) != "report.html"
    )

    if not paths:
        return "<p class='empty'>No plots found.</p>"

    groups = {}
    for path in paths:
        rel = os.path.relpath(path, plots_root)
        group = os.path.dirname(rel) or "summary"
        groups.setdefault(group, []).append(rel)

    out = []
    for group in sorted(groups, key=lambda g: (g != "summary", g)):
        out.append(f"<h2>{html.escape(group.upper())} — plots</h2>")
        for rel in groups[group]:
            label = os.path.splitext(os.path.basename(rel))[0].replace("_", " ")
            out.append(
                f"<figure><figcaption>{html.escape(label)}</figcaption>"
                f"<iframe class='plot' loading='lazy' "
                f"src='{html.escape(rel.replace(os.sep, '/'))}'></iframe>"
                f"</figure>"
            )
    return "".join(out)


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

        body = (
            f"<h1>{html.escape(title)}</h1>"
            f"<p class='sub'>{html.escape(case)} &middot; generated {stamp}</p>"
            f"<nav><a href='../case_summary.html'>summary table</a>"
            f"<a href='../index.html'>all reports</a></nav>"
            + _cards(page.summary)
            + "<h2>Console report</h2>"
            + f"<pre class='console'>{html.escape(page.buffer.getvalue())}</pre>"
            + _plots(plots_root)
        )

        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(
                f"<!doctype html><html><head><meta charset='utf-8'>"
                f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
                f"<title>{html.escape(title)}</title><style>{STYLE}</style>"
                f"</head><body><div class='wrap'>{body}</div></body></html>"
            )

        print(f"\nReport: {out_path}")


def write_index(plots_dir="plots"):
    """One page linking every case report that exists."""
    entries = []
    for path in sorted(glob.glob(os.path.join(plots_dir, "*", "report.html"))):
        case = os.path.basename(os.path.dirname(path))
        entries.append((case, os.path.relpath(path, plots_dir)))

    extra = [(name, rel) for name, rel in [
        ("Summary table (all four cases)", "case_summary.html"),
    ] if os.path.exists(os.path.join(plots_dir, rel))]

    items = "".join(
        f"<li><a href='{html.escape(rel.replace(os.sep, '/'))}'>"
        f"{html.escape(name.replace('_', ' '))}</a></li>"
        for name, rel in extra + entries
    ) or "<li class='empty'>No reports generated yet.</li>"

    os.makedirs(plots_dir, exist_ok=True)
    out_path = os.path.join(plots_dir, "index.html")

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(
            f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>CFR26 telemetry analysis</title><style>{STYLE}</style>"
            f"</head><body><div class='wrap'>"
            f"<h1>CFR26 telemetry analysis</h1>"
            f"<p class='sub'>Generated reports. Run a case script to refresh its "
            f"page.</p><ul>{items}</ul></div></body></html>"
        )

    return out_path
