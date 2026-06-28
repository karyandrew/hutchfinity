---
version: 0.2.1
sensitivity: public
---

# Hutchfinity system spec

This technical spec translates `docs/chest-prd.md` into module contracts for the authored Hutchfinity SCAD parts. The chest PRD remains the product authority; this page defines the first casing interface so `casing.scad` can exist without silently deciding the still-open magnet and peg recipes.

## Casing contract

`scad/casing.scad` emits one drawer-slot casing in print orientation: the casing top is on the build plate and the side/back walls rise upward. The physical part has a top, left side, right side, and back; it has no front and no bottom.

A casing is parameterized from the matching tub cell count and pitch. The tub slides through the open front and rides on the top surface of the casing below, a footer, or a tabletop. Stacked casings use the same XY footprint and later receive peg/socket geometry once the press-fit recipe is validated.

## Coordinate convention

| Axis | Meaning |
|---|---|
| X | Left/right across the drawer opening. |
| Y | Front/back; `Y=0` is the open front, the back wall is at maximum Y. |
| Z | Print Z. `Z=0` is the bed-facing top surface; walls rise in +Z from the top slab. |

This convention keeps the STL in the intended no-support print orientation. In installed use, the bed-facing slab is the upper riding surface and the open side opposite it is the missing bottom. Documentation should name whether a dimension is a print-coordinate value or an installed-use value when ambiguity matters.

## Dimensional formulas

Default values are intentionally conservative first-pass numbers, not final ergonomic values.

| Term | Formula / default | Notes |
|---|---|---|
| `pitch_xy` | 21mm | Half-pitch Gridfinity default. |
| `pitch_z` | 3.5mm | Half-pitch Z unit. |
| `tub_outer_x` | `cells_x * pitch_xy + 2 * tub_wall_thickness` | Matches current tub architecture where walls live outside the cell grid. |
| `tub_outer_y` | `cells_y * pitch_xy + 2 * tub_wall_thickness` | Same as X. |
| `inner_x` | `tub_outer_x + 2 * clearance_slide` | Sliding clearance on both side walls. |
| `inner_y` | `tub_outer_y + clearance_slide` | Rear clearance only; the front is open. |
| `outer_x` | `inner_x + 2 * side_wall_thickness` | Includes left and right walls. |
| `outer_y` | `inner_y + back_wall_thickness` | Includes back wall; no front wall. |
| `slot_height` | `cells_z * pitch_z` | Positive for drawer slots; `0` for a flat footer/tabletop riding plate. |
| `print_z` | `top_thickness + max(slot_height, 0)` | Top slab plus wall height in print orientation. |
| `bottom_thickness` | `0` | The casing has no floor/bottom plate. |

## Parameters

| Parameter | Default | Status |
|---|---:|---|
| `cells_x`, `cells_y`, `cells_z` | `6, 8, 24` | First-pass representative casing. |
| `pitch_xy`, `pitch_z` | `21, 3.5` | Stable defaults, user-overridable. |
| `tub_wall_thickness` | `1.6` | Current tub architecture value. |
| `clearance_slide` | `0.6` | Prototype value; tune after drawer-fit print. |
| `side_wall_thickness` | `2.4` | Prototype side wall value; should print as clean PETG perimeters. |
| `back_wall_thickness` | `2.4` | Prototype back wall value; matched to side walls for v0.1. |
| `top_thickness` | `2.4` | Prototype riding surface; bed-facing in print orientation. |
| `bottom_thickness` | `0` | Intentional: no floor/bottom plate. |
| `footer_threshold_xy` | `450` | Heuristic only; no automatic footer selection yet. |
| `detent_position` | `0.75` | Reserved for extended-warning magnet placement. |

## Provisional interfaces

Magnet and peg dimensions are not final in this spec. `wiki/magnet-press-fit.md`, hutchfinity#7, and PR #13 remain the live sources for press-fit validation. The casing module may expose named positions and disabled top-slab placeholders, but it must not lock final magnet bore, rib protrusion, socket diameter, peg profile, or bottom-interface peg bosses until the physical tests land. Bottom-interface peg sockets are deferred because the casing has no bottom plate; rendering them at interior XY positions would put them in air.

## Footer behavior

A footer is a casing configuration, not a fifth authored part. `cells_z = 0` emits the top/riding slab footprint without drawer-slot wall height. Positive `cells_z` values are risers; robot-vacuum clearance remains a named heuristic, not a fixed standard.

## Render checks

Minimum first-pass check:

```bash
openscad -o preview/casing-representative.stl scad/casing.scad
```

For visual review, render a PNG from the same file when OpenSCAD is available. If OpenSCAD is unavailable, static syntax and parameter review are still required, and the missing renderer is reported in the PR.

## Acceptance criteria

- Casing dimensions derive from tub cell count and pitch.
- The casing has no front and no bottom.
- Same XY footprint casings are vertically stackable by reserved peg interfaces.
- Tub body geometry is not rewritten to create the slide path.
- Magnet and peg geometry stays explicitly provisional until physical validation closes the dependency.
