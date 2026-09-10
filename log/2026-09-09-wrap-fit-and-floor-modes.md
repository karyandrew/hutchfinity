---
type: log
sensitivity: public
date: 2026-09-09
status: shelved
branch: chatgpt/wrap-2026-09-09-fit-and-floor-modes
issues:
  - https://github.com/karyandrew/hutchfinity/issues/20
  - https://github.com/karyandrew/hutchfinity/issues/29
  - https://github.com/karyandrew/hutchfinity/issues/30
---

# Wrap: Hutchfinity fit, magnet, and low-floor experiments

## Summary

This session preserved three connected prototype results without promoting untested conversation-generated geometry into production source.

The 10×10×10h tub slid successfully in its matching direct-parametric casing, the current hex pegs fit well, and magnetic attraction across the assembled interface was good. The glue-on pull remains a drawer pull; its long-term bond is untested, and the selected alignment aid is a shallow outline immediately outside the flange.

The dual-face magnet matrix failed as a transferable production recipe. Most long-rib candidates on the fine-profile print were too tight, while every new long-rib candidate on the coarse high-flow print had clearance and was far too loose. The unchanged 8B control remained the best coarse-process result, but one fine-profile control was itself too tight. The next bounded experiment is a plain round-bore dual-face coupon, not another rib-count search.

The Regular tub direction is now a thin mostly-flat floor, a shorter shell that preserves the existing clearance above the tallest intended inserts, and three floor modes: plain, integral grid, and a plain tub with a removable open-bottom grid. The removable insert keeps printable sloped perimeter rail ends while removing only unsupported bridging membranes. A current integral-grid slice was reported at approximately 3.5 hours versus approximately 5.5 hours for the former tub-plus-separate-grid workflow, with less filament and less handling.

No production SCAD or STL was committed in this wrap. Draft PR #31 remains unmerged because the current eight-rib magnet recipe is not yet a satisfactory cross-process production fit.

## Knowledge enumeration

| # | Category | Preserved result or decision | Durable record |
|---:|---|---|---|
| 1 | Physical fit | The 10×10×10h tub slides in its matching casing; the current hex pegs fit well. Validation is limited to the small prototype. | [Issue #20 physical-result comment](https://github.com/karyandrew/hutchfinity/issues/20#issuecomment-5612514760) |
| 2 | Pull alignment | Keep the broad glue-on pull flange and add a shallow outline immediately outside it; do not place a raised pad under the bond. Long-term bond durability remains unknown. | [Issue #20 physical-result comment](https://github.com/karyandrew/hutchfinity/issues/20#issuecomment-5612514760) |
| 3 | Magnet matrix | Fine-profile candidates were mostly too tight; coarse high-flow candidates all had clearance and were far too loose. The failed coarse candidates did not contact the magnet, so compliance does not explain that result. | [Issue #30 matrix-result comment](https://github.com/karyandrew/hutchfinity/issues/30#issuecomment-5612522876) |
| 4 | Magnet control | Magnets seat fully at 2.30 mm depth and attraction is good, but one fine-profile 8B control was too tight and insertion friction is marginally excessive. | [Issue #30 matrix-result comment](https://github.com/karyandrew/hutchfinity/issues/30#issuecomment-5612522876) |
| 5 | Next magnet experiment | Use one dual-face plain round-bore coupon sweeping 5.90–6.30 mm in 0.05 mm increments, plus unchanged 8B; retain 2.30 mm depth and 0.30 mm lead-in. Select the largest bore that reliably retains across intended processes. | [Issue #30 matrix-result comment](https://github.com/karyandrew/hutchfinity/issues/30#issuecomment-5612522876) |
| 6 | Regular tub architecture | Preserve approximately 2.2 mm structural walls, use a thin mostly-flat floor with only local stacking-foot accommodation, and shorten the shell rather than preserving unused Z. Default Regular tubs need not carry magnet wells. | [Issue #29 floor-mode comment](https://github.com/karyandrew/hutchfinity/issues/29#issuecomment-5612528258) |
| 7 | Floor modes | Support plain/no-grid, integral-grid, and plain-plus-removable-grid modes. The removable insert has no backing floor; cells open to the tub floor. Retain sloped perimeter rail ends and remove only portions that would bridge across edge cells. | [Issue #29 floor-mode comment](https://github.com/karyandrew/hutchfinity/issues/29#issuecomment-5612528258) |
| 8 | Production economics | The current integral-grid slice was reported at about 3.5 hours versus about 5.5 hours for the old tub plus separate grid, while also using less filament and eliminating a separate handling/installation operation. | [Issue #29 floor-mode comment](https://github.com/karyandrew/hutchfinity/issues/29#issuecomment-5612528258) |
| 9 | Prototype identity | 10×10×10h Print 02: `1a2ab09b70989dbb174f9cf0d2a9da5fad26be29a2bdafe6da010a61226957e1`; dual-face rib matrix: `e6eed5c62a8ff23b83302ba2b438192a3282b1df2c32aa531314af69b80101d6`; Regular floor modes revision 05: `d51ba7e090503f02a584c3c4beb71f346adf040f9ec285fce5630111a343e9a3`. | The three issue comments above |

## V&V

Verification:

- Read the current Hutchfinity governing instructions, Gridfinity system PRD, issues #20, #26, #29, and #30, and draft PR #31 before preservation.
- Posted and fetched back the three issue comments listed above.
- Replaced each owning issue's stale top-level `next-route` / `next-action` pair and fetched the resulting issue body back from GitHub.
- Issue #20 now routes canonical reconciliation of the successful small casing/tub and peg results to an agent.
- Issue #29 now identifies a physical `LIVE_TEST` operator action rather than an Owner Queue judgment.
- Issue #30 now routes the plain round-bore coupon build to an agent and explicitly leaves draft PR #31 unchanged pending physical evidence.
- No production SCAD, STL, slicer profile, or active implementation PR was changed by this knowledge harvest.
- No local OpenSCAD, slicer, mesh, or repository-hook command ran in this connector-only wrap. Geometry claims about the unprinted removable insert remain provisional.

Validation status: established

Evidence type: independent-non-behavioral

Evidence: operator-message: first-party physical observations and slicing times in the current session, preserved verbatim in the linked issue comments

Qualification: The operator observations directly test insertion, fit, retention, and print-time behavior of the named physical prototypes. GitHub readback establishes preservation fidelity. This evidence does not validate unprinted geometry, long-term glue durability, furniture-scale strength, or a final production magnet recipe.

Observation: The durable issue records preserve the reported successes, failures, corrections, and open gates without converting prototypes into accepted production source.

Falsifier: A direct operator correction showing that a recorded physical result is wrong, a hash mismatch for a named prototype packet, or later physical testing that contradicts a design proposal would require a corrective record and renewed validation.

Result: pass

## Step matrix

| Step | Result |
|---|---|
| Governing repository and issue state read | ✅ |
| Issue #20 physical result preserved and routing repaired | ✅ |
| Issue #29 low-floor/floor-mode direction preserved and routed to physical test | ✅ |
| Issue #30 magnet result preserved and routed to round-bore coupon | ✅ |
| Draft PR #31 merged or promoted | ⏭️ No — intentionally left draft and unmerged |
| Production SCAD/STL integration | ⏭️ No — physical gates remain |
| Local geometry/slicer checks during wrap | ⏭️ Unavailable on this connector-only surface |
| Public wrap archive | ✅ This file |
| Final carrier merge receipt | Recorded on the wrap carrier PR after landing |

## Verdict

Safe to close · 🅿️ Shelved

The session's useful knowledge and routing are preserved. Implementation is intentionally incomplete because the round-bore coupon, low-floor integral tub, and removable open-bottom insert still require physical validation.

## Reopen criteria

Validator: operator physical testing, followed by deterministic geometry and slicer checks during canonical source integration.

Gating condition: obtain the plain round-bore coupon results; test cup seating, stacking clearance, floor stiffness, and print quality on the low-floor integral-grid tub; test drop-in/removal and edge-cell behavior of the open-bottom sloped-edge insert; then reconcile the winning geometry into canonical source.

Work-state pointer: issues #20, #29, and #30; draft PR #31 remains the unmerged eight-rib carrier pending the magnet decision.
