---
sensitivity: public
version: 0.1.1
---

# Hutchfinity deterministic source packet

This packet contains two geometry-authoritative OpenSCAD source renders for issue #32: a square single-slot hero and a portrait single-slot exploded view. Product geometry is frozen to commit `29273ab21605eba859088c18fd1bc50087d86709`. The presentation callers import the authored modules; they do not copy or alter casing, tub, knob, peg, magnet-well, or committed STL geometry.

## Product-truth ledger

| Product truth | Pinned authority | Packet consequence |
|---|---|---|
| One drawer slot is one casing plus one tub; the knob is separate and optional. | `docs/chest-prd.md` HR-1 and the pinned module files | Both scenes contain one casing and one regular tub. This packet includes one separate glue-on knob. |
| The casing has back, sides, and top only—no front and no bottom. | `docs/chest-prd.md` HR-3; `docs/hutchfinity-spec.md` casing contract | The caller imports `hutchfinity_casing()` unchanged. A front or bottom request is a hard reject. |
| The tub rides on the support below and remains fully removable. | `docs/chest-prd.md` HR-5, HR-7, and HR-8 | The hero shows the tub partially extended, with no rails, rollers, captured slide hardware, or pull-out stop. |
| Same-footprint casings stack vertically with pegs. | `docs/chest-prd.md` HR-9; `docs/hutchfinity-spec.md` provisional interfaces | The exploded scene includes all seven pegs derived by the pinned casing position functions. |
| Tubs remain independently usable and retain their lip. | `docs/chest-prd.md` HR-6 | The caller imports the committed lipped regular-tub STL through `hutchfinity_regular_tub()`. |
| Side and back casing exterior planes remain flat. | `docs/chest-prd.md` HR-14 | No external lands, pads, bosses, lugs, or decorative additions are introduced. |
| Current dimensions, arrays, sockets, clearances, and assembly coordinates come from pinned source. | `docs/hutchfinity-spec.md`; pinned SCAD modules | Presentation code transforms whole parts only. It applies no deformation and requires `PRODUCT_SCALE=1`. |
| The product remains pre-1.0 and some physical interfaces remain provisional. | `README.md`; `docs/chest-prd.md` HR-11; `docs/hutchfinity-spec.md`; archived fit observations | Packet readiness is `CONDITIONAL`; these images are concept/prototype source renders, not proof of final physical fit or durability. |

## Scene contract

`single-slot-hero` contains one casing, one regular tub extended 150 mm while still engaged, and one knob in its intended assembled orientation. `single-slot-exploded` contains the same casing, tub, and knob plus seven authoritative pegs. Exploded displacement uses translation only after placing each whole part in its intended installed orientation.

Colors are presentation colors, not semantic masks or product color requirements. The render background is opaque and clean. The PNGs contain no text, arrows, dimensions, legend, labels, or branding.

## Allowed downstream transformations

- Replace the background or environment.
- Change lighting, shadow, photographic finish, and benign surface appearance.
- Apply presentation polish that leaves silhouette, openings, part inventory, dimensions, clearances, interfaces, and relative positions inspectably intact.
- Add exact copy, arrows, labels, dimensions, legends, or branding later with a deterministic compositor outside these source pixels.

## Hard rejects

- Redrawing the product from prose or substituting geometry from outside the pinned commit.
- Adding or deleting parts, a casing front or bottom, rails, rollers, captured slide hardware, a pull-out stop, or a monolithic multi-drawer body.
- Rotating, scaling, deforming, or changing casing/tub geometry, drawer count, openings, clearances, magnet/peg features, or assembly relationships.
- Breaking the casing's flat side or back planes.
- Treating draft or uncommitted geometry as current product source.
- Baking generated text, labels, dimensions, arrows, logos, or exact copy into the source raster.
- Representing a provisional interface as physically proven.

## Reproduction and verification

Use OpenSCAD `2026.09.23`, then run:

```sh
OPENSCAD=openscad ./scripts/render-presentation-packet.sh
python3 ./scripts/test_presentation_packet_negative.py --openscad openscad
```

The renderer exports the exact pinned commit into an owned temporary tree, overlays only the presentation callers, renders both PNGs, and verifies the pin, consumed blobs, exact render-dependency allowlists, scene inventories, geometry summaries, minimum image margins, output dimensions, and output hashes before replacing checked outputs. The negative suite makes real front, bottom, and rail mesh changes and proves each changed geometry summary is rejected. The manifest records camera inputs and resolved camera values, transforms, colors, output digests, image bounds, and the complete consumed-blob ledger.

## Claim boundary

Classification: `CONDITIONAL`.

The packet is mechanically complete for a source-preservation experiment. It does not claim that magnet wells, peg/socket fit, drawer fit at full product scale, glue durability, or proposed future tub floor modes are physically final. It does not authorize an image-model call or publication of a downstream generated result.
