---
sensitivity: public
type: log
date: TBD
date_modified: 2026-09-04
testbed: magnet_crush_rib_testbed v1.4.0
sources:
  - https://github.com/karyandrew/second-brain/issues/2249
  - magnet_crush_rib_testbed.scad
---

# Crush-rib trial 02 — TBD

## Setup

| | |
|---|---|
| Printer | Sovol SV08 MAX |
| Process profile | TBD — standard 0.4mm nozzle / 0.2mm layer height |
| Filament profile | TBD |
| Testbed | `magnet_crush_rib_testbed.scad` v1.4.0 |
| Rib count | 8 @ 45° spacing |
| Chamfer | 0.3mm lead-in |
| Physical validation status | Not run — result cells intentionally remain empty |

## Measurement convention — nominal net radial interference

For every row and column:

```text
nominal well radius = magnet radius + WELL_R_ADD[row]
rib-tip radius = nominal well radius - PROTRUSIONS[col]
nominal net radial interference = PROTRUSIONS[col] - WELL_R_ADD[row]
```

Interpret the signed result consistently:

- negative value = nominal radial clearance;
- zero = zero-engagement baseline; and
- positive value = nominal radial interference.

The designed value is reported separately from the physical result. Extrusion,
flow, shrinkage, polygonization, and actual magnet tolerance can shift the
printed rib-tip radius, so a positive nominal value does not certify that the
printed part achieved the same interference. Record insertion, seating,
retention, removal, and damage observations in `Result` without rewriting the
nominal geometry after seeing the outcome.

Row A uses `WELL_R_ADD[0] = 0.20 mm`; row B uses
`WELL_R_ADD[1] = 0.05 mm`.

### Process profile — TBD

```json
{}
```

### Filament profile — TBD

```json
{}
```

## Results

### Row A — 5×1mm magnets (nominal well-Ø 5.4mm, well-depth 1.5mm)

| Col | Rib protrusion | Nominal net radial interference | Interpretation | Result |
|---|---:|---:|---|---|
| 0 | 0.05mm | -0.15mm | 0.15mm clearance | |
| 1 | 0.10mm | -0.10mm | 0.10mm clearance | |
| 2 | 0.15mm | -0.05mm | 0.05mm clearance | |
| 3 | 0.20mm | **0.00mm** | **zero-engagement baseline** | |
| 4 | 0.25mm | +0.05mm | nominal interference | |
| 5 | 0.30mm | +0.10mm | nominal interference | |

### Row B — 6×1.5mm magnets (nominal well-Ø 6.1mm, well-depth 2.0mm)

| Col | Rib protrusion | Nominal net radial interference | Interpretation | Result |
|---|---:|---:|---|---|
| 0 | 0.05mm | **0.00mm** | **zero-engagement baseline** | |
| 1 | 0.10mm | +0.05mm | nominal interference | |
| 2 | 0.15mm | +0.10mm | nominal interference | |
| 3 | 0.20mm | +0.15mm | nominal interference | |
| 4 | 0.25mm | +0.20mm | nominal interference | |
| 5 | 0.30mm | +0.25mm | nominal interference | |

## Observation fields

For each tested cell, record at least:

- insertion method and qualitative force;
- whether the magnet seats flush, shy, or proud;
- retention against hand pull or the declared pull test;
- removal method and whether the fit remains repeatable;
- visible rib, wall, floor, or magnet damage; and
- any print defect that makes the cell uninterpretable.

Do not call the zero-engagement baseline a successful crush-rib fit merely because
a magnet stays in the printed well. Report retention from the complete printed
geometry separately from designed positive rib interference.

## Design implications for next iteration

TBD — pending print results.
