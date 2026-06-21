---
sensitivity: public
date: 2026-06-20
branch: codex/license-gpl3
pr: https://github.com/karyandrew/hutchfinity/pull/16
issue: https://github.com/karyandrew/hutchfinity/issues/1
---

# Wrap: GPLv3 License

## Summary

Resolved the repository license decision by adding GNU GPL v3.0 license text at the project root and documenting third-party license notices for the vendored Gridfinity Extended OpenSCAD source. The README now advertises the license and current upstream dependency accurately, and the vendor note no longer contains stale private-repo wording. PR #16 closes issue #1.

## Knowledge enumeration

| # | Category | Item | Durable artifact |
|---|---|---|---|
| 1 | License/source gotcha | The vendored Gridfinity Extended directory has repo-level GPLv3 text while some embedded utility snippets retain LGPL-3.0 notices; the project notice should preserve both instead of flattening them into one claim. | `THIRD_PARTY_NOTICES.md` |
| 2 | Public-safety cleanup | `VENDOR.md` contained stale private-repo wording adjacent to public license guidance. | `scad/gridfinity/vendor/extended/VENDOR.md` |

## V&V

Verification ran against the branch diff and PR metadata:

- `git diff --check` passed.
- Changed public docs were scanned for local paths, private-repo references, and domain-specific leakage.
- PR #16 was confirmed open, mergeable, non-draft, and linked to close #1.

Validation: Andrew explicitly said `ship it` after reviewing the drafted license change summary.

## Step matrix

✅ Wiki: no new Hutchfinity wiki page needed; license notes live in `THIRD_PARTY_NOTICES.md`
✅ Friction issues filed: none — no separate follow-up needed
⚠️ Friction judge: manual wrap review only — no delegated judge spawned from this Codex session
⚠️ Frontier judge: manual claim verification only — no delegated judge spawned from this Codex session
✅ Wrap log: `log/2026-06-20-wrap-license-gpl3.md` written
✅ Closure comment posted on #1: via PR body `Closes #1`
⏭️ claude-picked removed: N/A — no picked label applied in this session
⏭️ Family pickup: N/A — no absorbed sibling issues
✅ PR #16 — Add GPLv3 license merged → main
✅ Main clone fast-forwarded: Hutchfinity main clone updated after merge
✅ next-N follow-ups: none — scope complete
⏭️ Kickoff marker wiped: N/A — Codex worktree session; teardown is external

## Verdict

✅ Safe to close
