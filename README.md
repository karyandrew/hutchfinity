---
sensitivity: public
version: 1.0.0
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

## Why half-pitch

Gridfinity's standard pitch (42mm XY, 7mm Z) is too coarse for many small-parts organization use cases. The hutchfinity system uses **21mm XY / 3.5mm Z** — half of standard on each axis — for denser packing of small bins while preserving compatibility with standard gridfinity bin foot geometry. Bins printed for one pitch system can sit alongside bins printed for the other.

## Status

Pre-1.0. Architecture spec converged; SCAD and STL deliverables are being authored.

- **License**: GNU GPL v3.0 only; see `LICENSE` and `THIRD_PARTY_NOTICES.md`
- **Source**: OpenSCAD, built on top of [Gridfinity Extended OpenSCAD](https://github.com/ostat/gridfinity_extended_openscad)

## Credits

Gridfinity was created by **Zack Freedman** ([Hack Smith Industries](https://hackaday.io/project/180371-hack-smith-industries)). This project extends the gridfinity ecosystem; it isn't affiliated with the original creator.

## Contributing

Issues and PRs welcome.

## Repository map

- `wiki/` - evergreen implementation notes and validated recipes.
- `adr/` - architecture decision records.
