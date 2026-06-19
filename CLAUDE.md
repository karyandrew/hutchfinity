---
version: 1.1.0
---

# Hutchfinity - Claude Instructions

## Project

This repository is a parametric, modular drawer chest system built around Gridfinity Extended at half pitch: 21mm XY and 3.5mm Z. It is a general-purpose organizer project, not a domain-specific deployment.

The authored system parts are:

- `tub.scad` - drawer pan
- `casing.scad` - one-slot enclosure
- `handle.scad` - optional glue-on pull
- `peg.scad` - inter-casing stack link

Casings stack vertically into chests. Tubs slide drawer-style. Optional magnets provide closed retention and an extended-warning detent. All XY dimensions derive parametrically from tub cell count and pitch.

## Public Repository Hygiene

This repository is public. Compose every committed change for public exposure.

Do not add:

- Private-repo references or private workflow dependencies
- Domain-specific deployment context that narrows the project away from a general organizer
- Personal names, contact details, local paths, machine names, or runtime details
- License selections, inferred license policy, or contribution promises that depend on an unresolved license decision

If a useful instruction contains sensitive or private context, rewrite it in public-safe terms instead of preserving the sensitive wording.

## Workflow

Open GitHub issues may be used for work tracking, but do not pick up, sign, label, close, or otherwise mutate issues unless the user explicitly asks for that action.

Use a non-main branch for file changes. Do not commit, push, open a PR, or merge without explicit authorization. Before any commit or PR text, review the diff and public surfaces for local paths, personal details, private references, and domain-specific context.

## Versioning

Parametric SCAD modules carry semver in their headers. PRDs and reference docs carry frontmatter `version:` when they are maintained as versioned artifacts.
