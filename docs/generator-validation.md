---
sensitivity: public
version: 1.0.0
---

# Generator 2.3.0 validation record

This record covers the casing-generator correction and the related export, grid and output-preservation defects found while exercising it. It establishes software and file-import results, not physical fit or print performance.

The correction follows the current [slab direction](https://github.com/karyandrew/hutchfinity/issues/20#issuecomment-6842947338), [continuous peg-stop direction](https://github.com/karyandrew/hutchfinity/issues/20#issuecomment-6567523789), and [optional print-context direction](https://github.com/karyandrew/hutchfinity/issues/29#issuecomment-6842947591). The dimensional contract is in [hutchfinity-spec.md](hutchfinity-spec.md).

## Source identity

The checked source was based on commit `80a1fadffeeec18899310bbf038df88eba5f0d1a`, with the correction applied. The generator's `source_inputs_sha256` was:

```text
583d6909c073d876caec51c0346cb47281b4929d49f83a40f31651cddcb88e48
```

This digest covers the generator, print-settings module and all SCAD inputs. The complete suite, final HTTP builds and native import/export checks used that same input digest. Documentation and test files are not inputs to the geometry digest.

## Automated suite

**58 tests passed, with no skips.** The full suite runs the actual Manifold renderer for its live geometry and generator checks.

| Test file | Checks | Coverage |
|---|---:|---|
| [test_casing_geometry.py](../tests/test_casing_geometry.py) | 17 | Independent slab/floor defaults; continuous passage and measured bore sections; real peg clearance and stop collision; axial allowance; 288 socket-placement combinations; small casings; current fit callers; production-matching coupon; thick-floor and tall-grid geometry. |
| [test_generator.py](../tests/test_generator.py) | 17 | Complete module outputs; both floors; standard dimensions; one scaled pull; supported option endpoints; smallest module; serialized mesh indices; cups and compartment/wall options; invalid requests. |
| [test_generator_safety.py](../tests/test_generator_safety.py) | 24 | Explicit process import; per-part settings and every accessory instance; geometry-only default; malformed input and meshes; output rollback and recovery; concurrent writers; provenance; CLI routing; safe update and listener handling. |

Reproduce with a Manifold-capable OpenSCAD build on the path, or selected with `OPENSCAD_BIN`:

```bash
python3 -m unittest discover -s tests -v
```

## Actual HTTP builds

The app's real request handlers completed these builds and the resulting files were inspected:

| Request | Result |
|---|---|
| 2 × 2 × 5h integral-grid module, no print options | Complete module; no embedded process settings; printing recommendations present. |
| Invalid machine-profile import over that existing output | Clear error; all previous output hashes preserved. |
| 2 × 2 × 5h separate-grid module, 4 mm walls, 3 mm floor, 8 mm grid, process JSON and crossing constraint | Complete module; correct floor/slab coverage, casing pattern and settings on every peg and pull; manifest file hashes matched. |
| 1 × 1 × 2h cup with process JSON | Complete cup and companions; selected layer-height setting retained. |

## Native Orca import/export

**Twelve generated jobs passed native OrcaSlicer 2.5.0 CLI import, mesh inspection and export.** Each individual part was reported manifold with one connected component. Every exported mesh's reported repair counters were zero. Instance counts and selected object settings survived the round trip.

| Cases | Files exercised |
|---|---|
| Six module jobs | Tub, casing and accessories for a 2 × 2 × 5h module, each with selected process settings and as a geometry-only control. |
| Four cup jobs | 1 × 1 × 2h; 2 × 4 × 10h; 2 × 4 × 10h with two compartments across; 2 × 2 × 40h. |
| Two separate grids | 4 × 4 at 4 mm tub walls; the same with a 3 mm floor and 8 mm grid. |

The settings checks covered casing TPMS-D and 3 mm bottom coverage, tub floor coverage, solid pegs and pull, object names, and every accessory instance. Geometry-only controls retained no object process overrides.

### Mesh export decision

Production rendering preserves OpenSCAD's indexed native 3MF topology. Converting through binary STL and welding rounded coordinates had damaged thin cup facets. The four repaired cup cases retain their original 2,014 / 6,364 / 6,506 / 3,876 facets after serialization.

Some native cup meshes contain coincident-coordinate or zero-area boundary triangles with distinct indices. The generator preserves those source faces: deleting them opens adjacent surfaces. The actual written files introduced no additional such faces and retained the same indexed closure, positive volume and single component. This follows the indexed-edge definition in the [3MF Core specification, section 4.1](https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md); it is not a claim that every source triangle has non-zero area.

## Remaining acceptance

The following have not been established by these checks:

- Interactive browser and slicer GUI workflows.
- Slicing, toolpath performance or physical printing.
- Whole-coupon insertion, removal and retention; flush mating of a matching casing pair.
- Current tub sliding, bin seating, tub stacking, pull bond and representative slab stiffness in printed parts.
- Bambu Studio compatibility, load ratings, long-term creep or production qualification.

The current whole peg coupon matches the generator's 32-facet bore. Its sectioned mode is a geometry illustration, not a retention test. The held magnet-recipe work remains separate; ordinary generated tubs and casings have no magnet wells.
