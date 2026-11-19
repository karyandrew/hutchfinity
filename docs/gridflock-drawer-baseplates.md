---
sensitivity: public
version: 1.0.0
---

# GridFlock — optional drawer-sized baseplates

[GridFlock](https://github.com/yawkat/GridFlock) is an **optional, externally maintained** OpenSCAD generator for drawer-sized Gridfinity baseplates. It can size a plate to a measured drawer, distribute leftover margins, split to a specified print bed, and connect segments with puzzle joints. It is **not vendored or required** by Hutchfinity's tub, cup, or separate-grid generator.

## Pinned upstream and rights

- GridFlock: `yawkat/GridFlock` at `6d7256ab1550e241f6b7ab23e0c83d3f05b04c8a`.
- Its Gridfinity Rebuilt submodule: `kennetek/gridfinity-rebuilt-openscad` at `910e22d8607fd7f5f51ad5e5cbc5287a76810bfd`.
- GridFlock's repository advertises MIT/CC BY 4.0 dual licensing, with separate CC BY content for certain optional openGrid models. Preserve all applicable upstream notices if source is ever redistributed or vendored.
- These are reference/pin records, **not a new Hutchfinity runtime dependency** or approval to replace the existing Gridfinity Extended baseplate geometry.

The [web generator](https://gridflock.yawk.at/) does not expose custom cell dimensions. In the OpenSCAD source, `BASEPLATE_DIMENSIONS=[21,21]` supplies *true* half-pitch socket spacing; it is different from GridFlock's default half-width **filler** mode on a 42 mm grid. The GridFlock maintainer warns custom pitches are not formally tested.

## Reproducible example: 15 × 20 cells on a 500 mm bed

Example assembly envelope: **317 × 422 mm**; full usable-cell field: **315 × 420 mm** (`15×21` by `20×21`), with nominal 1 mm edge padding on each side. One piece fits a nominal 500 × 500 mm printer bed, so no inter-segment joints are needed in this configuration.

Prerequisites: Git, [uv](https://docs.astral.sh/uv/) to generate the connector outline file, and a development build of [OpenSCAD](https://openscad.org/downloads.html) with the Manifold backend. The recorded render used OpenSCAD **2026.09.23**.

```sh
git clone --recurse-submodules https://github.com/yawkat/GridFlock.git
cd GridFlock
git checkout 6d7256ab1550e241f6b7ab23e0c83d3f05b04c8a
git submodule update --init --recursive
mkdir -p paths
uv run extract_paths.py puzzle.svg paths/puzzle.scad

openscad --backend=Manifold --export-format=binstl \
  -o gridflock-15x20-21mm.stl \
  -D 'BASEPLATE_DIMENSIONS=[21,21]' \
  -D 'plate_size=[317,422]' \
  -D 'bed_size=[500,500]' \
  -D 'magnets=false' \
  -D 'filler_x=0' -D 'filler_y=0' \
  -D 'numbering=false' \
  -D 'connector_intersection_puzzle=false' \
  -D 'connector_edge_puzzle=false' \
  gridflock.scad
```

To test socket engagement before committing to a large print, use the same command but change `plate_size=[42,42]` and the STL output filename. The resulting 2×2 coupon is four 21 mm pockets in a 42×42 mm plate. For a smaller print bed, enable the appropriate connector mode and validate a representative joint's fit and assembly. Do not scale the whole STL in the slicer to adjust drawer fit; that alters pocket pitch and engagement. Prefer measured `plate_size` and/or `edge_adjust`.

## Digital render evidence (2026-11-19)

Both renders used the pinned GridFlock and submodule revisions, the 2026.09.23 OpenSCAD snapshot, `--backend=Manifold`, and the switches above.

| Artifact | Verified mesh bounds (mm) | Facets | SHA-256 (binary STL) |
|---|---:|---:|---|
| 2×2 half-pitch test coupon | 42 × 42 × 4.65 | 1,964 | `5b4023702a57af001a01aed73c390f789f2a7386c688f409d58c3f79c1602681` |
| 15×20 drawer example | 317 × 422 × 4.65 | 131,112 | `3a314e31b3c5c266e74585e9071bf9c4679cf461750052f7022d8253e196ea08` |

OpenSCAD reported `Status: NoError` and a manifold object for both. This is **CAD-only evidence**, not a claim that the geometry is physically interchangeable with Hutchfinity's Gridfinity Extended sockets, that a particular drawer has enough clearance, or that a 317×422 mm print will remain flat and dimensionally accurate. Print the small coupon, check existing bin-foot seating and release, confirm the drawer's minimum width/depth, and inspect the slicer preview before the full print.

The STL outputs are reproducible build products, not checked into the Hutchfinity source repository.
