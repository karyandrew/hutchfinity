---
version: 0.26.0
sensitivity: public
---

# Hutchfinity system spec

This contract implements the single-slot architecture in [`chest-prd.md`](chest-prd.md). It describes the current authored parts and generator. Historical trial dimensions and physical observations remain in their trial records; they are not defaults for newly generated parts.

## Current module

`python3 hutchfinity.py` opens the local generator. A module contains one tub, one matching casing, its complete peg set and one glue-on pull. Selecting the separate grid adds one removable grid. Cups have their own command and form.

`scad/hutchfinity.scad` derives every part from the same size and design options. The core in `scad/casing.scad` remains tub-agnostic: it takes direct slot dimensions and never imports the tub to infer them.

| Part | Current contract |
|---|---|
| Tub | Intact 1.30 mm floor, 2.2 mm structural walls, stacking lip, integral or separate grid. No magnet wells. |
| Casing | One top, two sides and a back; no front or bottom. Prints riding-slab-down. Flat side/back exterior faces. No default magnet wells. |
| Pegs | Laid-down hex pegs for vertical stacking; continuous bores have receivers at both faces and a narrower insertion stop. |
| Pull | One glue-on drawer pull with a flat bonding footprint; scales uniformly with its positioning guide on small tubs. |
| Grid | Integral grid or separate insert; separate-grid modules require at least 2 × 2 cells. |

No drawer-count parameter, rails, front stop, external stack pads or footer mode belongs to the casing. The bottom drawer rides on a tabletop or separate footer. Lateral linking and furniture-scale load qualification remain separate work.

## Dimensions and defaults

Input size is `cells_x × cells_y × bin_h`: width/depth in 21 mm cells and the tallest bin in 3.5 mm height units. The app supports 1–40 cells on each axis and 5–40h bins. These are geometric limits, not a promise that a part fits a particular printer. Check the complete casing footprint in the receiving slicer.

| Input | Generator default | Meaning |
|---|---:|---|
| Tub floor | 1.30 mm | Authored floor under the grid; independent of casing thickness. |
| Tub wall / rim wall | 2.2 / 0.4 mm | Structural wall and stacking rim. |
| Grid height | 5.0 mm | Grid above the authored floor. |
| Stack gap | 0.50 mm | Gap above the tallest bin lip when tubs stack. |
| Bin lip | 3.74 mm | Height added above the bin's nominal height. |
| Casing sides / back | 18 / 18 mm | Wall footprints containing the stack bores. |
| Casing riding slab | **3.0 mm** | Changes casing exterior height, not tub height or clear slot height. |
| Slot side clearance | 1.0 mm per side | Left/right running clearance around the tub body. |
| Slot back clearance | 0.5 mm | Extra depth at the closed back. |
| Slot top clearance | 1.0 mm | Clearance above the tub. |
| Peg spacing | 190 mm | Target spacing; count and safe positions are derived. |
| Receiving bore | 8.45 mm | Preserves the successful prototype's receiving diameter. |
| Nominal insertion depth | 10 mm | Maximum peg-tip depth, shortened when the casing requires it. |
| Socket mouth / peg-end chamfer | 0.5 / 2.5 mm | Independent opening and peg-tip shapes. |
| Throat reduction | 1.0 mm diameter | Default through throat is 7.45 mm. |

The standalone casing keeps direct slot inputs and 25 mm prototype side/back defaults. Its slab also defaults to 3.0 mm. Both entry points use the same shell and bore implementation. `--help` is the complete option/range reference; explicit overrides such as `--riding-slab 1.3` remain supported. Existing output files and saved presets are not silently regenerated.

### Formulas

With default wall/rim geometry, stack overlap is 4.30 mm:

```text
tub width  = cells_x × 21 + 2 × tub wall
tub depth  = cells_y × 21 + 2 × tub wall
tub height = floor + bin_h × 3.5 + bin lip + stack gap + stack overlap

slot width  = tub width + 2 × side clearance
slot depth  = tub depth + back clearance
slot height = tub height + top clearance

casing width  = slot width + 2 × side wall
casing depth  = slot depth + back wall
casing height = riding slab + slot height
```

Integral and separate-grid floor modes have the same tub height. Wall/rim options also change the derived stacking overlap; 4.30 mm is the default, not a constant for every configuration.

Grid pockets stay open through the selected grid height, including the 8 mm maximum. The cavity and insert lofts include only transitions inside their actual vertical extent, preserving thick-floor and thick-wall overrides without folded surfaces or detached corner fragments.

| Default module | Tub body width × depth × height | Casing width × depth × height |
|---|---|---|
| 10 × 10 × 10h | 214.4 × 214.4 × 44.84 mm | 252.4 × 232.9 × 48.84 mm |
| Regular, 12 × 16 × 20h | 256.4 × 340.4 × 79.84 mm | 294.4 × 358.9 × 83.84 mm |

The pull guide projects from the tub front. Body dimensions above exclude that projection; mesh bounds include it. The full-size pull flange is 90 × 32.9 mm and scales down uniformly where the wall band or tub width is smaller. It is a drawer pull, not a carrying handle.

## Coordinates and stacking

| Axis / face | Meaning |
|---|---|
| X | Left/right across the drawer opening. |
| Y | Front/back travel; Y = 0 is the open front. |
| Print Z = 0 | Bed-facing slab; installed top of the casing. |
| Print Z = casing height | Wall feet; installed bottom of the casing. |

The wall feet of the upper installed casing rest on the top of the casing below. Pegs register those mating faces. The open front span has no sockets because it has no matching wall foot. There is no hidden bottom plate.

Socket centers stay within the flat side/back footprints. Placement uses the actual receiving bore, mouth chamfer and material land. Short axes use a single centered position when two mouths would overlap; wider spans divide the spacing evenly. The manifest's peg count comes from that same position set. Equal-footprint casings also need matching wall and peg-placement settings to stack together. Height alone does not change the XY pattern.

## Continuous peg bore and insertion stop

The shared cutter opens a passage through the entire wall height. It does not connect two blind sockets with an arbitrary smaller hole: that would let the chamfered nose travel beyond the intended stop.

For the default 19.6 mm peg and 10 mm maximum tip insertion:

1. Each face has an 8.45 mm receiving zone.
2. The full-diameter zone ends 7.5 mm from the face.
3. A 0.5 mm transition narrows to the 7.45 mm throat.
4. The nose enters the throat while its matching taper seats. The tip reaches 10 mm and leaves 9.6 mm of the peg exposed.

Two flush casing faces provide 20 mm total tip travel for the same 19.6 mm peg, retaining 0.4 mm axial allowance. Both ends are mirrored. The transition follows the actual peg-end chamfer, including the peg's minimum tip diameter; blunt pegs retain a stop too.

Short casings reduce insertion depth, peg length and effective end chamfer together. The cutter rejects a closed/non-positive throat, missing full-diameter receiver, or receivers that eliminate the central stop. The narrowing prints as a taper rather than a horizontal blind-hole roof.

Use `scad/testbed/through_peg_socket_testbed.scad` for the current bore. The whole coupon tests fit and insertion from both faces. The sectioned version shows the geometry but cannot establish retention after its wall is opened. The older blind-socket coupon is historical clearance evidence only.

## Casing wall core

`casing_core` (CLI `--casing-core`, form select, saved with the other design options) is one exclusive choice for how the side and back walls are built. `solid` is the default and is identical to earlier output. `webbed` models the walls as two flat skins, cross webs and solid pillars, open at the feet, so a print needs almost no slicer-generated interior fill and never bridges over it. `open-infill` is a named value for a later change: it is refused as not yet available at the form, the CLI and the SCAD entry, and is never built as another value. Nothing here is printed or validated; physical claims stay with the validation issues.

Webbed layout, all in multiples of one deposited road (default 1.4 mm; a selected process's outer wall line width, or its line width, when it gives one in millimetres):

- Skins, webs and the ring around each bore are two roads wide, so a member is two contour loops with no infill and every junction is a T. A pocket is at least three roads; a narrower gap, a wall too thin for a pocket, or a casing with under 8 mm of cavity is built solid.
- Each peg gets a pillar across the full wall thickness, reaching the larger of the receiver and mouth-chamfer radius plus the ring along the wall. The bores, chamfers and insertion stop are cut afterwards exactly as in the solid casing.
- Between pillars, a wall's pockets are the fewest equal pockets whose pocket plus web is at most 24 mm. The two side-wall corners where they meet the back wall, the front ends of the side walls and every exterior and slot-facing plane stay solid for one skin.
- Pockets are vertical prisms from the top of the riding slab to the feet and are open there. The slab is never hollowed. The pattern depends on plan dimensions only, never on height or slab thickness, so stacked casings with the same footprint put skin on skin and web on web.
- The manifest records the mode, pocket count, the solid share of the wall footprint at the feet (bores not counted) and the road with its source. Webbed guidance recommends 100% casing infill with a solid-compatible pattern; no option sets a zero-top-shell value. The assumptions shown beside the control, in `PRINTING.md` and in `print-settings.json` come from one table in `print_settings.py`.

## Print settings and generated output

Each module exports separate, oriented 3MF jobs plus a manifest and printing companions. Geometry-only output remains available without embedded process settings. Optional CLI/form import accepts one exported Orca process JSON and retains only supported explicit object-setting values.

Supported context includes layer height, selected line widths, infill, wall loops and shell settings. Native process exports may identify themselves with `print_settings_id` without a `type` key. Printer/filament bundles and G-code are not imported. Preset `inherits` is not resolved. Global first-layer height/width remain in the receiving slicer.

Part recommendations keep pegs/pulls solid and preserve solid coverage through the authored tub floor and casing slab. The optional crossing constraint selects a casing sparse-infill pattern explicitly; it is not imposed on every printer or part. No option silently enables a global zero-top-shell trial.

`PRINTING.md` and `print-settings.json` distinguish exact applied values, recommendations, inherited fields and orientations. The manifest records output hashes and source provenance. A build must finish and validate its output before replacing previous good files. Each generated part must be one connected, closed solid at its serialized mesh precision. Native slicer compatibility and physical process performance require their own evidence.

## Source and validation map

| File | Role |
|---|---|
| `hutchfinity.py` | CLI/local app, input validation, rendered-mesh checks, 3MF jobs and manifests. |
| `print_settings.py` | Explicit process import, per-part recommendations and printing guidance. |
| `scad/hutchfinity.scad` | Shared sizing and current generator entry point. |
| `scad/casing.scad` | Tub-agnostic shell, safe socket positions and continuous bore cutter. |
| `scad/casing_core.scad` | Webbed wall layout: pillar zones, pockets and their cutter. |
| `scad/tub.scad` | Authored tub, integral grid, removable insert and pull guide. |
| `scad/peg.scad`, `scad/knob.scad` | Peg and pull geometry. |
| `scad/hutchfinity-assembly.scad` | Current-source inspection layout. |
| `scad/testbed/casing_mouth_fit_gauge.scad` | Current-source shallow entry/ceiling check. |
| `scad/testbed/through_peg_socket_testbed.scad` | Current bore/stop physical-test coupon. |
| `scad/casing-fit-test.scad` | Current-source casing fit wrapper; size and design overrides match the generator. |
| `scad/testbed/peg_socket_fit_testbed.scad` | Historical blind-socket clearance sweep. |
| `scad/testbed/casing-fit-trial-01.md` | Historical trial identity and observations. |
| `scad/reference/thin-floor-rev05/` | Preserved older thin-floor reference model. |

### Reproducible checks

```bash
python3 -m unittest discover -s tests -v
python3 hutchfinity.py 10 10 10 --out preview/current-module
python3 hutchfinity.py 12 16 20 --floor separate-grid --out preview/current-module
openscad -o preview/through-peg-coupon.stl scad/testbed/through_peg_socket_testbed.scad
openscad -o preview/through-peg-section.stl -D SECTION=true scad/testbed/through_peg_socket_testbed.scad
openscad -o preview/casing-mouth-fit-gauge.stl scad/testbed/casing_mouth_fit_gauge.scad
```

Use current OpenSCAD with the Manifold backend for the production generator suite. Focused geometric tests may also run on CGAL. Create output directories before invoking OpenSCAD directly. Generated meshes are not versioned source.

Acceptance covers actual passage connectivity, receiver/throat dimensions, both insertion faces, real-peg collision at the stop, axial allowance, small-module socket separation, unchanged tub heights, complete peg counts, watertight output, option combinations and CLI/form/3MF behavior.

## Validation boundaries and historical evidence

The earlier small prototype slid correctly and its hex pegs fit, but its geometry differs from the present authored generator. The later 45.79 mm thin-floor tub and the retired 23u/84.24 mm tub are separate artifacts too. Their results do not validate the current 44.84 mm tub, 3 mm slab or continuous stop bore.

Physical acceptance still requires the whole coupon, a matching casing pair and the current tub: insertion/protrusion/removal, flush mating, slide clearance, bin seating, tub stacking, pull size/bond and representative slab stiffness. Keep printer/profile/artifact identity with observations. No load rating, long-term creep result or production qualification follows from CAD checks.

Magnet wells remain disabled in ordinary generated parts. Optional standalone magnet geometry is a provisional historical interface; its recipe and printability need separate validation. Do not resurrect old 5 mm tub recipes or change the held 6 mm recipe as part of casing-generator repairs.

Current correction sources: [casing slab and through bore](https://github.com/karyandrew/hutchfinity/issues/20#issuecomment-6842947338), [peg-stop direction](https://github.com/karyandrew/hutchfinity/issues/20#issuecomment-6567523789), and [generator print context](https://github.com/karyandrew/hutchfinity/issues/29#issuecomment-6842947591).
