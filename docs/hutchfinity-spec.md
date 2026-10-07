---
version: 0.19.0
sensitivity: public
---

# Hutchfinity system spec

This technical spec translates `docs/chest-prd.md` into module contracts for the authored Hutchfinity SCAD parts. The chest PRD remains the product authority; this page defines the casing interface, the shared product magnet recipe, and the still-provisional peg interface.

## Casing contract

`scad/casing.scad` emits one drawer-slot casing in print orientation: the casing top is on the build plate and the side/back walls rise upward. The physical part has a top, left side, right side, and back; it has no front and no bottom. The current prototype cuts flat-wall stack sockets and canonical-recipe casing-side magnet wells by default.

The casing module is tub-agnostic. It accepts direct slot dimensions rather than importing `tub.scad` or deriving from tub cell count, pitch, or wall thickness. Assembly-level files such as `scad/hutchfinity-assembly.scad` choose casing slot dimensions that match a tub or preview target.

The target enclosed slot range is 200-450mm wide, 200-450mm deep, and 25-450mm tall. The current representative casing uses width for left/right across the drawer opening and depth for front/back drawer travel. For the regular tub, casing width spans the tub width, while casing depth uses the shared 16-cell front-to-back tub dimension. Stacked casings use the same flat casing footprint and prototype peg/socket geometry.

## Files

| File | Role |
|---|---|
| `scad/magnet_well.scad` | Single source of truth for the canonical 6 x 1.5mm product magnet recipe and its bore-minus-notch cutter. |
| `scad/casing.scad` | Standalone casing shell with flat-wall stack peg sockets and canonical product magnet wells. No tub import, no footer mode. |
| `scad/tub.scad` | Mini/regular/mega tub wrappers that import the current tub STLs and cut canonical product magnet wells. |
| `scad/peg.scad` | Prototype laid-down hex peg. |
| `scad/knob.scad` | Optional glue-on tub pull with a broad, thin flared base. |
| `scad/hutchfinity-assembly.scad` | Preview/assembly caller that can place casing, tub, knob, and pegs together. |
| `scad/casing-fit-test.scad` | Fit-test caller that maps current tub-source dimensions and named clearance candidates to a casing slot. |
| `scad/testbed/peg_socket_fit_testbed.scad` | Cheap coupon for provisional peg/socket clearance and chamfer checks. |
| `scad/testbed/hex_peg_set.scad` | Seven loose hex pegs for one representative casing stack interface. |
| `scad/testbed/peg_stack_interface_testbed.scad` | Rejected stack-land coupon retained only as a failed design reference. |
| `scad/testbed/casing_mouth_fit_gauge.scad` | Shallow front-mouth gauge for checking tub entry and top clearance before printing a full casing. |
| `scad/testbed/full_magnetic_drawer_inspection_set.scad` | Installed-coordinate inspection exports for aligned casing/tub magnet-interface and slot-fit checks. |
| `scad/testbed/magnet_well_shape_inspection.scad` | Printable face coupon generated from the canonical 6 x 1.5mm product magnet recipe. |
| `scad/testbed/mini_regular_mega_print_set.scad` | Selector source for the mini/regular/mega casing, magnetic tub, knob, and peg print packet. |
| `scad/testbed/build-mini-regular-mega-print-set.sh` | Builds the mini/regular/mega print packet and copies the matching committed grid baseplates. |
| `scad/testbed/casing-fit-trial-01.md` | Active physical-validation log; pre-canonical magnetic artifacts are marked superseded and must be regenerated before printing. |

No shared `hutchfinity-dimensions.scad` file is part of this pass.

## Coordinate convention

| Axis | Meaning |
|---|---|
| X | Left/right across the drawer opening. |
| Y | Front/back; `Y=0` is the open front, the back wall is at maximum Y. |
| Z | Print Z. `Z=0` is the bed-facing top surface; walls rise in +Z from the top slab. |

This convention keeps the STL in the intended no-support print orientation. In installed use, the bed-facing slab is the upper riding surface and the open side opposite it is the missing bottom. Documentation should name whether a dimension is a print-coordinate value or an installed-use value when ambiguity matters.

Socket face naming is deliberately explicit: installed-top sockets open on print `Z=0` through the top slab, while installed-bottom sockets open on the print `Z=print_z` wall-foot faces. The casing still has no bottom plate.

The PRD requires flat side and back exterior faces. External stack lands, pads, bosses, lugs, ribs, or other protrusions on the casing sides/back are rejected even if they would give peg sockets more material.

## Dimensional formulas

Default values are intentionally conservative fit-test numbers, not final ergonomic values. The current representative XY target is a thick-wall regular 12 x 16 tub with `256.4mm` left/right width and `340.4mm` front/back length from `docs/gridfinity-system-prd.md`. The fit-test caller maps that tub to a `258.4 x 340.9 x 85.24mm` slot: `1.0mm` side clearance per side, `0.5mm` closed-back clearance, and `1.0mm` top clearance. The current source tub height is 23u body height, so the tub exterior height is `23 * 3.5 + 3.74 = 84.24mm`, matching the rounded `84.2mm` total Z listed in `docs/gridfinity-system-prd.md`. The earlier PR #19 `73.74mm` value was a 20u representative casing target, not the current regular tub source height.

Thickness requirements are not finalized here. The printed part will not behave like a solid-wall analytical beam: slicer wall loops, sparse infill density/pattern, material, nozzle, and layer height all matter. This spec therefore keeps thicknesses as named prototype parameters rather than deriving them from a structural formula.

`scad/casing-fit-test.scad` is the physical-fit caller for issue #20. It separates three concepts that should not be conflated:

| Concept | Where it belongs | Notes |
|---|---|---|
| Tub source dimensions | `docs/gridfinity-system-prd.md` and tub build scripts | Current regular tub source is 23u total height with `2.2mm` walls, not the PR #19 20u casing target. |
| Casing slot clearance | `scad/casing-fit-test.scad` / assembly mapping | Geometry clearance around the printed tub; side, back, and top clearances are named separately. |
| Slicer contour compensation | Slicer/process profile and trial notes | The observed `+0.6mm` contour-compensation result was tub-print process evidence. It is not a casing wall-thickness formula. |


| Term | Formula / default | Notes |
|---|---|---|
| `slot_width` | `258.4mm` in the fit caller | Direct enclosed slot width: left/right across the drawer opening; tub width plus side clearance. |
| `slot_depth` | `340.9mm` in the fit caller | Direct enclosed slot depth: front/back drawer travel; shared tub front/back length plus closed-back clearance. |
| `slot_height` | `85.24mm` in the fit caller | Direct enclosed slot height for the current 23u source tub plus top clearance. |
| `outer_x` | `slot_width + 2 * side_thickness` | Includes left and right walls. |
| `outer_y` | `slot_depth + back_thickness` | Includes back wall; no front wall. |
| `print_z` | `top_thickness + slot_height` | Top slab plus wall height in print orientation. |
| `peg_axis_intervals_between` | `max(1, ceil((end - start) / peg_spacing))` | Derived; not an argument. |
| `peg_count` | length of perimeter socket positions | Derived from one `peg_spacing`; not an argument. |

There is no `bottom_thickness` term. The casing has no floor/bottom plate.

## Parameters

| Parameter | Default | Status |
|---|---:|---|
| `slot_width`, `slot_depth`, `slot_height` | `256.4, 340.4, 84.24` in `casing.scad`; `258.4, 340.9, 85.24` in the regular fit caller | Casing stays slot-dimension based; assembly/fit callers add tub clearance. |
| `side_thickness` | `25` | Prototype side wall value. |
| `back_thickness` | `25` | Prototype back wall value. |
| `top_thickness` | `10` | Prototype ceiling/riding surface; bed-facing in print orientation. |
| `peg_spacing` | `190` | Single target spacing. Count is derived per side and positions divide evenly between derived end insets. |
| `peg_diameter`, `peg_clearance` | `8, 0.45` | Prototype peg/socket fit values. |
| `peg_socket_depth`, `peg_chamfer` | `10, 2.5` | Prototype top-slab through-sockets and wall-foot sockets with generous chamfers at both ends. |
| `peg_socket_edge_land` | `4.0` | Minimum material land used when checking socket chamfer clearance. |
| `enable_peg_holes` | `true` | Cuts prototype top-slab sockets and matching wall-foot receiver sockets into the flat side/back wall footprints. |
| `enable_magnet_holes` | `true` | Cuts canonical 6 x 1.5mm product magnet wells into the installed top surface. |
| `casing_magnet_recipe` | `hutchfinity_magnet_recipe_6x1_5()` | Shared recipe from `scad/magnet_well.scad`; callers may substitute a different named recipe, not independent geometry scalars. |
| `casing_magnet_fore_aft_inset` | `8.0` | Magnet center inset from the front/back travel edges. |
| `casing_magnet_paramedian_offset` | `21.0` | Lateral offset for the optional paramedian columns around the centerline. |
| `extended_warning_travel_fraction` | `0.75` | Places the rear-pair warning detent wells at 75% drawer travel. |
| `show_debug_markers` | `false` | Optional reference-point markers only when peg holes are disabled. |

Not casing arguments: tub cell counts, pitch values, tub wall thickness, tub-to-slot clearance, bottom thickness, footer/base controls, `peg_count`, and `peg_edge_margin`. Those belong to tub generation, assembly mapping, a future footer/base design, or a future validated interface.

## Provisional interfaces

`scad/magnet_well.scad` is the sole authority for the canonical 6 x 1.5mm product recipe. The recipe is a `6.10mm` bore with `0.25mm` radial rib protrusion, yielding a `5.60mm` rib-tip diameter; eight ribs at 45-degree spacing; `0.80mm` rib width; `0.30mm` lead-in chamfer; and `2.30mm` well depth. Regular Tub trial 1 physically established the `0.25mm` crush fit. The `2.30mm` depth is the selected trial-2 correction and remains pending physical confirmation, so geometry is canonical while the depth validation state remains provisional.

The casing module cuts nine wells into the installed top surface, which is print `Z=0`: six closed-position wells in two front/back rows and three lateral columns, plus three rear-magnet wells at 75% drawer travel as an extended-warning detent. The lateral columns are median and paramedian, centered on the drawer midline with `21mm` offsets. Casing keeps its own position array and depth-envelope assertion but consumes the shared recipe.

`scad/tub.scad` wraps the current mini, regular, and mega tub STLs and cuts six bottom wells in two front/back rows and three median/paramedian lateral columns. Tub consumes the same shared recipe and asserts that its `2.30mm` well stays inside the `4.75mm` foot/cavity-floor envelope. These wrappers do not make `casing.scad` depend on the tub model. The Basket/Carrier probe and product inspection coupon also consume the same recipe; a different part is not a reason to redefine the same magnet hole.

The casing module cuts prototype peg sockets by default. The stack is casing-to-casing: the bottom wall feet of an upper casing sit on the top slab of the casing below, and pegs register that pair. The open front span has no sockets because there is no front wall-foot receiver in the casing above.

The external stack-land approach tested in the previous model is rejected by the flat side/back requirement. Current casing sockets are centered in the 25mm side/back wall footprints and spaced from the open front and rear edges by the derived socket end inset.

Peg sockets use generous 2.5mm chamfers at their openings and deepest ends. `scad/peg.scad` uses a laid-down hex profile with no crush ribs. The default printable peg is 8.45mm point-to-point, matching the current `8.0mm` nominal socket plus `0.45mm` prototype socket clearance. The module `hutchfinity_peg()` still models the installed vertical peg for assembly use; `hutchfinity_peg_print_layout()` rotates it onto a flat-friendly face for standalone/testbed printing. The casing stack interface remains provisional until tested on an actual casing pair.

`scad/testbed/peg_socket_fit_testbed.scad` renders a small clearance sweep using the same socket cutter and laid-down hex peg print module: `0.30`, `0.45`, and `0.60mm` socket clearance around the 8mm nominal socket diameter, tested against an 8.45mm point-to-point hex peg. The raised index marks count from left to right. This coupon is a physical validation aid, not a locked press-fit recipe.

Footer behavior is outside `casing.scad`. A footer, tabletop, or future base/riser belongs in assembly-level design, not in the casing module argument surface.

## Render checks

Minimum first-pass check:

```bash
openscad -o preview/casing-representative.stl scad/casing.scad
```

Generated review artifacts should live under `preview/<issue-or-head>/` or another explicit trial directory. Avoid suffixes such as `final`; they do not say what changed or what commit produced the file.

Fit-test caller check:

```bash
openscad -o preview/casing-fit-trial-01/casing-fit-regular-23u.stl scad/casing-fit-test.scad
openscad -o preview/casing-fit-trial-01/fit-pr19-20u-check.stl -D FIT_TUB_HEIGHT_U=20 scad/casing-fit-test.scad
```

Tub and coupon checks:

```bash
openscad -o preview/casing-fit-trial-01/peg-socket-fit-testbed.stl scad/testbed/peg_socket_fit_testbed.scad
openscad -o preview/casing-fit-trial-01/hex-peg-set-7.stl scad/testbed/hex_peg_set.scad
openscad -o preview/casing-fit-trial-01/tub-regular-magnetic.stl scad/tub.scad
openscad -o preview/casing-fit-trial-01/magnet-well-6x1.5-coupon.stl scad/testbed/magnet_well_shape_inspection.scad
```

Do not render or print `scad/testbed/peg_stack_interface_testbed.scad` for the current validation pass. It is retained only as a failed reference for the rejected external stack-land approach.

Assembly caller check:

```bash
openscad -o preview/casing-fit-trial-01/assembly-check.stl scad/hutchfinity-assembly.scad
openscad -o preview/casing-fit-trial-01/hex-peg-check.stl scad/peg.scad
openscad -o preview/casing-fit-trial-01/knob-check.stl scad/knob.scad
```

Physical validation packet:

```bash
openscad -o preview/casing-fit-trial-01/casing-mouth-fit-gauge.stl scad/testbed/casing_mouth_fit_gauge.scad
openscad -o preview/casing-fit-trial-01/casing-fit-regular-23u.stl scad/casing-fit-test.scad
openscad -o preview/casing-fit-trial-01/tub-regular-magnetic.stl scad/tub.scad
openscad -o preview/casing-fit-trial-01/peg-socket-fit-testbed.stl scad/testbed/peg_socket_fit_testbed.scad
openscad -o preview/casing-fit-trial-01/hex-peg-set-7.stl scad/testbed/hex_peg_set.scad
scad/testbed/build-mini-regular-mega-print-set.sh
```

Aligned inspection packet:

```bash
openscad -o preview/casing-fit-trial-01/aligned-inspection/casing-installed.stl -D INSPECTION_PART=1 scad/testbed/full_magnetic_drawer_inspection_set.scad
openscad -o preview/casing-fit-trial-01/aligned-inspection/tub-on-casing-top-closed.stl -D INSPECTION_PART=2 scad/testbed/full_magnetic_drawer_inspection_set.scad
openscad -o preview/casing-fit-trial-01/aligned-inspection/tub-in-slot-closed.stl -D INSPECTION_PART=4 scad/testbed/full_magnetic_drawer_inspection_set.scad
openscad -o preview/casing-fit-trial-01/aligned-inspection/pegs-installed.stl -D INSPECTION_PART=6 scad/testbed/full_magnetic_drawer_inspection_set.scad
```

Record the physical result in `scad/testbed/casing-fit-trial-01.md`. Casing and mouth-gauge artifacts print inverted; flip them into installed orientation for fit testing, with the slab above the tub and the walls down. The mouth gauge is a cheaper entry/ceiling check only; it does not replace full-depth casing slide validation. The current regular trial uses `1.0mm` side clearance per side, `0.5mm` at the closed back, and `1.0mm` above the tub.

For visual review, render a PNG from the same file when OpenSCAD is available. If OpenSCAD is unavailable, static syntax and parameter review are still required, and the missing renderer is reported in the PR.

## Acceptance criteria

- Casing dimensions are direct slot parameters, not coupled to tub internals.
- The casing has no front and no bottom.
- Same flat casing footprint casings cut a prototype two-ended peg/socket interface for vertical stacking.
- Tub body geometry is not rewritten to create the slide path.
- Optional knob geometry has a broad, thin glue base for tub attachment.
- Casing, mini/regular/mega Tub, Basket/Carrier, and the inspection coupon consume one canonical 6 x 1.5mm magnet recipe.
- The 0.25mm crush fit is physically established; the selected 2.30mm depth remains explicitly provisional until physical validation closes the dependency.
