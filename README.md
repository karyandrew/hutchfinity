---
sensitivity: public
version: 2.1.0
---

# hutchfinity

A parametric, modular drawer chest system built around gridfinity-extended tubs at **half-pitch**.

## What

- **Tubs** = drawer pans, sized in cells (X × Y × Z) at user-chosen pitch
- **Casings** = single-piece enclosures that house one tub each; back + sides + top, no bottom, no front
- **Pegs** = press-fit dowels that link stacked casings vertically
- **Knobs** = optional glue-on pulls with broad, thin glue bases
- **Magnets** = optional press-fit retention + extended-warning detent

Tubs slide drawer-style on the top of the casing below (or on a footer / tabletop for the bottom-most). Casings stack into chests of arbitrary height. Same flat casing footprint = stackable; varying heights are fine. Multi-column chest assembly is a v2 goal.

## Make parts

With Python and [OpenSCAD](https://openscad.org) installed, run `python3 hutchfinity.py`. Pick a size in the page that opens, and it saves one folder per module to `~/Downloads/hutchfinity`: `1-tub.3mf`, `2-casing.3mf`, `3-pegs-and-pull.3mf`, a `4-grid.3mf` if the grid is separate, and a `manifest.json`. Each 3MF is one print job, already oriented, that opens directly in OrcaSlicer with your active profile.

- `python3 hutchfinity.py 10 10 10 --stack-gap 0.8` does the same from a terminal. `--help` lists every option and its allowed range. Every run builds one tub, one casing, its pegs and one pull. Tubs hold at least a 5h bin.
- `python3 hutchfinity.py cup 2 4 10 --across 2` builds one cup, also from the app, into a `cups` folder. It takes cells wide, cells deep, height in 3.5 mm units, compartments and wall.
- `python3 hutchfinity.py --install-shortcut` adds a clickable `Hutchfinity.app` to a Mac's Desktop. It updates itself from `main` when opened.
- The generator's version is `VERSION` in `hutchfinity.py`, and each output's `manifest.json` records that version and the source commit.

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
