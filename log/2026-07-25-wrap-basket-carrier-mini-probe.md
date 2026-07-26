---
sensitivity: public
date: 2026-07-25
branch: codex/basket-carrier-mini-probe
pr: https://github.com/karyandrew/hutchfinity/pull/27
issue: https://github.com/karyandrew/hutchfinity/issues/26
---

# Wrap: Mini Basket/Carrier comparison probe

## Summary

Completed the CAD-only Mini Basket/Carrier comparison slice from issue #26. The change vendors the pinned MIT-licensed Gridfinity Basket source, adds a general half-pitch parameterized probe with plain, integral-grid, and removable-grid modes, and records reproducible comparisons against the current Mini tub. The evidence supports keeping the candidate as a parallel experimental module rather than subsuming the existing tub. PR #27 merged the work into `main`; physical printing and live-device work were deliberately excluded and remain future validation.

## Knowledge enumeration

| # | Category | Item | Durable artifact |
|---|---|---|---|
| 1 | Geometry comparison | With matched parameters, the candidate and current Mini tub share a `130.40 × 340.40 × 84.24 mm` envelope and approximately 98.5% volumetric intersection-over-union. | `scad/testbed/basket-carrier-mini-probe.md` |
| 2 | Datum clarification | Center-floor probes put the usable cavity spans within `0.003059 mm`; the older `79.30 mm` figure uses a different measurement convention and is not a like-for-like cavity datum. | `scad/testbed/basket-carrier-mini-probe.md` |
| 3 | Interface finding | The removable grid still has `6.370681 mm³` of direct intersection after a `0.01 mm` lift, exposing unresolved zero-clearance XY boundaries that need an intentional clearance contract. | `scad/testbed/basket-carrier-mini-probe.md` |
| 4 | Product direction | The candidate should remain a parallel experimental Basket/Carrier module until physical fit, handling, and removable-grid behavior are validated. | `scad/testbed/basket-carrier-mini-probe.md` |
| 5 | Reproduction pattern | Vendoring the pinned upstream source and rendering the plain candidate through the adapter produces a mesh identical to the directly rendered pinned source. | `scad/gridfinity/vendor/basket/VENDOR.md`; `scad/testbed/build-basket-carrier-mini-probe.sh` |

## V&V

Planned acceptance criteria came from issue #26's “Acceptance for this slice” section and its pre-implementation first execution slice.

Verification:

- The pinned upstream source and MIT license match the recorded upstream revision byte-for-byte.
- `bash -n scad/testbed/build-basket-carrier-mini-probe.sh` passed.
- `scad/testbed/build-basket-carrier-mini-probe.sh` rendered every comparison artifact and ended with `Verification gates passed`.
- The build asserted the matched Mini envelope, cavity floors, stack witness, casing witness, magnet variants, removable-grid evidence, and a non-Mini parameter smoke case.
- `git diff --check` and the staged diff check passed.
- A public-safety scan found no personal names, local paths, private-repository references, device context, or provider-specific workflow text.
- An independent Codex review rechecked the corrected cavity comparison and returned PASS.

Validation:

- The CAD slice answers its decision question: preserve the Basket/Carrier candidate as a parallel experiment rather than replacing the current tub.
- The representative Mini evidence is reproducible from source and identifies the removable-grid clearance question instead of hiding it.
- Physical printing was outside the authorized slice, so issue #26 remains open for that validation and any later adoption decision.

Post-hoc audit:

- PR #27 merged into `main` as `d15d1f0806f62351136273b246e58979e9da331e`.
- Issue #26 remains open.
- The implementation worktree was clean after merge.
- No printer or live device was contacted.

## Step matrix

✅ Upstream provenance: pinned source, MIT license, and vendor metadata preserved
✅ Candidate source: general parameterized Basket/Carrier probe added
✅ Mode boundary: plain, integral-grid, and removable-grid directions exposed
✅ Comparison evidence: envelope, cavity, magnets, rim, floor, stack, and casing recorded
✅ Reproduction: full OpenSCAD comparison build passed
✅ Public safety: committed surfaces reviewed and clean
✅ Independent review: Codex-only final review passed
✅ PR #27: merged to `main`
⏭️ Issue #26 closure: N/A — physical validation and final adoption remain open
⏭️ Printer/device work: N/A — explicitly outside scope
✅ Wrap log: `log/2026-07-25-wrap-basket-carrier-mini-probe.md`
⏭️ Worktree teardown: external after task exit

## Verdict

Safe to close · ✅ Complete

The authorized CAD-only Mini comparison slice is complete. The broader issue remains open at its explicit physical-validation boundary.
