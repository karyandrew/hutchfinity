---
sensitivity: public
version: 2.5.0
---

# hutchfinity

A parametric, modular drawer chest system built around gridfinity-extended tubs at **half-pitch**.

## What

- **Tubs** = drawer pans, sized in cells (X × Y × Z) at user-chosen pitch
- **Casings** = single-piece enclosures that house one tub each; back + sides + top, no bottom, no front
- **Pegs** = press-fit dowels that link stacked casings vertically
- **Knobs** = optional glue-on pulls with broad, thin glue bases
- **Magnets** = an optional retention/detent variant requiring separate validation; ordinary generated parts have no magnet wells

Tubs slide drawer-style on the top of the casing below (or on a footer / tabletop for the bottom-most). Casings with the same footprint, wall and peg-placement settings stack vertically; their heights can differ. Multi-column chest assembly is a v2 goal.

Generated casings have a **3.0 mm riding slab** by default; the tub floor remains **1.30 mm**. Peg holes run continuously through the casing walls, with full-size receiving zones at both faces and a narrower central throat to limit insertion. The new stop geometry is a CAD candidate pending physical coupon validation.

## Make parts

Install Python and a current [OpenSCAD build with the Manifold backend](https://openscad.org/downloads.html), then run `python3 hutchfinity.py`. Set `OPENSCAD_BIN` if the intended build is not on your path. The generator checks renderer support before building; the older OpenSCAD 2021 release is not supported by this generator.

Pick a size in the page that opens. One folder per module is saved to `~/Downloads/hutchfinity`:

- `1-tub.3mf`, `2-casing.3mf`, and `3-pegs-and-pull.3mf`;
- `4-grid.3mf` when the grid is separate;
- `PRINTING.md`, `print-settings.json`, and `manifest.json`.

Each 3MF is one print job, already oriented. With no print options selected, it contains plain geometry and uses your receiving slicer's settings. The companions still explain orientation, solid pegs/pulls and solid floor/slab coverage. Builds are staged and checked before replacing earlier successful output, and concurrent writers to the same output root are refused.

- `python3 hutchfinity.py 10 10 10 --stack-gap 0.8` does the same from a terminal. `--help` lists every option and its allowed range. Every run builds one tub, one casing, its pegs and one pull. Tubs hold at least a 5h bin.
- `python3 hutchfinity.py cup 2 4 10 --across 2` builds one cup, also from the app, into a `cups` folder. It takes cells wide, cells deep, height in 3.5 mm units, compartments and wall.
- `python3 hutchfinity.py module 10 10 10` is an explicit alias for the module command.
- `python3 hutchfinity.py --install-shortcut` adds a clickable `Hutchfinity.app` to a Mac's Desktop. Automatic updates only run from a clean `main` checkout.
- The manifest records the generator version, source commit, whether local changes were present, source-input hashes and output hashes.

### Optional print settings

Choose one exported **Orca process JSON** in the form, or pass it on the command line:

```bash
python3 hutchfinity.py 10 10 10 --process-profile process.json
python3 hutchfinity.py 10 10 10 --process-profile process.json --avoid-crossings
python3 hutchfinity.py cup 2 4 10 --across 2 --process-profile process.json
python3 hutchfinity.py 10 10 10 --plain-3mf
```

Only supported explicit object settings are copied. Preset inheritance is not resolved; printer, filament, first-layer settings, temperatures, speeds and G-code remain in the receiving slicer. The printing companions show what was applied and what is inherited. Per-part overrides keep pegs/pulls solid and cover the authored tub floor and casing slab. `--avoid-crossings` explicitly selects TPMS-D for casing sparse infill and leaves its density selected or inherited.

`--casing-core webbed` (or the form's casing wall core select) builds the casing side and back walls as two flat skins with cross webs and solid pillars around every peg bore, open at the feet, instead of solid walls. `--casing-core open-infill` keeps the casing body identical to solid and prints it with top surfaces off, so the slicer's infill shows where a top skin would have been. The generator adds setting regions to the casing job (a solid slab plate and a solid block around every peg bore, with top shells off for the casing only); they are written as modifier parts of one casing object and are never printed material. They need embedded print settings (a process JSON or the crossing option): with plain geometry output the file is the solid casing and the guide lists the settings and region positions to set up by hand. `solid` is the default. Neither option is print-proven; the printing guide states what each assumes of the slicer.

`--plain-3mf` applies no overrides and cannot be combined with a process profile or crossing override. If you launch the app without dimensions, choose design and print settings in the form; supplying those options without dimensions is rejected instead of silently ignoring them.

Settings-bearing files target OrcaSlicer. Import them as a project when you want the object settings retained, and inspect the resulting slice. Bambu Studio is a separate compatibility target; a Bambu printer used through Orca is not the same import path. See the generated printing guide for the exact validation scope.

## Verify a change

```bash
python3 -m unittest discover -s tests -v
```

The suite renders actual geometry and exercises generator output. The [system spec](docs/hutchfinity-spec.md) describes the shared casing implementation, dimensions, through-bore stop and current physical-test coupon. The [validation record](docs/generator-validation.md) lists the checked source, test coverage and native-import results. Physical fit and load performance remain separate from CAD and file-format checks.

## Why half-pitch

Gridfinity's standard pitch (42mm XY, 7mm Z) is too coarse for many small-parts organization use cases. The hutchfinity system uses **21mm XY / 3.5mm Z** — half of standard on each axis — for denser packing of small bins while preserving compatibility with standard gridfinity bin foot geometry. Bins printed for one pitch system can sit alongside bins printed for the other.

## Status

Pre-1.0. Architecture spec converged; SCAD source and the generator are being authored. Meshes are generated, never versioned.

- **License**: GNU GPL v3.0 only; see `LICENSE` and `THIRD_PARTY_NOTICES.md`
- **Source**: OpenSCAD, built on top of [Gridfinity Extended OpenSCAD](https://github.com/ostat/gridfinity_extended_openscad)

## Credits

Gridfinity was created by **Zack Freedman** ([Hack Smith Industries](https://hackaday.io/project/180371-hack-smith-industries)). This project extends the gridfinity ecosystem; it isn't affiliated with the original creator.

## Contributing

Issues and PRs welcome.

## Repository map

- `wiki/` - evergreen implementation notes and validated recipes.
- `adr/` - architecture decision records.
