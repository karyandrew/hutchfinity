#!/usr/bin/env python3
"""Tiny Hutchfinity generator: pick a part and size, get a checked STL.

    python3 hutchfinity.py                 opens the app in a browser
    python3 hutchfinity.py tub 10 10 10    writes one STL from the command line

Needs only Python and OpenSCAD. Set OPENSCAD_BIN if OpenSCAD is not on PATH.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
ENTRY = ROOT / "scad" / "hutchfinity.scad"
CUP = ROOT / "scad" / "gridfinity" / "vendor" / "extended" / "gridfinity_basic_cup.scad"
BASEPLATE = ROOT / "scad" / "gridfinity" / "vendor" / "extended" / "gridfinity_baseplate.scad"
PARTS = ("tub", "grid-insert", "casing", "pegs", "pull", "bin", "baseplate")
FLOORS = ("integral-grid", "plain")
MAC_APP = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"


class BuildError(Exception):
    pass


def find_openscad() -> list[str]:
    candidate = os.environ.get("OPENSCAD_BIN") or shutil.which("openscad") or MAC_APP
    if not (shutil.which(candidate) or Path(candidate).is_file()):
        raise BuildError("OpenSCAD not found. Install it or set OPENSCAD_BIN.")
    try:
        subprocess.run([candidate, "--version"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        # An Intel build on Apple Silicon may need Rosetta.
        if platform.system() == "Darwin" and shutil.which("arch"):
            return ["arch", "-x86_64", candidate]
        raise BuildError(f"OpenSCAD failed to start: {candidate}") from None
    return [candidate]


def scad_args(part: str, x: int, y: int, h: int, floor: str) -> tuple[Path, list[str], str]:
    """Return the source file, its overrides, and the output name for one part."""
    if part not in PARTS:
        raise BuildError(f"unknown part: {part}")
    if floor not in FLOORS:
        raise BuildError(f"unknown floor: {floor}")
    for value in (x, y, h):
        if not 1 <= value <= 40:
            raise BuildError("sizes must be whole numbers from 1 to 40")
    if part == "bin":
        return CUP, [
            f"pitch=[21,21,3.5]", f"width=[{x},0]", f"depth=[{y},0]", f"height=[{h},0]",
            'lip_style="minimum"', "enable_magnets=false", "enable_screws=false",
            'label_style="disabled"', 'fingerslide="none"',
            "vertical_chambers=1", "horizontal_chambers=1",
        ], f"bin-{x}x{y}x{h}h.stl"
    if part == "baseplate":
        return BASEPLATE, ["pitch=[21,21,3.5]", f"Width=[{x},0]", f"Depth=[{y},0]"], f"baseplate-{x}x{y}.stl"
    suffix = f"-{floor}" if part in ("tub", "casing", "pegs", "pull") else ""
    size = f"{x}x{y}" if part == "grid-insert" else f"{x}x{y}x{h}h"
    return ENTRY, [
        f'part="{part}"', f"cells_x={x}", f"cells_y={y}", f"bin_h={h}", f'floor_mode="{floor}"',
    ], f"{part}-{size}{suffix}.stl"


def stl_check(path: Path) -> dict:
    """Read a binary STL: size, facet count, closed surface, and separate pieces."""
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise BuildError("OpenSCAD did not write a valid binary STL")
    ids: dict[tuple, int] = {}
    edges: dict[tuple[int, int], int] = {}
    parent: list[int] = []

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for facet in range(count):
        offset = 84 + 50 * facet + 12
        triangle = []
        for corner in range(3):
            vertex = struct.unpack_from("<3f", data, offset + 12 * corner)
            if vertex not in ids:
                ids[vertex] = len(ids)
                parent.append(ids[vertex])
            triangle.append(ids[vertex])
        for a, b in zip(triangle, triangle[1:] + triangle[:1]):
            edges[(a, b)] = edges.get((a, b), 0) + 1
            parent[find(a)] = find(b)
    closed = all(edges.get((b, a)) == n for (a, b), n in edges.items())
    points = list(ids)
    return {
        "size_mm": [round(max(p[i] for p in points) - min(p[i] for p in points), 2) for i in range(3)],
        "facets": count,
        "closed": closed,
        "pieces": len({find(i) for i in range(len(parent))}),
    }


def build(part: str, x: int, y: int, h: int, floor: str, out_dir: Path) -> dict:
    source, overrides, name = scad_args(part, x, y, h, floor)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / name
    with tempfile.TemporaryDirectory() as work:
        stl = Path(work) / name
        command = find_openscad() + ["--backend=Manifold", "--export-format=binstl", "-o", str(stl)]
        for override in overrides:
            command += ["-D", override]
        run = subprocess.run(command + [str(source)], capture_output=True, text=True)
        log = run.stdout + run.stderr
        if run.returncode or not stl.exists():
            errors = [l for l in log.splitlines() if re.search(r"ERROR|Assertion", l)]
            raise BuildError("; ".join(errors) or log.strip()[-400:])
        check = stl_check(stl)
        if not check["closed"]:
            raise BuildError(f"{name} is not a closed solid; not saved")
        shutil.move(str(stl), target)
    notes = re.findall(r'ECHO: "(.*)"', log) if source == ENTRY else []
    return {"path": str(target), "name": name, "notes": notes, **check}


PAGE = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Hutchfinity</title><style>
:root{color-scheme:light dark}body{font:16px system-ui;max-width:26rem;margin:2rem auto;padding:0 1rem}
label{display:flex;justify-content:space-between;align-items:center;margin:.6rem 0}
input,select{font:inherit;width:9rem;padding:.25rem}button{font:inherit;padding:.5rem 1rem;margin-top:.6rem}
pre{white-space:pre-wrap}</style>
<h1>Hutchfinity</h1><form id=f>
<label>Part<select name=part>%s</select></label>
<label>Preset<select id=preset><option value="">custom<option value="6,16,20">Mini
<option value="12,16,20" selected>Regular<option value="18,16,20">Mega</select></label>
<label>Cells wide<input name=x type=number min=1 max=40 value=12></label>
<label>Cells deep<input name=y type=number min=1 max=40 value=16></label>
<label>Tallest bin (3.5 mm units)<input name=h type=number min=1 max=40 value=20></label>
<label>Floor<select name=floor><option>integral-grid<option>plain</select></label>
<button>Build STL</button></form><pre id=out></pre><script>
const f=document.getElementById('f'),o=document.getElementById('out');
document.getElementById('preset').onchange=e=>{if(!e.target.value)return;
 const v=e.target.value.split(',');f.x.value=v[0];f.y.value=v[1];f.h.value=v[2]};
f.onsubmit=async e=>{e.preventDefault();o.textContent='Building...';
 const r=await fetch('/build?'+new URLSearchParams(new FormData(f)));const j=await r.json();
 if(!r.ok){o.textContent='Could not build: '+j.error;return}
 o.textContent=`Saved ${j.path}\\n${j.size_mm.join(' x ')} mm, ${j.facets} facets, ${j.pieces} piece(s), closed solid\\n${j.notes.join('\\n')}`};
</script>""" % "".join(f"<option>{p}" for p in PARTS)


class App(BaseHTTPRequestHandler):
    out_dir = Path.home() / "Downloads" / "hutchfinity"

    def reply(self, status: int, body: bytes, kind: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/":
            return self.reply(200, PAGE.encode(), "text/html; charset=utf-8")
        if url.path != "/build":
            return self.reply(404, b"not found", "text/plain")
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            size = [int(q.get(k, "")) for k in ("x", "y", "h")]
            result, status = build(q.get("part", ""), *size, q.get("floor", FLOORS[0]), self.out_dir), 200
        except (BuildError, ValueError) as error:
            result, status = {"error": str(error)}, 400
        self.reply(status, json.dumps(result).encode(), "application/json")

    def log_message(self, *args) -> None:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("part", nargs="?", choices=PARTS)
    parser.add_argument("size", nargs="*", type=int, help="cells wide, cells deep, tallest bin")
    parser.add_argument("--floor", choices=FLOORS, default=FLOORS[0])
    parser.add_argument("--out", type=Path, default=App.out_dir)
    parser.add_argument("--port", type=int, default=8421)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if args.part:
        if len(args.size) != 3:
            parser.error("give three sizes: cells wide, cells deep, tallest bin")
        try:
            print(json.dumps(build(args.part, *args.size, args.floor, args.out), indent=2))
        except BuildError as error:
            print(f"Could not build: {error}", file=sys.stderr)
            return 1
        return 0
    App.out_dir = args.out
    server = ThreadingHTTPServer(("127.0.0.1", args.port), App)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Hutchfinity is at {url} (Ctrl-C to stop). STLs go to {args.out}")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
