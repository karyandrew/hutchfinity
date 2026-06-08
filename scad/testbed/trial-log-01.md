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
| Printer | Sovol SV08 MAX |
| Process profile | PHATTY MAX 0.6 nozzle - 0.5.0 (see below) |
| Filament profile | Sunlu PETG PHAT MAX - .6 1.1.1 (see below) |
| Testbed | `magnet_crush_rib_testbed.scad` v1.2.0 (v1.3.0 in this PR corrects label positioning, reduces $fn, and adds an assert guard — no well or rib geometry changes; trial data is valid for both) |
| Rib count | 8 @ 45° spacing |
| Chamfer | 0.3mm lead-in |

### Process profile — PHATTY MAX 0.6 nozzle - 0.5.0

```json
{
    "bottom_shell_layers": "2",
    "bottom_surface_pattern": "monotonic",
    "brim_type": "no_brim",
    "detect_thin_wall": "1",
    "elefant_foot_compensation": "1",
    "first_layer_flow_ratio": "1.3",
    "from": "User",
    "infill_direction": "90",
    "infill_wall_overlap": "35%",
    "inherits": "0.30mm Standard @Sovol SV08 MAX 0.6 nozzle",
    "initial_layer_infill_speed": "140",
    "initial_layer_line_width": "1.4",
    "initial_layer_print_height": "0.6",
    "initial_layer_speed": "120",
    "inner_wall_acceleration": "2500",
    "inner_wall_line_width": "1.4",
    "inner_wall_speed": "140",
    "internal_solid_infill_line_width": "1.4",
    "internal_solid_infill_speed": "180",
    "layer_height": "0.59",
    "line_width": "1.2",
    "name": "PHATTY MAX 0.6 nozzle - 0.5.0",
    "outer_wall_acceleration": "1000",
    "outer_wall_line_width": "1.4",
    "print_extruder_id": ["1"],
    "print_extruder_variant": ["Direct Drive Standard"],
    "reduce_crossing_wall": "1",
    "seam_gap": "-0.01",
    "seam_position": "nearest",
    "set_other_flow_ratios": "1",
    "skirt_loops": "0",
    "sparse_infill_density": "28%",
    "sparse_infill_line_width": "0.8",
    "sparse_infill_pattern": "tpmsd",
    "sparse_infill_speed": "220",
    "staggered_inner_seams": "1",
    "top_shell_layers": "2",
    "top_shell_thickness": "0",
    "top_surface_line_width": "1.4",
    "top_surface_speed": "120",
    "version": "2.3.2.60",
    "wall_direction": "cw",
    "wall_loops": "1"
}
```

### Filament profile — Sunlu PETG PHAT MAX - .6 1.1.1

```json
{
    "chamber_temperature": ["40"],
    "fan_cooling_layer_time": ["0"],
    "fan_max_speed": ["100"],
    "fan_min_speed": ["25"],
    "filament_extruder_variant": ["Direct Drive Standard"],
    "filament_flow_ratio": ["1.13"],
    "filament_max_volumetric_speed": ["50"],
    "filament_settings_id": ["Sunlu PETG PHAT MAX - .6 1.1.1"],
    "filament_vendor": ["Sunlu"],
    "from": "User",
    "full_fan_speed_layer": ["5"],
    "hot_plate_temp": ["85"],
    "inherits": "Generic PETG @Sovol SV08 MAX",
    "name": "Sunlu PETG PHAT MAX - .6 1.1.1",
    "nozzle_temperature": ["260"],
    "slow_down_layer_time": ["0"],
    "version": "2.3.2.60"
}
```

## Why PHATTY is marginal for this feature

| Setting | Value | Effect on wells |
|---|---|---|
| `layer_height` | 0.59mm | 1.1mm well = ~2 layers total; bore barely resolves |
| `outer_wall_line_width` | 1.4mm | Fat single wall; bore narrower than nominal |
| `wall_loops` | 1 | One perimeter — no redundancy, bore geometry is coarse |
| `filament_flow_ratio` | 1.13 | 13% over-extrusion narrows bore further |
| `first_layer_flow_ratio` | 1.3 | 130% first-layer flow raises well floor, reduces effective depth |
| `slow_down_layer_time` | 0 | No cooling on small features; top layers may fuse |

## Results

### Row A — 5×1mm magnets (nominal well-Ø 5.1mm, well-depth 1.1mm)

| Col | Protrusion | Result |
|---|---|---|
| 0 | 0.05mm | Inserted (only one that went in) |
| 1 | 0.10mm | Would not insert |
| 2 | 0.15mm | Would not insert |
| 3 | 0.20mm | Would not insert |
| 4 | 0.25mm | Would not insert |
| 5 | 0.30mm | Would not insert |

Over-extrusion + coarse layer geometry effectively closed the bore. The nominal 0.1mm bore clearance is insufficient at PHATTY settings — the bore is already undersize before ribs are considered.

### Row B — 6×1.5mm magnets (nominal well-Ø 6.1mm, well-depth 1.6mm)

| Col | Protrusion | Result |
|---|---|---|
| 0 | 0.05mm | Inserted, pulls right back out |
| 1 | 0.10mm | Inserted, pulls right back out |
| 2 | 0.15mm | Inserted, pulls right back out |
| 3 | 0.20mm | Inserted, pulls right back out |
| 4 | 0.25mm | ✅ Holds |
| 5 | 0.30mm | ✅ Holds |

**All 6×1.5mm magnets sit proud of the plate surface.** Effective well depth less than nominal 1.6mm due to first-layer over-extrusion raising the floor.

**Preference: shy is better than proud** for this use case — magnets in tub foot wells and casing arrays must not protrude above their surface or they interfere with mating geometry.

## Design implications for next iteration

1. **Well depth**: increase extra depth from +0.10mm to +0.5mm minimum. Needs physical validation at target print settings.

2. **5×1mm bore**: nominal Ø + 0.1mm is insufficient at PHATTY settings. Either: (a) increase bore clearance to +0.3–0.4mm for PHATTY, or (b) reprint at standard settings (0.4mm nozzle / 0.2mm layer) to characterize rib geometry cleanly before adding extrusion-width compensation.

3. **6×1.5mm recipe (tentative)**: 0.25mm protrusion holds at PHATTY. Pending flush/shy well depth confirmation and validation at standard settings before locking for casing.scad.

4. **Print settings for next testbed**: standard (0.4mm nozzle / 0.2mm layer height) — PHATTY is too coarse for features this small.
