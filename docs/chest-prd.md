---
sensitivity: public
version: 1.4.0
---

# Hutchfinity Chest PRD

**Audience:** agents and contributors drafting the Hutchfinity chest SCAD modules. Read this before designing or modifying `tub.scad`, `casing.scad`, `knob.scad`, or `peg.scad`.

This is a PRD, not a build guide. It captures the product contract for the modular drawer chest architecture. Implementation details that are still under physical validation are called out as open dependencies, not silently decided here.

## What you're building

Hutchfinity is a parametric, modular drawer chest system built around Gridfinity Extended at half pitch: 21mm XY and 3.5mm Z by default.

The system has four authored SCAD parts plus the underlying grid library:

| Part | Role |
|---|---|
| `tub.scad` | Drawer pan. Parametric on grid cell count and pitch. Slides in and out of a casing. |
| `casing.scad` | One-slot enclosure: back, sides, and top only. No bottom and no front. Stacks vertically. |
| `knob.scad` | Optional glue-on pull for the tub front. Kept separate so tubs remain backward-compatible. |
| `peg.scad` | Press-fit dowel that registers and retains vertically stacked casings. |
| Gridfinity Extended | Source geometry for half-pitch grid conventions and tub/bin compatibility. |

A single drawer slot is one tub plus one casing, with an optional knob. Chests gain height by stacking casing modules vertically, not by adding a `drawer_count` parameter to one monolithic model.

## Hard requirements

| # | Requirement | Rationale |
|---|---|---|
| HR-1 | **One drawer slot is one module.** The module consists of one tub plus one casing; knob is optional. | Keeps the system composable. Users can print, replace, and rearrange one slot at a time. |
| HR-2 | **Multiplicity comes from stacking, not a drawer-count parameter.** | A single parametric casing stays simple; tall chests are assemblies, not special-case models. |
| HR-3 | **Casing has back, sides, and top only.** No bottom, no front. | No front means there is an opening for the drawer. No bottom keeps the model simpler to print and lets each drawer ride on the top of the casing below, footer, or tabletop. |
| HR-4 | **Casing prints inverted with the top on the bed.** | Sides and back rise as vertical perimeters; the model should avoid bridges and manual supports. |
| HR-5 | **The bottom-most drawer can ride on a footer or tabletop.** Footer/base behavior is outside `casing.scad`. | Keeps the casing module a single supportless shell while leaving bottom support and robot-vacuum clearance to assembly-level design. |
| HR-6 | **Tub geometry remains compatible with the existing tub catalog.** The lip stays; optional magnet wells and glue-on knob bases must not break stacking or basic tub use. | Hutchfinity should extend tubs into drawers without making every tub a one-off chest-only part. |
| HR-7 | **Sliding interface is tub-on-casing-top.** Each tub rides on the top of the casing below; the bottom tub rides on the footer top or tabletop. | No rails, tracks, or drawer hardware in v1. |
| HR-8 | **Drawers are fully removable.** No pull-out stop in v1. | Clean removal is simpler, easier to print, and easier to inspect. |
| HR-9 | **Pegs register and retain vertical casing stacks.** Side-by-side and multi-column linking are v2. | v1 solves vertical chest assembly first. Lateral assemblies add another fit problem and should not block the single-column chest. |
| HR-10 | **Magnets provide closed retention and an extended-warning detent.** Magnet wells must not protrude into tub storage volume or interfere with mating surfaces. | Drawers should feel intentional in the closed position and warn before accidental over-extension. |
| HR-11 | **Press-fit dimensions are provisional until physical validation lands.** Use the current crush-rib testbed and magnet wiki as the live recipe source. | Trial-01 was PHATTY-process evidence; standard-settings validation is still pending. |
| HR-12 | **All XY dimensions derive from tub cell count and pitch.** | Parametric source stays the contract; manually tuned outer dimensions are drift magnets. |
| HR-13 | **v1 is general-purpose.** No domain-specific assumptions, labels, colors, storage categories, or workflow content belong in the chest architecture. | This repo is public OSS and the chest is a general organizer system. |
| HR-14 | **Back and side exterior faces stay flat.** No external stack pads, lugs, bosses, ribs, lands, or other protrusions on the casing sides or back. | Flat sides/back keep modules visually clean, easy to place against each other or other objects, and true to the simple shell architecture. Stack registration must be solved without changing the exterior side/back planes. |

## Architecture

### Module stack

Each drawer slot is a casing with a matching tub and optional knob:

```
top casing
  tub rides on top surface of casing below
middle casing
  tub rides on top surface of casing below
bottom casing
  tub rides on footer top or tabletop
footer or tabletop
```

Casings with the same XY footprint stack vertically. Heights may vary as long as the peg/socket pattern and tub clearance remain compatible.

### Casing

The casing is a single-piece inverted print:

- Top face on the build plate.
- Back and side walls print as vertical perimeters.
- Back and side exterior faces remain flat planes.
- No bottom face.
- No front face.
- Peg interface reference points are reserved for vertical stacking; final socket geometry remains testbed-gated and must not add side/back protrusions.
- Magnet wells for the tub above are reserved, but their casing-side orientation is an implementation risk: blind wells opening on the final top surface may conflict with top-on-bed printing. Validate whether they print cleanly as bed-side features, move the wells to an insert/post-process operation, or revise the casing orientation before locking `casing.scad`.

The inverted orientation is part of the product contract. If an implementation requires support material or bridges for the casing shell, it is violating the v1 intent.

### Footer

Footer/base behavior is outside `casing.scad`. The bottom drawer can ride on a tabletop, a future footer, or a future base/riser, but the casing module does not expose footer mode, footer threshold, or robot-vacuum policy parameters.

Default robot-vacuum clearance remains an assembly-level heuristic, not a casing rule. The current design assumption is a robot-vacuum navigation envelope around 450mm: roughly a 350mm round vacuum plus about 50mm of side clearance. Treat that as a heuristic comment in assembly/base design, not a fixed casing standard.

### Tub

The tub is the drawer pan. v1 tub requirements:

- Parametric on grid cell count and pitch.
- Retains the existing lip.
- Can receive optional magnet wells inside the existing foot envelope.
- Can receive an optional glue-on knob base.
- Does not require rails, rollers, or extra slide hardware.
- Remains useful as a tub outside the chest.

The available foot-envelope budget for tub magnets is about 4.75mm Z. The magnet design must not touch the 1.2mm floor above that envelope.

### Knob

The knob is a separate glue-on pull. It uses a broad, thin, flared base so it can be glued to the tub front without making the tub geometry chest-only.

v1 does not require snap-on or fastened knobs. Those can be future variants if glue-on knobs fail in use.

### Pegs

Pegs are mass-printable dowels for vertical casing stacks:

- Press-fit is the v1 target.
- Slip-fit plus glue is rejected for v1 because it gives weaker reversible registration.
- Snap-fit pegs are deferred.
- Pegs register and retain casing-to-casing stacking.
- Side-by-side casing linking is out of scope for v1.
- Compliant male geometry is an explicit exploration path: crush ribs, hollow/concave profiles, star-like polygons, or other shapes that make the peg deform more tolerantly than a solid cylinder.
- Candidate peg shapes should be validated in the print orientation that best preserves lengthwise strength and compliant fit. The current prototype prints laid down, then installs vertically as a stack connector.

Peg dimensions should use the same press-fit discipline as magnets: testbed first, then lock the recipe.

## Magnet and crush-rib requirements

Magnets are optional hardware, but the architecture reserves for them:

| Magnet role | Location | Intended function |
|---|---|---|
| Tub magnet array | Tub foot envelope | Moves with the drawer. |
| Casing closed-position array | Top of casing below | Retains the drawer closed. |
| Casing extended-warning array | Top of casing below, about 75% extended | Gives tactile warning before full removal. |

The current magnet sizes in use are:

| Size | Intended location | Status |
|---|---|---|
| 5x1mm disc | Tub foot wells | Pending standard-settings validation. |
| 6x1.5mm disc | Casing arrays | Tentative PHATTY result exists; standard-settings validation still required. |

Current non-dimensional crush-rib constraints:

| Parameter | Current direction |
|---|---|
| Rib count | 8 axial ribs |
| Rib spacing | 45 degrees |
| Rib pattern | Bore-minus-notch, so plate material protrudes inward |
| Chamfer | 0.3mm lead-in |
| Well depth | Prefer shy over proud; deeper wells are safer than protruding magnets |

Dimensional recipe authority lives in `wiki/magnet-press-fit.md` and the active crush-rib testbed. Do not use the older 3-rib recipe or the old `part OD + 0.1mm` / `part thickness + 0.1mm` dimensions as final chest requirements. Trial-01 showed that PHATTY settings distorted shallow wells and small bores enough to make that recipe unreliable.

## Parameters

| Parameter | Meaning | v1 guidance |
|---|---|---|
| `slot_width`, `slot_depth`, `slot_height` | Casing enclosed slot size | Direct casing inputs. Assembly may derive them from a tub, but `casing.scad` stays tub-agnostic. |
| `side_thickness`, `back_thickness`, `top_thickness` | Casing shell thicknesses | Implementation values TBD; must print cleanly and resist normal drawer use. There is no bottom thickness. |
| `peg_spacing` | Vertical stack reference spacing | Single casing input; peg count is derived by indexing corners and evenly dividing each side. |
| `pitch_xy`, `pitch_z`, `cells_x`, `cells_y`, `cells_z` | Tub/assembly grid sizing | Default 21mm XY and 3.5mm Z remain system conventions, but they are not casing-module arguments. |
| Tub-to-slot clearance | Assembly clearance from tub exterior to casing slot | Assembly/tub-fit concern, not a casing-module argument. |
| `peg_profile`, `peg_diameter`, `peg_clearance` | Peg press-fit recipe | TBD by testbed/prototype; include compliant male profiles, not just solid cylinders. |
| `magnet_small`, `magnet_standard` | Disc magnet sizes | 5x1mm and 6x1.5mm currently available. |
| `magnet_recipe` | Bore, depth, and rib geometry | Provisional until trial-02 standard-settings validation. |
| `detent_position` | Extended-warning magnet position | Assembly/interface value; tune by prototype. |

## Out of scope for v1

| Item | Reason |
|---|---|
| Multi-column chest assembly | Side-by-side casing linking adds lateral registration and tolerance problems. Defer to v2. |
| Snap-fit pegs | Press-fit dowels are the simpler validation path. |
| Pull-out tilt stop | Drawers intentionally come out cleanly in v1. |
| Rail, slide, bearing, or roller hardware | Tub-on-casing-top sliding is the v1 mechanism. |
| External stack lands, pads, bosses, lugs, or ribs on casing sides/back | Violates the flat side/back casing requirement. |
| Domain-specific layouts, labels, colors, or workflows | Hutchfinity is a general-purpose public OSS system. |
| Final magnet and peg press-fit dimensions | Physical validation is still open. |

## Open dependencies

| Dependency | Effect on this PRD |
|---|---|
| Magnet crush-rib trial-02 | Locks or revises the provisional magnet well and rib recipe. |
| Casing-side magnet well printability | Decides whether casing wells can be blind bed-side features, need post-processing/inserts, or require a casing orientation revision. |
| Peg press-fit validation | Locks peg/socket dimensions and peg profile. Shape candidates should include compliant male geometry such as crush ribs, hollow/concave sections, and star-like polygons. |
| Tub XY formula updates | May change casing and array placement if the tub formula changes. |
| License decision | Required before release packaging and external contribution expectations are final. |

## Owner success criteria

System works when all hold:

1. **Single-slot printability.** A casing prints inverted without supports, bridging surprises, or fragile unsupported features.
2. **Drawer fit.** A matching tub slides in and out by hand without binding under ordinary FDM variance.
3. **Drawer retention.** Closed-position magnets hold the tub closed under normal handling but do not make the drawer annoying to open.
4. **Extended warning.** The detent near 75% extension is noticeable before full drawer removal.
5. **Full removal.** The drawer can be removed cleanly without tools.
6. **Vertical stack.** Two or more casings with the same XY footprint stack squarely using pegs.
7. **Footer behavior.** The bottom drawer rides cleanly on a footer or tabletop without needing a special bottom casing.
8. **Tub compatibility.** A tub with optional chest features remains usable as a normal tub and does not lose its lip/stacking behavior.
9. **General-purpose presentation.** The public repo describes a modular organizer system, not a private deployment context.
10. **Validation honesty.** Pending press-fit dimensions stay marked provisional until the physical test data exists.

## Implementation guidance

- Keep authored modules to `tub.scad`, `casing.scad`, `knob.scad`, and `peg.scad`.
- Do not add `drawer_count` to `casing.scad`.
- Keep magnet and peg recipes named and centralized so testbed results can update them without hunting through geometry.
- Keep `casing.scad` tub-agnostic; use `hutchfinity-assembly.scad` for fit previews that place casing beside tubs, knobs, pegs, or future footer/base geometry.
- Put hardcoded heuristic values behind named parameters and comments.
- Render and inspect single-slot prototypes before generating tall assemblies.
- Validate one casing/tub/peg/magnet combination before scaling to multiple heights or footprints.

## Anti-patterns

- Monolithic multi-drawer chest models.
- Hidden bottom plates in the casing.
- Front rails or captured drawer hardware in v1.
- External stack pads, lands, lugs, bosses, or ribs that break flat casing sides/back.
- Stale crush-rib dimensions copied from old issue text after newer trial data exists.
- Public docs that cite private planning sources or domain-specific deployment context.
- Adding lateral multi-column linking while the single-column vertical stack is still unvalidated.

## References

- `README.md` - project overview and public status.
- `wiki/magnet-press-fit.md` - current magnet press-fit recipe and trial status.
- `scad/testbed/trial-log-01.md` - PHATTY-process crush-rib trial data.
- `hutchfinity#2` - chest PRD issue.
- `hutchfinity#7` - crush-rib testbed iteration 2.
- `hutchfinity PR #13` - open draft PR for testbed v1.4.0 and trial-02 scaffold.
