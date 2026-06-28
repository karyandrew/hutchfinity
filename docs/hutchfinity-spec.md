---
version: 0.3.0
sensitivity: public
---

# Hutchfinity system spec

This technical spec translates `docs/chest-prd.md` into module contracts for the authored Hutchfinity SCAD parts. The chest PRD remains the product authority; this page defines the first casing interface so `casing.scad` can exist without silently deciding the still-open magnet and peg recipes.

## Casing contract

`scad/casing.scad` emits one drawer-slot casing in print orientation: the casing top is on the build plate and the side/back walls rise upward. The physical part has a top, left side, right side, and back; it has no front and no bottom.

The casing module is tub-agnostic. It accepts direct slot dimensions rather than importing `tub.scad` or deriving from tub cell count, pitch, or wall thickness. Assembly-level files such as `scad/hutchfinity-assembly.scad` choose casing slot dimensions that match a tub or preview target.

The target enclosed slot range is 200-450mm wide, 200-450mm deep, and 25-450mm tall. Stacked casings use the same outer XY footprint and later receive peg/socket geometry once the press-fit recipe is validated.

## Files

| File | Role |
|---|---|
| `scad/casing.scad` | Standalone casing shell. No tub import, no footer mode. |
| `scad/hutchfinity-assembly.scad` | Preview/assembly caller that can place casing, tub, handle, and pegs together. |

No shared `hutchfinity-dimensions.scad` file is part of this pass.

## Coordinate convention

| Axis | Meaning |
|---|---|
| X | Left/right across the drawer opening. |
| Y | Front/back; `Y=0` is the open front, the back wall is at maximum Y. |
| Z | Print Z. `Z=0` is the bed-facing top surface; walls rise in +Z from the top slab. |

This convention keeps the STL in the intended no-support print orientation. In installed use, the bed-facing slab is the upper riding surface and the open side opposite it is the missing bottom. Documentation should name whether a dimension is a print-coordinate value or an installed-use value when ambiguity matters.

## Dimensional formulas

Default values are intentionally conservative first-pass numbers, not final ergonomic values.

Thickness requirements are not finalized here. The printed part will not behave like a solid-wall analytical beam: slicer wall loops, sparse infill density/pattern, material, nozzle, and layer height all matter. This spec therefore keeps thicknesses as named prototype parameters rather than deriving them from a structural formula.

| Term | Formula / default | Notes |
|---|---|---|
| `slot_width` | `210mm` | Direct enclosed slot width; assembly may derive it from a tub, but casing does not. |
| `slot_depth` | `210mm` | Direct enclosed slot depth. |
| `slot_height` | `84mm` | Direct enclosed slot height. |
| `outer_x` | `slot_width + 2 * side_thickness` | Includes left and right walls. |
| `outer_y` | `slot_depth + back_thickness` | Includes back wall; no front wall. |
| `print_z` | `top_thickness + slot_height` | Top slab plus wall height in print orientation. |
| `peg_axis_intervals` | `max(1, ceil(span / peg_spacing))` | Derived; not an argument. |
| `peg_count` | length of perimeter reference positions | Derived from one `peg_spacing`; not an argument. |

There is no `bottom_thickness` term. The casing has no floor/bottom plate.

## Parameters

| Parameter | Default | Status |
|---|---:|---|
| `slot_width`, `slot_depth`, `slot_height` | `210, 210, 84` | First-pass representative enclosed slot dimensions. |
| `side_thickness` | `2.4` | Prototype side wall value, not a final scale formula. |
| `back_thickness` | `2.4` | Prototype back wall value, not a final scale formula. |
| `top_thickness` | `2.4` | Prototype riding surface; bed-facing in print orientation. |
| `peg_spacing` | `190` | Single target spacing. Count is derived per side and positions divide evenly between corners. |
| `show_debug_markers` | `false` | Optional reference-point markers only; not socket geometry. |

Not casing arguments: tub cell counts, pitch values, tub wall thickness, tub-to-slot clearance, bottom thickness, footer/base controls, `peg_count`, `peg_edge_margin`, and magnet placement parameters. Those belong to tub generation, assembly mapping, a future footer/base design, or a future validated interface.

## Provisional interfaces

Magnet and peg dimensions are not final in this spec. `wiki/magnet-press-fit.md`, hutchfinity#7, and PR #13 remain the live sources for press-fit validation.

The casing module currently exposes only peg reference positions derived from `peg_spacing`; it does not cut peg sockets. The reference pattern indexes the perimeter corners, derives interval counts from the single spacing value, and divides each side evenly. This avoids separate X/Y peg-count knobs and avoids a free-floating edge-margin parameter.

Magnet wells are also deferred from `casing.scad` until the casing-side printability and press-fit recipe are validated. When added, chamfer can stay fixed inside the recipe rather than becoming a public casing argument.

Footer behavior is outside `casing.scad`. A footer, tabletop, or future base/riser belongs in assembly-level design, not in the casing module argument surface.

## Render checks

Minimum first-pass check:

```bash
openscad -o preview/casing-representative.stl scad/casing.scad
```

Assembly caller check:

```bash
openscad -o /tmp/hutchfinity-assembly-check.stl scad/hutchfinity-assembly.scad
```

For visual review, render a PNG from the same file when OpenSCAD is available. If OpenSCAD is unavailable, static syntax and parameter review are still required, and the missing renderer is reported in the PR.

## Acceptance criteria

- Casing dimensions are direct slot parameters, not coupled to tub internals.
- The casing has no front and no bottom.
- Same XY footprint casings are vertically stackable by reserved peg interfaces.
- Tub body geometry is not rewritten to create the slide path.
- Magnet and peg geometry stays explicitly provisional until physical validation closes the dependency.
