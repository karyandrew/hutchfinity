---
sensitivity: public
type: log
date: 2026-07-04
testbed: casing-fit-test v0.1.0 and peg_socket_fit_testbed v0.1.0
status: planned
---

# Casing fit trial 01 — planned

## Purpose

Validate the representative regular-tub casing interface from hutchfinity#20 without conflating tub-process compensation, casing slot clearance, or peg/socket press-fit.

## Print artifacts

| Artifact | Source | Export command |
|---|---|---|
| Mouth fit gauge | `scad/testbed/casing_mouth_fit_gauge.scad` | `openscad -o /tmp/hutchfinity-casing-mouth-fit-gauge.stl scad/testbed/casing_mouth_fit_gauge.scad` |
| Regular 23u casing fit target | `scad/casing-fit-test.scad` | `openscad -o /tmp/hutchfinity-casing-fit-regular-23u.stl scad/casing-fit-test.scad` |
| Peg/socket clearance coupon | `scad/testbed/peg_socket_fit_testbed.scad` | `openscad -o /tmp/hutchfinity-peg-socket-fit-testbed.stl scad/testbed/peg_socket_fit_testbed.scad` |


## Physical orientation

Print the casing and mouth-gauge artifacts in their OpenSCAD orientation: the top slab is on the build plate and the side/back walls rise upward. For fit testing, flip the printed part into installed orientation: top slab above the tub, side walls down, open front at the drawer entrance. The tub should sit on a flat reference surface, tabletop, footer, or casing-below surrogate. Testing with the slab underneath the tub is invalid for drawer clearance.

## Design critique before print

| Artifact | What it actually proves | What it does not prove | CAD solid volume |
|---|---|---|---:|
| Mouth fit gauge | Tub can enter the representative width and immediate ceiling height without forced spreading or top rub. | Full-depth sliding friction, back clearance, long-wall bow, stack behavior, or peg behavior. | `617.6cm^3` |
| Regular 23u casing fit target | Full-depth slot behavior for the current representative casing. | Final clearance recipe unless tested against a real printed tub and recorded. | `2979.1cm^3` |
| Peg/socket clearance coupon | First-pass insertion/retention feel across three socket clearances. | Actual casing socket behavior under full slab stiffness, slicer infill, and stack loading. | `26.9cm^3` |

The mouth gauge keeps full slot width and height because those are the dimensions being tested; it only reduces drawer-travel depth. Its CAD solid volume is about 21% of the full casing target before slicer infill. If it fails, change `SIDE_CLEARANCE` or `TOP_CLEARANCE` before spending plastic on the full casing.

## Pre-print render checks

| Artifact | Render status | Measured STL bounds | Expected bounds | Result |
|---|---|---:|---:|---|
| Mouth fit gauge | Manifold | `389.2 x 48.0 x 94.24mm` | `389.2 x 48.0 x 94.24mm` | Match |
| Regular 23u casing fit target | Manifold | `389.2 x 280.2 x 94.24mm` | `389.2 x 280.2 x 94.24mm` | Match |
| Peg/socket clearance coupon | Manifold | `122.0 x 46.0 x 20.0mm` | `122.0 x 46.0 x 20.0mm` | Match |

The peg/socket coupon Y envelope includes loose pegs placed in front of the coupon blocks. Coupon blocks occupy `Y=0..26mm`; peg centers are at `Y=-16mm`, so the full exported Y envelope is `-20..26mm`.

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
| Any socket cracking, whitening, or delamination | TBD |

## Decision hooks

| Observation | Design response |
|---|---|
| Mouth gauge binds at side walls | Increase `SIDE_CLEARANCE` before spending a full casing print. |
| Tub binds at side walls | Increase `SIDE_CLEARANCE` in `casing-fit-test.scad`; do not change tub source geometry in this issue. |
| Tub bottoms against back before front is acceptable | Increase `BACK_CLEARANCE`. |
| Tub rubs top surface | Increase `TOP_CLEARANCE` or revisit tested tub height. |
| Tub rattles unacceptably | Keep clearance lower and inspect print/process variance first. |
| No peg coupon has acceptable insertion and retention | Keep peg/socket provisional and move to a peg-profile testbed. |
| One coupon is clearly best | Update prototype `PEG_CLEARANCE` only after confirming on an actual casing socket. |
