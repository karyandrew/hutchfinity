---
version: 1.0.0
---

# Hutchfinity — repo-specific instructions

## Project

`karyandrew/hutchfinity` is a parametric, modular drawer chest system built around gridfinity-extended tubs at **half-pitch** (21mm XY / 3.5mm Z). General-purpose organizer; not bound to any single application domain. OpenSCAD source; targets FDM printers with ≥256mm² build envelope (A1-tier and up).

System parts: tub (drawer), casing (enclosure), handle (glue-on), peg (inter-casing stack link). Casings stack vertically into chests; tubs slide drawer-style; magnets provide tactile detent. All XY dimensions are derived parametrically from tub cell count + pitch.

## Pre-flight: read at session start

Before acting on any task, load these files in full:

- [`.claude/.cache/second-brain/.claude/rules/shared-rules.md`](.claude/.cache/second-brain/.claude/rules/shared-rules.md) — cross-repo behavioral rules (canonical, fetched at SessionStart)
- [`.claude/.cache/second-brain/.claude/rules/sensitivity.md`](.claude/.cache/second-brain/.claude/rules/sensitivity.md) — sensitivity frontmatter policy

If the cache is missing, the launch wasn't `claude-sb` — pause and surface this before substantive work.

## Dependencies

`karyandrew/second-brain` — canonical cross-repo rules, sensitivity policy, skills, slash commands. Inherited via the `claude-sb` launch wrapper (`CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` + `--add-dir ~/second-brain`). User-level symlink (`~/.claude/commands` → `~/second-brain/.claude/commands`) delivers slash commands. PreToolUse hook `.claude/hooks/guard-second-brain-present.sh` warns if inheritance isn't detected.

## Session Pre-Flight

Open GitHub issues are the sole work-tracking surface (no `TODO.md`). Per second-brain `wiki/pm-via-issue-deps.md`, pick work from the ready set: open issues whose `blockedBy` is empty and which don't carry the `claude-in-progress` label. Use `gh issue list --state open --repo karyandrew/hutchfinity` for titles; read bodies on demand.

## Public Repo

This repo is public from initial commit per [`second-brain/adr/0011-hutchfinity-public-repo.md`](https://github.com/karyandrew/second-brain/blob/main/adr/0011-hutchfinity-public-repo.md). Every commit is composed assuming public exposure. Hygiene baseline:

- No references to private `karyandrew/*` repos
- No domain-specific application context that doxxes the operator
- No addresses, phones, alt-emails
- License: see `LICENSE` (or hutchfinity#1 if not yet picked)

## Git Workflow

Solo dev. Work on a `claude/*` branch, open a PR, merge it with a merge commit (not squash, not rebase), and delete the branch if auto-delete didn't. Canonical rule lives in second-brain `rules/shared-rules.md` → Git Workflow.

## Versioning

Parametric SCAD modules carry semver in their headers. PRDs and reference docs carry frontmatter `version:`. Canonical rule: [second-brain/.claude/rules/versioning.md](https://github.com/karyandrew/second-brain/blob/main/.claude/rules/versioning.md).
