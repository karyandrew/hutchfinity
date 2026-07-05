---
sensitivity: public
type: log
date: 2026-07-04
testbed: casing-fit-test v0.1.0 and peg_socket_fit_testbed v0.1.0
status: planned; model revised 2026-07-05
---

# Casing fit trial 01 — planned

## Purpose

Validate the representative regular-tub casing interface from hutchfinity#20 without conflating tub-process compensation, casing slot clearance, or peg/socket press-fit.

## Print artifacts

| Artifact | Source | Export command |
|---|---|---|
| Mouth fit gauge | `scad/testbed/casing_mouth_fit_gauge.scad` | `openscad -o preview/casing-fit-trial-01/casing-mouth-fit-gauge.stl scad/testbed/casing_mouth_fit_gauge.scad` |
| Regular 23u casing fit target | `scad/casing-fit-test.scad` | `openscad -o preview/casing-fit-trial-01/casing-fit-regular-23u.stl scad/casing-fit-test.scad` |
| Peg/socket clearance coupon | `scad/testbed/peg_socket_fit_testbed.scad` | `openscad -o preview/casing-fit-trial-01/peg-socket-fit-testbed.stl scad/testbed/peg_socket_fit_testbed.scad` |
| Peg stack interface coupon | `scad/testbed/peg_stack_interface_testbed.scad` | `openscad -o preview/casing-fit-trial-01/peg-stack-interface-testbed.stl scad/testbed/peg_stack_interface_testbed.scad` |


## Physical orientation

Print the casing and mouth-gauge artifacts in their OpenSCAD orientation: the top slab is on the build plate and the side/back walls rise upward. In that print view, the visible sockets on the wall-foot face are the installed-bottom sockets. The installed-top sockets open on the bed-facing `Z=0` top slab and can be easy to miss in a top-only preview. For fit testing, flip the printed part into installed orientation: top slab above the tub, side walls down, open front at the drawer entrance. The tub should sit on a flat reference surface, tabletop, footer, or casing-below surrogate. Testing with the slab underneath the tub is invalid for drawer clearance.

## Design critique before print

| Artifact | What it actually proves | What it does not prove | CAD solid volume |
|---|---|---|---:|
| Mouth fit gauge | Tub can enter the representative width and immediate ceiling height without forced spreading or top rub. | Full-depth sliding friction, back clearance, long-wall bow, stack behavior, or peg behavior. | `617.6cm^3` |
| Regular 23u casing fit target | Full-depth slot behavior for the current representative casing. | Final clearance recipe unless tested against a real printed tub and recorded. | `2974.7cm^3` |
| Peg/socket clearance coupon | First-pass insertion/retention feel across three socket clearances. | Actual casing pair behavior: top-slab socket plus wall-foot receiver, full slab stiffness, slicer infill, and stack loading. | `26.9cm^3` |
| Peg stack interface coupon | Whether a 20mm peg can mate a lower top-slab through-socket to an upper wall-foot blind receiver at the side-wall edge condition without face interference. | Full casing stack squareness, long-wall tolerance, or retention under load. | `24.9cm^3` |

The mouth gauge keeps full slot width and height because those are the dimensions being tested; it only reduces drawer-travel depth. Its CAD solid volume is about 21% of the full casing target before slicer infill. If it fails, change `SIDE_CLEARANCE` or `TOP_CLEARANCE` before spending plastic on the full casing.

2026-07-05 critique update: the original peg was only a chamfered cylinder. `scad/peg.scad` now defaults to a six-rib star/crush profile: 8.0mm nominal diameter, 7.4mm core, 8.6mm rib peaks, 0.85mm rib width, and 0.75mm rib end relief before the end chamfers. Regenerate the peg/socket and stack-interface coupons before physical testing.

2026-07-05 edge-land update: the first ribbed-peg socket inset left the socket chamfer tangent to the outside casing edge. `scad/casing.scad` now adds `4.0mm` of edge land beyond the chamfer opening, moving the current socket center from `6.725mm` to `10.725mm` from the outside side/back edge.

## Pre-print render checks

| Artifact | Render status | Measured STL bounds | Expected bounds | Result |
|---|---|---:|---:|---|
| Mouth fit gauge | Manifold | `389.2 x 48.0 x 94.24mm` | `389.2 x 48.0 x 94.24mm` | Match |
| Regular 23u casing fit target | Manifold | `389.2 x 280.2 x 94.24mm` | `389.2 x 280.2 x 94.24mm` | Match |
| Peg/socket clearance coupon | Manifold | `122.0 x 46.0 x 20.0mm` | `122.0 x 46.0 x 20.0mm` | Match |
| Peg stack interface coupon | Manifold | `60.0 x 56.0 x 20.0mm` | `60.0 x 56.0 x 20.0mm` | Match |

The peg/socket coupon Y envelope includes loose pegs placed in front of the coupon blocks. Coupon blocks occupy `Y=0..26mm`; peg centers are at `Y=-16mm`, so the full exported Y envelope is `-20..26mm`.

The peg stack interface coupon deliberately uses the casing side-wall edge condition rather than a centered socket in a block. The first draft used centered sockets and would have overestimated surrounding material; the committed coupon uses `SIDE_THICKNESS = 25mm` and `peg_socket_inset(...)` from `casing.scad`.

## Geometry under test

| Value | Trial setting |
|---|---:|
| Tub exterior XY target | `255.2 x 339.2mm` |
| Casing slot, width-wise | `339.2 x 255.2 x 84.24mm` |
| Side/back/top slot clearance | `0.0 / 0.0 / 0.0mm` |
| Side wall / back wall / top | `25 / 25 / 10mm` full casing; mouth gauge uses `8mm` back stop |
| Mouth gauge slot depth | `40.0mm` |
| Peg diameter | `8.0mm` |
| Peg socket clearances | `0.30`, `0.45`, `0.60mm` |
| Peg/socket chamfer | `2.5mm` |
| Peg socket edge land | `4.0mm` beyond the socket chamfer opening |
| Peg profile | Six-rib star/crush peg; `7.4mm` core and `8.6mm` rib peaks by default |
| Casing socket faces | Installed top opens on print `Z=0`; installed bottom/wall-foot sockets open on print `Z=print_z` |
| Peg stack interface coupon | `25mm` side-wall strip, socket center at casing socket inset, `10mm` lower through-socket + `10mm` upper blind receiver + `20mm` peg |

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
| Best peg coupon by insertion force | TBD |
| Best peg coupon by retention | TBD |
| Ribbed peg crushes without shaving or splitting socket walls | TBD |
| Any socket cracking, whitening, or delamination | TBD |
| Peg aligns top-slab socket to wall-foot receiver on stack-interface coupon | TBD |
| Peg aligns top-slab socket to wall-foot receiver between two casing artifacts | TBD |

## Decision hooks

| Observation | Design response |
|---|---|
| Mouth gauge binds at side walls | Increase `SIDE_CLEARANCE` before spending a full casing print. |
| Tub binds at side walls | Increase `SIDE_CLEARANCE` in `casing-fit-test.scad`; do not change tub source geometry in this issue. |
| Tub bottoms against back before front is acceptable | Increase `BACK_CLEARANCE`. |
| Tub rubs top surface | Increase `TOP_CLEARANCE` or revisit tested tub height. |
| Tub rattles unacceptably | Keep clearance lower and inspect print/process variance first. |
| No peg coupon has acceptable insertion and retention | Keep peg/socket provisional and move to a peg-profile testbed. |
| Ribbed peg is too tight or shaves badly | Reduce rib peak overage, increase socket clearance, or add a dedicated peg-profile sweep. |
| Peg registers coupon but not actual casing pair | Keep coupon result as screening only; revise casing top/foot socket geometry. |
| One coupon is clearly best | Update prototype `PEG_CLEARANCE` only after confirming on an actual casing socket. |
