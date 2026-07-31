"""
build_cutoff_review.py — generate the cutoff-selection worksheet.

Why this exists: `case_common.py` currently carries exactly TWO cutoff
constants, `SKIDPAD_CUTOFF_HZ = 2.0` and `AUTOX_END_CUTOFF_HZ = 5.0`, and
applies them to every signal regardless of that signal's actual content.
Accel and brake events have no chosen cutoff at all — they silently
inherit the 5 Hz autocross value. This tool lays out every decision that
actually needs making, puts the relevant plots next to each one, and gives
you somewhere to record the answer.

It does not decide anything. It builds the worksheet; you fill it in.

Run it AFTER filter_compare.py has produced plots for every file:

    uv run filter_compare.py comp2026_data/skidpad_austin_both.csv \
        comp2026_data/autocross_*.csv comp2026_data/endurance_full.csv \
        --freqs 2 3 5 8 10 15 20

    uv run filter_compare.py comp2026_data/accel_*.csv \
        comp2026_data/braketest*.csv --freqs 2 3 5 8 10 15 20 --zoom-on-peak

    uv run build_cutoff_review.py

Outputs:

    review_cutoffs/<event>.html    one scrollable page per event, plots
                                   embedded inline in worklist order
    cutoff_decisions.yaml          one block per cell, with blank
                                   `chosen_hz:` / `why:` fields to fill in

WHICH PLOT SETTLES IT. The `_panels` view is the primary one — raw redrawn
behind each cutoff, so nothing is occluded. The `_residual` view is what
settles a borderline call: it shows what each cutoff DISCARDS, so coherent
structure there means real signal is being deleted rather than noise. The
README records a real 6-8 Hz mode carrying 5.88mm, and both 5 and 8 Hz sit
ON that resonance — the worst place to be, because the reported peak then
becomes hypersensitive to the exact value. Deciding whether that mode
belongs in the answer is the substance of this exercise.
"""

import json
from pathlib import Path

from case_common import SKIDPAD_CUTOFF_HZ, AUTOX_END_CUTOFF_HZ

RESULTS_DIR = Path("filter_compare_results")
REVIEW_DIR = Path("review_cutoffs")
WORKSHEET = Path("cutoff_decisions.yaml")


# Representative files per event. Multiple files means the decision should
# hold across all of them — a cutoff that only suits one driver's run is
# not a cutoff.
EVENT_FILES = {
    "skidpad":   ["skidpad_austin_both"],
    "autocross": ["autocross_andrew1", "autocross_andrew2",
                  "autocross_josh1", "autocross_josh2"],
    "endurance": ["endurance_full"],
    "accel":     ["accel_corinne1", "accel_corinne2", "accel_jamie_both"],
    "brake":     ["braketest1", "braketest2"],
}


# The cells that actually need a decision. This is deliberately NOT a full
# 9-signal x 5-event grid — most of that grid is N/A, and padding it out
# with blanks makes the real decisions harder to find.
#
# Note roll and pitch each appear TWICE under different quantities. That is
# the point, not a duplication bug: case2/case3 report them as body ANGLES
# while case4 reports physical wheel TRAVEL, and those are different
# physical questions about the same sensors. Wheel hop is real travel but
# is not chassis attitude, so the travel answer can legitimately sit above
# the 6-8 Hz mode while the angle answer sits below it.
#
#   key            -> label, filter_compare plot stem, consumer, events
CELLS = [
    {
        "key": "lateral_g",
        "label": "Lateral G",
        "stem": "lateral",
        "used_by": "case1_max_gs; steady-segment detection in case3/case4",
        "events": ["skidpad", "autocross", "endurance"],
        "note": "Combined G is derived from lateral and longitudinal, so it "
                "inherits whatever those two get — it is not an independent "
                "decision.",
    },
    {
        "key": "longitudinal_g",
        "label": "Longitudinal G",
        "stem": "longitudinal",
        "used_by": "case1_max_gs; braking/accel segmentation in case3/case4",
        "events": ["skidpad", "autocross", "endurance", "accel", "brake"],
        "note": "",
    },
    {
        "key": "roll_angle",
        "label": "Roll — as body ANGLE",
        "stem": "roll",
        "used_by": "case2_max_roll",
        "events": ["skidpad", "autocross", "endurance"],
        "note": "Reported as a chassis attitude angle. Wheel hop is not "
                "chassis attitude, so excluding the 6-8 Hz mode here is "
                "defensible — but it is a MODELLING CHOICE, not noise "
                "rejection, and has to be documented as one.",
    },
    {
        "key": "pitch_angle",
        "label": "Pitch — as body ANGLE",
        "stem": "pitch",
        "used_by": "case3_max_pitch",
        "events": ["skidpad", "autocross", "endurance", "accel", "brake"],
        "note": "Same reasoning as roll angle. README records peak pitch "
                "moving ~12% across 2->10 Hz, so this choice has real "
                "consequences.",
    },
    {
        "key": "corner_travel",
        "label": "Corner travel — as physical WHEEL TRAVEL",
        "stem": "roll",
        "used_by": "case4_combined_roll_pitch",
        "events": ["skidpad", "autocross", "endurance", "accel", "brake"],
        "note": "SHARES the roll/pitch shock-pot plots — filter_compare does "
                "not plot per-corner travel separately, but it is the same "
                "four sensors and the same frequency content, so the plots "
                "answer the same question. Here the reported quantity is how "
                "far the wheel really moved, and it really does move at "
                "6-8 Hz — so this cutoff should probably sit ABOVE the mode "
                "even where the angle cutoffs sit below it.",
    },
    {
        "key": "brake_pressure_front",
        "label": "Front brake pressure",
        "stem": "brake_pressure_front",
        "used_by": "case_common.find_braking_windows (via case3)",
        "events": ["autocross", "endurance", "brake"],
        "note": "SAMPLED AT 10 Hz, not 100 — measured from the raw samples, "
                "matching its firmware task rate, and the only channel here "
                "that is not 100 Hz. Its NYQUIST IS 5 Hz, so the 5, 8, 10, 15 "
                "and 20 Hz options are all at or above it and mean nothing "
                "for this signal. The real choice is 2 vs 3 Hz. "
                "Also: used for event segmentation, not reporting, so the "
                "cutoff needs clean window edges rather than a faithful peak "
                "— and endurance_full saturates at 2000 psi.",
    },
    {
        "key": "vehicle_speed",
        "label": "Vehicle speed",
        "stem": "vehicle_speed",
        "used_by": "case_common.find_static_window — currently used RAW",
        "events": ["skidpad", "autocross", "endurance", "accel", "brake"],
        "note": "Currently NOT filtered at all: thresholded raw at 0.5 m/s to "
                "pick the stopped-car window that every shock pot is "
                "baselined against. Noise around that threshold can let a "
                "not-actually-stationary stretch qualify as stopped and "
                "quietly corrupt a whole file's baseline. Deciding to leave "
                "it raw is a valid outcome — but it should be a decision, "
                "not an oversight.",
    },
]


def current_cutoff(event):
    """What this cell inherits today, before any of this review."""

    if event == "skidpad":
        return SKIDPAD_CUTOFF_HZ, "SKIDPAD_CUTOFF_HZ"

    if event in ("autocross", "endurance"):
        return AUTOX_END_CUTOFF_HZ, "AUTOX_END_CUTOFF_HZ"

    # accel and brake were never given one — they fall through to the
    # autocross constant by accident of the if/else in each case script.
    return AUTOX_END_CUTOFF_HZ, "AUTOX_END_CUTOFF_HZ (inherited by accident — never chosen)"


def load_attenuation(file_stem):
    path = RESULTS_DIR / file_stem / "peak_attenuation.json"

    if not path.exists():
        return None

    with open(path) as fh:
        return json.load(fh)


def plot_paths(file_stem, stem, prefer_zoom=True):
    """Relative paths from REVIEW_DIR to the three views."""

    extent = "zoom" if prefer_zoom else "full"

    base = Path("..") / RESULTS_DIR / file_stem

    return {
        view: base / f"{stem}_{extent}_{view}.png"
        for view in ("panels", "residual", "overlay")
    }


# ── HTML ──────────────────────────────────────────────────────────────────

STYLE = """
:root {
  color-scheme: light dark;
  --surface: #fcfcfb;
  --card: #ffffff;
  --border: #e4e3df;
  --text: #0b0b0b;
  --muted: #52514e;
  --accent: #2a78d6;
  --warn: #ec835a;
}
@media (prefers-color-scheme: dark) {
  :root {
    --surface: #1a1a19;
    --card: #232322;
    --border: #383835;
    --text: #ffffff;
    --muted: #c3c2b7;
    --accent: #3987e5;
    --warn: #ec835a;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 2rem 1.5rem 6rem;
  background: var(--surface); color: var(--text);
  font: 15px/1.6 ui-sans-serif, system-ui, -apple-system, sans-serif;
}
.wrap { max-width: 1400px; margin: 0 auto; }
h1 { font-size: 1.6rem; margin: 0 0 .3rem; }
h2 { font-size: 1.15rem; margin: 0 0 .2rem; }
.sub { color: var(--muted); margin: 0 0 2rem; }
.cell {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 10px; padding: 1.25rem 1.5rem; margin-bottom: 1.75rem;
}
.meta { color: var(--muted); font-size: .875rem; margin: .35rem 0; }
.meta code {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 4px; padding: .05rem .35rem; font-size: .85em;
}
.note {
  border-left: 3px solid var(--warn); padding: .5rem .85rem;
  margin: .85rem 0; color: var(--muted); font-size: .9rem;
  background: var(--surface); border-radius: 0 6px 6px 0;
}
.tablewrap { overflow-x: auto; margin: 1rem 0; }
table { border-collapse: collapse; font-size: .85rem; min-width: 100%; }
th, td {
  border: 1px solid var(--border); padding: .3rem .6rem;
  text-align: right; white-space: nowrap;
}
th:first-child, td:first-child { text-align: left; }
th { color: var(--muted); font-weight: 600; }
figure { margin: 1.25rem 0 0; }
figcaption {
  color: var(--muted); font-size: .8rem; margin-bottom: .4rem;
  text-transform: uppercase; letter-spacing: .04em;
}
a.interactive {
  color: var(--accent); text-transform: none; letter-spacing: 0;
  font-weight: 600; margin-left: .5rem;
}
iframe.plot {
  width: 100%; height: 540px; border: 1px solid var(--border);
  border-radius: 6px; background: #fff; display: block;
}
.hint {
  color: var(--muted); font-size: .8rem; margin-top: .4rem;
}
img {
  width: 100%; height: auto; display: block;
  border: 1px solid var(--border); border-radius: 6px;
  background: #fff; cursor: zoom-in;
}

/* Lightbox: click any plot to inspect it at full resolution. Scroll to
   zoom, drag to pan, Esc or click the backdrop to close. The plots are
   220 dpi PNGs, so there is real detail to get at — the page itself has
   to scale them down to fit the column. */
#lb {
  position: fixed; inset: 0; z-index: 999; display: none;
  background: rgba(0,0,0,.92); overflow: hidden;
}
#lb.open { display: block; }
#lb img {
  position: absolute; top: 0; left: 0;
  width: auto; max-width: none; border: 0; border-radius: 0;
  transform-origin: 0 0; cursor: grab; user-select: none;
  image-rendering: -webkit-optimize-contrast;
}
#lb img.dragging { cursor: grabbing; }
#lb-bar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
  display: flex; gap: .75rem; align-items: center;
  padding: .6rem 1rem; background: rgba(0,0,0,.6);
  color: #fff; font-size: .85rem;
}
#lb-bar .spacer { flex: 1; }
#lb-bar button {
  background: rgba(255,255,255,.14); color: #fff;
  border: 1px solid rgba(255,255,255,.25); border-radius: 6px;
  padding: .25rem .7rem; font-size: .85rem; cursor: pointer;
}
#lb-bar button:hover { background: rgba(255,255,255,.26); }
#lb-hint { opacity: .65; }
.filehead {
  font-size: .9rem; font-weight: 600; margin: 1.5rem 0 .25rem;
  padding-top: 1rem; border-top: 1px dashed var(--border);
}
.missing {
  color: var(--warn); font-size: .85rem; font-style: italic;
}
nav { margin: 0 0 2rem; font-size: .9rem; }
nav a { color: var(--accent); margin-right: 1rem; }
"""


LIGHTBOX = """
<div id="lb">
  <div id="lb-bar">
    <strong id="lb-title"></strong>
    <span class="spacer"></span>
    <span id="lb-hint">scroll = zoom &middot; drag = pan &middot; Esc = close</span>
    <button data-z="out">&minus;</button>
    <span id="lb-pct">100%</span>
    <button data-z="in">+</button>
    <button data-z="fit">fit</button>
    <button data-z="1">1:1</button>
    <button data-z="close">close</button>
  </div>
  <img id="lb-img" alt="">
</div>
<script>
(function () {
  var lb = document.getElementById('lb'),
      img = document.getElementById('lb-img'),
      pct = document.getElementById('lb-pct'),
      title = document.getElementById('lb-title'),
      scale = 1, tx = 0, ty = 0, natW = 0, natH = 0;

  function apply() {
    img.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')';
    pct.textContent = Math.round(scale * 100) + '%';
  }

  function fit() {
    var vh = window.innerHeight - 48;
    scale = Math.min((window.innerWidth - 32) / natW, vh / natH, 1);
    tx = (window.innerWidth - natW * scale) / 2;
    ty = 48 + Math.max(0, (vh - natH * scale) / 2);
    apply();
  }

  // Zoom about the cursor, so the detail under the pointer stays put —
  // otherwise zooming into a transient walks it off screen.
  function zoomAt(cx, cy, factor) {
    var next = Math.min(8, Math.max(0.05, scale * factor));
    tx = cx - (cx - tx) * (next / scale);
    ty = cy - (cy - ty) * (next / scale);
    scale = next;
    apply();
  }

  document.addEventListener('click', function (e) {
    var t = e.target;
    if (t.tagName === 'IMG' && t.id !== 'lb-img') {
      img.src = t.getAttribute('src');
      title.textContent = t.getAttribute('alt') || '';
      lb.classList.add('open');
      img.onload = function () {
        natW = img.naturalWidth; natH = img.naturalHeight; fit();
      };
      if (img.complete && img.naturalWidth) {
        natW = img.naturalWidth; natH = img.naturalHeight; fit();
      }
    }
  });

  document.getElementById('lb-bar').addEventListener('click', function (e) {
    var z = e.target.getAttribute('data-z');
    if (!z) return;
    if (z === 'close') lb.classList.remove('open');
    else if (z === 'fit') fit();
    else if (z === '1') { scale = 1; tx = 0; ty = 48; apply(); }
    else zoomAt(window.innerWidth / 2, window.innerHeight / 2, z === 'in' ? 1.3 : 1 / 1.3);
  });

  lb.addEventListener('click', function (e) {
    if (e.target === lb) lb.classList.remove('open');
  });

  lb.addEventListener('wheel', function (e) {
    if (!lb.classList.contains('open')) return;
    e.preventDefault();
    zoomAt(e.clientX, e.clientY, e.deltaY < 0 ? 1.12 : 1 / 1.12);
  }, { passive: false });

  var dragging = false, sx = 0, sy = 0;

  img.addEventListener('pointerdown', function (e) {
    dragging = true; sx = e.clientX - tx; sy = e.clientY - ty;
    img.classList.add('dragging'); img.setPointerCapture(e.pointerId);
  });

  img.addEventListener('pointermove', function (e) {
    if (!dragging) return;
    tx = e.clientX - sx; ty = e.clientY - sy; apply();
  });

  img.addEventListener('pointerup', function (e) {
    dragging = false; img.classList.remove('dragging');
    img.releasePointerCapture(e.pointerId);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') lb.classList.remove('open');
  });

  window.addEventListener('resize', function () {
    if (lb.classList.contains('open')) fit();
  });
})();
</script>
"""


def attenuation_table(att, stem, cutoffs):
    """Peak-retained row for this signal — the numerical version of what
    the plots show by eye."""

    if not att or stem not in att.get("signals", {}):
        return '<p class="missing">No attenuation data — re-run filter_compare.py.</p>'

    sig = att["signals"][stem]

    head = "".join(f"<th>{c} Hz</th>" for c in cutoffs)

    cells = "".join(
        f"<td>{100 * sig['retained'].get(str(c), 0):.0f}%</td>"
        for c in cutoffs
    )

    table = (
        '<div class="tablewrap"><table>'
        f"<tr><th>raw peak</th><th>raw p99.9</th>{head}</tr>"
        f"<tr><td>{sig['raw_peak']:.3f}</td>"
        f"<td>{sig.get('raw_p999', float('nan')):.3f}</td>{cells}</tr>"
        "</table></div>"
    )

    # A max far above p99.9 means the denominator is a 1-2 sample spike,
    # so a low "% retained" is the filter correctly rejecting a glitch
    # rather than destroying signal. Say so, rather than letting the
    # percentages be read at face value.
    if sig.get("spike_dominated"):

        ratio = sig["raw_peak"] / sig["raw_p999"]

        table += (
            f'<div class="note"><strong>Read the percentages with care.</strong> '
            f"The raw max ({sig['raw_peak']:.3f}) is {ratio:.1f}× the p99.9 "
            f"({sig['raw_p999']:.3f}), so it is a 1–2 sample spike, not the "
            f"real peak of the manoeuvre. Every percentage below is measured "
            f"against that spike — a low number here means the filter is "
            f"rejecting a glitch, not destroying signal. Judge this cell from "
            f"the plots and the p99.9 column.</div>"
        )

    return table


def build_event_page(event, cells):

    files = EVENT_FILES[event]

    parts = [
        f"<h1>Cutoff review — {event}</h1>",
        f'<p class="sub">{len(cells)} decisions. Record answers in '
        f"<code>cutoff_decisions.yaml</code>. "
        f"<strong>Click any plot to zoom</strong> — scroll to zoom, drag to "
        f"pan, Esc to close.</p>",
        "<nav>" + "".join(
            f'<a href="{e}.html">{e}</a>'
            for e in EVENT_FILES
        ) + "</nav>",
    ]

    for n, cell in enumerate(cells, 1):

        cur, cur_name = current_cutoff(event)

        parts.append('<div class="cell">')
        parts.append(f"<h2>{n}. {cell['label']}</h2>")
        parts.append(
            f'<p class="meta">used by <code>{cell["used_by"]}</code></p>'
        )
        parts.append(
            f'<p class="meta">currently <strong>{cur} Hz</strong> '
            f"— <code>{cur_name}</code></p>"
        )

        if cell["note"]:
            parts.append(f'<div class="note">{cell["note"]}</div>')

        for file_stem in files:

            att = load_attenuation(file_stem)

            cutoffs = att["cutoffs"] if att else []

            parts.append(f'<div class="filehead">{file_stem}</div>')
            parts.append(attenuation_table(att, cell["stem"], cutoffs))

            paths = plot_paths(file_stem, cell["stem"])

            for view, caption in (
                ("panels", "primary — raw behind each cutoff"),
                ("residual", "what each cutoff DISCARDS — structure here means real signal"),
                ("overlay", "all cutoffs together — CLICK LEGEND to add/remove frequencies"),
            ):
                # The overlay is embedded LIVE, not as a picture. Toggling
                # cutoffs off is the thing you actually need once the choice
                # is down to two or three candidates, and no static image
                # can do it. The iframe is lazy, so a page with 28 of them
                # only builds the charts you scroll to.
                if view == "overlay":

                    interactive = paths[view].with_suffix(".html")

                    if (REVIEW_DIR / interactive).exists():

                        parts.append(
                            f"<figure><figcaption>{caption}</figcaption>"
                            f'<iframe class="plot" loading="lazy" '
                            f'src="{interactive.as_posix()}" '
                            f'title="{cell["label"]} interactive overlay"></iframe>'
                            f'<div class="hint">Click a legend entry to hide that '
                            f"cutoff; double-click one to isolate it. Drag to "
                            f"box-zoom, double-click the plot to reset."
                            f' <a class="interactive" target="_blank" '
                            f'href="{interactive.as_posix()}">open full width ↗</a>'
                            f"</div></figure>"
                        )
                        continue

                parts.append(
                    f"<figure><figcaption>{caption}</figcaption>"
                    f'<img loading="lazy" src="{paths[view].as_posix()}" '
                    f'alt="{cell["label"]} {view}"></figure>'
                )

        parts.append("</div>")

    return (
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Cutoff review — {event}</title><style>{STYLE}</style></head>"
        f"<body><div class='wrap'>{''.join(parts)}</div>{LIGHTBOX}</body></html>"
    )


# ── YAML worksheet ────────────────────────────────────────────────────────

def build_worksheet():

    lines = [
        "# cutoff_decisions.yaml — fill in `chosen_hz` and `why` for each cell.",
        "#",
        "# Generated by build_cutoff_review.py. Open the matching page in",
        "# review_cutoffs/<event>.html to see the plots for each cell.",
        "#",
        "# `current_hz` is what the code does TODAY. Leaving a cell unchanged",
        "# is a valid answer — but write down WHY, so the next person knows it",
        "# was decided rather than inherited.",
        "#",
        "# Reminder: the README records a real 6-8 Hz mode carrying 5.88mm of",
        "# travel. A cutoff below it is EXCLUDING REAL SIGNAL on purpose, which",
        "# is a legitimate modelling choice for body-attitude angles but must",
        "# be documented as a choice, not as noise rejection. Sitting exactly",
        "# ON the mode (5 or 8 Hz) is the one option to avoid — the reported",
        "# peak becomes hypersensitive to the exact value.",
        "",
        "decisions:",
    ]

    for cell in CELLS:

        for event in cell["events"]:

            cur, cur_name = current_cutoff(event)

            files = EVENT_FILES[event]

            att = load_attenuation(files[0])

            lines.append(f"  - quantity: {cell['key']}")
            lines.append(f"    event: {event}")
            lines.append(f"    used_by: \"{cell['used_by']}\"")
            lines.append(f"    current_hz: {cur}          # {cur_name}")
            lines.append(f"    review_page: review_cutoffs/{event}.html")

            if att and cell["stem"] in att.get("signals", {}):

                retained = att["signals"][cell["stem"]]["retained"]

                summary = ", ".join(
                    f"{c}Hz {100 * retained[str(c)]:.0f}%"
                    for c in att["cutoffs"]
                    if str(c) in retained
                )

                lines.append(f"    # peak retained ({files[0]}): {summary}")

                if att["signals"][cell["stem"]].get("spike_dominated"):
                    lines.append(
                        "    # [!] raw max is a 1-2 sample spike, not the real "
                        "peak — those percentages understate what survives. "
                        "Judge from the plots."
                    )

            lines.append("    chosen_hz:            # <-- fill in")
            lines.append("    why:                  # <-- fill in")
            lines.append("")

    return "\n".join(lines)


def main():

    REVIEW_DIR.mkdir(exist_ok=True)


    for event in EVENT_FILES:

        cells = [c for c in CELLS if event in c["events"]]

        page = REVIEW_DIR / f"{event}.html"

        page.write_text(build_event_page(event, cells), encoding="utf-8")

        print(f"  {page}  ({len(cells)} cells)")


    if WORKSHEET.exists():

        print(
            f"\n  [!] {WORKSHEET} already exists — writing "
            f"{WORKSHEET}.new instead so your answers are not overwritten."
        )

        target = Path(str(WORKSHEET) + ".new")

    else:
        target = WORKSHEET


    target.write_text(build_worksheet(), encoding="utf-8")

    total = sum(len(c["events"]) for c in CELLS)

    print(f"  {target}  ({total} decisions)")

    print(f"\nOpen review_cutoffs/skidpad.html to start.")


if __name__ == "__main__":
    main()
