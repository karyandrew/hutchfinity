---
version: 0.10.1
sensitivity: public
---

# Hutchfinity system spec

This technical spec translates `docs/chest-prd.md` into module contracts for the authored Hutchfinity SCAD parts. The chest PRD remains the product authority; this page defines the first casing interface so `casing.scad` can exist without silently deciding the still-open magnet and peg recipes.

## Casing contract

`scad/casing.scad` emits one drawer-slot casing in print orientation: the casing top is on the build plate and the side/back walls rise upward. The physical part has a top, left side, right side, and back; it has no front and no bottom.

The casing module is tub-agnostic. It accepts direct slot dimensions rather than importing `tub.scad` or deriving from tub cell count, pitch, or wall thickness. Assembly-level files such as `scad/hutchfinity-assembly.scad` choose casing slot dimensions that match a tub or preview target.

The target enclosed slot range is 200-450mm wide, 200-450mm deep, and 25-450mm tall. The current representative casing is oriented width-wise for the regular tub: the casing opening width spans the tub long axis, while drawer travel uses the tub short axis. Stacked casings use the same outer XY footprint and prototype peg/socket geometry.

## Files

| File | Role |
|---|---|
| `scad/casing.scad` | Standalone casing shell. No tub import, no footer mode. |
| `scad/peg.scad` | Prototype chamfered press-fit peg. |
| `scad/knob.scad` | Optional glue-on tub pull with a broad, thin flared base. |
| `scad/hutchfinity-assembly.scad` | Preview/assembly caller that can place casing, tub, knob, and pegs together. |
| `scad/casing-fit-test.scad` | Fit-test caller that maps current tub-source dimensions and named clearance candidates to a casing slot. |
| `scad/testbed/peg_socket_fit_testbed.scad` | Cheap coupon for provisional peg/socket clearance and chamfer checks. |
| `scad/testbed/peg_stack_interface_testbed.scad` | Cheap side-wall edge-condition coupon for the two-ended top-slab socket to wall-foot receiver stack interface. |
| `scad/testbed/casing_mouth_fit_gauge.scad` | Shallow front-mouth gauge for checking tub entry and top clearance before printing a full casing. |
| `scad/testbed/casing-fit-trial-01.md` | Planned physical validation log for the #20 casing fit and peg/socket coupon print. |

No shared `hutchfinity-dimensions.scad` file is part of this pass.

## Coordinate convention

| Axis | Meaning |
|---|---|
| X | Left/right across the drawer opening. |
| Y | Front/back; `Y=0` is the open front, the back wall is at maximum Y. |
| Z | Print Z. `Z=0` is the bed-facing top surface; walls rise in +Z from the top slab. |

This convention keeps the STL in the intended no-support print orientation. In installed use, the bed-facing slab is the upper riding surface and the open side opposite it is the missing bottom. Documentation should name whether a dimension is a print-coordinate value or an installed-use value when ambiguity matters.

## Dimensional formulas

Default values are intentionally conservative fit-test numbers, not final ergonomic values. The current representative XY target is a regular 12 x 16 tub oriented width-wise: `255.2 x 339.2mm` exterior XY from `docs/gridfinity-system-prd.md`, with casing `slot_width=339.2mm` and `slot_depth=255.2mm` before any explicit casing clearance. The current source tub height is 23u body height, so the default casing slot height is `23 * 3.5 + 3.74 = 84.24mm`, matching the rounded `84.2mm` total Z listed in `docs/gridfinity-system-prd.md`. The earlier PR #19 `73.74mm` value was a 20u representative casing target, not the current regular tub source height.

Thickness requirements are not finalized here. The printed part will not behave like a solid-wall analytical beam: slicer wall loops, sparse infill density/pattern, material, nozzle, and layer height all matter. This spec therefore keeps thicknesses as named prototype parameters rather than deriving them from a structural formula.

`scad/casing-fit-test.scad` is the physical-fit caller for issue #20. It separates three concepts that should not be conflated:

| Concept | Where it belongs | Notes |
|---|---|---|
| Tub source dimensions | `docs/gridfinity-system-prd.md` and tub build scripts | Current regular tub source is 23u total height, not the PR #19 20u casing target. |
| Casing slot clearance | `scad/casing-fit-test.scad` / assembly mapping | Geometry clearance around the printed tub; side, back, and top clearances are named separately. |
| Slicer contour compensation | Slicer/process profile and trial notes | Andrew's `0.6` contour-compensation observation is process evidence, not a SCAD dimension by itself. |


| Term | Formula / default | Notes |
|---|---|---|
| `slot_width` | `339.2mm` | Direct enclosed slot width; width-wise regular tub orientation uses the tub long axis across the opening. |
| `slot_depth` | `255.2mm` | Direct enclosed slot depth; width-wise regular tub orientation uses the tub short axis for drawer travel. |
| `slot_height` | `84.24mm` | Direct enclosed slot height for the current 23u source tub plus minimum lip estimate. |
| `outer_x` | `slot_width + 2 * side_thickness` | Includes left and right walls. |
| `outer_y` | `slot_depth + back_thickness` | Includes back wall; no front wall. |
| `print_z` | `top_thickness + slot_height` | Top slab plus wall height in print orientation. |
| `peg_axis_intervals` | `max(1, ceil((span - 2 * socket_inset) / peg_spacing))` | Derived; not an argument. |
| `peg_count` | length of perimeter socket positions | Derived from one `peg_spacing`; not an argument. |

There is no `bottom_thickness` term. The casing has no floor/bottom plate.

## Parameters

| Parameter | Default | Status |
|---|---:|---|
| `slot_width`, `slot_depth`, `slot_height` | `339.2, 255.2, 84.24` | Representative width-wise regular-tub source dimensions before explicit fit clearance. |
| `side_thickness` | `25` | Prototype side wall value, not a final scale formula. |
| `back_thickness` | `25` | Prototype back wall value, not a final scale formula. |
| `top_thickness` | `10` | Prototype ceiling/riding surface; bed-facing in print orientation. |
| `peg_spacing` | `190` | Single target spacing. Count is derived per side and positions divide evenly between corners. |
| `peg_diameter`, `peg_clearance` | `8, 0.45` | Prototype peg/socket fit values. |
| `peg_socket_depth`, `peg_chamfer` | `10, 2.5` | Prototype top-slab through-sockets and wall-foot sockets with generous chamfers at both ends. |
| `enable_peg_holes` | `true` | Cuts prototype top-slab sockets and matching wall-foot sockets by default. |
| `show_debug_markers` | `false` | Optional reference-point markers only when peg holes are disabled. |

Not casing arguments: tub cell counts, pitch values, tub wall thickness, tub-to-slot clearance, bottom thickness, footer/base controls, `peg_count`, `peg_edge_margin`, and magnet placement parameters. Those belong to tub generation, assembly mapping, a future footer/base design, or a future validated interface.

## Provisional interfaces

Magnet dimensions are not final in this spec. `wiki/magnet-press-fit.md`, hutchfinity#7, and PR #13 remain the live sources for magnet press-fit validation.

The casing module cuts prototype peg sockets derived from `peg_spacing`. Socket centers are restricted to side-wall and back-wall footprints; the open front span has no sockets because there is no front wall to receive a peg from the casing above. Each casing has top-slab sockets for the casing above and matching wall-foot sockets for the casing below. This avoids separate X/Y peg-count knobs, avoids a public edge-margin parameter, and keeps peg locations tied to actual mating material.

Peg sockets and pegs both use generous 2.5mm chamfers at their ends. In the casing, top and wall-foot sockets are chamfered at the opening and at the deepest end of the cut. In `peg.scad`, each dowel end tapers down for easier insertion. The stack interface remains prototype geometry until the coupon and an actual casing pair are physically tested.

`scad/testbed/peg_socket_fit_testbed.scad` renders a small clearance sweep using the same socket cutter and peg module: `0.30`, `0.45`, and `0.60mm` socket clearance around the 8mm prototype peg. The raised index marks count from left to right. This coupon is a physical validation aid, not a locked press-fit recipe.

Magnet wells are deferred from `casing.scad` until the casing-side printability and press-fit recipe are validated. When added, chamfer can stay fixed inside the recipe rather than becoming a public casing argument.

Footer behavior is outside `casing.scad`. A footer, tabletop, or future base/riser belongs in assembly-level design, not in the casing module argument surface.

## Render checks

Minimum first-pass check:

```bash
openscad -o preview/casing-representative.stl scad/casing.scad
```

Fit-test caller check:

```bash
openscad -o preview/casing-fit-regular-23u.stl scad/casing-fit-test.scad
openscad -o /tmp/hutchfinity-fit-pr19-20u-check.stl -D FIT_TUB_HEIGHT_U=20 scad/casing-fit-test.scad
```

Peg/socket coupon check:

```bash
openscad -o /tmp/hutchfinity-peg-socket-fit-testbed.stl scad/testbed/peg_socket_fit_testbed.scad
openscad -o /tmp/hutchfinity-peg-stack-interface-testbed.stl scad/testbed/peg_stack_interface_testbed.scad
```

Assembly caller check:

```bash
openscad -o /tmp/hutchfinity-assembly-check.stl scad/hutchfinity-assembly.scad
openscad -o /tmp/hutchfinity-peg-check.stl scad/peg.scad
openscad -o /tmp/hutchfinity-knob-check.stl scad/knob.scad
```

Physical validation packet:

```bash
openscad -o /tmp/hutchfinity-casing-mouth-fit-gauge.stl scad/testbed/casing_mouth_fit_gauge.scad
openscad -o /tmp/hutchfinity-casing-fit-regular-23u.stl scad/casing-fit-test.scad
openscad -o /tmp/hutchfinity-peg-socket-fit-testbed.stl scad/testbed/peg_socket_fit_testbed.scad
openscad -o /tmp/hutchfinity-peg-stack-interface-testbed.stl scad/testbed/peg_stack_interface_testbed.scad
```

Record the physical result in `scad/testbed/casing-fit-trial-01.md`. Casing and mouth-gauge artifacts print inverted; flip them into installed orientation for fit testing, with the slab above the tub and the walls down. The mouth gauge is a cheaper entry/ceiling check only; it does not replace full-depth casing slide validation. Keep the default trial at zero explicit casing clearance first; if it binds, adjust the named side/back/top clearances in the fit-test caller rather than changing tub source geometry.

For visual review, render a PNG from the same file when OpenSCAD is available. If OpenSCAD is unavailable, static syntax and parameter review are still required, and the missing renderer is reported in the PR.

## Acceptance criteria

- Casing dimensions are direct slot parameters, not coupled to tub internals.
- The casing has no front and no bottom.
- Same XY footprint casings reserve a prototype two-ended peg/socket interface for vertical stacking.
- Tub body geometry is not rewritten to create the slide path.
- Optional knob geometry has a broad, thin glue base for tub attachment.
- Magnet geometry stays explicitly provisional until physical validation closes the dependency.
