---
sensitivity: public
type: experiment
date: 2026-07-25
issue: hutchfinity#26
status: CAD probe complete; historical magnet-comparison metrics predate the canonical recipe; physical Mini trial pending
---

# Mini Basket/Carrier CAD probe

## Scope

This probe tests whether the pinned Gridfinity Basket source can support a
Hutchfinity Basket/Carrier without replacing the current Tub implementation.
It is a general parameterized testbed instantiated only at Mini size. It does
not add a fifth production module, fan out Regular/Mega variants, change the
Gridfinity system PRD, or claim physical validation.

2026-08-15 magnet-recipe correction: the probe now consumes the same canonical
6 x 1.5mm recipe as Tub and Casing from `scad/magnet_well.scad`: `6.10mm` bore,
`5.60mm` rib-tip diameter from `0.25mm` radial crush, eight `0.80mm` ribs,
`0.30mm` lead-in chamfer, and `2.30mm` depth. Magnet-volume measurements below
are retained as pre-canonical provenance and must be regenerated before they
are used for a current magnetic comparison. The envelope, floor, stack, and
magnet-free findings remain separate from that superseded cutter geometry.

The reproducible packet is built with:

```bash
scad/testbed/build-basket-carrier-mini-probe.sh
```

Generated STLs and `metrics.tsv` are written under
`preview/issue-26/basket-carrier-mini-probe/`.

## Source and parameter map

The probe retains Gridfinity Basket at pinned revision
`549dc4015e4511daeb7b942de96d2531101701db`. The source and MIT notice are
preserved under `scad/gridfinity/vendor/basket/`; the adapter includes the
unchanged source inside a parameterized testbed module.

The Mini instance uses:

| Parameter | Value |
|---|---:|
| Hutchfinity cells | `6 x 16 x 23` |
| Hutchfinity pitch | `21mm XY / 3.5mm Z` |
| Upstream `GridSize` | `[6, 16, 10.5]` |
| Wall thickness | `2.2mm` |
| Additional floor height | `1.29mm` |
| Standoff | `1.75mm` |
| Top padding | `1.25mm` |
| XY / Z tolerance | `0.50 / 0.25mm` |
| Generator magnet holes | disabled |

The upstream source calculates height in 7mm units. The adapter maps the
current Hutchfinity target explicitly rather than treating `10.5` as an
unexplained constant:

```text
target height = 23 * 3.5 + 3.74 = 84.24mm
upstream Z = (84.24 - 4.4 - 1.29 - 1.75 - 0.25 - (2.2 - 0.4) - 1.25) / 7
           = 10.5
```

The matched `2.2mm` wall exceeds the upstream Customizer's advertised `2.0mm`
range, but the pinned source accepts it and all probe renders are manifold.
A non-catalog `4 x 5 x 12` parameterization smoke render was also manifold at
the expected `88.4 x 109.4 x 45.74mm`, confirming the adapter is not a
Mini-only geometry wrapper.

## Floor contracts

The module boundary exposes three modes:

| Mode | Probe geometry | Result |
|---|---|---|
| `plain` | Solid flat floor, no internal grid | Reproduces the pinned matched mesh. |
| `integral` | Upstream internal Gridfinity pockets | Manifold; same outer envelope. |
| `removable` | Plain floor plus an explicit `126 x 336 x 4mm` removable-grid seat check | Contract defined, but zero-clearance fit remains unresolved. |

`plain` and `removable` intentionally share basket geometry in this slice. The
distinction is the removable mode's requirement to accept the committed Mini
baseplate.

A `1 x 1mm` center-floor intersection probe measures the rendered cavity with
the same endpoints in both meshes:

| Mesh | Center floor Z | Lip-top Z | Center floor-to-lip span |
|---|---:|---:|---:|
| Current Mini | `4.703059mm` | `84.240000mm` | `79.536941mm` |
| Candidate plain | `4.700000mm` | `84.240000mm` | `79.540000mm` |

The candidate is therefore about `0.003059mm` deeper at the center floor, not
materially different at this datum. The PRD's separate nominal `79.30mm`
cavity term uses a different body/floor convention and is not used for this
like-for-like mesh comparison. Both designs use the same nominal
`126 x 336mm` cavity XY.

At exact seating height, the committed `126 x 336 x 4mm` Mini baseplate and
candidate produce `6.370681mm³` of Boolean intersection. Lifting the baseplate
`0.01mm` preserves the same residual, so it is an XY zero-clearance boundary
problem rather than floor-plane contact alone. The residual is thin and spread
across the seat boundary; it is CAD evidence that an explicit clearance/corner
contract is still needed, not a physical binding measurement.

## Magnet and casing datums

Generator magnet holes are disabled. When requested, the probe cuts the shared
canonical Hutchfinity product interface from `scad/magnet_well.scad`:

- six wells at X `-21 / 0 / +21mm` and Y `-162.2 / +162.2mm`;
- `6.10mm` bore and `5.60mm` rib-tip diameter from `0.25mm` radial crush;
- eight ribs at 45-degree spacing with `0.80mm` rib width;
- `2.30mm` depth and `0.30mm` lead-in chamfer;
- the same `hutchfinity_magnet_well_cuts()` recipe consumed by Tub and Casing.

The default Basket/Carrier plain-floor envelope is `4.70mm`, so the canonical
`2.30mm` well retains `2.40mm` of modeled material below the cut. That is a CAD
envelope check, not physical depth validation.

The candidate's exact `130.4 x 340.4 x 84.24mm` envelope fits the existing
Mini CAD slot datum of `132.4 x 340.9 x 85.24mm`. The overflow witness contains
only its isolated `1mm³` reference cube, so there is no candidate material
outside that slot after the comparison's `0.01mm` Boolean epsilon. This is a
CAD containment check, not drawer-slide validation.

## Historical pre-canonical mesh comparison

All figures below come from OpenSCAD `2026.04.26` and the generated
`metrics.tsv`. Magnet-free rows remain useful. Rows involving magnet cuts used
the former Tub-side cutter and must be regenerated before current magnetic
volume or overlap conclusions are drawn.

| Configuration | Current volume | Candidate volume | Shared | Current-only | Candidate-only | Union | IoU |
|---|---:|---:|---:|---:|---:|---:|---:|
| Both magnet-free | `362496.793898` | `360318.767490` | `358712.075338` | `3784.718559` | `1606.692152` | `364103.486050` | `98.519%` |
| Current magnetic, candidate plain | `362351.516706` | `360318.767490` | `358566.798146` | `3784.718559` | `1751.969344` | `364103.486050` | `98.479%` |
| Both use the former shared magnet wells | `362351.516706` | `360162.816282` | `358556.123146` | `3795.393560` | `1606.693136` | `363958.209842` | `98.516%` |

The middle row reproduces the issue's original comparison configuration.
The candidate-only volume matches the recorded value within `0.001mm³`; the
shared and current-only figures differ by about `0.4mm³`, within the mesh
Boolean/export variation observed during reproduction.

Under the former cutter, the shared cut removed `145.277192mm³` from the
current Tub and `155.951208mm³` from the candidate. The positions and cutter
parameters matched at that time; the approximately `10.67mm³` difference came
from the different lower floor/stacking profiles intersected by those cuts.
These values are historical and are not measurements of the canonical recipe.

## Stack check

The upstream nesting offset is:

```text
84.24 - 1.75 - 0.25 = 82.24mm
```

The two-candidate intersection at that offset is empty. The generated
self-stack witness therefore contains only its isolated `1mm³`, 12-facet
reference cube. This verifies non-interference for the CAD pair; it does not
verify printed stack feel, stability, or retention.

## CAD recommendation

Keep the Basket/Carrier as a parallel experimental candidate for the next
physical gate; do not subsume Tub yet.

The probe is too close to reject: it reproduces the target envelope, reaches
about `98.5%` volumetric IoU in the historical comparison, uses authored
parametric source, maps the shared canonical magnet interface, and self-stacks
without CAD overlap. It is also too early to replace Tub: the floor/rim
residuals are material, the removable-grid contract has unresolved
zero-clearance boundaries, the canonical magnetic comparison has not been
regenerated, and no physical Mini trial has checked casing slide, stack feel,
or print behavior.

The final disposition remains gated:

- **Subsume Tub** only if the physical Mini preserves casing fit, stacking,
  ordinary tub use, and the selected floor contract without SKU-specific
  patches.
- **Remain parallel** if the Basket/Carrier options are useful but its floor,
  rim, or removable-grid behavior should not redefine the current Tub.
- **Reject** if resolving fit or print behavior breaks the matched envelope,
  stack datum, or general parameterization.
