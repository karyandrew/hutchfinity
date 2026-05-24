# hutchfinity

A parametric, modular drawer chest system built around gridfinity-extended tubs at **half-pitch**.

## What

- **Tubs** = drawer pans, sized in cells (X × Y × Z) at user-chosen pitch
- **Casings** = single-piece enclosures that house one tub each; back + sides + top, no bottom, no front
- **Pegs** = press-fit dowels that link stacked casings vertically
- **Handles** = optional glue-on pulls
- **Magnets** = optional press-fit retention + extended-warning detent

Tubs slide drawer-style on the top of the casing below (or on a footer / tabletop for the bottom-most). Casings stack into chests of arbitrary height. Same XY footprint = stackable; varying heights are fine. Multi-column chest assembly is a v2 goal.

## Why half-pitch

Gridfinity's standard pitch (42mm XY, 7mm Z) is too coarse for many small-parts organization use cases. The hutchfinity system uses **21mm XY / 3.5mm Z** — half of standard on each axis — for denser packing of small bins while preserving compatibility with standard gridfinity bin foot geometry. Bins printed for one pitch system can sit alongside bins printed for the other.

## Status

Pre-1.0. Architecture spec converged; SCAD and STL deliverables are being authored.

- **License**: see open issue (pending decision)
- **Source**: OpenSCAD, built on top of [vector76/gridfinity-extended](https://github.com/vector76/gridfinity-extended_openscad)

## Credits

Gridfinity was created by **Zack Freedman** ([Hack Smith Industries](https://hackaday.io/project/180371-hack-smith-industries)). This project extends the gridfinity ecosystem; it isn't affiliated with the original creator.

## Contributing

Issues welcome. PRs welcome once LICENSE lands.
