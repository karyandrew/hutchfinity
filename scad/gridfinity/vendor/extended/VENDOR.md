---
sensitivity: public
---

# Vendored: Gridfinity Extended

- **Upstream:** https://github.com/ostat/gridfinity_extended_openscad
- **Pinned SHA:** `8b3a6c570c40ec1501ed61bc958835c06ffb7b8c` (2026-02-27)
- **License:** GNU GPL v3.0 (see `LICENSE`)

Files retained: `combined/gridfinity_basic_cup.scad`, `combined/gridfinity_baseplate.scad`. The `combined/` variants are auto-generated single-file builds — self-contained, no module path setup required.

GPL-3.0 is copyleft. Published derivative SCAD configs that include or build on these vendored files need to preserve the upstream license terms and notices.

## Toolchain

Requires OpenSCAD snapshot build (2023.x or newer) — Extended uses trailing commas in argument lists, which the 2021.01 stable parser rejects. Tested with OpenSCAD 2026.04.26 snapshot.

## Re-pin

Fetch the same two `combined/` files at the new upstream SHA, update this file.
