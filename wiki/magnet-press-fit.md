---
type: evergreen
sensitivity: public
version: 1.1.0
---

# Magnet press-fit — crush-rib recipe

Disc magnets in tub foot wells and casing arrays are retained by a crush-rib bore: the nominal bore is slightly undersized relative to the magnet, with inward-protruding ribs that compress on insertion to provide holding force.

**Preference: shy over proud.** Magnets must not protrude above their surface — they would interfere with mating geometry. Err on the side of wells that are slightly too deep over wells that are too shallow.

## Magnet sizes in use

| Size | OD | H | Application |
|---|---|---|---|
| Small | 5mm | 1mm | Tub foot wells |
| Standard | 6mm | 1.5mm | Casing arrays |

## Crush-rib geometry

| Parameter | Value | Notes |
|---|---|---|
| Rib count | 8 | FDM-validated; ≤5 → polygon bore, ≥30 → unprintable at 0.4mm nozzle |
| Rib spacing | 45° | Uniform; 8 × 45° |
| Rib width | 0.8mm | Base chord at bore wall |
| Chamfer | 0.3mm lead-in | 45° cone at well opening; aids centering, must not eat rib engagement depth |
| Rib pattern | Bore-minus-notch | Rib-shaped notches subtracted from bore cylinder; plate material protrudes inward |

The bore-minus-notch approach (subtract rib-notch polygons from the bore, so plate material protrudes) is the correct FDM pattern. Do not subtract ribs from the plate (that makes the bore larger, not smaller).

## Trial-01 results — PHATTY settings (2026-06-07)

Printer: Sovol SV08 MAX. Process: 0.6mm nozzle, 0.59mm layer, 1.4mm line width, 1 wall loop, 1.13 flow ratio. See `scad/testbed/trial-log-01.md` for full profiles.

| Magnet | Protrusion | Result |
|---|---|---|
| 5×1mm | 0.05mm (baseline) | Insertable only |
| 5×1mm | 0.10–0.30mm | Would not insert |
| 6×1.5mm | 0.05–0.20mm | Inserts, pulls out |
| 6×1.5mm | 0.25mm | ✅ Holds |
| 6×1.5mm | 0.30mm | ✅ Holds |

**All 6×1.5mm magnets sat proud** at PHATTY settings — first-layer over-extrusion (1.3× flow) raised the well floor.

**PHATTY is marginal for these features:** 0.59mm layer + 1.4mm width + 1.13 flow = ~2 layers total for a 1.1mm well, coarse bore geometry, reduced effective depth. Results characterize PHATTY settings specifically; standard settings (0.4mm nozzle / 0.2mm layer) are required for clean characterization.

## Tentative recipe (pending standard-settings validation)

| Magnet | Protrusion | WELL_R_ADD | WELL_D_ADD | Status |
|---|---|---|---|---|
| 5×1mm | TBD | TBD | ≥0.50mm | Pending iteration 2 — PHATTY bore too tight to characterize |
| 6×1.5mm | 0.25mm | 0.10mm | ≥0.50mm | Tentative (PHATTY); validate at standard settings |

**WELL_D_ADD must be ≥0.50mm** to ensure magnets sit shy at PHATTY settings. Iteration 1 used 0.10mm, which was insufficient.

## Testbed

`scad/testbed/magnet_crush_rib_testbed.scad` v1.4.0 — 6×2 grid sweeping rib protrusion 0.05–0.30mm for both magnet sizes. Trial-02 uses `WELL_R_ADD = [0.20, 0.05]` for the 5×1mm and 6×1.5mm rows respectively, plus `WELL_D_ADD = 0.50mm`. Print at target process settings to characterize the per-printer recipe.

Nominal radial fit is `protrusion - WELL_R_ADD[row]`. In the 5×1mm row, columns 0–2 are clearance controls, column 3 is zero fit, and columns 4–5 provide 0.05mm and 0.10mm radial interference. In the 6×1.5mm row, column 0 is zero fit and columns 1–5 provide 0.05–0.25mm radial interference. These are nominal geometry values, not physical-fit results.

## Open issues

- hutchfinity#7 — iteration 2: deeper wells, standard settings, 5×1mm bore fix
