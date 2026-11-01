---
sensitivity: public
version: 2.0.0
---

# Neutral item-class selection

The selection contract maps generic geometry and handling needs to the existing half-pitch bin catalog. It deliberately separates two evidence levels:

1. Current-source geometry gives wall span, floor shape, and open-top height.
2. Independently trusted physical and lane evidence supplies actual load, retrieval, base-engagement, and handling evidence.

Only the second level can support `ACCEPTED`. The first remains `PROVISIONAL` even when every calculated margin is positive.

## Current catalog inventory

The catalog lists 22 bin sizes. No generated mesh is stored in the repository.

A bin is defined by its generator recipe: the size, the OpenSCAD definitions `hutchfinity.py` uses for it, the last commit touching the vendored cup source, and that source's SHA-256 hash. Physical-fit evidence applies to what the recipe generates, not to one stored file. A test builds all 22 bins with the generator and checks each against its catalog dimensions. A different OpenSCAD version can change a mesh without changing the recipe, so record the version with any physical test. Ranking uses a calculated material figure: outer volume minus wall-span volume.

The current official OpenSCAD snapshot parses and renders the unchanged source, so the historical OpenSCAD 2021 parser failure is obsolete.

For current 21 mm-pitch, minimum-lip bins, the source-derived dimensions are:

```text
wall thickness = 0.95 mm below 6h, 1.2 mm below 12h, otherwise 1.6 mm
wall span XY   = cells × 21 − 0.5 − 2 × wall thickness
floor height   = 5.7 mm
open-top Z     = height_units × 3.5 + 3.74 − 5.7
floor radius   = 3.75 − wall thickness
flat-floor span XY = wall span − 2 × floor radius
```

The wall span is larger than the conservative full-footprint span because the cavity has rounded floor edges. That distinction matters for rigid flat objects and prevents a mesh or wall bounding box from being presented as a fit oracle.

## Deterministic selection

For every allowed orientation, the selector:

- rotates item dimensions, uncertainty, and requested grab clearance together;
- forms a required envelope by adding dimension + uncertainty + clearance on each known axis;
- rejects negative wall-span margins and rounded-corner conflicts;
- applies minimum long-axis, unobstructed-top, quantity, and flat-floor constraints;
- treats missing axes and a wall-pass/floor-fail split as `inconclusive`;
- rejects unsupported compartment, visibility, and retrieval-mode requirements;
- ranks passing build-managed SKUs by footprint, then height, parsed material-volume proxy, and wasted source-derived volume; and
- reports one next sufficient candidate when one exists.

A negative margin is a failure, never a “tight” pass. `CUSTOM_SKU_REQUIRED` is emitted only when a fully dimensioned class has no passing current candidate and no named inconclusive physical-fit target.

The numeric uncertainty and clearance values in `item-classes.json` are public v1 selection-policy inputs, not physical measurements or private quantities. Changing one changes the item-class hash and invalidates receipts bound to the prior revision.

## Initial mapping result

| Neutral class | Preferred target | Fallback | Source result |
|---|---|---|---|
| `long-rod-178` | `bin-2x9x10h` | `bin-2x10x10h` | Inconclusive: long-axis margin is 2.8 mm after uncertainty and grab clearance; cross-section and Z are intentionally unknown. |
| `square-stack-49` | `bin-3x3x10h` | `bin-3x5x10h` | Calculated pass: wall margins 5.6 × 5.6 × 0.54 mm; conservative flat-floor XY margins 0.5 × 0.5 mm. |
| `short-roll-40x15` | `bin-2x4x10h` | `bin-2x5x10h` | Calculated pass: the 81.1 mm wall span satisfies the 80 mm long-axis constraint; conservative clearance-envelope capacities are 2 and 4. Desired private capacity remains external. |
| `flat-185x82x13` | `bin-5x9x5h` | none | Inconclusive: positive wall margins include 0.6 mm on the long axis, but conservative flat-floor long-axis margin is −5.0 mm. Physical sampling is mandatory. |

All four rows remain `PROVISIONAL`: no exact artifact/item-class physical fit was run. The two calculated passes are geometry/handling calculations, not physical acceptance.

## Software checks, physical evidence, and downstream demand

The CLI now schema-checks closed dataset wrappers, records, demand requests, and generated output with date-time format enforcement. It resolves mappings against the repository's authoritative class set and catalog, recomputes class hashes and selections, and verifies the current source bytes and generator recipes. A local physical-receipt claim is checked against the authoritative class envelope, minimum quantity, SKU, lane fields, six physical checks, and workaround prohibition.

Those checks prove software structure, source binding, and internal consistency only. Local caller-controlled JSON cannot prove that a sample was measured, an artifact was printed, a lane receipt came from an independent authority, or any physical check occurred. With no independently trusted physical/lane evidence configured, the CLI refuses every `ACCEPTED` claim and therefore refuses accepted-demand promotion. It does not create a signer or trust anchor from its own output.

The useful software residue is the closed neutral contract, authoritative binding, deterministic fit calculations, strict quantity/date handling, and fail-closed non-authorizing demand boundary. The remaining acceptance work is physical: preserve independently trusted lane evidence, print the exact artifact, bind a representative sample or surrogate, perform all fit and handling checks, and resolve the long-rod unknown axes and flat-object floor conflict. All four current mappings remain `PROVISIONAL/not_run`, and production authorization remains outside this interface.

## Local use

Use Python 3.10+ and `jsonschema` 4.x. The catalog is generated with
`python3 scripts/hutchfinity_catalog.py build-catalog --output catalog/bin-skus.json`.
Then run `select` with `--catalog catalog/bin-skus.json`,
`--classes catalog/item-classes.json`, and `--output catalog/item-class-map.json`.
Run the owned suite with `python3 -m unittest discover -s tests -v`.
