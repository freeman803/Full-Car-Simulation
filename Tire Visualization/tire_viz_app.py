"""
Local web app for the MF-Tyre 6.2 tire curve visualizer.

Serves a single-page UI (tire_viz_app.html) plus a small JSON API on
127.0.0.1 and opens it in the default browser. The tire model itself is
reused from tire_visualizer.py.

Usage:
    python tire_viz_app.py [path/to/file.tir] [--port N] [--no-browser]

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


class AppHandler(BaseHTTPRequestHandler):
    tire: MF62Tire  # set on the class before serving

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

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, HTML_PATH.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/info":
            t = self.tire
            self._json(200, {
                "file": t.path.name,
                "fnomin_n": t.FZ0,
                "nompres_psi": round(t.P0 / PSI_TO_PA, 2),
                "r0_m": t.R0,
                "my_all_zero": all(t.c(f"QSY{i}") == 0.0 for i in range(1, 9)),
            })
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/sweep":
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
            lo, hi = float(req["min"]), float(req["max"])
            n = max(2, min(int(req.get("points", 300)), MAX_POINTS))
            fixed = req.get("fixed", {})
            vals = {k: float(fixed.get(k, 0.0)) for k in INPUT_KEYS if k != swept}
            vals[swept] = np.linspace(lo, hi, n)

            out = self.tire.forces(
                fz=vals["fz"],
                alpha=np.deg2rad(vals["sa"]),
                kappa=vals["sr"],
                press=np.asarray(vals["pressure"]) * PSI_TO_PA,
                gamma=np.deg2rad(vals["camber"]),
            )
            self._json(200, {"x": _clean(vals[swept]), "y": _clean(out[output])})
        except Exception as exc:  # bad request -> readable message, keep serving
            self._json(400, {"error": str(exc)})


def find_free_port(start: int) -> int:
    for port in range(start, start + 50):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("no free port found")


def main() -> None:
    args = [a for a in sys.argv[1:]]
    open_browser = "--no-browser" not in args
    port = None
    if "--port" in args:
        port = int(args[args.index("--port") + 1])
    tir_args = [a for a in args if a.endswith(".tir")]
    tir_path = Path(tir_args[0]) if tir_args else DEFAULT_TIR
    if not tir_path.exists():
        print(f"Tire file not found: {tir_path}")
        sys.exit(1)

    AppHandler.tire = MF62Tire(tir_path)
    port = port or find_free_port(8317)
    server = ThreadingHTTPServer(("127.0.0.1", port), AppHandler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Tire visualizer running at {url}  (Ctrl+C to stop)")
    print(f"Tire file: {tir_path}")
    if open_browser:
        threading.Timer(0.6, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
