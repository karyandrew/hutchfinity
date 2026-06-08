---
sensitivity: public
type: log
date: 2026-06-07
testbed: magnet_crush_rib_testbed v1.2.0
---

# Crush-rib trial 01 — 2026-06-07

## Setup

| | |
|---|---|
| Printer | Sovol SV08 |
| Profile | PHATTY (0.6mm nozzle / 0.3mm layer height) |
| Filament | Sunlu Clear PETG |
| Testbed | `magnet_crush_rib_testbed.scad` v1.2.0 |
| Rib count | 8 @ 45° spacing |
| Chamfer | 0.3mm lead-in |

**Note:** PHATTY settings are marginal for these features. At 0.3mm layer height the 5×1mm well (1.1mm deep) is ~3 layers; the 0.8mm rib engagement zone is ~2 layers. Coarse geometry on small holes.

OrcaSlicer profile for this print: **not yet captured** — to be added from local session.

## Results

### Row A — 5×1mm magnets (well-Ø 5.1mm, well-depth 1.1mm)

| Col | Protrusion | Result |
|---|---|---|
| 0 | 0.05mm | Inserted — only one that went in |
| 1 | 0.10mm | Would not insert |
| 2 | 0.15mm | Would not insert |
| 3 | 0.20mm | Would not insert |
| 4 | 0.25mm | Would not insert |
| 5 | 0.30mm | Would not insert |

5×1mm bore is too tight overall at current nominal Ø (OD + 0.1mm) with PHATTY extrusion. Only 0.05mm protrusion was insertable. Retention result at 0.05mm not recorded (insertion alone was the finding).

### Row B — 6×1.5mm magnets (well-Ø 6.1mm, well-depth 1.6mm)

| Col | Protrusion | Result |
|---|---|---|
| 0 | 0.05mm | Inserted, pulls right back out |
| 1 | 0.10mm | Inserted, pulls right back out |
| 2 | 0.15mm | Inserted, pulls right back out |
| 3 | 0.20mm | Inserted, pulls right back out |
| 4 | 0.25mm | ✅ Holds — does not pull out |
| 5 | 0.30mm | ✅ Holds — does not pull out |

**All 6×1.5mm magnets sit proud of the plate surface.** Well depth (1.6mm = magnet H + 0.10mm) is insufficient to seat flush.

## Design implications for next iteration

1. **Well depth**: increase extra depth from +0.10mm to at least +0.5mm. Magnets must seat shy (preferred) not proud. Proud magnets will interfere with mating casing surface.

2. **5×1mm bore**: nominal Ø + 0.1mm is already too tight at PHATTY settings. Next testbed should widen bore clearance or test at standard (0.4mm / 0.2mm) settings to separate rib geometry from extrusion-width overextrusion artifact.

3. **6×1.5mm recipe**: protrusion 0.25–0.30mm holds. With correct well depth (flush/shy), target 0.25mm as the conservative starting point for casing.scad.

4. **Print settings**: PHATTY at 0.3mm layer height is too coarse for 1–2mm deep features. Next testbed print at standard settings (0.4mm nozzle / 0.2mm layer) to get clean rib geometry before locking recipe.
