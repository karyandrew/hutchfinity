---
sensitivity: public
version: 5.1.0
---

# Gridfinity System PRD — Dental Practice Organization

**Audience:** agents drafting and testing SCAD models for the dental gridfinity system. Read this before designing or modifying any tub / baseplate / bin config. It's the owner's north star — your work points at it.

This is a PRD, not an SOP. It captures intent. The inventory operating manual lives at [`kary-dental/docs/dental_office_inventory_guide.md`](https://github.com/karyandrew/kary-dental/blob/main/docs/dental_office_inventory_guide.md); category and material inventory by operatory specialty lives in the "Dental Armamentarium" gdoc (planned for ingest into kary-dental).

## What you're building

Three printable artifact types, all at Gridfinity Extended (half pitch — 21mm XY, 3.5mm Z) — a deliberate variant of stock Gridfinity, not interoperable with 42mm parts.

| Artifact | Role |
|---|---|
| **Tubs** (3 SKUs: mini, regular, mega) | Bounding containers that sit in operatory drawers or on shelves/counters. PETG. Implemented as 1×1 Gridfinity Extended cups at custom pitch — walls and lip live outside the cell grid. Same model printed in different colors per operatory specialty. |
| **Internal baseplates** (3 sizes, one per tub) | Vanilla Gridfinity grid plate (just a grid — no clips, no locks). Drops into a tub at standard 21mm pitch. Bins sit on it via standard Gridfinity foot pattern. |
| **Bins** | Standard Gridfinity cups at 21mm pitch with foot pattern. Mix-and-match across all tubs. Color-coded per inventory category. Staff-printable. |

## Hard requirements (owner-stated)

| # | Requirement | Rationale |
|---|---|---|
| HR-1 | **Tubs stack on each other** (drawer + shelf use). Lip of lower tub seats the flat base of upper tub. Stackability is per-pitch — same-size tubs stack; mixed sizes do not. | Drawer is primary; shelf storage is real and frequent. Without stackability the system breaks for shelf use. |
| HR-2 | **Bins sit on the baseplate via standard Gridfinity foot pattern.** No clip, no lock — gravity + foot fit. | Baseplate is a vanilla gridfinity grid. Standard part. Don't invent locking mechanisms. |
| HR-3 | **Tubs and bins are portable; bins mix-and-match across tubs.** | Same internal grid pitch (21mm) everywhere = bins move freely between any tub without re-fit. |
| HR-4 | **Constrained model catalog.** All tubs share Z and depth (Y); only width (X) varies — 3 SKUs total. Bin sizes drawn from a small standard set. Don't spawn a new model per quirk. | Production sanity, visual consistency, learnable system. |
| HR-5 | **Easy to print, cheap to replace.** Bins must be staff-printable on a Bambu (no manual supports, no exotic settings, predictable). PETG, normal layer heights, no orientation tricks. | Replacement is routine, not engineering. Staff is not Andrew. |
| HR-6 | **Items retrievable by finger or college plier.** Bin geometry must permit one-handed access during procedures. | Point-of-use clinical work. No tool-fetching to retrieve. |
| HR-7 | **Color codes the operatory specialty (tub) and inventory category (bin).** | Glance-to-find is the primary navigation system. Labels are SKU-level (required); color is category-level (convenience). |
| HR-8 | **Label-bearable surface on every bin.** Brother P-Touch labels (12mm or 24mm with QR) adhere to bin walls, floors, or undersides. | Item ID labels are required (line in inventory guide). No special label holders — use existing bin geometry surfaces. |
| HR-9 | **No captured crevices.** Tub, baseplate, and bins are independent pieces that separate cleanly for cleaning. | Clinical setting; biofilm and disinfectant residue trap in crevices. |
| HR-10 | **Single-piece tub at all standard sizes (≤500mm bed).** | Seams capture debris. SV08 MAX is 500×500×500mm; mega tub fits as one piece. |
| HR-11 | **PETG body** (tubs, baseplates, bins). Autoclavable parts (cassettes, bur blocks) are a separate workstream on X2D / PPA-GF — not this PRD. | PETG: tough, dishwasher-tolerant, printable on the fleet, cheap. Autoclave-grade is overkill for organizers. |
| HR-12 | **Walls and lip live outside the cell grid.** Tub internal cavity is exactly `N × 21mm` (X) × `M × 21mm` (Y) so the internal baseplate at standard 21mm pitch fits natively. | Inverts the v2.0.0 architecture (tub-as-scaled-bin); the baseplate seats into a cell-grid-sized cavity rather than a wall-eaten cavity. |
| HR-13 | **No magnet holes, no label holders, no scoops on any bin** — for the whole catalog lineage, including prototypes, until owner reverses. Labels adhere directly to bin geometry per HR-8. | Tactile cleanliness, print simplicity, fewer crevices. Reinforces HR-9 (no captured crevices) and HR-5 (staff-printable, predictable). |

## Color codes

Each operatory specialty maps to a color. Tubs are printed in that color; bins per category in that operatory may further encode item type (sub-color or hue variant — TBD).

| Color | Category | Mnemonic source |
|---|---|---|
| Green | Hygiene | Cavitron tip, mint toothpaste |
| Blue | Endo & IVS | Blu Core |
| Pink | Removable | Denture acrylic |
| Gray | Ortho | Brackets |
| Yellow | Restorative | Bonding agent |
| Orange | Fixed + Crown + Implant pros | Rely-X Universal; revised from Black to free Black for Records/Eval. Crown is the most common subset of Fixed → shares. Implant pros is fixed-prosth-on-implants → same logic, shares. |
| Black | Records/Eval | X-ray |
| Purple | Perio | (perio = purple by convention) |
| Red | Surgery / Exo | Bloody socket |
| Brown | General consumables | Weak alliteration ("Brown" / "Basic"). Brown items show up across many specialties — basic exam kit (mirror, explorer, cotton tweezers, 11/12 explorer), anesthesia carpules, chairside disposables (microbrushes, air/water tips). |
| (no specialty color) | Anesthesia & Sedation | Cart-level supply rather than a specialty workflow — staff goes to the cart, not the color. Default un-coded PETG. |
| N/A | Pedo, Cosmetic/Bleaching, Photography | Not in current practice scope. |

**Color rules:**
- **White is the wildcard** — allowed on any tub or bin, but **cannot be assigned to a specialty**. Assigning white to a category would break glance-to-find: any uncoded white piece would falsely signal that category. White means "nonspecific," everywhere.
- Orange / Yellow proximity is acceptable — Fixed and Restorative share a lot of workflow; confusing the two is harmless.
- Color stability is load-bearing — once staff learns "green = hygiene," reassigning the color burns trust. Color → category mapping changes go through Andrew, not the agent.

## Drawer compatibility

Tub catalog must serve this drawer set:

| Drawer | H × W × D interior (mm) | Plan | Slack W × D (mm) | H slack (mm) |
|---|---|---|---|---|
| Cart shallow | 74 × 318 × 419 | **excluded** (tub Z 84.2 > 74) | — | −10.2 |
| Cabinet narrow | 89 × 305 × 381 | 1× regular | 49.8 × 41.8 | 4.8 |
| **Cabinet med** (15"=381 wide; dominant) | 89 × 381 × 381 | 1× regular + 1× mini | **−3.4 × 41.8** (W interference; v5.0.0 marginal — physical drawer test gates validation) | 4.8 |
| Cabinet x-wide (24") | 89 × 610 × 381 | 1× mega + 1× mini *or* 2× regular | 99.6 × 41.8 (M+m) / 99.6 × 41.8 (2R) | 4.8 |
| Cart standard | 89 × 318 × 419 | 1× regular | 62.8 × 79.8 | 4.8 |
| Cart medium | 114 × 318 × 419 | 1× regular; items extend above tub | 62.8 × 79.8 | 29.8 |
| Cart deep | 140 × 318 × 419 | 1× regular; items extend above tub | 62.8 × 79.8 | 55.8 |
| Counter | TBD | 1× mega | TBD | TBD |

**Key principle:** items / bins may stick up above the tub Z. Tub height isn't sized to fill the drawer — only to retain bins, give structural rigidity, and provide the stacking lip. Bins are flexible (fast to reprint, waste OK). Tub catalog stays small (3 SKUs).

**Mini's two pairing roles:**
1. Alongside regular in cabinet med (binding constraint; pinned mini width to 5 cells in v3.x at W=2.625, bumped to 6 cells in v4.0.0 at W=1.6 — fit becomes marginal, gated on physical drawer test).
2. Alongside mega in cabinet x-wide.

## Architecture

Tubs are implemented as **1×1 Gridfinity Extended cups at custom pitch**, not as N×M bins. The cell-grid pitch (21mm) is unchanged; what changes per tub size is the cup's outer pitch.

```
pitch_xy = N × 21 + 2W + C   // C = library cup-outer clearance — see Tolerances
width = [1, 0]
depth = [1, 0]
height = [23, 0]              // body 23×3.5 = 80.5mm; sized so a 20h max bin's lip top
                              // does not exceed lower body top → upper tub bottom clears
                              // bin lip when tubs stack (see Vertical stack-fit section)
wall_thickness = W
floor_thickness = 1.2         // vendor default (was 3.5 in v3.x)
lip_style = "minimum"
flat_base = "gridfinity"      // stackable via lip on tubs of same pitch
```

Cavity (actual) = `pitch_xy − C − 2W` per library at `gridfinity_basic_cup.scad:798` (`container_width = num_x × pitch − clearance − 2 × wall_thickness`). With `pitch_xy = N × 21 + 2W + C`, cavity = `N × 21` exactly. Internal baseplate exterior renders at `N × 21` exactly — the library does NOT apply outer clearance to baseplates; the `clearance` parameter in `gridfinity_baseplate.scad` affects internal pocket sizing, not the outer envelope. Cavity and baseplate are the same `N × 21` dimension by construction; design clearance is zero. PETG dimensional variance (~±0.2mm typical) provides the natural play that lets the baseplate seat without binding.

Same-size tubs stack on each other (shared pitch_xy → matched lip pattern). Mixed-size tubs do not stack.

### Wall thickness

**W = 1.6mm** — vendor library auto-default for tubs at h≥16u (`gridfinity_basic_cup.scad:768`: `wall_thickness=0` → `1.6` when `num_z ≥ 16`). Set explicitly in `TUB_FLAGS` so the value is visible at the build call site.

Tubs aren't structural — they retain bins and provide the stacking lip. The prior v3.x value of 2.625mm (= 21/8 — "pitch elegance") was cosmetic, cost drawer slack, and ate print time without rigidity gain. Reversed in v4.0.0; the divisor framing is dropped. Cup walls are independently set by the cup library default of 1.2mm at h<16u; tubs and cups don't need to match.

Floor thickness `floor_thickness=1.2mm` follows the same logic — vendor `default_floor_thickness` (line 518). Prior 3.5mm "floor sandwich" was over-spec; thinner floor + same body height grows the cavity Z. Z is just `Nu body`, and cavity Z is whatever's left after `floor_thickness`. v5.0.0 sets body height to **23u** (was 21u in v4.x) — sized so a 20h max bin's lip top sits at or below the lower body top, allowing tub-on-tub stacking without the upper tub crashing into bin lips. See [Vertical stack-fit](#vertical-stack-fit-half-pitch-correction) for the geometry derivation.

## Stock Gridfinity baseplate compatibility

Half-pitch (21mm) cells preserve a real backward-compat surface to stock 42mm Gridfinity baseplates: **any 2×2-or-larger arrangement of half-pitch bins mates a stock 42mm baseplate** (verified in hand). 1×1 half-pitch bins do NOT — the half-scaled foot is too small for the stock pocket and rattles. Footprint commensurability (2 half-pitch cells = 1 stock cell) plus the library-canonical foot pattern is what makes the mate work.

This compatibility constrains foot/lip geometry choices going forward:

- **Slimmer half-pitch feet** would mitigate the half-pitch sandwich math (recovering ~7mm of tub Z by reducing the foot+lip+floor sandwich consumption) but **would also erode the stock-baseplate mate.** Foot-to-pocket lock relies on chamfer engagement, and chamfer geometry is foot-height-dependent — shorter foot = different chamfer profile = degraded engagement to stock pockets. The stock-baseplate compat is tested-and-valued, so slim-foot proposals are blocked unless the export-compat is explicitly waived.
- **Importing stock 42mm community designs** is independent of foot height — boolean surgery (strip stock foot, add half-pitch foot pattern) works regardless of slimming choices. Slim feet would only break the *export* direction (half-pitch arrangement → stock baseplate), not the import direction.

Considered and rejected: switching to 25mm pitch (Nested Tub System PRD 1.0.0 candidate, archived 2026-05-13 at [`docs/archive/nested-tub-system-prd.md`](archive/nested-tub-system-prd.md)). 25mm forfeits stock-baseplate mate entirely with no offsetting concrete benefit. Per-axis rationale at [`docs/archive/prd-decision.md`](archive/prd-decision.md).

## Tolerances

All multi-part fits are tracked here as named terms. PRD edits that change any tolerance update both this table and the architecture math, in the **same PR as the SCAD/STL change** they affect. Tribal knowledge ages out; the PRD is the contract.

| Term | Value | Where it lives | What it does |
|---|---|---|---|
| `C` (library cup-outer clearance) | 0.5mm total (= 0.25/side) | Library default, applied automatically to cup outer: lip extent = `pitch_xy − C`. Not a tunable knob in wrappers. | Spaces adjacent same-pitch tubs apart so 2× regular in cabinet x-wide sit with ~0.25mm/side between them. |
| Tub cavity ↔ baseplate | 0mm design clearance (snug; PETG variance is the slop) | Tub `pitch_xy` formula sets cavity = `N × 21` = baseplate exterior. | Baseplate seats on tub floor without rattle. Not a sliding fit — installed once. |
| Bin foot ↔ baseplate pocket | 0.5mm total (Gridfinity standard) | Library default in cup foot vs baseplate cell math. | Bins drop in/out of pockets one-handed. |
| Tub exterior ↔ drawer | per-drawer slack column in Drawer compatibility table (smallest = **−3.4mm interference**, cabinet med — v4.0.0 marginal, validates by physical print) | Drawer compatibility table. | Finger access; survives temperature/humidity expansion. |
| Tub stack mate | 0 (gridfinity foot ↔ lip is intentionally snug) | Library `flat_base = "gridfinity"`. | Two same-size tubs lock by foot/lip geometry, not by clearance. |

## Vertical stack-fit (half-pitch correction)

Standard gridfinity assumes "tub of N units holds bin of (N − 1) units" — at full pitch (1u = 7mm), the floor + bin foot + bin lip sandwich consumes ~1u of vertical space and the rule works. **At half-pitch (1u = 3.5mm) the lib does NOT scale the cupbase / lip / floor constants down**, so the sandwich consumes more than 1u and the rule breaks.

### Empirical geometry (mini tub, half-pitch)

Verified by spot-probing the rendered STLs at cell centers:

| Surface | Z (mm) | Notes |
|---|---|---|
| Tub foot pattern bottom | 0 | external |
| Tub foot pattern top | 4.75 | = `gf_cupbase_*_taper_height` sum (NOT `gf_base_grid_clearance_height`) |
| **Tub interior cavity floor** | **4.75** | floor sits on top of foot pattern; `floor_thickness=1.2` is in addition but is "inside" the body Z |
| Baseplate (sitting on cavity floor) | 4.75 → 8.75 | 4mm thick |
| **Bin Z=0 (= foot bottom)** | **4.75** | baseplate pocket is open through, so foot rests at pocket-bottom = baseplate bottom |
| Bin lip top | 4.75 + N×3.5 + 3.74 | lip = 3.74mm constant |
| Tub body top | N_tub × 3.5 | |
| Tub rim (= body top + lip) | N_tub × 3.5 + 3.74 | |

### Stack-fit invariant

When two same-size tubs stack, the upper tub's external bottom seats at the lower tub's body top (= `N_tub × 3.5`). For the upper tub bottom to NOT crash into bin lip tops in the lower tub:

```
bin lip top ≤ lower tub body top
4.75 + N_bin × 3.5 + 3.74 ≤ N_tub × 3.5
8.49 + N_bin × 3.5 ≤ N_tub × 3.5
N_bin ≤ N_tub − 2.43

→ rule (rounded for clearance):  N_bin ≤ N_tub − 3
```

So at half-pitch a **23h tub holds a 20h max bin** with 2.01mm clearance below the upper tub bottom when stacked. v4.x's 21h tub left a 20h bin protruding 2.96mm above the rim — broke HR-1.

### Off-by-one history

- Initial v5.0.0 attempt bumped 21h → 22h, but bin lip top still exceeded body top by 1.49mm. The half-pitch sandwich is ~3h, not the standard ~1h.
- Discovered by building an empirical assembly (tub + baseplate + bins + stacked upper tub) in OpenSCAD and bbox-probing each component's Z extent.
- Methodology: render each isolated piece (`probe-1h-lipnone.stl`, etc), spot-probe at cell centers via `intersection() { import(stl); cube at (X, Y, Z); }`, find the Z transition where solid → cavity.
- Closes [#146](https://github.com/karyandrew/3d-printing/issues/146).

## Tub catalog

Three SKUs. Identical Z and depth (Y); only width (X) varies.

| Tub | Cells (W × D × H) | pitch_xy (X × Y mm) | Cavity W × D (mm) | Cavity Z (mm) | Exterior W × D (mm) (= pitch_xy − C) | Total Z incl lip (mm) |
|---|---|---|---|---|---|---|
| Mini    | 6 × 16 × 23  | 129.7 × 339.7 | 126 × 336 | 79.3 | 129.2 × 339.2 | 84.2 |
| Regular | 12 × 16 × 23 | 255.7 × 339.7 | 252 × 336 | 79.3 | 255.2 × 339.2 | 84.2 |
| Mega    | 18 × 16 × 23 | 381.7 × 339.7 | 378 × 336 | 79.3 | 381.2 × 339.2 | 84.2 |

Mini bumped 5→6 cells X in v4.0.0; H bumped 21→23 in v5.0.0 (see Vertical stack-fit section).

Lip protrusion above body ≈ 3.74mm (constant — does NOT scale with pitch_z). Cavity Z = body − floor_thickness = 80.5 − 1.2 = 79.3mm.

| Param | Value (all 3 SKUs) |
|---|---|
| Pitch (cell grid) | 21 × 21 × 3.5mm |
| Wall thickness | 1.6mm (vendor h≥16 default) |
| Base | Flat (`flat_base="gridfinity"`) |
| Lip | `lip_style="minimum"` |
| Floor | 1.2mm (vendor default) |
| Material | PETG |
| Printer | SV08 MAX |
| Nozzle / layer | 0.6mm / 0.3mm |

## Baseplate specs

Three baseplates, one per tub size. Standard 21mm Gridfinity pitch. Exterior = `N × 21` exactly — library does NOT apply outer clearance to baseplates (`clearance` in `gridfinity_baseplate.scad` affects internal pocket sizing, not the outer envelope). Cavity = `N × 21` by construction (see Architecture); design clearance is zero.

| Baseplate | Cells (W × D) | Exterior W × D (mm) | Tub cavity | Design clearance |
|---|---|---|---|---|
| Mini    | 6 × 16  | 126 × 336 | 126 × 336 | 0 (snug) |
| Regular | 12 × 16 | 252 × 336 | 252 × 336 | 0 (snug) |
| Mega    | 18 × 16 | 378 × 336 | 378 × 336 | 0 (snug) |

All single-piece printable (largest = 378mm < SV08 500mm bed).

| Param | Value (all 3) |
|---|---|
| Pitch | 21 × 21mm (standard Gridfinity) |
| Z thickness | ~4mm |
| Pattern | Vanilla Gridfinity grid (through-pockets, one per cell) |
| Material | PETG |
| Printer | SV08 MAX, single piece |

No clips, no special locks. Baseplate sits in the tub bottom, bins drop in via foot pattern.

## Bin specs

Standard bin set — keep tight. Add only when inventory→bin mapping forces it.

| Param | Value |
|---|---|
| Pitch | 21 × 21 × 3.5mm |
| Base | Foot pattern (`flat_base="off"`) |
| Lip | `lip_style="minimum"` (note: reduced lip on small bins is a derived spec to preserve interior volume + finger access — not a separate requirement) |
| Compartments | Single (`divx=1, divy=1`) baseline; multi-compartment as inventory demands |
| Color | Per inventory category (see Color codes table) |
| Material | PETG (default) |
| Printer | Bambu (P1S mid-calibration / A1 limited / X2D for autoclavable category — separate) |
| Nozzle / layer | 0.4mm / 0.2mm |
| Print constraint | No manual supports. No orientation tricks. Predictable for staff to run. (HR-5) |

Two physical instances of each bin per item per operatory (front = active, back = reserve — 2-bin pattern from inventory guide).

**Foot-pattern gotcha (read before editing `dental/build-stl.sh`):** bins MUST use `flat_base="off"` (library default) so the cup gets N×M individual feet at the cell pitch and mates baseplate pockets. Do NOT copy `flat_base="gridfinity"` from `TUB_FLAGS` — that collapses the entire N×M footprint to ONE big pad (per `pad_copy` logic in `scad/gridfinity/vendor/extended/gridfinity_basic_cup.scad:7801`). The `gridfinity` value is only correct for tubs because tubs stack on each other lip-to-foot; bins sit IN baseplates. Tripped on first bin build (rebuilt as commit `eb24396`).

**HR-13 reminder (cross-reference):** no magnets, no label holders, no scoops on bins. `BIN_FLAGS` sets `enable_magnets=false`, `enable_screws=false`, `label_style="disabled"`, `fingerslide="none"` explicitly so the rule is visible at the build call site even though the library defaults already match.

## Owner success criteria

System works when all hold:

1. **Drawer fit.** Each tub size seats in its target drawer (per Drawer compatibility table). Closes and opens without binding. Finger-access clearance preserved.
2. **Stackability.** Two same-size tubs stack stably on a level surface; lift the upper tub from the lip without lower tub coming with it under <500g vertical force.
3. **Baseplate seat.** Baseplate sits flat on the tub floor with 0.25mm/side clearance; doesn't lift when bins are removed.
4. **Bin retrieval.** Items in any bin can be picked with a college plier or a finger; one-handed; no tools to extract the bin itself.
5. **Mix-and-match.** Bins move from any tub to any other tub and seat correctly without re-fitting.
6. **Staff-printable.** A trained assistant prints a replacement bin from STL → slicer → printer → done. No agent intervention.
7. **Glance-to-find.** Person who's seen the color legend once can locate the tub for a category in <3s on a shelf or in an open drawer.
8. **2-bin operatory pattern.** Empty back-position is visible at a glance; restock between patients.
9. **Subjective.** Team reaction is "holy shit this is sweet," not "what the fuck is this mess." Owner judges; agents don't override.
10. **Print-fleet validation gate.** [#66](https://github.com/karyandrew/3d-printing/issues/66) passed before production batch ([#68](https://github.com/karyandrew/3d-printing/issues/68)).

## Open items (do NOT silently decide)

When you hit one of these, surface as a blocker — don't pick.

| # | Item | Blocker |
|---|---|---|
| 1 | Bin sub-color within a tub (item type vs whole-tub-uniform) | UX question — owner |
| 2 | Standard bin size set (final) | Inventory→bin mapping; expected to evolve months 1–2 of practice operation per inventory guide |
| 3 | Bin printer assignment (P1S vs A1 vs X2D) | P1S calibration; potential P1S retirement |
| 4 | Counter-use megatub footprint (when counter dimensions need a bigger SKU than 18×16) | Counter measurement; current mega is locked to 18×16 for cabinet x-wide compatibility |

## Implementation guidance

**File paths:**
- Vendored library: `scad/gridfinity/vendor/<lib>/` + `VENDOR.md` (SHA + provenance)
- Dental build script: `scad/gridfinity/dental/build-stl.sh`
- Rendered STLs: `scad/gridfinity/stl/`
- Bins (when introduced): `scad/gridfinity/dental/bin-{X}x{Y}x{Z}.scad` — cells X × Y × cell-height Z. Build mechanism for bins is TBD (likely added as a second pass in `build-stl.sh` once bin work starts).

**Build pattern:** `dental/build-stl.sh` is a plain bash script that invokes the vendor combined file directly via `openscad -D <var>=<value>` flags. Project-level constants (wall thickness, lip style, floor thickness, chambers, magnets/screws) live in `TUB_FLAGS` / `BASEPLATE_FLAGS` arrays at the top of the script. Per-SKU params (pitch X for tubs; Width for baseplates) inline per invocation line. Adding a SKU = one new line. **Do not introduce per-SKU wrapper `.scad` files**; the WET wrapper pattern was the v3.0.0/v3.1.0 architecture and was retired in v3.2.0 (see Anti-patterns).

**STL naming:** `tub-{mini,regular,mega}.stl`, `baseplate-{mini,regular,mega}.stl`.

**Library:** Gridfinity Extended ([ostat/gridfinity_extended_openscad](https://github.com/ostat/gridfinity_extended_openscad)) at SHA `8b3a6c570c40ec1501ed61bc958835c06ffb7b8c`. **Don't change the library or the SHA without owner sign-off.**

**Toolchain:** OpenSCAD snapshot ≥ 2023.x (Extended uses trailing-comma syntax that 2021.01 stable rejects). Verified with 2026.04.26 snapshot.

**Each new SKU commit must include:**
- New invocation line in `dental/build-stl.sh`
- Rendered STL in `stl/`
- Bounding-box dimensional check vs spec (in PR description or commit message)
- OpenSCAD manifold check (`Status: NoError`, expected genus)
- One-PR-per-validation-gate for novel architectures; multiple SKUs may ship in one PR when they share architecture and differ only in param values (the v3.2.0 refactor PR shipped all 3 tubs + 3 baseplates because they're geometrically identical except for axis params).

## Anti-patterns

- Picking a different library or pitch.
- **Modeling tubs as scaled-up N×M bins** — walls eat the cell-grid cavity. Tubs are 1×1 cups at custom pitch; cell grid lives in the internal baseplate (HR-12).
- **Re-introducing per-SKU wrapper `.scad` files** when adding a SKU. The v3.0.0/v3.1.0 wrapper pattern was three near-identical files per family differing in 1–2 params; v3.2.0 retired it for `dental/build-stl.sh`. Add a line, not a file.
- Silently filling in an open item.
- Bundling tubs + baseplates + bins in one PR before the tub validates.
- Skipping pre-print validation (manifold, bounding box, visual).
- Adding a new tub size when an existing one almost works.
- Designing a special label holder. Use bin walls/floors/undersides.
- Inventing "clip" or "lock" mechanisms on the baseplate. It's just a grid.

## References

- Inventory operating system: [`kary-dental/docs/dental_office_inventory_guide.md`](https://github.com/karyandrew/kary-dental/blob/main/docs/dental_office_inventory_guide.md)
- Category and operatory armamentarium: "Dental Armamentarium" gdoc (planned for ingest)
- Design execution tracker: [3d-printing#105](https://github.com/karyandrew/3d-printing/issues/105)
- v3.0.0 architecture rewrite: [3d-printing#139](https://github.com/karyandrew/3d-printing/issues/139)
- v3.0.0 doc-cleanup precursor (folded in): [3d-printing#138](https://github.com/karyandrew/3d-printing/issues/138)
- Upstream ask: [kary-dental#52](https://github.com/karyandrew/kary-dental/issues/52)
- Library: [Gridfinity Extended](https://github.com/ostat/gridfinity_extended_openscad) (vendored at `scad/gridfinity/vendor/extended/`)
- Production gate: [3d-printing#66](https://github.com/karyandrew/3d-printing/issues/66) (validation sequence)
- Production batch: [3d-printing#68](https://github.com/karyandrew/3d-printing/issues/68)
- Printer fleet specs: [`docs/project-reference.md`](project-reference.md)
- Validation sequence: [`docs/validation-sequence.md`](validation-sequence.md)
- SV08 status: [`printer/sv08/handoff_state.md`](../printer/sv08/handoff_state.md)
- Sensitivity / HIPAA: bins do not store PHI. Patient data lives only in HIPAA-regulated systems per [`second-brain/.claude/rules/sensitivity.md`](https://github.com/karyandrew/second-brain/blob/main/.claude/rules/sensitivity.md).
- Autoclavable workstream (separate PRD): [3d-printing#61](https://github.com/karyandrew/3d-printing/issues/61), [3d-printing#122](https://github.com/karyandrew/3d-printing/issues/122)
