---
sensitivity: public
type: log
date: TBD
testbed: magnet_crush_rib_testbed v1.4.0
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

| Col | Protrusion | Nominal radial fit | Result |
|---|---|---|---|
| 0 | 0.05mm | 0.15mm clearance | |
| 1 | 0.10mm | 0.10mm clearance | |
| 2 | 0.15mm | 0.05mm clearance | |
| 3 | 0.20mm | Zero fit | |
| 4 | 0.25mm | 0.05mm interference | |
| 5 | 0.30mm | 0.10mm interference | |

### Row B — 6×1.5mm magnets (nominal well-Ø 6.1mm, well-depth 2.0mm)

| Col | Protrusion | Nominal radial fit | Result |
|---|---|---|---|
| 0 | 0.05mm | Zero fit | |
| 1 | 0.10mm | 0.05mm interference | |
| 2 | 0.15mm | 0.10mm interference | |
| 3 | 0.20mm | 0.15mm interference | |
| 4 | 0.25mm | 0.20mm interference | |
| 5 | 0.30mm | 0.25mm interference | |

## Design implications for next iteration

TBD — pending print results.
