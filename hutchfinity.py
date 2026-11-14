#!/usr/bin/env python3
"""Hutchfinity generator: build a full drawer module as Orca-ready 3MF files.

    python3 hutchfinity.py                     opens the app in a browser
    python3 hutchfinity.py 10 10 10            builds one complete module
    python3 hutchfinity.py cup 2 4 10          builds one cup
    python3 hutchfinity.py --install-shortcut  adds a clickable app to the Desktop

Sizes are cells wide, cells deep, and height in 3.5 mm units. --help lists every option.
Needs only Python and OpenSCAD. Set OPENSCAD_BIN if OpenSCAD is not on PATH.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import errno
from functools import lru_cache
import hashlib
import html
import json
import math
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.client import HTTPConnection, HTTPException
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree as ET

from print_settings import (
    PrintOptions, PrintSettingsError, load_print_options, part_record,
    print_options, write_printing_files,
)

VERSION = "2.3.0"
ROOT = Path(__file__).resolve().parent
ENTRY = ROOT / "scad" / "hutchfinity.scad"
CUP = ROOT / "scad" / "gridfinity" / "vendor" / "extended" / "gridfinity_basic_cup.scad"
FLOORS = {"integral-grid": "integral-grid", "separate-grid": "plain"}  # name: tub.scad floor_mode
MAC_APP = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
DEFAULT_OUT = Path.home() / "Downloads" / "hutchfinity"
PORT = 8421
IDLE_EXIT_SECONDS = 30 * 60

# name, OpenSCAD variable, default, help, lowest, highest.
DESIGN_OPTIONS = [
    ("pull_guide", "pull_guide", True, "raised guide on the tub front for gluing the pull", None, None),
    ("wall", "WALL", 2.2, "tub wall, mm", 1.2, 4.0),
    ("rim_wall", "MIN_WALL", 0.4, "tub wall at the rim, mm", 0.3, 1.0),
    ("floor_thickness", "FLOOR_THICKNESS", 1.3, "tub floor under the grid, mm", 0.8, 3.0),
    ("grid_height", "GRID_Z", 5.0, "grid height, mm", 5.0, 8.0),
    ("stack_gap", "STACK_GAP", 0.5, "air gap above the tallest bin when stacked, mm", 0.0, 5.0),
    ("bin_lip", "BIN_LIP", 3.74, "bin lip height, mm", 3.0, 5.0),
    ("grid_clearance", "INSERT_CLEARANCE", 1.0, "separate grid clearance per side, mm", 0.2, 2.0),
    ("side_wall", "side_wall", 18.0, "casing side wall, mm", 18.0, 40.0),
    ("back_wall", "back_wall", 18.0, "casing back wall, mm", 18.0, 40.0),
    ("riding_slab", "riding_slab", 3.0, "casing slab the tub above rides on, mm", 1.0, 10.0),
    ("side_clearance", "side_clearance", 1.0, "tub to casing, each side, mm", 0.2, 3.0),
    ("back_clearance", "back_clearance", 0.5, "tub to casing, back, mm", 0.2, 3.0),
    ("top_clearance", "top_clearance", 1.0, "tub to casing, top, mm", 0.2, 5.0),
    ("peg_spacing", "peg_spacing", 190.0, "target peg spacing, mm", 15.0, 400.0),
    ("peg_bore", "peg_bore", 8.45, "peg socket bore and peg width, mm", 6.0, 9.0),
    ("peg_depth", "peg_depth_max", 10.0, "peg socket depth, mm", 5.0, 15.0),
    ("peg_chamfer", "peg_chamfer", 0.5, "socket opening chamfer, mm", 0.0, 0.75),
    ("peg_end_chamfer", "peg_end_chamfer", 2.5, "peg end chamfer, mm", 0.0, 4.0),
    ("pull_width", "PULL_FLANGE_X", 90.0, "full-size pull flange width, mm", 60.0, 120.0),
    ("pull_height", "PULL_FLANGE_Z", 32.9, "full-size pull flange height, mm", 31.0, 40.0),
]
CELLS_RANGE = (1, 40)
CUP_HEIGHT_RANGE = (2, 40)  # At 1 the source breaks into separate pieces.
CUP_COMPARTMENTS_RANGE = (1, 10)
CUP_MIN_COMPARTMENT_MM = 10.0
CUP_WALL_RANGE = (0.6, 3.0)  # Unset: the cup source picks a wall from the height.
TUB_HEIGHT_RANGE = (5, 40)  # A tub must hold at least a 5h bin.
BED_MM = 500.0  # Only spaces objects out in the file; the slicer arranges them.


class BuildError(Exception):
    pass


@lru_cache(maxsize=4)
def _checked_openscad(candidate: str) -> tuple[str, ...]:
    if not (shutil.which(candidate) or Path(candidate).is_file()):
        raise BuildError("OpenSCAD not found. Install it or set OPENSCAD_BIN.")
    command = [candidate]
    try:
        subprocess.run(command + ["--version"], capture_output=True, check=True, timeout=10)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # An Intel build on Apple Silicon may need Rosetta.
        if platform.system() == "Darwin" and shutil.which("arch"):
            command = ["arch", "-x86_64", candidate]
            try:
                subprocess.run(command + ["--version"], capture_output=True, check=True, timeout=10)
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
                raise BuildError("OpenSCAD failed to start, including the Rosetta fallback") from None
        else:
            raise BuildError("OpenSCAD failed to start") from None
    try:
        help_run = subprocess.run(command + ["--help"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        raise BuildError("Could not check OpenSCAD's renderer support") from None
    if "Manifold" not in help_run.stdout + help_run.stderr:
        raise BuildError("This generator needs an OpenSCAD build with the Manifold backend; "
                         "install a current development build and set OPENSCAD_BIN if needed.")
    return tuple(command)


def find_openscad() -> list[str]:
    candidate = os.environ.get("OPENSCAD_BIN") or shutil.which("openscad") or MAC_APP
    return list(_checked_openscad(candidate))


def check_range(label: str, value, low, high) -> None:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not low <= value <= high):
        raise BuildError(f"{label} must be from {low} to {high}; got {value}")


def check_size(x: int, y: int, h: int) -> None:
    if any(type(value) is not int for value in (x, y, h)):
        raise BuildError("cell counts and bin height must be whole numbers")
    check_range("cells wide", x, *CELLS_RANGE)
    check_range("cells deep", y, *CELLS_RANGE)
    check_range("tallest bin", h, *TUB_HEIGHT_RANGE)


def scad_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    raise BuildError(f"bad value: {value!r}")


def design_overrides(design: dict) -> list[str]:
    if not isinstance(design, dict):
        raise BuildError("design options must be an object")
    known = {option[0]: option for option in DESIGN_OPTIONS}
    overrides = []
    for name, value in design.items():
        if name not in known:
            raise BuildError(f"unknown option: {name}")
        _, var, default, _, low, high = known[name]
        if isinstance(default, bool) and type(value) is not bool:
            raise BuildError(f"{name} must be true or false")
        if low is not None:
            check_range(name.replace("_", " "), value, low, high)
        if value != default:
            overrides.append(f"{var}={scad_value(value)}")
    return overrides


def scad_source(part: str, x: int, y: int, h: int, floor: str, design: dict) -> tuple[Path, list[str]]:
    if floor not in FLOORS:
        raise BuildError(f"unknown floor: {floor}")
    return ENTRY, [
        f'part="{part}"', f"cells_x={x}", f"cells_y={y}", f"bin_h={h}", f'floor_mode="{FLOORS[floor]}"',
        *design_overrides(design),
    ]


def checked_mesh(points: list[tuple], triangles: list[tuple[int, int, int]]) -> dict:
    """Validate oriented indexed topology without destroying its vertex identity.

    Manifold can retain collinear boundary triangles between different indexed
    vertices. Removing these opens the adjacent surface. Keep that topology,
    require exactly two oppositely oriented faces per edge and positive volume,
    and count connected surfaces so callers can reject disconnected parts.
    """
    if not points or not triangles:
        raise BuildError("OpenSCAD wrote an empty mesh")
    if not all(len(point) == 3 and all(math.isfinite(value) for value in point) for point in points):
        raise BuildError("OpenSCAD wrote non-finite mesh coordinates")
    edges: dict[tuple[int, int], int] = {}
    edge_faces: dict[tuple[int, int], int] = {}
    parent = list(range(len(triangles)))
    volume = 0.0

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for face, corners in enumerate(triangles):
        if (len(corners) != 3 or len(set(corners)) != 3
                or any(type(index) is not int or index < 0 or index >= len(points) for index in corners)):
            raise BuildError("OpenSCAD wrote invalid mesh triangle indices")
        a, b, c = [points[index] for index in corners]
        ab, ac = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
        normal = [ab[1] * ac[2] - ab[2] * ac[1],
                  ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0]]
        volume += sum(a[i] * normal[i] for i in range(3)) / 6
        for a, b in zip(corners, corners[1:] + corners[:1]):
            edges[(a, b)] = edges.get((a, b), 0) + 1
            edge = (min(a, b), max(a, b))
            if edge in edge_faces:
                parent[find(face)] = find(edge_faces[edge])
            else:
                edge_faces[edge] = face
    low = [min(p[i] for p in points) for i in range(3)]
    high = [max(p[i] for p in points) for i in range(3)]
    return {
        "points": points,
        "triangles": triangles,
        "low": low,
        "size_mm": [round(high[i] - low[i], 2) for i in range(3)],
        "facets": len(triangles),
        "closed": math.isfinite(volume) and volume > 0
                  and all(n == 1 and edges.get((b, a)) == 1 for (a, b), n in edges.items()),
        "pieces": len({find(i) for i in range(len(parent))}),
        "volume_mm3": volume,
    }


def read_stl(path: Path) -> dict:
    """Read legacy binary STL fixtures; production renders retain native 3MF indices."""
    data = path.read_bytes()
    if len(data) < 84:
        raise BuildError("OpenSCAD did not write a valid binary STL")
    count = struct.unpack_from("<I", data, 80)[0]
    if count == 0 or len(data) != 84 + 50 * count:
        raise BuildError("OpenSCAD did not write a valid binary STL")
    ids, triangles = {}, []
    for facet in range(count):
        offset = 84 + 50 * facet + 12
        coordinates = [struct.unpack_from("<3f", data, offset + 12 * corner) for corner in range(3)]
        if not all(math.isfinite(value) for point in coordinates for value in point):
            raise BuildError("OpenSCAD wrote non-finite STL coordinates")
        coordinates = [tuple(round(value, 6) for value in point) for point in coordinates]
        if len(set(coordinates)) < 3:
            continue
        corners = []
        for vertex in coordinates:
            if vertex not in ids:
                ids[vertex] = len(ids)
            corners.append(ids[vertex])
        triangles.append(tuple(corners))
    return checked_mesh(list(ids), triangles)


def read_3mf(path: Path) -> dict:
    """Read one native OpenSCAD mesh, preserving its indexed Manifold topology.

    A binary STL intermediary loses shared indices and rounds coordinates to
    float32. Welding it can collapse the vendor cup's thin hull triangles.
    OpenSCAD's indexed 3MF retains the topology that the slicer actually uses.
    """
    try:
        with zipfile.ZipFile(path) as archive:
            model = ET.fromstring(archive.read("3D/3dmodel.model"))
        if model.attrib.get("unit", "millimeter") != "millimeter":
            raise BuildError("OpenSCAD 3MF must use millimeters")
        objects = {obj.attrib["id"]: obj for obj in model.findall("{*}resources/{*}object")}
        items = model.findall("{*}build/{*}item")
        if len(items) != 1:
            raise BuildError("OpenSCAD must export one mesh object for this part")
        transform = items[0].attrib.get("transform")
        if transform and [float(value) for value in transform.split()] != [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]:
            raise BuildError("OpenSCAD mesh has an unexpected placement transform")
        mesh = objects[items[0].attrib["objectid"]].find("{*}mesh")
        if mesh is None:
            raise BuildError("OpenSCAD did not export a direct mesh object")
        points = [tuple(float(vertex.attrib[axis]) for axis in ("x", "y", "z"))
                  for vertex in mesh.findall("{*}vertices/{*}vertex")]
        triangles = [tuple(int(triangle.attrib[index]) for index in ("v1", "v2", "v3"))
                     for triangle in mesh.findall("{*}triangles/{*}triangle")]
    except (zipfile.BadZipFile, ET.ParseError, KeyError, ValueError) as error:
        raise BuildError(f"OpenSCAD did not write a valid 3MF mesh: {error}") from None
    return checked_mesh(points, triangles)


def run_openscad(label: str, source: Path, overrides: list[str]) -> dict:
    with tempfile.TemporaryDirectory() as work:
        path = Path(work) / "part.3mf"
        command = find_openscad() + ["--backend=Manifold", "-o", str(path)]
        for override in overrides:
            command += ["-D", override]
        try:
            run = subprocess.run(command + [str(source)], capture_output=True, text=True)
        except OSError as error:
            raise BuildError(f"{label}: could not run OpenSCAD: {error.strerror}") from None
        log = run.stdout + run.stderr
        if run.returncode or not path.exists():
            errors = [line for line in log.splitlines() if re.search(r"ERROR|Assertion", line)]
            raise BuildError(f"{label}: " + ("; ".join(errors) or log.strip()[-400:]))
        mesh = read_3mf(path)
    if not mesh["closed"]:
        raise BuildError(f"{label} is not a closed solid; nothing was saved")
    mesh["notes"] = re.findall(r'ECHO: "(.*)"', log) if source == ENTRY else []
    return mesh


def render(part: str, x: int, y: int, h: int, floor: str, design: dict) -> dict:
    return run_openscad(part, *scad_source(part, x, y, h, floor, design))


def render_cup(x: int, y: int, h: int, across: int = 1, along: int = 1, wall: float | None = None) -> dict:
    if any(type(value) is not int for value in (x, y, h, across, along)):
        raise BuildError("cup size and compartment counts must be whole numbers")
    check_range("cup cells wide", x, *CELLS_RANGE)
    check_range("cup cells deep", y, *CELLS_RANGE)
    check_range("cup height", h, *CUP_HEIGHT_RANGE)
    check_range("compartments across", across, *CUP_COMPARTMENTS_RANGE)
    check_range("compartments along", along, *CUP_COMPARTMENTS_RANGE)
    if wall is not None:
        check_range("cup wall", wall, *CUP_WALL_RANGE)
    if x * 21 / across < CUP_MIN_COMPARTMENT_MM or y * 21 / along < CUP_MIN_COMPARTMENT_MM:
        raise BuildError(f"compartments must be at least {CUP_MIN_COMPARTMENT_MM:g} mm wide")
    defines = [
        "pitch=[21,21,3.5]", f"width=[{x},0]", f"depth=[{y},0]", f"height=[{h},0]",
        'lip_style="minimum"', "enable_magnets=false", "enable_screws=false",
        'label_style="disabled"', 'fingerslide="none"',
        f"vertical_chambers={across}", f"horizontal_chambers={along}",
    ]
    if wall is not None:
        defines.append(f"wall_thickness={wall!r}")
    mesh = run_openscad("cup", CUP, defines)
    if mesh["pieces"] != 1:
        raise BuildError(f"the cup came out in {mesh['pieces']} pieces; nothing was saved")
    return mesh


@contextmanager
def output_workspace(out: Path):
    """Serialize writers and keep unfinished jobs away from published files."""
    out.mkdir(parents=True, exist_ok=True)
    with (out / ".hutchfinity-build.lock").open("a+b") as lock:
        lock.seek(0)
        if not lock.read(1):
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise BuildError("Another build is using this output folder. Wait for it to finish and try again.") from None
        work = None
        preserve_recovery = False
        try:
            work = Path(tempfile.mkdtemp(prefix=".hutchfinity-building-", dir=out))
            try:
                yield work
            except BaseException as error:
                backup = work / "previous"
                preserve_recovery = backup.is_dir() and any(backup.iterdir())
                if preserve_recovery and isinstance(error, Exception):
                    raise BuildError(f"Output replacement could not be completed. "
                                     f"Previous files are preserved for recovery in {backup}") from error
                raise
        finally:
            if work is not None and not preserve_recovery:
                shutil.rmtree(work)
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def publish_directory(staging: Path, target: Path) -> None:
    """Replace a complete module only after every render and file write passed."""
    backup = staging.parent / "previous"
    had_previous = target.exists()
    if target.is_symlink() or (had_previous and not target.is_dir()):
        raise BuildError("The module destination must be an ordinary folder")
    if had_previous:
        target.rename(backup)
    try:
        staging.rename(target)
    except BaseException:
        if had_previous:
            backup.rename(target)
        raise


def publish_cup_files(staging: Path, target: Path) -> None:
    """Replace this cup's files with rollback, preserving all other cups."""
    target.mkdir(parents=True, exist_ok=True)
    backup = staging.parent / "previous"
    backup.mkdir()
    moved, installed = [], []
    try:
        for source in sorted(staging.iterdir()):
            destination = target / source.name
            if destination.exists() or destination.is_symlink():
                if destination.is_dir():
                    raise BuildError(f"A folder occupies the output filename {source.name}")
                destination.rename(backup / source.name)
                moved.append(source.name)
            source.rename(destination)
            installed.append(source.name)
    except BaseException:
        for name in installed:
            (target / name).unlink()
        for name in moved:
            (backup / name).rename(target / name)
        raise


def build_cup(x, y, h, out: Path, across=1, along=1, wall=None, printing: PrintOptions | None = None) -> dict:
    """Build one cup as one 3MF, in a cups folder beside the modules."""
    try:
        with output_workspace(out) as work:
            return _build_cup(x, y, h, out, across, along, wall, printing, work)
    except OSError as error:
        raise BuildError(f"Could not save cup files: {error.strerror or str(error)}") from None


def _build_cup(x, y, h, out, across, along, wall, printing, work) -> dict:
    mesh = render_cup(x, y, h, across, along, wall)
    name = f"cup-{x}x{y}x{h}h"
    if across > 1 or along > 1:
        name += f"-{across}x{along}-compartments"
    if wall is not None:
        name += f"-{wall:g}mm-wall"
    folder = work / "result"
    folder.mkdir()
    path = folder / f"{name}.3mf"
    printing = printing or print_options()
    parts = {"Cup": part_record("Cup", 1, printing)}
    settings = None if printing.geometry_only else {name: part["applied_overrides"] for name, part in parts.items()}
    write_3mf(path, [("Cup", mesh, 1)], BED_MM, settings)
    guides = write_printing_files(folder, [{"file": path.name, "parts": parts}], printing, stem=name)
    files = [file_record(path), *(file_record(p) for p in guides)]
    publish_cup_files(folder, out / "cups")
    return {
        "path": str(out / "cups" / path.name),
        "files": files,
        "notes": [f"Print settings and orientation are listed in {name}.PRINTING.md."],
        "summary": f"{' x '.join(map(str, mesh['size_mm']))} mm, {mesh['facets']} facets",
        "size_mm": mesh["size_mm"],
    }


def write_3mf(path: Path, objects: list[tuple[str, dict, int]], bed: float = 500.0,
              object_settings: dict[str, dict[str, str]] | None = None) -> None:
    """Write named objects, each with a copy count, laid out in rows from the bed corner.

    Plain files share meshes between copies. With settings, each physical copy
    gets its own direct mesh resource so Orca can retain its object overrides.
    Printer, filament and all unlisted settings remain the receiver's choice.
    """
    gap = 8.0
    resources, items = [], []
    settings_root = ET.Element("config")
    cursor_x, cursor_y, row = gap, gap, 0.0
    resources_to_write = objects if object_settings is None else [
        (name, mesh, 1) for name, mesh, copies in objects for _ in range(copies)
    ]
    for index, (name, mesh, copies) in enumerate(resources_to_write, start=1):
        low = mesh["low"]
        vertices = "".join(
            f'<vertex x="{p[0] - low[0]:.6f}" y="{p[1] - low[1]:.6f}" z="{p[2] - low[2]:.6f}"/>'
            for p in mesh["points"]
        )
        triangles = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh["triangles"])
        resources.append(
            f'<object id="{index}" name="{html.escape(name)}" type="model"><mesh>'
            f"<vertices>{vertices}</vertices><triangles>{triangles}</triangles></mesh></object>"
        )
        if object_settings is not None:
            obj = ET.SubElement(settings_root, "object", id=str(index))
            ET.SubElement(obj, "metadata", key="name", value=name)
            for key, value in sorted(object_settings.get(name, {}).items()):
                ET.SubElement(obj, "metadata", key=key, value=value)
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
            '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
            + ('<Default Extension="config" ContentType="application/xml"/>' if object_settings is not None else '')
            + '</Types>',
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
        )
        archive.writestr("3D/3dmodel.model", model)
        if object_settings is not None:
            archive.writestr("Metadata/model_settings.config", ET.tostring(settings_root, encoding="utf-8", xml_declaration=True))


def source_commit() -> str:
    try:
        run = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    return run.stdout.strip() if run.returncode == 0 else "unknown"


def source_provenance() -> dict:
    """A commit alone does not identify a build made from modified sources."""
    try:
        status = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=normal"],
                                capture_output=True, text=True, timeout=5)
        dirty = bool(status.stdout) if status.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        dirty = None
    digest = hashlib.sha256()
    inputs = [ROOT / "hutchfinity.py", ROOT / "print_settings.py", *sorted((ROOT / "scad").rglob("*.scad"))]
    for path in inputs:
        digest.update(path.relative_to(ROOT).as_posix().encode() + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return {"source_commit": source_commit(), "source_dirty": dirty,
            "source_inputs_sha256": digest.hexdigest()}


def file_record(path: Path, **extra) -> dict:
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        **extra,
    }


def build_module(x, y, h, floor, out: Path, design=None, printing: PrintOptions | None = None) -> dict:
    """Build one complete module: one 3MF per print job, plus a manifest."""
    design = {} if design is None else design
    printing = printing or print_options()
    check_size(x, y, h)
    design_overrides(design)
    if not isinstance(floor, str) or floor not in FLOORS:
        raise BuildError(f"unknown floor: {floor}")
    if floor == "separate-grid" and min(x, y) < 2:
        raise BuildError("a separate grid needs at least 2 x 2 cells")
    try:
        with output_workspace(out) as work:
            return _build_module(x, y, h, floor, out, design, printing, work)
    except OSError as error:
        raise BuildError(f"Could not save module files: {error.strerror or str(error)}") from None


def _build_module(x, y, h, floor, out, design, printing, work) -> dict:
    provenance = source_provenance()
    render_part = lambda part: render(part, x, y, h, floor, design)
    tub, casing, peg, pull = (render_part(p) for p in ("tub", "casing", "peg", "pull"))
    peg_match = re.search(r"\b(\d+) pegs\b", "\n".join(casing["notes"]))
    if not peg_match or int(peg_match[1]) < 1:
        raise BuildError("The casing renderer did not report a valid peg count")
    peg_total = int(peg_match[1])
    target = out / f"hutchfinity-{x}x{y}x{h}h-{floor}"
    folder = work / "result"
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise BuildError("The module destination must be an ordinary folder")
    folder.mkdir()
    jobs = [
        ("1-tub.3mf", [("Tub", tub, 1)]),
        ("2-casing.3mf", [("Casing", casing, 1)]),
        ("3-pegs-and-pull.3mf", [("Peg", peg, peg_total), ("Pull", pull, 1)]),
    ]
    if floor == "separate-grid":
        jobs.append(("4-grid.3mf", [("Grid", render_part("grid-insert"), 1)]))
    for _, objects in jobs:
        for name, mesh, _ in objects:
            if mesh["pieces"] != 1:
                raise BuildError(f"{name} came out in {mesh['pieces']} pieces; no output was replaced")
    records, print_jobs = [], []
    defaults = {option[0]: option[2] for option in DESIGN_OPTIONS}
    floor_depths = {"Tub": design.get("floor_thickness", defaults["floor_thickness"]),
                    "Casing": design.get("riding_slab", defaults["riding_slab"])}
    for name, objects in jobs:
        parts = {part: part_record(part, copies, printing, floor_depths.get(part)) for part, _, copies in objects}
        settings = None if printing.geometry_only else {part: record["applied_overrides"] for part, record in parts.items()}
        write_3mf(folder / name, objects, BED_MM, settings)
        print_jobs.append({"file": name, "parts": parts})
        records.append(file_record(folder / name, parts={o[0]: o[2] for o in objects}))
    records.extend(file_record(path) for path in write_printing_files(folder, print_jobs, printing))
    manifest = {
        "generator_version": VERSION,
        **provenance,
        "size": {"cells_x": x, "cells_y": y, "bin_h": h, "floor": floor},
        "design_overrides": design,
        "printing": printing.record(),
        "peg_total": peg_total,
        "sizes_mm": {"tub": tub["size_mm"], "casing": casing["size_mm"], "pull": pull["size_mm"], "peg": peg["size_mm"]},
        "facets": {"tub": tub["facets"], "casing": casing["facets"], "pull": pull["facets"], "peg": peg["facets"]},
        "notes": tub["notes"] + casing["notes"] + pull["notes"] + ["See PRINTING.md for orientations, exact process overrides, and inherited settings."],
        "files": records,
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if source_provenance()["source_inputs_sha256"] != provenance["source_inputs_sha256"]:
        raise BuildError("Source files changed during the build; retry with stable sources")
    if target.exists():
        # Preserve user-added files without following or writing through links.
        for existing in target.iterdir():
            destination = folder / existing.name
            if not destination.exists():
                if existing.is_dir() and not existing.is_symlink():
                    shutil.copytree(existing, destination, symlinks=True)
                else:
                    shutil.copy2(existing, destination, follow_symlinks=False)
    publish_directory(folder, target)
    return {
        "path": str(target),
        "files": records,
        "notes": manifest["notes"],
        "summary": f"{peg_total} pegs, {sum(r['bytes'] for r in records) / 1e6:.1f} MB total",
    }


def field(label: str, name: str, default, low=None, high=None) -> str:
    if isinstance(default, bool):
        checked = " checked" if default else ""
        return f"<label>{html.escape(label)}<input type=checkbox name={name}{checked}></label>"
    step = "1" if isinstance(default, int) else "any"
    text = html.escape(f"{label} ({low} to {high})")
    return f"<label>{text}<input name={name} type=number min={low} max={high} step={step} value={default}></label>"


def print_fields(casing: bool = False) -> str:
    avoid = '<label>Avoid casing infill crossings<input type=checkbox name=avoid_crossings></label>' if casing else ''
    return ('<details><summary>Print settings</summary>'
            '<label>Orca process JSON (optional)<input type=file name=process_profile accept=".json,application/json"></label>'
            + avoid + '<label>Plain geometry 3MF<input type=checkbox name=plain_3mf></label>'
            '<p>With no print options, the 3MF stays plain and the companion guide lists recommendations. '
            'Selected process overrides only: printer, filament, first-layer and unlisted settings '
            'come from your active slicer profiles. Plain geometry applies no overrides.</p></details>')


def page() -> str:
    floors = "".join(f"<option>{name}" for name in FLOORS)
    design = "".join(field(label, name, default, low, high) for name, _, default, label, low, high in DESIGN_OPTIONS)
    return f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Hutchfinity</title><style>
:root{{color-scheme:light dark}}body{{font:16px system-ui;max-width:30rem;margin:2rem auto;padding:0 1rem}}
label{{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin:.5rem 0}}
input[type=number],select{{font:inherit;width:7rem;padding:.25rem}}button{{font:inherit;padding:.5rem 1rem;margin-top:.6rem}}
summary{{margin-top:.8rem;cursor:pointer}}pre{{white-space:pre-wrap}}</style>
<h1>Hutchfinity <small>{VERSION}</small></h1><h2>Module</h2><form id=f>
<label>Preset<select id=preset><option value="">custom<option value="6,16,20">Mini
<option value="12,16,20">Regular<option value="18,16,20">Mega<option value="10,10,10" selected>10 x 10 x 10h</select></label>
<label>Cells wide<input name=x type=number min=1 max=40 value=10></label>
<label>Cells deep<input name=y type=number min=1 max=40 value=10></label>
<label>Tallest bin, 3.5 mm units (5 to 40)<input name=h type=number min=5 max=40 value=10></label>
<label>Floor<select name=floor>{floors}</select></label>
<details><summary>Dimensions</summary>{design}</details>
{print_fields(casing=True)}
<button>Build module</button></form><h2>Cup</h2><form id=c>
<label>Cells wide (1 to 40)<input name=x type=number min=1 max=40 value=2></label>
<label>Cells deep (1 to 40)<input name=y type=number min=1 max=40 value=2></label>
<label>Height, 3.5 mm units (2 to 40)<input name=h type=number min=2 max=40 value=10></label>
<label>Compartments across (1 to 10)<input name=across type=number min=1 max=10 value=1></label>
<label>Compartments along (1 to 10)<input name=along type=number min=1 max=10 value=1></label>
<label>Wall, mm (0.6 to 3, blank is automatic)<input name=wall type=number min=0.6 max=3 step=any></label>
{print_fields()}
<button>Build cup</button></form><pre id=out></pre><script>
const f=document.getElementById('f'),c=document.getElementById('c'),o=document.getElementById('out');
document.getElementById('preset').onchange=e=>{{if(!e.target.value)return;
 const v=e.target.value.split(',');f.x.value=v[0];f.y.value=v[1];f.h.value=v[2]}};
const send=(form,path)=>async e=>{{e.preventDefault();o.textContent='Building...';
 const buttons=[...document.querySelectorAll('button')];buttons.forEach(b=>b.disabled=true);
 try{{const q=Object.fromEntries(new FormData(form));delete q.process_profile;
 form.querySelectorAll('input[type=checkbox]').forEach(b=>q[b.name]=b.checked?'1':'0');
 const file=form.querySelector('[name=process_profile]').files[0];
 if(file){{q.process_profile=JSON.parse(await file.text());q.profile_name=file.name}}
 const r=await fetch(path,{{method:'POST',headers:{{'X-Hutchfinity':'1','Content-Type':'application/json'}},body:JSON.stringify(q)}});const j=await r.json();
 o.textContent=r.ok?`Saved to ${{j.path}}\\n${{j.summary}}\\n${{j.files.map(x=>x.file).join('\\n')}}\\n${{j.notes.join('\\n')}}`:'Could not build: '+j.error;
 }}catch(error){{o.textContent='Could not build: '+error.message}}
 finally{{buttons.forEach(b=>b.disabled=false)}}}};
f.onsubmit=send(f,'/build');c.onsubmit=send(c,'/cup');
</script>"""


def form_integer(value, label: str) -> int:
    if type(value) is int:
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
        return int(value)
    raise BuildError(f"{label} must be a whole number")


def form_boolean(value, label: str) -> bool:
    if type(value) is bool:
        return value
    if value in ("0", "1"):
        return value == "1"
    raise BuildError(f"{label} must be true or false")


def form_number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise BuildError(f"{label} must be numeric")
    try:
        result = float(value)
    except (ValueError, OverflowError):
        raise BuildError(f"{label} must be numeric") from None
    if not math.isfinite(result):
        raise BuildError(f"{label} must be finite")
    return result


def parse_form(q: dict) -> tuple:
    size = [form_integer(q.get(k, ""), k) for k in ("x", "y", "h")]
    design = {}
    for name, _, default, *_ in DESIGN_OPTIONS:
        if name in q:
            value = form_boolean(q[name], name) if isinstance(default, bool) else form_number(q[name], name)
            if value != default:
                design[name] = value
    return size, q.get("floor", "integral-grid"), design


def parse_cup_form(q: dict) -> tuple:
    wall = q.get("wall", "")
    return ([form_integer(q.get(k, ""), k) for k in ("x", "y", "h")],
            form_integer(q.get("across", 1), "across"), form_integer(q.get("along", 1), "along"),
            form_number(wall, "wall") if wall not in ("", None) else None)


def parse_print_form(q: dict) -> PrintOptions:
    return print_options(q.get("process_profile"), profile_name=q.get("profile_name"),
                         avoid_crossings=form_boolean(q.get("avoid_crossings", False), "avoid_crossings"),
                         geometry_only=form_boolean(q.get("plain_3mf", False), "plain_3mf"))


class App(BaseHTTPRequestHandler):
    out_dir = DEFAULT_OUT
    last_used = time.time()
    active_builds = 0
    activity_lock = threading.Lock()

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
        if url.path == "/health":
            state = {"application": "hutchfinity", "version": VERSION,
                     "output": str(App.out_dir.resolve())}
            return self.reply(200, json.dumps(state).encode(), "application/json")
        if url.path not in ("/build", "/cup"):
            return self.reply(404, b"not found", "text/plain")
        # A custom header keeps other web pages from triggering builds here.
        if self.headers.get("X-Hutchfinity") != "1":
            return self.reply(403, b"forbidden", "text/plain")
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        self.run_build(url.path, q)

    def do_POST(self) -> None:
        url = urlparse(self.path)
        if url.path not in ("/build", "/cup"):
            return self.reply(404, b"not found", "text/plain")
        if self.headers.get("X-Hutchfinity") != "1":
            return self.reply(403, b"forbidden", "text/plain")
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2_000_000:
                raise ValueError("request must contain at most 2 MB of JSON")
            q = json.loads(self.rfile.read(length))
            if not isinstance(q, dict):
                raise ValueError("request must be a JSON object")
        except (ValueError, UnicodeError) as error:
            return self.reply(400, json.dumps({"error": str(error)}).encode(), "application/json")
        self.run_build(url.path, q)

    def run_build(self, path: str, q: dict) -> None:
        with App.activity_lock:
            App.last_used = time.time()
            App.active_builds += 1
        try:
            printing = parse_print_form(q)
            if path == "/cup":
                size, across, along, wall = parse_cup_form(q)
                result, status = build_cup(*size, self.out_dir, across, along, wall, printing), 200
            else:
                size, floor, design = parse_form(q)
                result, status = build_module(*size, floor, self.out_dir, design, printing), 200
            if platform.system() == "Darwin":
                try:
                    subprocess.run(["open", "-R", result["path"]], check=False)
                except OSError:
                    pass  # The saved path remains usable if Finder cannot open.
        except (BuildError, ValueError, TypeError) as error:
            result, status = {"error": str(error)}, 400
        finally:
            with App.activity_lock:
                App.last_used = time.time()
                App.active_builds -= 1
        self.reply(status, json.dumps(result).encode(), "application/json")

    def log_message(self, *args) -> None:
        pass


def self_update() -> None:
    """Update only a clean main checkout, leaving feature branches untouched."""
    try:
        branch = subprocess.run(["git", "-C", str(ROOT), "symbolic-ref", "--short", "HEAD"],
                                capture_output=True, text=True, timeout=5)
        status = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"],
                                capture_output=True, text=True, timeout=5)
        if branch.returncode or branch.stdout.strip() != "main" or status.returncode or status.stdout:
            return
        before = source_commit()
        result = subprocess.run(["git", "-C", str(ROOT), "pull", "-q", "--ff-only", "origin", "main"],
                                capture_output=True, timeout=8)
    except (OSError, subprocess.TimeoutExpired):
        return
    if result.returncode == 0 and source_commit() != before:
        os.execv(sys.executable, [sys.executable, str(Path(__file__).resolve()), "--no-update", *sys.argv[1:]])


def matching_listener(port: int, out: Path) -> bool:
    """Identify the loopback app before treating an occupied port as reuse."""
    connection = HTTPConnection("127.0.0.1", port, timeout=1)
    try:
        connection.request("GET", "/health")
        response = connection.getresponse()
        if response.status != 200:
            return False
        state = json.loads(response.read(4096))
        return (isinstance(state, dict) and state.get("application") == "hutchfinity"
                and state.get("version") == VERSION and state.get("output") == str(out.resolve()))
    except (OSError, HTTPException, ValueError, UnicodeError):
        return False
    finally:
        connection.close()


def serve(out: Path, port: int, open_browser: bool, idle_exit: bool) -> int:
    check_range("port", port, 1, 65535)
    url = f"http://127.0.0.1:{port}/"
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), App)
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            if matching_listener(port, out):
                if open_browser:
                    webbrowser.open(url)
                return 0
            raise BuildError(f"Port {port} is in use by another app or a Hutchfinity instance with "
                             "different settings. Stop that listener or choose another --port.") from None
        raise BuildError(f"Could not start the app on port {port}: {error.strerror or str(error)}") from None
    App.out_dir = out
    print(f"Hutchfinity {VERSION} is at {url} (Ctrl-C to stop). Files go to {out}")
    if open_browser:
        webbrowser.open(url)
    server.timeout = 30
    try:
        while not idle_exit or App.active_builds or time.time() - App.last_used < IDLE_EXIT_SECONDS:
            server.handle_request()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
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


def add_print_arguments(parser: argparse.ArgumentParser, *, casing=False) -> None:
    parser.add_argument("--process-profile", type=Path, help="exported Orca process JSON; import only supported object overrides, without resolving inherits")
    parser.add_argument("--plain-3mf", action="store_true", help="geometry only; apply no print overrides")
    if casing:
        parser.add_argument("--avoid-crossings", action="store_true", help="use TPMS-D for casing sparse infill; keep density from the selected or active profile")


def cup_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="hutchfinity.py cup", description="Build one cup.")
    parser.add_argument("size", nargs=3, type=int, help="cells wide, cells deep (1 to 40), height in 3.5 mm units (2 to 40)")
    parser.add_argument("--across", type=int, default=1, help="compartments across the width (1 to 10, default 1)")
    parser.add_argument("--along", type=int, default=1, help="compartments along the depth (1 to 10, default 1)")
    parser.add_argument("--wall", type=float, help="wall, mm (0.6 to 3; default: chosen from the height)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    add_print_arguments(parser)
    args = parser.parse_args(argv)
    try:
        printing = load_print_options(args.process_profile, geometry_only=args.plain_3mf)
        print(json.dumps(build_cup(*args.size, args.out, args.across, args.along, args.wall, printing), indent=2))
    except (BuildError, PrintSettingsError) as error:
        print(f"Could not build: {error}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    if sys.argv[1:2] == ["cup"]:
        return cup_main(sys.argv[2:])
    argv = sys.argv[1:]
    module_command = argv[:1] == ["module"]
    if module_command:
        argv = argv[1:]
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("size", nargs="*", type=int, help="cells wide, cells deep, tallest bin")
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--floor", choices=list(FLOORS), default="integral-grid", help="grid built into the tub, or printed separately")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    add_print_arguments(parser, casing=True)
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
    args = parser.parse_args(argv)
    try:
        if args.install_shortcut:
            print(install_shortcut(Path.home() / "Desktop"))
            return 0
        if not args.size:
            design_changed = any(getattr(args, option[0]) != option[2] for option in DESIGN_OPTIONS)
            if (module_command or args.process_profile is not None or args.avoid_crossings
                    or args.plain_3mf or args.floor != "integral-grid" or design_changed):
                parser.error("give three sizes with module, design or print options; "
                             "to use the app, start it without those options and choose them in the form")
            if not args.no_update:
                self_update()
            return serve(args.out, args.port, not args.no_browser, args.idle_exit)
        if len(args.size) != 3:
            parser.error("give three sizes: cells wide, cells deep, tallest bin")
        design = {
            option[0]: getattr(args, option[0]) for option in DESIGN_OPTIONS if getattr(args, option[0]) != option[2]
        }
        printing = load_print_options(args.process_profile, avoid_crossings=args.avoid_crossings, geometry_only=args.plain_3mf)
        result = build_module(*args.size, args.floor, args.out, design, printing)
        print(json.dumps(result, indent=2))
    except (BuildError, PrintSettingsError) as error:
        print(f"Could not build: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
