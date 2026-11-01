#!/usr/bin/env python3
"""Hutchfinity Regular low-Z floor-mode prototypes.

Revision 05 corrects the removable-grid edge topology without discarding the
useful sloped fit geometry:

1. Every Gridfinity pocket remains open completely through to the tub floor.
2. The insert outer envelope again follows the tub cavity as it widens above
   the lower stacking foot.  The resulting 45-degree outward growth is an FDM
   overhang, not a bridge.
3. Only the unsupported perimeter spans are removed: each edge pocket is
   extended laterally through the insert boundary at every Z.  The grid-rail
   ends between those openings retain their sloped overhanging buttresses.
4. The same shortest plain tub works with or without this removable insert.

The low-Z variants deliberately omit magnets. Magnet wells therefore do not
set a global floor thickness or consume interior height.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cadquery as cq
from cadquery import exporters

ROOT = Path(__file__).resolve().parents[1]
STL_DIR = ROOT / "stl"
VERIFY_DIR = ROOT / "verification"

# Regular Hutchfinity / half-pitch Gridfinity envelope.
PITCH = 21.0
CELLS_X = 12
CELLS_Y = 16
PITCH_Z = 3.5
MAX_BIN_H = 20
BIN_LIP_Z = 3.74
TUB_LIP_Z = 3.74
STACK_CLEARANCE = 2.01
WALL = 2.2
MIN_WALL = 0.4
OUTER_X = CELLS_X * PITCH + 2 * WALL       # 256.4
OUTER_Y = CELLS_Y * PITCH + 2 * WALL       # 340.4
INNER_X = CELLS_X * PITCH                  # 252
INNER_Y = CELLS_Y * PITCH                  # 336
OUTER_RADIUS = 4.0 + WALL                   # 6.2
INNER_RADIUS = 4.0
TOP_SLOPE = WALL - MIN_WALL                 # 1.8

# Existing lower self-stacking envelope.
STANDOFF = 1.75
Z_TOLERANCE = 0.25
XY_TOLERANCE = 0.5
FOOT_VERTICAL_Z = STANDOFF + Z_TOLERANCE    # 2.0
FOOT_TOP_Z = STANDOFF + Z_TOLERANCE + WALL + XY_TOLERANCE  # 4.7
FOOT_INSET = WALL + XY_TOLERANCE            # 2.7 per side
FOOT_X = OUTER_X - 2 * FOOT_INSET
FOOT_Y = OUTER_Y - 2 * FOOT_INSET
FOOT_RADIUS = OUTER_RADIUS - FOOT_INSET

# Floor modes.
PLAIN_FLOOR_TOP = 1.20
INTEGRAL_FLOOR_TOP = 1.30
INSERT_CLEARANCE = 1.00  # nominal clearance per side at the lowest tub-floor profile
GRID_STRUCTURE_Z = 5.00

# Pull flange / visual placement outline.
PULL_FLANGE_X = 90.0
PULL_FLANGE_Z = 34.0
PULL_FLANGE_RADIUS = 5.0
GUIDE_CLEARANCE = 0.50
GUIDE_RING = 1.40
GUIDE_PROJECTION = 0.60
GUIDE_OVERLAP = 0.08
GUIDE_INNER_X = PULL_FLANGE_X + 2 * GUIDE_CLEARANCE
GUIDE_INNER_Z = PULL_FLANGE_Z + 2 * GUIDE_CLEARANCE
GUIDE_OUTER_X = GUIDE_INNER_X + 2 * GUIDE_RING
GUIDE_OUTER_Z = GUIDE_INNER_Z + 2 * GUIDE_RING
GUIDE_INNER_RADIUS = PULL_FLANGE_RADIUS + GUIDE_CLEARANCE
GUIDE_OUTER_RADIUS = GUIDE_INNER_RADIUS + GUIDE_RING

EPS = 0.01


@dataclass(frozen=True)
class TubMode:
    key: str
    floor_top: float
    seat_datum: float
    integral_grid: bool
    description: str

    @property
    def body_top(self) -> float:
        # Preserve the established stack clearance above a 20h cup lip.
        return self.seat_datum + MAX_BIN_H * PITCH_Z + BIN_LIP_Z + STACK_CLEARANCE

    @property
    def total_z(self) -> float:
        return self.body_top + TUB_LIP_Z


PLAIN = TubMode(
    key="plain",
    floor_top=PLAIN_FLOOR_TOP,
    seat_datum=PLAIN_FLOOR_TOP,
    integral_grid=False,
    description="plain/no-grid tub",
)
INTEGRAL = TubMode(
    key="integral",
    floor_top=INTEGRAL_FLOOR_TOP,
    seat_datum=INTEGRAL_FLOOR_TOP,
    integral_grid=True,
    description="integral-grid tub",
)


def rounded_face(width: float, depth: float, radius: float) -> cq.Face:
    return cq.Sketch().rect(width, depth).vertices().fillet(radius)._faces.Faces()[0]


def rounded_wire(width: float, depth: float, radius: float, z: float = 0.0) -> cq.Wire:
    return rounded_face(width, depth, radius).outerWire().translate(cq.Vector(0, 0, z))


def rounded_solid(width: float, depth: float, radius: float, z0: float, z1: float) -> cq.Solid:
    if z1 <= z0:
        raise ValueError("z1 must exceed z0")
    return cq.Solid.extrudeLinear(
        rounded_wire(width, depth, radius, z0), [], cq.Vector(0, 0, z1 - z0)
    )


def loft_rounded_rect(profiles: Iterable[tuple[float, float, float, float]]) -> cq.Solid:
    wires = [rounded_wire(w, d, r, z) for z, w, d, r in profiles]
    return cq.Solid.makeLoft(wires, ruled=True)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def outer_profile_at(z: float) -> tuple[float, float, float]:
    if z <= FOOT_VERTICAL_Z:
        return FOOT_X, FOOT_Y, FOOT_RADIUS
    if z < FOOT_TOP_Z:
        t = (z - FOOT_VERTICAL_Z) / (FOOT_TOP_Z - FOOT_VERTICAL_Z)
        return (
            lerp(FOOT_X, OUTER_X, t),
            lerp(FOOT_Y, OUTER_Y, t),
            lerp(FOOT_RADIUS, OUTER_RADIUS, t),
        )
    return OUTER_X, OUTER_Y, OUTER_RADIUS


def inner_profile_at(z: float, wall: float = WALL) -> tuple[float, float, float]:
    w, d, r = outer_profile_at(z)
    return w - 2 * wall, d - 2 * wall, max(r - wall, 0.05)


def tub_envelope(total_z: float) -> cq.Shape:
    low = rounded_solid(FOOT_X, FOOT_Y, FOOT_RADIUS, 0.0, FOOT_VERTICAL_Z + EPS)
    taper = loft_rounded_rect(
        [
            (FOOT_VERTICAL_Z, FOOT_X, FOOT_Y, FOOT_RADIUS),
            (FOOT_TOP_Z, OUTER_X, OUTER_Y, OUTER_RADIUS),
        ]
    )
    upper = rounded_solid(OUTER_X, OUTER_Y, OUTER_RADIUS, FOOT_TOP_Z - EPS, total_z)
    return low.fuse(taper).fuse(upper).clean()


def cavity_profiles(floor_top: float, total_z: float) -> list[tuple[float, float, float, float]]:
    p: list[tuple[float, float, float, float]] = []
    w, d, r = inner_profile_at(floor_top)
    p.append((floor_top, w, d, r))

    if floor_top < FOOT_VERTICAL_Z - EPS:
        w, d, r = inner_profile_at(FOOT_VERTICAL_Z)
        p.append((FOOT_VERTICAL_Z, w, d, r))
    if floor_top < FOOT_TOP_Z - EPS:
        w, d, r = inner_profile_at(FOOT_TOP_Z)
        p.append((FOOT_TOP_Z, w, d, r))

    top_slope_start = total_z - TOP_SLOPE
    p.extend(
        [
            (top_slope_start, INNER_X, INNER_Y, INNER_RADIUS),
            (
                total_z,
                OUTER_X - 2 * MIN_WALL,
                OUTER_Y - 2 * MIN_WALL,
                OUTER_RADIUS - MIN_WALL,
            ),
            (
                total_z + 0.10,
                OUTER_X - 2 * MIN_WALL,
                OUTER_Y - 2 * MIN_WALL,
                OUTER_RADIUS - MIN_WALL,
            ),
        ]
    )
    return p


def mostly_flat_plain_tub(mode: TubMode) -> cq.Shape:
    env = tub_envelope(mode.total_z)
    cavity = loft_rounded_rect(cavity_profiles(mode.floor_top, mode.total_z))
    return env.cut(cavity).clean()


def gridfinity_cell_cavity() -> cq.Solid:
    """One 21 mm receiving recess, open at its top."""
    return loft_rounded_rect(
        [
            (0.00, 15.30, 15.30, 1.15),
            (0.35, 15.30, 15.30, 1.15),
            (1.05, 16.70, 16.70, 1.85),
            (2.85, 16.70, 16.70, 1.85),
            (5.00, 20.98, 20.98, 3.99),
            (5.03, 20.98, 20.98, 3.99),
        ]
    )


def all_cell_cutters(z0: float) -> cq.Compound:
    cell = gridfinity_cell_cavity()
    cutters: list[cq.Shape] = []
    for ix in range(CELLS_X):
        x = -INNER_X / 2 + PITCH / 2 + PITCH * ix
        for iy in range(CELLS_Y):
            y = -INNER_Y / 2 + PITCH / 2 + PITCH * iy
            cutters.append(cell.translate(cq.Vector(x, y, z0)))
    return cq.Compound.makeCompound(cutters)


def add_integral_grid(base: cq.Shape, mode: TubMode) -> cq.Shape:
    env = tub_envelope(mode.total_z)
    slab = rounded_solid(
        INNER_X + 0.02,
        INNER_Y + 0.02,
        INNER_RADIUS + 0.01,
        mode.floor_top - EPS,
        mode.floor_top + GRID_STRUCTURE_Z,
    )
    filled = base.fuse(slab).intersect(env).clean()
    return filled.cut(all_cell_cutters(mode.floor_top)).clean()


def handle_outline(total_z: float) -> cq.Shape:
    outer = rounded_face(GUIDE_OUTER_X, GUIDE_OUTER_Z, GUIDE_OUTER_RADIUS).outerWire()
    inner = rounded_face(GUIDE_INNER_X, GUIDE_INNER_Z, GUIDE_INNER_RADIUS).outerWire()
    center_z = total_z / 2
    outer = outer.rotate((0, 0, 0), (1, 0, 0), 90).translate(
        cq.Vector(0, -OUTER_Y / 2 + GUIDE_OVERLAP, center_z)
    )
    inner = inner.rotate((0, 0, 0), (1, 0, 0), 90).translate(
        cq.Vector(0, -OUTER_Y / 2 + GUIDE_OVERLAP, center_z)
    )
    return cq.Solid.extrudeLinear(
        outer,
        [inner],
        cq.Vector(0, -(GUIDE_PROJECTION + GUIDE_OVERLAP), 0),
    )


def build_tub(mode: TubMode) -> cq.Shape:
    body = mostly_flat_plain_tub(mode)
    if mode.integral_grid:
        body = add_integral_grid(body, mode)
    return body.fuse(handle_outline(mode.total_z)).clean()


CELL_PROFILE = [
    (0.00, 15.30),
    (0.35, 15.30),
    (1.05, 16.70),
    (2.85, 16.70),
    (5.00, 20.98),
]
EDGE_CHANNEL_OVERLAP = 0.12
EDGE_CHANNEL_MARGIN = 2.0


def insert_profile_at(local_z: float) -> tuple[float, float, float]:
    """Insert envelope at local print Z, following the installed tub cavity."""
    installed_z = PLAIN_FLOOR_TOP + local_z
    w, d, r = inner_profile_at(installed_z)
    return (
        w - 2 * INSERT_CLEARANCE,
        d - 2 * INSERT_CLEARANCE,
        max(r - INSERT_CLEARANCE, 0.05),
    )


def insert_outer_profiles() -> list[tuple[float, float, float, float]]:
    """Sloped nesting envelope in local print coordinates.

    Local Z=0 rests on the tub's 1.20 mm central floor.  The envelope stays
    narrow through the vertical portion of the lower stacking foot, then grows
    outward at 45 degrees until the full cavity width is reached.
    """
    events = [0.0]
    for installed in (FOOT_VERTICAL_Z, FOOT_TOP_Z):
        local = installed - PLAIN_FLOOR_TOP
        if EPS < local < GRID_STRUCTURE_Z - EPS:
            events.append(local)
    events.append(GRID_STRUCTURE_Z)

    profiles: list[tuple[float, float, float, float]] = []
    for local_z in events:
        w, d, r = insert_profile_at(local_z)
        profiles.append((local_z, w, d, r))
    return profiles


def rect_wire(width: float, depth: float, cx: float, cy: float, z: float) -> cq.Wire:
    return (
        cq.Sketch()
        .rect(width, depth)
        ._faces.Faces()[0]
        .outerWire()
        .translate(cq.Vector(cx, cy, z))
    )


def edge_opening_channel(axis: str, side: int, tangent_center: float) -> cq.Solid:
    """Loft one edge-pocket opening through the changing outer envelope.

    The channel uses the same Z-dependent aperture width as the standard cell
    cavity, overlaps that cavity slightly, and extends beyond the sloped insert
    boundary.  This removes only the unsupported outer span; the rail ends
    between neighboring channels keep their sloped overhang geometry.
    """
    if axis not in {"x", "y"} or side not in {-1, 1}:
        raise ValueError("invalid edge channel")

    edge_center = (INNER_X / 2 - PITCH / 2) if axis == "x" else (INNER_Y / 2 - PITCH / 2)
    edge_center *= side
    wires: list[cq.Wire] = []
    for z, aperture in CELL_PROFILE:
        w, d, _ = insert_profile_at(z)
        half_envelope = (w / 2) if axis == "x" else (d / 2)
        inner_edge = edge_center + side * (aperture / 2 - EDGE_CHANNEL_OVERLAP)
        outer_edge = side * (half_envelope + EDGE_CHANNEL_MARGIN)
        lo, hi = sorted((inner_edge, outer_edge))
        radial = hi - lo
        radial_center = (lo + hi) / 2

        if axis == "x":
            wires.append(rect_wire(radial, aperture, radial_center, tangent_center, z))
        else:
            wires.append(rect_wire(aperture, radial, tangent_center, radial_center, z))
    return cq.Solid.makeLoft(wires, ruled=True)


def all_edge_opening_channels() -> cq.Compound:
    channels: list[cq.Shape] = []
    for iy in range(CELLS_Y):
        y = -INNER_Y / 2 + PITCH / 2 + PITCH * iy
        channels.append(edge_opening_channel("x", -1, y))
        channels.append(edge_opening_channel("x", 1, y))
    for ix in range(CELLS_X):
        x = -INNER_X / 2 + PITCH / 2 + PITCH * ix
        channels.append(edge_opening_channel("y", -1, x))
        channels.append(edge_opening_channel("y", 1, x))
    return cq.Compound.makeCompound(channels)


def build_open_bottom_insert() -> cq.Shape:
    # Restore the cavity-following flare.  Its 2.7 mm radial growth over 2.7 mm
    # Z is a supported 45-degree overhang.
    blank = loft_rounded_rect(insert_outer_profiles())

    # Start standard pocket cutters below Z=0 so every square is genuinely open
    # through to the tub floor, then extend only the perimeter pockets through
    # the changing boundary to eliminate the former bridged outer wall.
    insert = blank.cut(all_cell_cutters(-EPS))
    insert = insert.cut(all_edge_opening_channels()).clean()

    # The two orthogonal channels at each rounded outer corner can leave one
    # tiny isolated lens outside the connected lattice.  It is not a useful
    # rail buttress and would print as loose debris, so retain only the connected
    # grid body.
    solids = insert.Solids()
    return max(solids, key=lambda solid: solid.Volume()).clean()


def export_shape(shape: cq.Shape, path: Path) -> None:
    exporters.export(shape, str(path), tolerance=0.06, angularTolerance=0.12)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(name: str, shape: cq.Shape, kind: str, **extra: object) -> dict:
    path = STL_DIR / name
    export_shape(shape, path)
    bb = shape.BoundingBox()
    return {
        "file": name,
        "kind": kind,
        "cad_valid": shape.isValid(),
        "cad_solids": len(shape.Solids()),
        "cad_faces": len(shape.Faces()),
        "cad_volume_mm3": shape.Volume(),
        "cad_bounds_mm": [bb.xlen, bb.ylen, bb.zlen],
        "sha256": sha256(path),
        **extra,
    }


def main() -> None:
    STL_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_DIR.mkdir(parents=True, exist_ok=True)

    plain = build_tub(PLAIN)
    integral = build_tub(INTEGRAL)
    insert = build_open_bottom_insert()

    for label, shape in [
        ("plain", plain),
        ("integral", integral),
        ("insert", insert),
    ]:
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise RuntimeError(f"invalid {label} shape")

    # At every representative Z, an edge-pocket center must remain open all
    # the way to the exterior while the grid rail midway between neighboring
    # pockets must remain present.  That is the exact distinction between a
    # removed bridging wall and the retained sloped overhang buttresses.
    edge_support_samples = []
    edge_cell_y = -INNER_Y / 2 + PITCH / 2
    between_cells_y = edge_cell_y + PITCH / 2
    edge_cell_x = -INNER_X / 2 + PITCH / 2
    between_cells_x = edge_cell_x + PITCH / 2
    for z in (0.05, 0.79, 1.00, 2.00, 3.49, 4.90):
        w, d, _ = insert_profile_at(z)
        hx, hy = w / 2, d / 2
        sample = {
            "z_mm": z,
            "profile_xy_mm": [w, d],
            "right_edge_pocket_open": not insert.isInside((hx - 0.25, edge_cell_y, z)),
            "right_edge_rail_present": insert.isInside((hx - 0.25, between_cells_y, z)),
            "top_edge_pocket_open": not insert.isInside((edge_cell_x, hy - 0.25, z)),
            "top_edge_rail_present": insert.isInside((between_cells_x, hy - 0.25, z)),
        }
        if not all(
            sample[k]
            for k in (
                "right_edge_pocket_open",
                "right_edge_rail_present",
                "top_edge_pocket_open",
                "top_edge_rail_present",
            )
        ):
            raise RuntimeError(f"edge topology check failed: {sample}")
        edge_support_samples.append(sample)

    outputs = [
        record(
            "01-regular-integral-grid-low-z-no-magnets.stl",
            integral,
            "tub",
            mode=INTEGRAL.key,
            floor_top_z_mm=INTEGRAL.floor_top,
            bin_seat_z_mm=INTEGRAL.seat_datum,
            body_top_z_mm=INTEGRAL.body_top,
            total_z_mm=INTEGRAL.total_z,
            grid_top_z_mm=INTEGRAL.floor_top + GRID_STRUCTURE_Z,
        ),
        record(
            "02-regular-plain-low-z-no-magnets.stl",
            plain,
            "tub",
            mode=PLAIN.key,
            floor_top_z_mm=PLAIN.floor_top,
            bin_seat_z_mm=PLAIN.seat_datum,
            body_top_z_mm=PLAIN.body_top,
            total_z_mm=PLAIN.total_z,
            grid_top_z_mm=None,
            accepts_open_bottom_insert=True,
        ),
        record(
            "03-regular-open-bottom-sloped-edge-grid-insert.stl",
            insert,
            "insert",
            cells=[CELLS_X, CELLS_Y],
            backing_floor_thickness_mm=0.0,
            nominal_clearance_each_side_at_floor_mm=INSERT_CLEARANCE,
            installed_bottom_z_mm=PLAIN_FLOOR_TOP,
            installed_bin_seat_z_mm=PLAIN_FLOOR_TOP,
            installed_grid_top_z_mm=PLAIN_FLOOR_TOP + GRID_STRUCTURE_Z,
            perimeter_wall=False,
            edge_pockets_open_to_tub_wall=True,
            sloped_edge_buttresses=True,
            maximum_edge_overhang_degrees=45.0,
        ),
    ]

    old_floor = FOOT_TOP_Z
    data = {
        "artifact": "Hutchfinity Regular low-Z floor modes 05",
        "grid": {
            "cells_xy": [CELLS_X, CELLS_Y],
            "pitch_xy_mm": PITCH,
            "pitch_z_mm": PITCH_Z,
            "max_bin_height_u": MAX_BIN_H,
        },
        "stack_fit": {
            "target_clearance_above_20h_bin_lip_mm": STACK_CLEARANCE,
            "formula_body_top_mm": "bin_seat + 20*3.5 + 3.74 + 2.01",
            "formula_total_z_mm": "body_top + 3.74 tub lip",
            "old_floor_or_seat_datum_mm": old_floor,
            "old_total_z_mm": 84.24,
        },
        "shared": {
            "outer_xy_mm": [OUTER_X, OUTER_Y],
            "wall_mm": WALL,
            "magnet_wells": False,
            "lower_stacking_profile": {
                "vertical_to_z_mm": FOOT_VERTICAL_Z,
                "taper_to_full_envelope_z_mm": FOOT_TOP_Z,
                "bottom_inset_each_side_mm": FOOT_INSET,
            },
            "handle_outline": {
                "pull_flange_mm": [PULL_FLANGE_X, PULL_FLANGE_Z],
                "clearance_each_side_mm": GUIDE_CLEARANCE,
                "line_width_mm": GUIDE_RING,
                "projection_mm": GUIDE_PROJECTION,
            },
        },
        "modes": {
            PLAIN.key: {
                "floor_top_z_mm": PLAIN.floor_top,
                "bin_seat_z_mm": PLAIN.seat_datum,
                "body_top_z_mm": PLAIN.body_top,
                "total_z_mm": PLAIN.total_z,
                "z_reduction_vs_84p24_mm": 84.24 - PLAIN.total_z,
            },
            INTEGRAL.key: {
                "floor_top_z_mm": INTEGRAL.floor_top,
                "bin_seat_z_mm": INTEGRAL.seat_datum,
                "grid_top_z_mm": INTEGRAL.floor_top + GRID_STRUCTURE_Z,
                "body_top_z_mm": INTEGRAL.body_top,
                "total_z_mm": INTEGRAL.total_z,
                "z_reduction_vs_84p24_mm": 84.24 - INTEGRAL.total_z,
            },
            "removable_open_bottom_sloped_edge": {
                "uses_tub_mode": PLAIN.key,
                "tub_floor_top_z_mm": PLAIN.floor_top,
                "insert_backing_floor_mm": 0.0,
                "bin_seat_z_mm": PLAIN.seat_datum,
                "grid_top_z_mm": PLAIN.seat_datum + GRID_STRUCTURE_Z,
                "body_top_z_mm": PLAIN.body_top,
                "total_z_mm": PLAIN.total_z,
                "z_reduction_vs_84p24_mm": 84.24 - PLAIN.total_z,
                "insert_clearance_each_side_at_floor_mm": INSERT_CLEARANCE,
                "perimeter_wall": False,
                "pockets_open_through": True,
                "outer_envelope_follows_tub_cavity": True,
                "sloped_edge_buttresses": True,
                "maximum_edge_overhang_degrees": 45.0,
            },
        },
        "removable_insert_edge_topology": {
            "bottom_profile_xy_mm": list(insert_profile_at(0.0)[:2]),
            "top_profile_xy_mm": list(insert_profile_at(GRID_STRUCTURE_Z)[:2]),
            "radial_outward_growth_each_side_mm": (
                insert_profile_at(GRID_STRUCTURE_Z)[0] - insert_profile_at(0.0)[0]
            ) / 2,
            "growth_start_z_mm": FOOT_VERTICAL_Z - PLAIN_FLOOR_TOP,
            "growth_end_z_mm": FOOT_TOP_Z - PLAIN_FLOOR_TOP,
            "maximum_overhang_degrees": 45.0,
            "edge_channels_follow_cell_aperture": True,
            "support_samples": edge_support_samples,
        },
        "outputs": outputs,
    }
    (VERIFY_DIR / "build.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
