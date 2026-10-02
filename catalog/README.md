---
sensitivity: public
version: 1.2.0
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

The same `consume-admission` decision path validates independently admitted lane and physical-fit evidence, accepted mapping claims, and demand handoffs. Real evidence defaults to `catalog/trust/production-admission.json`, a versioned repository-governed contract with `configuration: unconfigured` and empty profiles, lanes, and admissions. There is no enrolled real evidence. Unrun real mappings remain `PROVISIONAL/not_run`.

The trust grant comes from repository governance of the admission registry, **not** the receipt directory, a receipt PASS field, a signer label, or a matching hash. Deployments must protect the installed code and registry from evidence submitters and review registry changes independently of receipt submission. This is a bounded admission contract, not a signature service or a claim that a writable checkout authenticates its own evidence. Configuring production admission requires an independently governed enrollment decision and observed physical evidence; this change performs neither. No CLI argument or environment variable selects an alternative trust root.

Each admission pins receipt identities, paths, digests, exact neutral class revision, SKU, lane, profile identity/revision/content digest, and minimum representative sample count (at least two). Current governed profiles and lanes must exist and match exactly; revoked, stale, unknown, malformed, duplicate, or unconfigured states refuse. Admitted bytes still undergo semantic validation. Both receipts must bind the current source revision and content, selected output bytes, and the same lane/profile tuple. The lane must attest reproduced source/output linkage, both functional checks, all bin/cup representative checks, and output-bound smallest thin-wall, multi-cell, and tallest artifacts. This contract is scoped to bin/cup selection; it does not accept a large-part lane in its place.

Physical-fit v2 records require all six load, quantity, retrieval, adjacency, base-engagement, and handling checks, the exact selected orientation, sufficient samples and quantity, a known class envelope, and recorded uncertainty covering the required upper envelope without exceeding class uncertainty. Tested quantity cannot exceed calculated capacity. Failed, inconclusive, not-run, stale, incomplete, or workaround-dependent evidence refuses. Source-derived failed/inconclusive candidates cannot be accepted. Legacy v1 local receipts retain consistency diagnostics but confer no trust.

Demand validates the same admission again and preserves authority/revision, receipt, lane, and profile provenance. Every manifest carries `production_authorized: false` and `integrated_system_accepted: false`. Component lanes and fit receipts cannot satisfy the separate integrated artifact-set gate. That physical run remains required after both matching component lanes pass; this consumer does not implement or imply integrated acceptance.

## Synthetic controls and reproduction

`catalog/trust/synthetic-admission.json` is an explicitly isolated test authority. Its receipts are fabricated software fixtures, not observations. Profile and functional-artifact digests are test values. The synthetic mapping and demand request under `receipts/` are test inputs; the actual catalog, class set, and generated mappings remain unchanged. Test admission cannot cross into the real scope. Synthetic decisions say `SYNTHETIC_ACCEPTED`; synthetic manifests retain `evidence_scope: synthetic_test_only`.

From the repository root, with Python and the declared `jsonschema` dependency:

```sh
export PYTHONDONTWRITEBYTECODE=1
# Default real root: exit 2, unconfigured.
python3 scripts/hutchfinity_catalog.py consume-admission --admission-id synthetic-pair-v1
# Same consumer with isolated test enrollment: exit 0.
python3 scripts/hutchfinity_catalog.py consume-admission \
  --evidence-scope synthetic_test_only --admission-id synthetic-pair-v1
# Compatibility alias for the same synthetic consumer.
python3 scripts/hutchfinity_catalog.py consume-synthetic-admission
# Unknown test admission: exit 2.
python3 scripts/hutchfinity_catalog.py consume-admission \
  --evidence-scope synthetic_test_only --admission-id caller-created-pair
# Non-authorizing, synthetic-only demand; writes only a temporary output.
python3 scripts/hutchfinity_catalog.py build-demand \
  --catalog catalog/bin-skus.json --classes catalog/item-classes.json \
  --maps catalog/receipts/synthetic-maps.json \
  --request catalog/receipts/synthetic-demand-request.json \
  --receipts-dir catalog/receipts --evidence-scope synthetic_test_only \
  --output /tmp/hutchfinity-synthetic-demand.json
python3 -m unittest discover -s tests -p 'test_hutchfinity_catalog.py' -v
git diff --check
```

The suite copies the consumer and catalog into an isolated test checkout. It exercises both unadmitted caller changes and deliberately test-enrolled invalid evidence with matching admission digests, proving semantic refusals beyond the hash guard. A second admitted class/SKU pair checks generality and minimum-quantity semantics. No test configures real admission or creates purported real physical receipts.
