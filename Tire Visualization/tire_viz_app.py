"""
Local web app for the Magic Formula tire curve visualizer.

Serves a single-page UI (tire_viz_app.html) plus a small JSON API. Every
.tir file next to this script is loaded and offered in a dropdown, so both
MF-Tyre 6.1/6.2 and PAC2002 files can be compared without restarting. By
default it binds 127.0.0.1 (local-only) and opens the default browser. Pass
--host 0.0.0.0 to serve the whole LAN (e.g. hosting on a shared server). The
tire model itself is reused from tire_visualizer.py.

Usage:
    python tire_viz_app.py [path/to/file.tir] [--host H] [--port N] [--no-browser]

A .tir path on the command line becomes the default selection; all other
.tir files in this folder are still available in the dropdown.

or double-click run_tire_app.bat.
"""
from __future__ import annotations

import json
import socket
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from math import isfinite
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from tire_visualizer import DEFAULT_TIR, PSI_TO_PA, MF62Tire  # noqa: E402

HTML_PATH = HERE / "tire_viz_app.html"
INPUT_KEYS = ("pressure", "fz", "sa", "sr", "camber")
OUTPUT_KEYS = ("fx", "fy", "mx", "my", "mz")
MAX_POINTS = 2000


def _clean(arr) -> list:
    """JSON-safe list: non-finite values become null."""
    return [float(v) if isfinite(v) else None for v in np.asarray(arr, dtype=float)]


def _tire_info(name: str, t: MF62Tire) -> dict:
    """JSON-safe summary of one loaded tire for the UI header/notes."""
    return {
        "name": name,
        "file": t.path.name,
        "format": t.format,
        "fnomin_n": t.FZ0,
        "nompres_psi": round(t.P0 / PSI_TO_PA, 2) if t.pressure_dependent else None,
        "pressure_dependent": t.pressure_dependent,
        "r0_m": t.R0,
        # MY is identically zero when the QSY1..QSY6 terms are all zero; QSY7
        # and QSY8 are only exponents, so they don't affect a zero result.
        "my_all_zero": all(t.c(f"QSY{i}") == 0.0 for i in range(1, 7)),
    }


class AppHandler(BaseHTTPRequestHandler):
    tires: dict = {}       # {display name: MF62Tire}, set before serving
    tire_names: list = []  # display order for the dropdown
    default_tire: str = "" # key into tires used when none is requested

    def log_message(self, fmt, *args):  # keep the console quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json")

    def _pick(self, name):
        """Resolve a requested tire name to (name, model), falling back to the
        default when it is missing or unknown."""
        if name and name in self.tires:
            return name, self.tires[name]
        return self.default_tire, self.tires[self.default_tire]

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send(200, HTML_PATH.read_bytes(), "text/html; charset=utf-8")
        elif parsed.path == "/api/tires":
            self._json(200, {
                "tires": [_tire_info(n, self.tires[n]) for n in self.tire_names],
                "default": self.default_tire,
            })
        elif parsed.path == "/api/info":
            q = parse_qs(parsed.query)
            name, t = self._pick((q.get("tire") or [None])[0])
            self._json(200, _tire_info(name, t))
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if urlparse(self.path).path != "/api/sweep":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(length))
            swept = req["swept"]
            output = req["output"]
            if swept not in INPUT_KEYS:
                raise ValueError(f"unknown input '{swept}'")
            if output not in OUTPUT_KEYS:
                raise ValueError(f"unknown output '{output}'")
            name, tire = self._pick(req.get("tire"))
            lo, hi = float(req["min"]), float(req["max"])
            n = max(2, min(int(req.get("points", 300)), MAX_POINTS))
            fixed = req.get("fixed", {})
            vals = {k: float(fixed.get(k, 0.0)) for k in INPUT_KEYS if k != swept}
            vals[swept] = np.linspace(lo, hi, n)

            out = tire.forces(
                fz=vals["fz"],
                alpha=np.deg2rad(vals["sa"]),
                kappa=vals["sr"],
                press=np.asarray(vals["pressure"]) * PSI_TO_PA,
                gamma=np.deg2rad(vals["camber"]),
            )
            self._json(200, {"x": _clean(vals[swept]), "y": _clean(out[output]), "tire": name})
        except Exception as exc:  # bad request -> readable message, keep serving
            self._json(400, {"error": str(exc)})


def find_free_port(start: int, host: str = "127.0.0.1") -> int:
    for port in range(start, start + 50):
        with socket.socket() as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError("no free port found")


def main() -> None:
    args = [a for a in sys.argv[1:]]
    open_browser = "--no-browser" not in args
    port = None
    if "--port" in args and args.index("--port") + 1 < len(args):
        port = int(args[args.index("--port") + 1])
    # Bind address. Default is loopback (local-only). Pass --host 0.0.0.0 to
    # serve the whole LAN, e.g. when hosting on a shared server.
    host = "127.0.0.1"
    if "--host" in args and args.index("--host") + 1 < len(args):
        host = args[args.index("--host") + 1]
    local_only = host in ("127.0.0.1", "localhost")

    tir_args = [Path(a) for a in args if a.lower().endswith(".tir")]
    for p in tir_args:
        if not p.exists():
            print(f"Tire file not found: {p}")
            sys.exit(1)

    # Discover every .tir file next to this script (case-insensitive suffix,
    # so both `.tir` and `.TIR` are found), plus any file passed on the command
    # line. De-duplicate by resolved path so the same file — e.g. a CLI path
    # that points at a folder file, possibly typed in a different case — is
    # never listed twice.
    discovered: dict = {}          # display name -> Path
    seen_paths: dict = {}          # resolved path (lower) -> display name
    for p in [*sorted(HERE.iterdir(), key=lambda q: q.name.lower()), *tir_args]:
        if not (p.is_file() and p.suffix.lower() == ".tir"):
            continue
        rp = str(p.resolve()).lower()
        if rp in seen_paths:
            continue
        seen_paths[rp] = p.name
        discovered[p.name] = p

    tires: dict = {}
    for name, p in discovered.items():
        try:
            tires[name] = MF62Tire(p)
        except Exception as exc:  # a malformed file shouldn't sink the others
            print(f"  Skipping {name}: {exc}")
    if not tires:
        print("No usable .tir files found next to tire_viz_app.py.")
        sys.exit(1)

    # Default to the CLI file (by the display name it was registered under),
    # else the built-in default, else whatever loaded — but only if it actually
    # loaded, so a malformed CLI file can't leave default_tire dangling.
    cli_default = seen_paths.get(str(tir_args[0].resolve()).lower()) if tir_args else None
    if cli_default and cli_default in tires:
        default_tire = cli_default
    elif DEFAULT_TIR.name in tires:
        default_tire = DEFAULT_TIR.name
    else:
        default_tire = next(iter(tires))

    AppHandler.tires = tires
    AppHandler.tire_names = list(tires.keys())
    AppHandler.default_tire = default_tire

    port = port or find_free_port(8317, host)
    server = ThreadingHTTPServer((host, port), AppHandler)
    # 127.0.0.1 in the URL is only right on the server itself; when bound to
    # all interfaces, teammates reach it at this machine's LAN IP instead.
    shown_host = "127.0.0.1" if local_only else host
    url = f"http://{shown_host}:{port}/"
    print(f"Tire visualizer running at {url}  (Ctrl+C to stop)")
    if not local_only:
        print("Serving on all interfaces — teammates use this machine's LAN "
              "IP (run 'ipconfig' to find it), e.g. http://<LAN-IP>:%d/" % port)
    print(f"Tires loaded ({len(tires)}): "
          + ", ".join(f"{n} [{t.format}]" for n, t in tires.items()))
    print(f"Default tire: {default_tire}")
    # Only pop a browser when serving locally; a LAN/headless host has none.
    if open_browser and local_only:
        threading.Timer(0.6, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
