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
| Regular 23u casing fit target | `scad/casing-fit-test.scad` | `openscad -o /tmp/hutchfinity-casing-fit-regular-23u.stl scad/casing-fit-test.scad` |
| Peg/socket clearance coupon | `scad/testbed/peg_socket_fit_testbed.scad` | `openscad -o /tmp/hutchfinity-peg-socket-fit-testbed.stl scad/testbed/peg_socket_fit_testbed.scad` |


## Pre-print render checks

| Artifact | Render status | Measured STL bounds | Expected bounds | Result |
|---|---|---:|---:|---|
| Regular 23u casing fit target | Manifold | `389.2 x 280.2 x 94.24mm` | `389.2 x 280.2 x 94.24mm` | Match |
| Peg/socket clearance coupon | Manifold | `122.0 x 46.0 x 20.0mm` | `122.0 x 46.0 x 20.0mm` | Match |

The peg/socket coupon Y envelope includes loose pegs placed in front of the coupon blocks. Coupon blocks occupy `Y=0..26mm`; peg centers are at `Y=-16mm`, so the full exported Y envelope is `-20..26mm`.

## Geometry under test

| Value | Trial setting |
|---|---:|
| Tub exterior XY target | `255.2 x 339.2mm` |
| Casing slot, width-wise | `339.2 x 255.2 x 84.24mm` |
| Side/back/top slot clearance | `0.0 / 0.0 / 0.0mm` |
| Side wall / back wall / top | `25 / 25 / 10mm` |
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
| Casing prints inverted without supports | TBD |
| Top riding surface is flat enough for drawer slide | TBD |
| Tub enters slot without forced spreading | TBD |
| Tub slides full depth without binding | TBD |
| Closed position has acceptable side play | TBD |
| Back clearance is acceptable at full insertion | TBD |
| Top clearance avoids rubbing lip/items | TBD |
| Best peg coupon by insertion force | TBD |
| Best peg coupon by retention | TBD |
| Any socket cracking, whitening, or delamination | TBD |

## Decision hooks

| Observation | Design response |
|---|---|
| Tub binds at side walls | Increase `SIDE_CLEARANCE` in `casing-fit-test.scad`; do not change tub source geometry in this issue. |
| Tub bottoms against back before front is acceptable | Increase `BACK_CLEARANCE`. |
| Tub rubs top surface | Increase `TOP_CLEARANCE` or revisit tested tub height. |
| Tub rattles unacceptably | Keep clearance lower and inspect print/process variance first. |
| No peg coupon has acceptable insertion and retention | Keep peg/socket provisional and move to a peg-profile testbed. |
| One coupon is clearly best | Update prototype `PEG_CLEARANCE` only after confirming on an actual casing socket. |
