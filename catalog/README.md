---
sensitivity: public
version: 1.1.0
---

# Neutral item-class catalog

This directory is the public, item-neutral boundary between Hutchfinity bin geometry and an external inventory system. It contains no item names, locations, production quantities, or production authorization.

## Artifacts

- `bin-skus.json` inventories every tracked bin STL. `build_managed` means the current build script names the output; `tracked_unmanaged` means the STL exists but the current script does not reproduce it. The latter is `stale` and is excluded from selection.
- `item-classes.json` contains the four initial public geometry/handling classes. Null dimensions are unknown, not zero.
- `item-class-map.json` is deterministic generated output. Every current mapping is `PROVISIONAL` and has `physical_fit_state: not_run`.
- `schemas/` contains closed JSON Schemas for item classes, bin SKUs, mappings, physical-fit receipts, demand requests, non-authorizing demand manifests, and each serialized dataset wrapper.

Regenerate and test from the repository root:

```sh
python3 scripts/hutchfinity_catalog.py build-catalog --output catalog/bin-skus.json
python3 scripts/hutchfinity_catalog.py select \
  --catalog catalog/bin-skus.json \
  --classes catalog/item-classes.json \
  --output catalog/item-class-map.json
python3 scripts/hutchfinity_catalog.py validate-maps \
  --catalog catalog/bin-skus.json \
  --classes catalog/item-classes.json \
  --maps catalog/item-class-map.json \
  --receipts-dir catalog/physical-fit-receipts
python3 -m unittest discover -s tests -v
```

Every CLI input and generated output is validated with Draft 2020-12 schemas and format checking. The CLI requires the repository's authoritative class set and catalog, recomputes class bindings, resolves selected SKUs, and hashes the referenced source and artifact files. The source/output hashes are exact SHA-256 values. `source_output_link_state: unverified` is deliberate: an existing STL proves that a render exists, but not that its bytes came from the current source revision. A source-only calculation and an STL bounding box are not physical-fit evidence.

## Acceptance and demand boundary

Local `hutchfinity-physical-fit-receipt/v1` JSON can be checked for schema and referential consistency, including class envelope, tested quantity, exact item-class revision, SKU, STL hash, validation lane, and all six physical checks. That caller-controlled JSON cannot prove a physical test or lane validation occurred. This CLI therefore never promotes it to `ACCEPTED`; it fails closed until independently trusted physical and lane evidence is integrated through a separately governed trust boundary.

Demand generation schema-checks requests, rejects nonpositive, Boolean, and noninteger quantities, rejects provisional mappings, and refuses caller-asserted acceptance. Any future manifest remains schema-constrained to `production_authorized: false`; it can communicate neutral demand to downstream planning but cannot dispatch a run, approve manufacturing, or satisfy an external validation/production gate.
