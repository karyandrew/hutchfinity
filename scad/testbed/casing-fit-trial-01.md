---
sensitivity: public
type: log
date: 2026-07-04
testbed: casing-fit-test v0.4.2, casing.scad v0.10.6, tub.scad v0.2.2, magnet_well.scad v0.1.0, and peg_socket_fit_testbed v0.4.0
status: magnetic print set regenerated with 2.2mm tub walls, 1.0mm side clearance, and 1.0mm top clearance; peg/socket coupon printed 2026-07-08; casing/tub physical validation pending
---

# Casing fit trial 01 — magnetic print set pending physical validation

## Purpose

Validate the representative regular-tub casing interface from hutchfinity#20 without conflating tub-process compensation, casing slot clearance, or peg/socket press-fit.

2026-07-05 correction: the external stack-land casing is no longer the physical target. The PRD now requires flat casing side and back exterior faces, so external stack lands/pads/bosses are invalid even though they move peg holes away from thin edges. `casing.scad` v0.9.0 restores the flat casing and cuts stack sockets into the side/back wall footprints by default.

2026-07-08 correction: the observed `+0.6mm` slicer contour compensation improvement was from printed tubs, not casings. The regenerated casing set uses `25 / 25 / 10mm` side/back/top material, `1.0mm` side clearance per side, `1.0mm` top clearance, midline/paramedian casing magnet wells, and a `2.2mm` wall regular tub source via `tub.scad` v0.2.2.

2026-07-08 orientation correction: width means left/right across the drawer opening; depth/length means front-to-back drawer travel. The mini/regular/mega casing set varies in width with tub width (`6/12/18` cells), while all three share the `16`-cell front-to-back tub length.

2026-07-09 magnet alignment correction: tub bottom wells use the same median and paramedian X columns as casing wells, with front/back rows along Y. In the regular aligned assembly, both parts use X columns `133.2 / 154.2 / 175.2mm` and Y rows `8.0 / 332.4mm`.

## Print artifacts

| Artifact | Source | Export command |
|---|---|---|
| Mouth fit gauge | `scad/testbed/casing_mouth_fit_gauge.scad` | `openscad -o preview/casing-fit-trial-01/casing-mouth-fit-gauge.stl scad/testbed/casing_mouth_fit_gauge.scad` |
| Regular 23u casing fit target | `scad/casing-fit-test.scad` | `openscad -o preview/casing-fit-trial-01/casing-fit-regular-23u.stl scad/casing-fit-test.scad` |
| Regular magnetic tub | `scad/tub.scad` | `openscad -o preview/casing-fit-trial-01/tub-regular-magnetic.stl scad/tub.scad` |
| Aligned inspection set | `scad/testbed/full_magnetic_drawer_inspection_set.scad` | `openscad -o preview/casing-fit-trial-01/aligned-inspection/casing-installed.stl -D INSPECTION_PART=1 scad/testbed/full_magnetic_drawer_inspection_set.scad` |
| Magnet-well shape coupon | `scad/testbed/magnet_well_shape_inspection.scad` | `openscad -o preview/casing-fit-trial-01/magnet-well-shape-inspection.stl scad/testbed/magnet_well_shape_inspection.scad` |
| Peg/socket clearance coupon | `scad/testbed/peg_socket_fit_testbed.scad` | `openscad -o preview/casing-fit-trial-01/peg-socket-fit-testbed.stl scad/testbed/peg_socket_fit_testbed.scad` |
| Hex peg set | `scad/testbed/hex_peg_set.scad` | `openscad -o preview/casing-fit-trial-01/hex-peg-set-7.stl scad/testbed/hex_peg_set.scad` |
| Mini/regular/mega magnetic print set | `scad/testbed/mini_regular_mega_print_set.scad` | `scad/testbed/build-mini-regular-mega-print-set.sh` |


## Physical orientation

Print the casing and mouth-gauge artifacts in their OpenSCAD orientation: the top slab is on the build plate and the side/back walls rise upward. In that print view, installed-top sockets open on the bed-facing `Z=0` top slab and installed-bottom receiver sockets open on the wall-foot face at `Z=print_z`. For fit testing, flip the printed part into installed orientation: top slab above the tub, side walls down, open front at the drawer entrance. The upper casing's wall feet sit on the top of the casing below; there is no separate bottom drawer-support part. The tub should sit on a flat reference surface, tabletop, footer, or casing-below surrogate. Testing with the slab underneath the tub is invalid for drawer clearance.

## Design critique before print

| Artifact | What it actually proves | What it does not prove | CAD solid volume |
|---|---|---|---:|
| Mouth fit gauge | Tub can enter the representative width and immediate ceiling height without forced spreading or top rub. | Full-depth sliding friction, back clearance, long-wall bow, stack behavior, peg behavior, or magnetic retention. | Regenerated manifold STL |
| Regular 23u casing fit target | Full-depth slot behavior for the flat-side/back representative casing, including visible stack sockets and nine casing magnet wells. | Final clearance recipe unless tested against a real printed tub and recorded; validated peg/stack or magnet behavior. | Regenerated manifold STL |
| Regular magnetic tub | Bottom magnet-well printability and fit against the casing magnet pattern. | Casing slide behavior by itself; non-regular tub behavior. | Regenerated manifold STL |
| Peg/socket clearance coupon | First-pass insertion/retention feel across three socket clearances. | Actual casing pair behavior: top-slab socket plus wall-foot receiver, full slab stiffness, slicer infill, and stack loading. | Regenerated manifold STL |

The mouth gauge keeps full slot width and height because those are the dimensions being tested; it only reduces drawer-travel depth. Its CAD solid volume is about 21% of the full casing target before slicer infill. If it fails, change `SIDE_CLEARANCE` or `TOP_CLEARANCE` before spending plastic on the full casing.

2026-07-07 critique update: the ribbed peg profile was rejected because the ribs landed on the laid-down contact geometry and did not produce a clean printable/manifold peg. `scad/peg.scad` now uses a plain laid-down hex profile with an 8.45mm point-to-point diameter.

2026-07-05 rejected stack-land update: the side/back wall centerline model was treating the wall strip as the whole receiver, but the external `40 x 50mm` stack-land correction breaks the flat side/back requirement. Keep the lesson, not the geometry: peg sockets need more thoughtful placement without protruding from the casing sides/back.

2026-07-07 peg-print update: the printable peg artifact now lays a plain hex peg on one flat face. Assembly/test-fit semantics still use the peg as a vertical stack connector after printing.

## Pre-print render checks

| Artifact | Render status | Measured STL bounds | Expected bounds | Result |
|---|---|---:|---:|---|
| Mouth fit gauge | Manifold | `308.4 x 48.0 x 95.24mm` | `308.4 x 48.0 x 95.24mm` | Match |
| Regular 23u casing fit target | Manifold with stack sockets and casing magnet wells | `308.4 x 365.9 x 95.24mm` | `308.4 x 365.9 x 95.24mm` | Match |
| Regular magnetic tub | Manifold with bottom magnet wells | `256.395 x 340.397 x 84.24mm` | `256.4 x 340.4 x 84.24mm` | Match within imported STL tessellation |
| Peg/socket clearance coupon | Manifold | `122.0 x 46.225 x 10.6mm` | `122.0 x 46.225 x 10.6mm` including `0.6mm` index marks over `10mm` socket blocks | Match |
| Hex peg set | Manifold, 7 parts | `110.0 x 30.45 x 7.318mm` | `110.0 x 30.45 x 7.318mm` | Match |
| Magnet-well shape coupon | Manifold | `54.0 x 22.0 x 4.0mm` | Two face coupons showing tub and casing well profiles | Match |

### Mini/regular/mega print set

The committed generator is `scad/testbed/mini_regular_mega_print_set.scad`; the
committed packet builder is `scad/testbed/build-mini-regular-mega-print-set.sh`.
It exports the casing, magnetic tub, copied grid baseplate, glue-on knob, and
seven loose hex pegs to `preview/casing-fit-trial-01/mini-regular-mega-print-set/`.

| Artifact | Measured STL bounds |
|---|---:|
| `casing-mini-23u-magnetic.stl` | `182.400 x 365.900 x 95.240mm` |
| `casing-regular-23u-magnetic.stl` | `308.400 x 365.900 x 95.240mm` |
| `casing-mega-23u-magnetic.stl` | `434.400 x 365.900 x 95.240mm` |
| `tub-mini-magnetic.stl` | `130.395 x 340.397 x 84.240mm` |
| `tub-regular-magnetic.stl` | `256.395 x 340.397 x 84.240mm` |
| `tub-mega-magnetic.stl` | `382.395 x 340.397 x 84.240mm` |
| `grid-mini-baseplate.stl` | `126.000 x 336.000 x 4.000mm` |
| `grid-regular-baseplate.stl` | `252.000 x 336.000 x 4.000mm` |
| `grid-mega-baseplate.stl` | `378.000 x 336.000 x 4.000mm` |
| `knob-glue-on.stl` | `90.000 x 34.000 x 19.000mm` |
| `hex-peg-set-7.stl` | `110.000 x 30.450 x 7.318mm` |

The casing and tub front/back dimensions are intentionally constant across the
three sizes. Mini, regular, and mega vary left/right width only.

The peg/socket coupon Y envelope includes loose pegs placed in front of the coupon blocks. Coupon blocks occupy `Y=0..26mm`; laid-down peg centers are at `Y=-16mm`, so the full exported Y envelope is about `-20.225..26mm`. The laid-down pegs reduce the coupon's exported Z envelope from the old upright-peg `20mm` to `10.6mm`.

## Geometry under test

| Value | Trial setting |
|---|---:|
| Tub exterior XY target | `256.4 x 340.4mm` |
| Tub wall thickness | `2.2mm` |
| Casing slot, width x front/back depth x height | `258.4 x 340.9 x 85.24mm` |
| Side/back/top slot clearance | `1.0mm per side / 0.5mm closed back / 1.0mm top` |
| Side wall / back wall / top | `25 / 25 / 10mm` full casing; mouth gauge uses `8mm` back stop |
| Structural thickness change | No casing `+0.6mm`; tub source wall thickness is now `2.2mm` to absorb the printed-tub contour-compensation lesson in CAD. |
| Stack land width / length | Rejected; side/back exterior faces must remain flat |
| Mouth gauge slot depth | `40.0mm` |
| Casing magnet wells | Nine wells: three median/paramedian columns at closed front row, closed rear row, and 75% rear-magnet warning row; 8-rib bore-minus-notch profile, `6.40mm` bore, `6.10mm` rib-tip diameter, `1.60mm` deep, `0.30mm` chamfer |
| Tub magnet wells | Six bottom wells: two front/back rows by three median/paramedian columns; 8-rib bore-minus-notch profile, `5.40mm` bore, `5.25mm` rib-tip diameter, `1.10mm` deep, `0.30mm` chamfer |
| Magnet lateral columns | Median plus `+/-21.0mm` paramedian offsets for optional extra retention |
| Nominal tub-to-slot clearance | `1.0mm` per side, `0.5mm` closed back, `1.0mm` top in CAD |
| Aligned-STL side clearance | Tub is aligned to leave the full `1.0mm` per side clearance in the casing slot. |
| Aligned-STL back clearance | Tub front starts at the open front; the `0.5mm` depth clearance is at the closed back. |
| Aligned-STL top clearance | Tub top sits `1.0mm` below the installed casing ceiling. |
| Peg diameter | `8.45mm` point-to-point hex |
| Peg socket clearances | `0.30`, `0.45`, `0.60mm` around an `8.0mm` nominal socket diameter |
| Peg/socket chamfer | `2.5mm` |
| Peg socket placement | Enabled in `casing.scad` v0.10.4; sockets center in the flat side/back wall footprints |
| Peg profile | Plain laid-down hex peg; no crush ribs |
| Hex peg set count | `7`, matching the representative casing's socket count per stack interface |
| Casing socket faces | Installed-top sockets open on print `Z=0`; installed-bottom wall-foot receivers open on print `Z=print_z` |

## Setup to record

| Field | Value |
|---|---|
| Printer | TBD |
| Material | TBD |
| Nozzle | TBD |
| Layer height | TBD |
| Wall loops | TBD |
| Infill density/pattern | TBD |
| Slicer contour compensation | TBD |
| Elephant-foot compensation | TBD |

## Observations to record

| Check | Result |
|---|---|
| Mouth gauge accepts tub entrance without forced spreading | TBD |
| Mouth gauge top clearance avoids immediate rub | TBD |
| Casing prints inverted without supports | TBD |
| Top riding surface is flat enough for drawer slide | TBD |
| Tub enters slot without forced spreading | TBD |
| Tub slides full depth without binding | TBD |
| Mouth gauge result agrees with full casing mouth behavior | TBD |
| Closed position has acceptable side play | TBD |
| Back clearance is acceptable at full insertion | TBD |
| Top clearance avoids rubbing lip/items | TBD |
| Best peg coupon by insertion force | `0.30mm` and `0.45mm` socket clearances both felt about right; `0.60mm` was loose. |
| Best peg coupon by retention | `0.30mm` and `0.45mm` socket clearances both felt about right; `0.60mm` was loose. |
| Hex peg inserts without shaving or splitting socket walls | TBD |
| Any socket cracking, whitening, or delamination | TBD |
| Peg aligns top-slab socket to wall-foot receiver between two casing artifacts | TBD |
| Tub magnet wells accept 5mm magnets without cracking or loose fall-out | TBD |
| Casing magnet wells accept 6mm magnets without cracking or loose fall-out | TBD |
| Closed magnet alignment and retention are useful | TBD |
| 75% travel warning detent is noticeable without feeling like a hard stop | TBD |
| Tub wall-source CAD fix for the printed `+0.6mm` contour-compensation result | Implemented as `2.2mm` tub walls in CAD; physical print validation pending. |

2026-07-08 peg/socket coupon result: the rightmost coupon, `0.60mm` socket clearance, was loose. The other two inserts, `0.30mm` and `0.45mm`, both felt about right. Keep the current `0.45mm` prototype casing socket clearance unless actual casing-pair stack testing shows it needs the tighter `0.30mm` fit.

## Decision hooks

| Observation | Design response |
|---|---|
| Mouth gauge binds at side walls | Increase `SIDE_CLEARANCE` before spending a full casing print. |
| Tub binds at side walls | Measure printed tub exterior first, then increase `SIDE_CLEARANCE` in `casing-fit-test.scad` if CAD clearance is insufficient. |
| Tub bottoms against back before front is acceptable | Increase `BACK_CLEARANCE`. |
| Tub rubs top surface | Increase `TOP_CLEARANCE` or revisit tested tub height. |
| Tub rattles unacceptably | Keep clearance lower and inspect print/process variance first. |
| No peg coupon has acceptable insertion and retention | Keep peg/socket provisional and move to a peg-profile testbed. |
| Hex peg is too tight or shaves badly | Reduce point-to-point peg diameter, increase socket clearance, or add a dedicated peg-profile sweep. |
| Peg strategy requires external side/back protrusions | Reject the geometry and redesign around flat exterior casing faces. |
| One coupon is clearly best | Confirm against the actual casing sockets before updating prototype `PEG_CLEARANCE`. |
| Tub magnets are loose | Increase the tub bore/tip fit or revisit the 5mm pocket recipe before changing casing magnet positions. |
| Casing magnets are loose | Move from the default 6mm pocket toward the stronger `6mm R20/P20` candidate before changing magnet count. |
| Magnet wells are too tight or split walls | Loosen the bore/tip fit or reduce chamfer before changing the midline/paramedian array layout. |
| Tub source remains weaker than tubs printed with `+0.6mm` contour compensation | Revisit tub wall/pathing source; do not thicken the casing or rely on slicer contour compensation. |
