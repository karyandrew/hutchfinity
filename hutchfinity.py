#!/usr/bin/env python3
"""Hutchfinity generator: build a full drawer module as Orca-ready 3MF files.

    python3 hutchfinity.py                     opens the app in a browser
    python3 hutchfinity.py module 10 10 10     builds one module folder
    python3 hutchfinity.py bin 2 2 10          builds one part
    python3 hutchfinity.py --install-shortcut  adds a clickable app to the Desktop

Sizes are cells wide, cells deep, and tallest bin. --help lists every option.
Needs only Python and OpenSCAD. Set OPENSCAD_BIN if OpenSCAD is not on PATH.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

VERSION = "1.2.0"
ROOT = Path(__file__).resolve().parent
ENTRY = ROOT / "scad" / "hutchfinity.scad"
CUP = ROOT / "scad" / "gridfinity" / "vendor" / "extended" / "gridfinity_basic_cup.scad"
BASEPLATE = ROOT / "scad" / "gridfinity" / "vendor" / "extended" / "gridfinity_baseplate.scad"
TARGETS = ("module", "tub", "grid-insert", "casing", "pegs", "pull", "bin", "baseplate")
FLOORS = ("integral-grid", "plain")
MAC_APP = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
DEFAULT_OUT = Path.home() / "Downloads" / "hutchfinity"
PORT = 8421
IDLE_EXIT_SECONDS = 30 * 60

# name, OpenSCAD variable, default, help, lowest, highest.
DESIGN_OPTIONS = [
    ("pull_guide", "pull_guide", True, "raised guide on the tub front for gluing the pull", None, None),
    ("wall", "WALL", 2.2, "tub wall, mm", 1.2, 4.0),
    ("rim_wall", "MIN_WALL", 0.4, "tub wall at the rim, mm", 0.3, 1.0),
    ("integral_floor", "INTEGRAL_FLOOR", 1.3, "integral-grid floor, mm", 0.8, 3.0),
    ("plain_floor", "PLAIN_FLOOR", 1.2, "plain floor, mm", 0.8, 3.0),
    ("stack_gap", "STACK_GAP", 0.5, "air gap above the tallest bin when stacked, mm", 0.0, 5.0),
    ("bin_lip", "BIN_LIP", 3.74, "bin lip height, mm", 3.0, 5.0),
    ("insert_clearance", "INSERT_CLEARANCE", 1.0, "grid insert clearance per side, mm", 0.2, 2.0),
    ("side_wall", "side_wall", 18.0, "casing side wall, mm", 18.0, 40.0),
    ("back_wall", "back_wall", 18.0, "casing back wall, mm", 18.0, 40.0),
    ("riding_slab", "riding_slab", 1.3, "casing slab the tub above rides on, mm", 1.0, 10.0),
    ("side_clearance", "side_clearance", 1.0, "tub to casing, each side, mm", 0.2, 3.0),
    ("back_clearance", "back_clearance", 0.5, "tub to casing, back, mm", 0.2, 3.0),
    ("top_clearance", "top_clearance", 1.0, "tub to casing, top, mm", 0.2, 5.0),
    ("peg_spacing", "peg_spacing", 190.0, "target peg spacing, mm", 100.0, 400.0),
    ("peg_bore", "peg_bore", 8.45, "peg socket bore and peg width, mm", 6.0, 9.0),
    ("peg_depth", "peg_depth_max", 10.0, "peg socket depth, mm", 5.0, 15.0),
    ("peg_chamfer", "peg_chamfer", 0.5, "socket opening chamfer, mm", 0.0, 0.75),
    ("peg_end_chamfer", "peg_end_chamfer", 2.5, "peg end chamfer, mm", 0.0, 4.0),
    ("pull_width", "PULL_FLANGE_X", 90.0, "full-size pull flange width, mm", 60.0, 120.0),
    ("pull_height", "PULL_FLANGE_Z", 32.9, "full-size pull flange height, mm", 31.0, 40.0),
    ("corner_steps", "CORNER_STEPS", 8, "mesh: facets per tub corner", 4, 32),
    ("cell_corner_steps", "CELL_CORNER_STEPS", 6, "mesh: facets per grid-pocket corner", 3, 16),
    ("casing_fn", "casing_fn", 32, "mesh: facets per peg socket", 16, 96),
]
# name, default, help, lowest, highest. Every tub gets exactly one pull.
COUNT_OPTIONS = [
    ("tubs", 1, "tubs in the module", 1, 20),
    ("casings", 1, "casings in the module", 0, 20),
    ("spare_pegs", 0, "pegs beyond what the casings need", 0, 50),
    ("insert", 0, "grid inserts (for a plain floor)", 0, 20),
]
CELLS_RANGE = (1, 40)
TUB_HEIGHT_RANGE = (5, 40)  # A tub must hold at least a 5h bin.
BIN_HEIGHT_RANGE = (1, 40)
BED_RANGE = (100.0, 1000.0)


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


def check_range(label: str, value, low, high) -> None:
    if not low <= value <= high:
        raise BuildError(f"{label} must be from {low} to {high}; got {value}")


def check_size(part: str, x: int, y: int, h: int) -> None:
    check_range("cells wide", x, *CELLS_RANGE)
    check_range("cells deep", y, *CELLS_RANGE)
    check_range("tallest bin" if part != "bin" else "bin height", h,
                *(BIN_HEIGHT_RANGE if part in ("bin", "baseplate") else TUB_HEIGHT_RANGE))


def scad_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    raise BuildError(f"bad value: {value!r}")


def design_overrides(design: dict) -> list[str]:
    known = {option[0]: option for option in DESIGN_OPTIONS}
    overrides = []
    for name, value in design.items():
        if name not in known:
            raise BuildError(f"unknown option: {name}")
        _, var, default, _, low, high = known[name]
        if low is not None:
            check_range(name.replace("_", " "), value, low, high)
        if value != default:
            overrides.append(f"{var}={scad_value(value)}")
    return overrides


def scad_source(part: str, x: int, y: int, h: int, floor: str, design: dict) -> tuple[Path, list[str]]:
    check_size(part, x, y, h)
    if floor not in FLOORS:
        raise BuildError(f"unknown floor: {floor}")
    if part == "bin":
        return CUP, [
            "pitch=[21,21,3.5]", f"width=[{x},0]", f"depth=[{y},0]", f"height=[{h},0]",
            'lip_style="minimum"', "enable_magnets=false", "enable_screws=false",
            'label_style="disabled"', 'fingerslide="none"',
            "vertical_chambers=1", "horizontal_chambers=1",
        ]
    if part == "baseplate":
        return BASEPLATE, ["pitch=[21,21,3.5]", f"Width=[{x},0]", f"Depth=[{y},0]"]
    if part not in ("tub", "grid-insert", "casing", "peg", "pegs", "pull"):
        raise BuildError(f"unknown part: {part}")
    return ENTRY, [
        f'part="{part}"', f"cells_x={x}", f"cells_y={y}", f"bin_h={h}", f'floor_mode="{floor}"',
        *design_overrides(design),
    ]


def read_stl(path: Path) -> dict:
    """Read a binary STL into shared vertices and triangles, and check it is closed."""
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise BuildError("OpenSCAD did not write a valid binary STL")
    ids: dict[tuple, int] = {}
    triangles: list[tuple[int, int, int]] = []
    edges: dict[tuple[int, int], int] = {}
    parent: list[int] = []

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for facet in range(count):
        offset = 84 + 50 * facet + 12
        corners = []
        for corner in range(3):
            vertex = struct.unpack_from("<3f", data, offset + 12 * corner)
            if vertex not in ids:
                ids[vertex] = len(ids)
                parent.append(ids[vertex])
            corners.append(ids[vertex])
        triangles.append(tuple(corners))
        for a, b in zip(corners, corners[1:] + corners[:1]):
            edges[(a, b)] = edges.get((a, b), 0) + 1
            parent[find(a)] = find(b)
    points = list(ids)
    low = [min(p[i] for p in points) for i in range(3)]
    high = [max(p[i] for p in points) for i in range(3)]
    return {
        "points": points,
        "triangles": triangles,
        "low": low,
        "size_mm": [round(high[i] - low[i], 2) for i in range(3)],
        "facets": count,
        "closed": all(edges.get((b, a)) == n for (a, b), n in edges.items()),
        "pieces": len({find(i) for i in range(len(parent))}),
    }


def render(part: str, x: int, y: int, h: int, floor: str, design: dict) -> dict:
    source, overrides = scad_source(part, x, y, h, floor, design)
    with tempfile.TemporaryDirectory() as work:
        stl = Path(work) / "part.stl"
        command = find_openscad() + ["--backend=Manifold", "--export-format=binstl", "-o", str(stl)]
        for override in overrides:
            command += ["-D", override]
        run = subprocess.run(command + [str(source)], capture_output=True, text=True)
        log = run.stdout + run.stderr
        if run.returncode or not stl.exists():
            errors = [line for line in log.splitlines() if re.search(r"ERROR|Assertion", line)]
            raise BuildError(f"{part}: " + ("; ".join(errors) or log.strip()[-400:]))
        mesh = read_stl(stl)
    if not mesh["closed"]:
        raise BuildError(f"{part} is not a closed solid; nothing was saved")
    mesh["notes"] = re.findall(r'ECHO: "(.*)"', log) if source == ENTRY else []
    return mesh


def write_3mf(path: Path, objects: list[tuple[str, dict, int]], bed: float = 500.0) -> None:
    """Write named objects, each with a copy count, laid out in rows from the bed corner.

    Copies share one mesh. This is plain 3MF with no slicer settings, so it picks
    up whatever printer and filament profile is active in Orca.
    """
    gap = 8.0
    resources, items = [], []
    cursor_x, cursor_y, row = gap, gap, 0.0
    for index, (name, mesh, copies) in enumerate(objects, start=1):
        low = mesh["low"]
        vertices = "".join(
            f'<vertex x="{p[0] - low[0]:.4f}" y="{p[1] - low[1]:.4f}" z="{p[2] - low[2]:.4f}"/>'
            for p in mesh["points"]
        )
        triangles = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh["triangles"])
        resources.append(
            f'<object id="{index}" name="{html.escape(name)}" type="model"><mesh>'
            f"<vertices>{vertices}</vertices><triangles>{triangles}</triangles></mesh></object>"
        )
        width, depth, _ = mesh["size_mm"]
        for _copy in range(copies):
            if cursor_x > gap and cursor_x + width > bed - gap:
                cursor_x, cursor_y, row = gap, cursor_y + row + gap, 0.0
            items.append(f'<item objectid="{index}" transform="1 0 0 0 1 0 0 0 1 {cursor_x:.3f} {cursor_y:.3f} 0"/>')
            cursor_x += width + gap
            row = max(row, depth)
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        f'<metadata name="Application">hutchfinity {VERSION}</metadata>'
        f"<resources>{''.join(resources)}</resources><build>{''.join(items)}</build></model>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>',
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
        )
        archive.writestr("3D/3dmodel.model", model)


def source_commit() -> str:
    run = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True)
    return run.stdout.strip() if run.returncode == 0 else "unknown"


def file_record(path: Path, **extra) -> dict:
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        **extra,
    }


def build_module(x, y, h, floor, out: Path, design=None, counts=None, bed=500.0) -> dict:
    """Build the print set for one module: one 3MF per print job, plus a manifest."""
    design = design or {}
    counts = {**{option[0]: option[1] for option in COUNT_OPTIONS}, **(counts or {})}
    for name, _, _, low, high in COUNT_OPTIONS:
        check_range(name.replace("_", " "), counts[name], low, high)
    render_part = lambda part: render(part, x, y, h, floor, design)
    tub, casing, peg, pull = (render_part(p) for p in ("tub", "casing", "peg", "pull"))
    check_range("bed", bed, *BED_RANGE)
    for label, mesh in (("tub", tub), ("casing", casing)):
        if max(mesh["size_mm"][:2]) > bed or mesh["size_mm"][2] > bed:
            raise BuildError(f"the {label} is {' x '.join(map(str, mesh['size_mm']))} mm, too big for a {bed:g} mm bed")
    pegs_needed = int(re.search(r"(\d+) pegs", casing["notes"][0]).group(1))
    peg_total = pegs_needed * counts["casings"] + counts["spare_pegs"]

    folder = out / f"hutchfinity-{x}x{y}x{h}h-{floor}"
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.3mf"):
        old.unlink()
    jobs = [
        ("1-tub.3mf", [("Tub", tub, counts["tubs"])]),
        ("2-casing.3mf", [("Casing", casing, counts["casings"])]),
        ("3-pegs-and-pulls.3mf", [("Peg", peg, peg_total), ("Pull", pull, counts["tubs"])]),
    ]
    if counts["insert"]:
        jobs.append(("4-grid-insert.3mf", [("Grid insert", render_part("grid-insert"), counts["insert"])]))
    records = []
    for name, objects in jobs:
        objects = [o for o in objects if o[2] > 0]
        if objects:
            write_3mf(folder / name, objects, bed)
            records.append(file_record(folder / name, parts={o[0]: o[2] for o in objects}))
    manifest = {
        "generator_version": VERSION,
        "source_commit": source_commit(),
        "size": {"cells_x": x, "cells_y": y, "bin_h": h, "floor": floor},
        "design_overrides": design,
        "counts": counts,
        "peg_total": peg_total,
        "sizes_mm": {"tub": tub["size_mm"], "casing": casing["size_mm"], "pull": pull["size_mm"], "peg": peg["size_mm"]},
        "facets": {"tub": tub["facets"], "casing": casing["facets"], "pull": pull["facets"], "peg": peg["facets"]},
        "notes": tub["notes"] + casing["notes"] + pull["notes"],
        "files": records,
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return {
        "path": str(folder),
        "files": records,
        "notes": manifest["notes"],
        "summary": f"{peg_total} pegs, {counts['tubs']} pull(s), "
        f"{sum(r['bytes'] for r in records) / 1e6:.1f} MB total",
    }


def build_part(part, x, y, h, floor, out: Path, design=None, bed=500.0) -> dict:
    mesh = render("pegs" if part == "pegs" else part, x, y, h, floor, design or {})
    size = f"{x}x{y}" if part in ("grid-insert", "baseplate") else f"{x}x{y}x{h}h"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{part}-{size}.3mf"
    write_3mf(path, [(part, mesh, 1)], bed)
    return {
        "path": str(path),
        "files": [file_record(path)],
        "notes": mesh["notes"],
        "summary": f"{' x '.join(map(str, mesh['size_mm']))} mm, {mesh['facets']} facets, {mesh['pieces']} piece(s)",
        "size_mm": mesh["size_mm"],
        "pieces": mesh["pieces"],
    }


def build(target, x, y, h, floor, out, design=None, counts=None, bed=500.0) -> dict:
    if target not in TARGETS:
        raise BuildError(f"unknown part: {target}")
    if target == "module":
        return build_module(x, y, h, floor, out, design, counts, bed)
    return build_part(target, x, y, h, floor, out, design, bed)


def field(label: str, name: str, default, low=None, high=None) -> str:
    if isinstance(default, bool):
        checked = " checked" if default else ""
        return f"<label>{html.escape(label)}<input type=checkbox name={name}{checked}></label>"
    step = "1" if isinstance(default, int) else "any"
    text = html.escape(f"{label} ({low} to {high})")
    return f"<label>{text}<input name={name} type=number min={low} max={high} step={step} value={default}></label>"


def page() -> str:
    targets = "".join(f"<option>{t}" for t in TARGETS)
    counts = "".join(field(label, name, default, low, high) for name, default, label, low, high in COUNT_OPTIONS)
    design = "".join(field(label, name, default, low, high) for name, _, default, label, low, high in DESIGN_OPTIONS)
    return f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Hutchfinity</title><style>
:root{{color-scheme:light dark}}body{{font:16px system-ui;max-width:30rem;margin:2rem auto;padding:0 1rem}}
label{{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin:.5rem 0}}
input[type=number],select{{font:inherit;width:7rem;padding:.25rem}}button{{font:inherit;padding:.5rem 1rem;margin-top:.6rem}}
summary{{margin-top:.8rem;cursor:pointer}}pre{{white-space:pre-wrap}}</style>
<h1>Hutchfinity <small>{VERSION}</small></h1><form id=f>
<label>Build<select name=target>{targets}</select></label>
<label>Preset<select id=preset><option value="">custom<option value="6,16,20">Mini
<option value="12,16,20">Regular<option value="18,16,20">Mega<option value="10,10,10" selected>10 x 10 x 10h</select></label>
<label>Cells wide<input name=x type=number min=1 max=40 value=10></label>
<label>Cells deep<input name=y type=number min=1 max=40 value=10></label>
<label>Tallest bin, 3.5 mm units (5 to 40)<input name=h type=number min=5 max=40 value=10></label>
<label>Floor<select name=floor><option>integral-grid<option>plain</select></label>
<details><summary>Quantities</summary>{counts}</details>
<details><summary>Dimensions and mesh</summary>{design}</details>
<button>Build</button></form><pre id=out></pre><script>
const f=document.getElementById('f'),o=document.getElementById('out');
document.getElementById('preset').onchange=e=>{{if(!e.target.value)return;
 const v=e.target.value.split(',');f.x.value=v[0];f.y.value=v[1];f.h.value=v[2]}};
f.target.onchange=()=>{{f.h.min=['bin','baseplate'].includes(f.target.value)?1:5}};
f.onsubmit=async e=>{{e.preventDefault();o.textContent='Building...';
 const q=new URLSearchParams(new FormData(f));f.querySelectorAll('input[type=checkbox]').forEach(c=>q.set(c.name,c.checked?'1':'0'));
 const r=await fetch('/build?'+q,{{headers:{{'X-Hutchfinity':'1'}}}});const j=await r.json();
 o.textContent=r.ok?`Saved to ${{j.path}}\\n${{j.summary}}\\n${{j.files.map(x=>x.file).join('\\n')}}\\n${{j.notes.join('\\n')}}`:'Could not build: '+j.error}};
</script>"""


def parse_form(q: dict) -> tuple:
    size = [int(q.get(k, "")) for k in ("x", "y", "h")]
    design = {}
    for name, _, default, *_ in DESIGN_OPTIONS:
        if name in q:
            kind = type(default)
            value = q[name] == "1" if kind is bool else kind(q[name])
            if value != default:
                design[name] = value
    counts = {option[0]: int(q[option[0]]) for option in COUNT_OPTIONS if option[0] in q}
    return q.get("target", "module"), size, q.get("floor", FLOORS[0]), design, counts


class App(BaseHTTPRequestHandler):
    out_dir = DEFAULT_OUT
    last_used = time.time()

    def reply(self, status: int, body: bytes, kind: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        App.last_used = time.time()
        url = urlparse(self.path)
        if url.path == "/":
            return self.reply(200, page().encode(), "text/html; charset=utf-8")
        if url.path != "/build":
            return self.reply(404, b"not found", "text/plain")
        # A custom header keeps other web pages from triggering builds here.
        if self.headers.get("X-Hutchfinity") != "1":
            return self.reply(403, b"forbidden", "text/plain")
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            target, size, floor, design, counts = parse_form(q)
            result, status = build(target, *size, floor, self.out_dir, design, counts), 200
            if platform.system() == "Darwin":
                subprocess.run(["open", "-R", result["path"]], check=False)
        except (BuildError, ValueError) as error:
            result, status = {"error": str(error)}, 400
        App.last_used = time.time()
        self.reply(status, json.dumps(result).encode(), "application/json")

    def log_message(self, *args) -> None:
        pass


def self_update() -> None:
    """Fast-forward this checkout if it can, and restart on the new code."""
    before = source_commit()
    try:
        subprocess.run(["git", "-C", str(ROOT), "pull", "-q", "--ff-only"], capture_output=True, timeout=8)
    except subprocess.TimeoutExpired:
        return
    if source_commit() != before:
        os.execv(sys.executable, [sys.executable, str(Path(__file__).resolve()), "--no-update", *sys.argv[1:]])


def serve(out: Path, port: int, open_browser: bool, idle_exit: bool) -> int:
    url = f"http://127.0.0.1:{port}/"
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), App)
    except OSError:
        if open_browser:  # Already running from an earlier click.
            webbrowser.open(url)
        return 0
    App.out_dir = out
    print(f"Hutchfinity {VERSION} is at {url} (Ctrl-C to stop). Files go to {out}")
    if open_browser:
        webbrowser.open(url)
    server.timeout = 30
    try:
        while not idle_exit or time.time() - App.last_used < IDLE_EXIT_SECONDS:
            server.handle_request()
    except KeyboardInterrupt:
        pass
    return 0


def install_shortcut(desktop: Path) -> Path:
    if platform.system() != "Darwin":
        raise BuildError("the clickable shortcut is macOS only; run python3 hutchfinity.py here")
    path = "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"
    script = (
        f'do shell script "export PATH={path}; cd {shlex_quote(str(ROOT))}; '
        f'nohup python3 hutchfinity.py --idle-exit > /dev/null 2>&1 &"'
    )
    target = desktop / "Hutchfinity.app"
    subprocess.run(["osacompile", "-o", str(target), "-e", script], check=True)
    return target


def shlex_quote(text: str) -> str:
    if re.search(r'["\\]', text):
        raise BuildError(f"unsupported characters in path: {text}")
    return "'" + text.replace("'", "'\\''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", nargs="?", choices=TARGETS)
    parser.add_argument("size", nargs="*", type=int, help="cells wide, cells deep, tallest bin")
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--floor", choices=FLOORS, default=FLOORS[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--bed", type=float, default=500.0, help="bed width used to lay out rows, mm")
    for name, default, label, low, high in COUNT_OPTIONS:
        parser.add_argument(f"--{name.replace('_', '-')}", type=int, default=default,
                            help=f"{label} ({low} to {high}, default {default})")
    for name, _, default, label, low, high in DESIGN_OPTIONS:
        flag = f"--{name.replace('_', '-')}"
        if isinstance(default, bool):
            parser.add_argument(flag, action=argparse.BooleanOptionalAction, default=default, help=label)
        else:
            parser.add_argument(flag, type=type(default), default=default, help=f"{label} ({low} to {high}, default {default})")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--no-update", action="store_true", help="skip the git update at app start")
    parser.add_argument("--idle-exit", action="store_true", help="stop the app after 30 idle minutes")
    parser.add_argument("--install-shortcut", action="store_true", help="add Hutchfinity.app to the Desktop")
    args = parser.parse_args()
    try:
        if args.install_shortcut:
            print(install_shortcut(Path.home() / "Desktop"))
            return 0
        if not args.target:
            if not args.no_update:
                self_update()
            return serve(args.out, args.port, not args.no_browser, args.idle_exit)
        if len(args.size) != 3:
            parser.error("give three sizes: cells wide, cells deep, tallest bin")
        design = {
            option[0]: getattr(args, option[0]) for option in DESIGN_OPTIONS if getattr(args, option[0]) != option[2]
        }
        counts = {option[0]: getattr(args, option[0]) for option in COUNT_OPTIONS}
        print(json.dumps(build(args.target, *args.size, args.floor, args.out, design, counts, args.bed), indent=2))
    except BuildError as error:
        print(f"Could not build: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
