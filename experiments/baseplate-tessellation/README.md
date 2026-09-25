---
sensitivity: public
version: 1.3.0
---

# Baseplate tessellation experiment

This directory contains a baseplate-only experiment. It does not alter the normal tub, bin, or baseplate build and does not establish physical or production fit.

## Effective current control

The pinned combined vendor source declares `fa=6`, `fs=0.1`, and `fn=0`, then assigns those values to `$fa`, `$fs`, and `$fn` before the top-level baseplate call. The pocket chamfers and corner radii in `frame_cavity`, `pad_oversize`, and `outer_baseplate` inherit the special variables. Positive `$fn` overrides the adaptive controls. With `$fn=0`, a full circle uses `ceil(max(min(360/$fa, 2*pi*r/$fs), 5))` fragments, so changing `$fa` alone is not a complete contract: either the angle or segment-length term can be active for a given radius. Some optional/debug helpers force 64 or 128 fragments; the experiment records that they are not evidence of a single global effective value.

## Predeclared matrix and limits

`matrix.tsv` is fixed before render measurement:

| ID | `fn` | `fa` (degrees) | `fs` (mm) |
|---|---:|---:|---:|
| current | 0 | 6 | 0.10 |
| fine | 0 | 8 | 0.15 |
| medium | 0 | 12 | 0.20 |
| coarse | 0 | 16 | 0.30 |

The matrix keeps `fn=0` so both adaptive constraints remain active and varies both limiting inputs. A candidate clears the narrow sampled contact/datum check only when all three classes satisfy:

- component count, watertight edge incidence, consistent orientation, Euler characteristic, and genus unchanged;
- exact overall bounds differ by no more than 0.01mm on any exterior datum;
- observed pocket-wall maximum plus one 0.025mm sample spacing no more than 0.05mm;
- symmetric sampled p99 pocket-wall deviation no more than 0.025mm; and
- no cross-section datum difference over 0.01mm among any pocket placements.

The 0.05mm maximum budget reserves 80% of the nominal 0.25mm per-side foot clearance for manufacturing and process effects. It is a conservative experiment budget, not a claim about printer capability. The 0.025mm p99 limit prevents a candidate from consuming the entire synthetic budget across most of the interface. Sloped and vertical `pad_oversize` pocket walls are isolated by cell-relative extent and inward face orientation, then measured independently of overall bounds. Four fixed cross-sections measure pocket pitch, depth range, opening, and land thickness across every placement. A second diagnostic samples inside every Z slab with no spacing above 0.1mm, and a separately clipped diagnostic samples interface-adjacent horizontal lands. Repetition analysis checks every wall placement by cross-section datums and vertex/centroid surface distance while explicitly leaving exact identity unproved.

The local comparator samples every unique mating-wall edge contour at 0.025mm spacing plus triangle centroids. Adding one spacing to the observed maximum is a conservative diagnostic threshold, not a certified geometric upper bound. The finite horizontal samples and adaptive Z sections improve coverage but do not prove the unsampled continuum or a volumetric minimum wall/land. Consequently `bounded_surface_check_pass` remains false, `surface_acceptance` remains `INCONCLUSIVE`, and volumetric acceptance remains `UNKNOWN` even when the narrower diagnostics pass. A production candidate needs a valid full-surface and volumetric oracle in addition to the physical gate.

## Run

Use an OpenSCAD snapshot compatible with the pinned vendor source and write results outside the repository:

```sh
OUTPUT_DIRECTORY=baseplate-tessellation-run
OPENSCAD_BIN=openscad experiments/baseplate-tessellation/run.sh "$OUTPUT_DIRECTORY"
```

The runner renders Mini, Regular, and Mega for every row from one commit and toolchain, records hashes and mesh audits, then compares each candidate with `current`. It explicitly selects the `Manifold` backend for every row and records that choice in the manifest; `OPENSCAD_BACKEND` may select another backend only for a separate complete run. The output directory must be empty. It exits before producing evidence if OpenSCAD is unavailable, preserves every attempted case and exit code in `cases.tsv`, and does not create `run.json` for an incomplete matrix. Each render defaults to a 900-second limit and each audit/comparison to 300 seconds; override them with `RENDER_TIMEOUT_SECONDS` and `COMPARE_TIMEOUT_SECONDS`. The pinned vendor source requires an OpenSCAD 2023-or-newer snapshot, as recorded in its vendor metadata. `render_seconds` is OpenSCAD's own reported rendering duration; `process_wall_seconds` is a secondary process observation and becomes `null` if the host clock yields an impossible negative value. Timing should be repeated on the same host before drawing performance conclusions.

The comparison reports the observed symmetric contour maximum and p99, plus a clearly named `sampled_max_plus_spacing_diagnostic_mm`. It hashes contact triangulations for diagnostic purposes and measures cross-section datums and sampled geometry across every pocket placement; triangulation hashes may differ when a CSG exporter splits the same surface differently. The stronger topology result also checks orientation, Euler characteristic, and genus. These remain synthetic sampled diagnostics and deliberately do not claim exact repeated-pocket identity, continuous full-surface equivalence, volumetric equivalence, or physical fit.

## Acceptance boundary

Do not copy a matrix row into the production build merely because this experiment passes. Selection requires complete numerical output, review of the representative pocket sections, and the existing representative physical-engagement gate. Production use remains separately gated by the exact artifact and printer/profile validation lane.
