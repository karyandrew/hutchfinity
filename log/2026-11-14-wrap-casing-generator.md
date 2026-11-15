---
type: log
sensitivity: public
date_created: 2026-11-14
date_modified: 2026-11-14
status: blocked
branch: fix/casing-generator-spec
pull_request: https://github.com/karyandrew/hutchfinity/pull/58
---

# Casing generator repair and delivery checkpoint

<!-- sbu-disposition:v1 execution -->

## Summary

PR #58 implements the casing, peg and optional print-context requirements in the current generator, repairs the parameter-boundary and export defects found while exercising that path, and adds failure-handling coverage. The implementation was published as commit `505b02f7199a21a01a9663ce9eb4a9d0a22d6b93`. This checkpoint adds documentation; it does not change the tested generator inputs.

The requested delivery behavior is automatic testing, merge and deployment for eligible PRs. That outcome is **not established**: the repository's trusted CI enrollment and write access remain pending, the PR is open and unmerged, and no installed application update has been observed.

The software checks support the repaired paths described below. Physical fit, stiffness, actual slicing, interactive GUI use and Bambu Studio compatibility remain separate acceptance work. This record does not declare all project issues fixed.

## PKB scope

The durable product decisions are preserved in the existing system specification, chest PRD, generator documentation and validation record. This log preserves the event, evidence boundary and continuation; it does not introduce a new competing specification.

Current authority includes issue #20's slab and chamfered-peg stop decisions and issue #29's optional print-context direction. Those operative comments were reread during the wrap audit. Issue #20 had 38 comments and issue #29 had 15, with no later requirement change observed.

## Knowledge enumeration

- Topic/claim: Casing slab and tub floor defaults are independent — Decision: bank — Reason: the current casing slab defaults to 3.0 mm and tub floor to 1.30 mm, while explicit thinner overrides remain possible; artifact:docs/hutchfinity-spec.md
- Topic/claim: Peg sockets are continuous two-face bores — Decision: bank — Reason: 8.45 mm receiving regions connect through a 7.45 mm stop throat; artifact:docs/hutchfinity-spec.md
- Topic/claim: The insertion stop depends on the peg chamfer — Decision: bank — Reason: straight receiving depth 7.5 mm plus a 0.5 mm taper yields 10 mm tip insertion; a 19.6 mm peg leaves 0.4 mm total axial allowance; artifact:docs/hutchfinity-spec.md
- Topic/claim: Small casing sizes need adapted socket placement and peg counts — Decision: bank — Reason: the shared implementation keeps mouths separate and inside the wall footprint, with two pegs for 1 by 1 and seven for standard sizes; artifact:docs/generator-validation.md
- Topic/claim: Physical fit coupons must match production bore facets — Decision: bank — Reason: current coupons use the production 32-facet bores; higher-resolution mathematical stop checks remain distinct; artifact:docs/generator-validation.md
- Topic/claim: Ordinary generated tubs and casings have no magnet wells — Decision: bank — Reason: legacy wells default off and the held magnet recipe remains outside this repair; artifact:docs/hutchfinity-spec.md
- Topic/claim: Thick-wall, thick-floor and tall-grid extremes exposed malformed geometry — Decision: bank — Reason: folded lofts, detached corner fragments and capped pockets were repaired and exercised together; artifact:docs/generator-validation.md
- Topic/claim: Native indexed 3MF preserves the renderer's topology — Decision: bank — Reason: export retains indexed boundaries and checks finite coordinates, oriented paired edges, volume and connected components; artifact:docs/generator-validation.md
- Topic/claim: Coincident-coordinate or zero-area source boundary faces cannot be silently welded away — Decision: bank — Reason: the four affected cup cases preserve their original facet counts and introduce no additional such faces; artifact:docs/generator-validation.md
- Topic/claim: Optional print context is an allowlisted Orca process import — Decision: bank — Reason: CLI and form support the agreed opt-in workflow while plain geometry remains the default; artifact:docs/generator-validation.md
- Topic/claim: Accessory metadata must cover every instance — Decision: bank — Reason: pegs and pull carry their own mesh/settings metadata with 100 percent rectilinear recommendations, and slab/floor coverage is calculated from actual thickness; artifact:docs/generator-validation.md
- Topic/claim: Complete outputs should replace older builds transactionally — Decision: bank — Reason: staging, locking, rollback, recovery preservation and source/output provenance protect prior builds and user notes; artifact:docs/generator-validation.md
- Topic/claim: Input and startup failures need explicit handling — Decision: bank — Reason: typed input, module routing, renderer capability checks, occupied-port identification and duplicate-submit handling are covered; artifact:docs/generator-validation.md
- Topic/claim: Updates occur on a subsequent clean-main application launch — Decision: bank — Reason: feature/dirty checkouts, ordinary CLI use and an already running process do not establish an updated installation; artifact:log/2026-11-14-wrap-casing-generator.md
- Topic/claim: PRs should automatically merge and deploy after their required checks — Decision: bank — Reason: this requested outcome remains incomplete and is preserved with its exact public boundary here; artifact:log/2026-11-14-wrap-casing-generator.md
- Topic/claim: Earlier prototype success validates the current casing and tub — Decision: skip — Reason: that evidence does not establish the current 44.84 mm tub, 3 mm slab or continuous stop bore.
- Topic/claim: The native Orca round trips establish slicing or physical acceptance — Decision: skip — Reason: they establish import, inspection, export and metadata retention only.
- Topic/claim: The broader batch, basket, cassette and held magnet work is complete — Decision: skip — Reason: these are separate project scopes and no completion claim is made.

Contribution baseline: 80a1fadffeeec18899310bbf038df88eba5f0d1a

The independent audit recomputed the source-input digest, checked the preserved receipts and reread the material issue comments. It found no additional distinct product decision needing a new evergreen page. The existing product documents remain the canonical owners.

The automated novelty check searched fetched main `80a1fadffeeec18899310bbf038df88eba5f0d1a` and returned exit 2, `ASK/REVIEW`, for the following candidates because its separate digest-bound judge was not invoked. These candidates are retained here for review; no novelty authorization or new evergreen-page delivery is claimed. Issue bodies were not supplied to that automated recall pass; the material issue comments were read separately.

| Candidate | Verdict | Proposed existing owner |
|---|---|---|
| Independent 3.0 mm casing / 1.30 mm floor defaults | ASK/REVIEW | docs/hutchfinity-spec.md |
| Chamfer-derived stop in the continuous receiving-region/throat bore | ASK/REVIEW | docs/hutchfinity-spec.md |
| Preserve native indexed 3MF boundary topology | ASK/REVIEW | docs/generator-validation.md |
| Allowlisted optional process import and every accessory instance | ASK/REVIEW | docs/generator-validation.md |
| Staging, locking, rollback and recovery preservation for output replacement | ASK/REVIEW | docs/generator-validation.md |
| Launch-time update is distinct from observed installed adoption | ASK/REVIEW | This checkpoint |

Friction judge: not-selected — the closeout uses bounded independent source/evidence review; no separate friction-judge result is claimed.

## V&V

Validation status: Validation not established
Reason: The requested repair-to-automatic-deployment outcome remains unverified. The execution-start administrative provenance record was not captured, so a complete execution closeout pass cannot be claimed retrospectively.

The scoped software verification is preserved in [the generator validation record](../docs/generator-validation.md). The historical receipts describe the working source based on `80a1fadffeeec18899310bbf038df88eba5f0d1a`; they are not rewritten as runs originally performed at the later publication commit.

| Check | Observed result | Boundary |
|---|---|---|
| Source identity | The 25 Python/SCAD implementation inputs recompute to SHA-256 `583d6909c073d876caec51c0346cb47281b4929d49f83a40f31651cddcb88e48` | Binds implementation bytes; documentation-only additions do not change this digest |
| Full test suite | 58 tests passed, zero skips, 36.366 seconds | Includes live native Manifold checks; not a trusted CI run |
| Native OrcaSlicer 2.5.0 qualification | Twelve import/inspect/export cases passed, with manifold parts, one-component checks and zero reported repair counters | Does not establish actual slicing or GUI behavior |
| HTTP workflow | Plain module, process-bearing extreme module and process-bearing cup builds passed; invalid profiles preserved prior output hashes | Actual HTTP requests; interactive browser workflow remains unverified |
| Serialization | Four affected cups preserved facet counts and indexed boundaries, with no added coincident-coordinate or zero-area faces | Does not claim that all source boundary faces have nonzero area |
| Source review | Independent digest and receipt readback, current governing issue comments, clean pre-wrap checkout and passing diff check | Review supports the stated evidence, not physical acceptance |
| Repository delivery | PR #58 ready/open/unmerged at wrap readback | Automatic CI, merge and installation adoption remain unverified |

Receipt digests:

- Full-suite log: `581ca084f1ba9241507961c0187375201edeb3857851da3c3f8e9e13fdff7ed5`.
- Twelve-case native Orca receipt: `d58a886ee53871a45eb5e47caf6ff24dd78a8d5743102ef20c3f95e250595021`.

Traceability: updated/current — docs/hutchfinity-spec.md and docs/chest-prd.md reflect the casing, peg, floor and print-context requirements implemented in hutchfinity.py, print_settings.py and the current SCAD callers; docs/generator-validation.md records verification and acceptance limits.

Acceptance: no explicit acceptance of physical performance or a deployed installation was obtained.

The portable documentation audit returned exit 0. Its product-PRD metadata advisory was `missing-delivery-disposition` for `docs/chest-prd.md`; this is recorded as an advisory, not a clean full-gate result. The audit reported no applicable wiki/skill architecture changes and no lexical rename pair. The wrap stage-order check passed. Citation resolution is checked against the committed checkpoint after publication. A complete execution-wrap validator result and merged-head receipt remain unavailable for the reasons above.

### Remaining acceptance and continuation

1. Complete the repository's trusted CI enrollment and write access, qualify the exact PR candidate, and observe automatic integration. Do not infer queue success from the absence of checks or from a native auto-merge setting.
2. Verify the actual generator installation adopts the accepted main revision through its documented delivery path.
3. Under issue #20, print and exercise the current whole coupon and matching casing pair: insertion, removal, retention and flush mating.
4. Under issues #29 and #37, verify the current tub slide, bin seating, stacking, pull size/bond and representative slab stiffness. Load rating, creep and production qualification require their own results.
5. Exercise interactive browser and slicer GUI workflows, actual slicing and Bambu Studio compatibility.

The software repair does not close those issues or change the held magnet recipe.

## Step matrix

| Step | State |
|---|---|
| Closeout classification | WORK_HANDOFF |
| Current branch | fix/casing-generator-spec |
| Freshness before wrap authorship | 0 commits behind fetched main; main `80a1fadffeeec18899310bbf038df88eba5f0d1a` |
| Published implementation | `505b02f7199a21a01a9663ce9eb4a9d0a22d6b93` |
| Wrap publication | Documentation-only update on PR #58; final head belongs in the PR metadata after publication |
| CI | Enrollment and repository write access pending |
| Merge | NOT MERGED at observed readback |
| Deployment | No installed-update result observed |
| Governing issues | Read without mutation; physical and separate product scopes remain open |
| Full execution-wrap gate | Not established; missing original kickoff provenance and no merged-head receipt |

External writes: the repair branch/commit and PR #58; PR metadata updates; bounded audit-worker launches. The wrap adds this public checkpoint to the same PR. Infrastructure access attempts and their private continuation are preserved separately; no successful merge or deployment is reported.

Closeability target: this casing-generator conversation.
Separate lifecycle status: PR #58 remains open and unmerged. Physical acceptance stays with the existing product issues; automatic CI and installation adoption remain pending.

## Verdict

❌ DO NOT close — the repair remains unmerged and automatic delivery has not been verified; the missing original execution-start provenance also prevents a complete execution-wrap pass.

Merge status: NOT MERGED — trusted CI enrollment and repository write access remain pending.

## Reopen criteria

Validator: the trusted CI result for the current candidate, observed automatic integration, actual installation revision readback, and the separate physical/slicing checks appropriate to each existing issue.

Gating condition: restore the authenticated repository-access path, complete and qualify enrollment, and continue from the current PR without repeating settled product decisions.

Work-state pointer: https://github.com/karyandrew/hutchfinity/pull/58
