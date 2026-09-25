---
sensitivity: public
version: 1.2.0
---

# Baseplate tessellation investigation evidence

## Result boundary

The unchanged pinned vendor source was rendered for the declared 12-case matrix. The `fine` row passed the predeclared narrow sampled contact, topology, bounds, and cross-section datum checks for Mini, Regular, and Mega. Follow-up comparator diagnostics also cleared for sampled horizontal lands, adaptive Z sections, repeated-pocket samples, and stronger topology invariants. `bounded_surface_check_pass` nevertheless remains false. `fine` is **not accepted as a production contract**: the comparator is not an exact full-surface Hausdorff oracle, no volumetric minimum-wall analysis was performed, and no physical engagement was attempted. The exact-artifact physical gate in issue #37 remains required.

`medium` and `coarse` failed the predeclared contact and functional-datum limits for every artifact. File-size reduction did not override those failures.

## Immutable inputs

- Source commit: `fcd783e7a937c09fb32e1d5e248e91fe3092c481`
- Pinned vendor revision: `8b3a6c570c40ec1501ed61bc958835c06ffb7b8c`
- Pinned vendor source SHA-256: `675d73a6af4fe53d8e4c2de3c700d065698ff29b54f73fa671f6d5beab157fad`
- Current production build script SHA-256: `b081030822c869457d6239b13059f6f949b830f35cc3fcebd4d8db2a7e0fdb39`
- Matrix SHA-256: `b632d308fd2aa5a3be93e09667426285ed4268f27bae43f4846eebf334daae3a`
- OpenSCAD: `2026.09.23`, `x86_64`, explicit `Manifold` backend for all 12 renders
- OpenSCAD command wrapper SHA-256: `a8bd71cc2eb4c8a0d2a42c6735953d97c6f9f57b6e8275c798ad208e3a9191f1`
- OpenSCAD executable SHA-256: `cb643638df94177e50c5c6e2749f986a03395f503b3a0512448f5478ed9c194d`
- Complete run-manifest SHA-256: `b7d11bc9b0bdff7f50091591c49e5dc60891ac66d77c006e5245d31d2c7fdde6`

The manifest records `render_source_matches_vendor: true`; no assertion was disabled and no source substitution or syntax rewrite was used. Raw meshes and the complete manifest remain outside the repository.

## Effective tessellation trace

The active path is the top-level call through `set_environment` → `gridfinity_baseplate` → `baseplate` → `baseplate_regular` → `frame_plain`/`frame_cavity`. The combined source assigns `fa=6`, `fs=0.1`, and `fn=0` to `$fa`, `$fs`, and `$fn` before that call. `frame_cavity` invokes `pad_oversize`; its mating-pocket tapers and radii use inherited-fragment cylinders. `outer_baseplate` also uses inherited-fragment cylinders.

Because `$fn=0`, OpenSCAD derives fragment counts from both `$fa` and `$fs`; `$fa` alone is not the control. The render readback confirmed the exact `fs`, `fa`, and `fn` tuple for every matrix row. Fixed 64/128-fragment assignments exist in debug, optional, and unrelated helper paths, but the regular baseplate render left those paths disabled.

## Predeclared matrix and limits

The matrix was fixed before these renders:

| ID | `fn` | `fa` degrees | `fs` mm |
|---|---:|---:|---:|
| current | 0 | 6 | 0.10 |
| fine | 0 | 8 | 0.15 |
| medium | 0 | 12 | 0.20 |
| coarse | 0 | 16 | 0.30 |

The predeclared limits were: topology and component count preserved; exterior-datum delta at most 0.01mm; the observed contact maximum plus one 0.025mm sample spacing at most 0.05mm; sampled symmetric p99 at most 0.025mm; and functional/cross-section datum delta at most 0.01mm. The maximum-plus-spacing value is a conservative diagnostic, not a proven upper bound. Four cross-sections at Z 0.4, 1.4, 2.7, and 3.5mm measured opening, center, adjacent-pocket land, pitch, and contact depth for every pocket placement.

## Reproducible current baseline

`render_seconds` is OpenSCAD's reported rendering duration. It is a single-run observation, not a performance benchmark.

| Artifact | SHA-256 | Bytes | Facets | Components | Watertight | Bounds mm | Render seconds |
|---|---|---:|---:|---:|---|---|---:|
| Mini | `3e73db9a247e331dac00b8ed3bd12f8a4a08f1916224bea6a59b4fff65f1a058` | 12,747,945 | 49,788 | 1 | yes | `[-63,-168,0]` to `[63,168,4]` | 0.425 |
| Regular | `2a6efe8ee9eed103c07361514c66d14a1d781f2b2d4ac1d46cdbca32162b0f7c` | 25,422,483 | 99,324 | 1 | yes | `[-126,-168,0]` to `[126,168,4]` | 0.665 |
| Mega | `1428ac306badba381ab640b987584cc82319fe858cc9e9d1c2684f449880ce14` | 38,187,081 | 148,860 | 1 | yes | `[-189,-168,0]` to `[189,168,4]` | 0.957 |

The baseline facet counts and bounds match the tracked repository artifacts. Their byte hashes differ because those tracked files do not carry recoverable renderer provenance; only this run is the reproducible experiment baseline.

## Candidate measurements

All candidate meshes were one component and watertight. Reductions are measured against the same-class current baseline.

| Candidate | Artifact | SHA-256 | Bytes | Byte reduction | Facets | Facet reduction | Render seconds |
|---|---|---|---:|---:|---:|---:|---:|
| fine | Mini | `856964e9c2879198317086fceba871012b00b24deecd204b48496c29c89b0b52` | 11,915,398 | 6.53% | 45,884 | 7.84% | 0.326 |
| fine | Regular | `b931f1f9cc9c91c45a76408012cee3be635b222d107c79b09d777c04def8324a` | 23,757,144 | 6.55% | 91,580 | 7.80% | 0.647 |
| fine | Mega | `3b8dda3a7c0205b6ba606934b691df33d21acdf862705c3b91ea4c55a5203ad8` | 35,652,157 | 6.64% | 137,276 | 7.78% | 0.863 |
| medium | Mini | `0d99eb8bbcf1f6b6384853a59e13abada96854a1853624b92ac7c4f6bfbb7f6e` | 6,403,307 | 49.77% | 25,084 | 49.62% | 0.267 |
| medium | Regular | `86d1ef623b66fd249f4d7cfc3078dd04974d222a78ef515a84bf19185f963381` | 12,745,526 | 49.87% | 50,044 | 49.62% | 0.500 |
| medium | Mega | `b83e4ecc495b73cdc0b5f24f59856a46296700d55e63c39c5e1e30285c719505` | 19,131,654 | 49.90% | 75,004 | 49.61% | 0.704 |
| coarse | Mini | `3bc029ec89a762b5a47f9f9688c43eac1a1371afd1d449c1b0d3680d034bd904` | 6,249,485 | 50.98% | 24,292 | 51.21% | 0.289 |
| coarse | Regular | `ae11e421142be5d00a1485a7b9b767b7c0814edf445ed2465d2164aeed037edd` | 12,471,158 | 50.94% | 48,484 | 51.19% | 0.446 |
| coarse | Mega | `069103e0ae648bbd0b01e4932d59bc986da9cee71a7a3f8f78ab0ebb271d652f` | 18,728,921 | 50.95% | 72,676 | 51.18% | 0.688 |

## Sampled contact and functional results

Values were identical across Mini, Regular, and Mega to displayed precision. Placement cross-section datum variation was below `6.4e-14`mm in every baseline/candidate class, so no size-dependent datum corruption was observed by this oracle.

| Candidate | Sampled max mm | Max + spacing diagnostic mm | Symmetric p99 mm | Max functional datum delta mm | Max exterior bound delta mm | Narrow sampled/datum result |
|---|---:|---:|---:|---:|---:|---|
| fine | 0.0173514 | 0.0423514 | 0.0108395 | 0.00913481 | 0.00913481 | clears for all three classes |
| medium | 0.0384015 | 0.0634015 | 0.0384015 | 0.0356625 | 0.0205429 | does not clear for any class |
| coarse | 0.0657476 | 0.0907476 | 0.0452389 | 0.0349277 | 0.0349277 | does not clear for any class |

The baseline adjacent-pocket land widths at the four sections were 5.08, 4.30, 4.08, and 2.48mm. The `fine` section openings/lands differed by no more than the 0.00913481mm aggregate functional-datum limit, preserved the 0–4mm contact-depth range, and had maximum computed pitch error below `1.5e-14`mm. These are cross-section measurements, not a volumetric minimum-wall guarantee.

The original comparator isolates inward-facing, non-horizontal `pad_oversize` walls, samples every unique edge contour at 0.025mm spacing plus triangle centroids for one canonical pocket, and evaluates section datums at every placement. This is actual but finite mating-surface evidence. It remains inconclusive for full-surface equivalence because it is neither an exact Hausdorff computation nor an independently validated volumetric oracle.

### Follow-up comparator diagnostics

The unchanged canonical meshes were reanalyzed without altering the canonical render manifest. The repaired comparator:

- samples horizontal interface-adjacent lands in a clipped pocket-local window;
- samples 45 sections inside every wall Z slab, with no adjacent section spacing above 0.1mm;
- checks every repeated wall placement by fixed-section datums and vertex/centroid distance while retaining `identity_proved: false`; and
- strengthens topology preservation from component/watertight booleans to consistent orientation, Euler characteristic, and genus.

| Candidate | Horizontal sampled max mm | Adaptive-Z sampled datum max mm | Enhanced sampled diagnostics |
|---|---:|---:|---|
| fine | 0.00794120 | 0.00913481 | clears for all three classes |
| medium | 0.0178586 | 0.0381440 | does not clear for any class |
| coarse | 0.0303638 | 0.0349277 | does not clear for any class |

For `fine`, maximum within-row repeated-pocket vertex/centroid deviation was below `7e-10`mm across all placements. This supports “no sampled size-dependent corruption observed,” not exact pocket identity. The full meshes preserve genus 96, 192, and 288 for Mini, Regular, and Mega respectively across every row. These follow-up diagnostics are implementation evidence only: continuous all-Z/full-surface and volumetric equivalence remain unknown.

## Exact checks

| Check | Result |
|---|---|
| Kickoff packet validator | PASS — operator-stated requirement, full body receipt, `comments_state: none`, learned/applied governing records |
| `bash -n experiments/baseplate-tessellation/run.sh` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest experiments/baseplate-tessellation/test_mesh_audit.py` | PASS — 9 tests, including known pass/fail comparison, contact partition, horizontal sampling, all-Z spacing, repeated pockets, topology orientation, manifest assembly, and timing rejection |
| Complete matrix | PASS — 12/12 renders and audits; 9/9 comparisons; all exit 0 |
| Enhanced retained-mesh comparison | PASS — 9/9 executed; `fine` clears the enhanced sampled diagnostics, `medium`/`coarse` do not, and all retain `bounded_surface_check_pass: false` |
| Vendor immutability | PASS — render-source hash equals pinned source hash |
| Backend consistency | PASS — explicit Manifold backend for every baseline/candidate render |
| OpenSCAD diagnostics | PASS — all 12 report manifold `Status: NoError`; no assertion was disabled |
| Second clean rerun | PASS — all 12 output hashes matched the first complete run |
| Production build isolation | PASS — production SCAD, STL, and build script are unchanged |

## Acceptance reconciliation

| Criterion | Status | Evidence or residue |
|---|---|---|
| Current baseline records all three classes reproducibly | MET | Version, architecture, backend, source/tool hashes, artifact hashes, bytes, facets, components, watertightness, exact bounds, and render durations are recorded. |
| Effective tessellation control established | MET | Active inherited `$fn/$fa/$fs` path is traced and read back; fixed-fragment exceptions are bounded. |
| Matrix and tolerances declared before selection | MET | Four rows and numerical limits predated the official render run. |
| Accepted candidate preserves topology, datums, and contact surface | PARTIAL | `fine` clears the narrow and enhanced sampled diagnostics, including stronger topology invariants. Full-surface and volumetric equivalence remain unknown, so no candidate is accepted. |
| Baseplate-only build flags explicit; tub/bin fidelity unchanged | PARTIAL | The isolated runner provides an explicit baseplate-only contract. Production flags remain unchanged pending acceptance, so tub/bin behavior is untouched. |
| Measured reductions reported without a precommitted claim | MET | Per-artifact byte, facet, and single-run render measurements are recorded for all candidates. |
| Current documentation records the per-class contract | PARTIAL | The experiment contract and results are current; no candidate has cleared the gates required for a production contract. |
| Representative physical engagement passes and #37 gate remains | NOT MET | No physical operation occurred. Exact-artifact representative engagement and production validation remain in issue #37. |
